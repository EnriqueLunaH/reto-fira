"""Supabase identity and account administration. No prediction/model dependencies."""

import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import string
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from uuid import UUID


class AccountError(Exception):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def read_env(path):
    """Read literal KEY=value settings; never execute shell substitutions."""
    values = {}
    if Path(path).is_file():
        for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, sep, value = line.partition('=')
            if sep and re.fullmatch(r'[A-Z][A-Z0-9_]*', key.strip()):
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key.strip()] = value
    # Environment variables take precedence over a local file.
    return {**values, **os.environ}


def user_id(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise AccountError('Usuario no encontrado.', 404) from None


def email_address(value):
    value = value.strip().lower()
    if len(value) > 254 or not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', value):
        raise AccountError('Escribe un correo electrónico válido.', 400)
    return value


def check_password(value):
    if not 12 <= len(value) <= 128 or not all((re.search(r'[a-z]', value),
            re.search(r'[A-Z]', value), re.search(r'[0-9]', value), any(c in string.punctuation for c in value))):
        raise AccountError('La contraseña debe tener de 12 a 128 caracteres e incluir mayúscula, minúscula, número y símbolo.', 400)
    return value


def profile_fields(form, parcels):
    """Validate assignments against the existing, read-only parcel catalog."""
    name = form.get('name', '').strip()
    phone = form.get('phone', '').strip()
    if not name or len(name) > 120 or len(phone) > 40:
        raise AccountError('El nombre es obligatorio (máximo 120 caracteres); el teléfono admite hasta 40.', 400)
    mode = form.get('access_mode', 'none')
    if mode not in {'none', 'selected', 'municipalities', 'all'}:
        raise AccountError('Selecciona un tipo de acceso válido.', 400)
    ids = sorted(set(form.getlist('parcel_ids'))) if mode == 'selected' else []
    chosen = sorted(set(form.getlist('municipalities'))) if mode == 'municipalities' else []
    catalog = {municipality_key(p): {'state': p['state'], 'municipality': p['municipality']} for p in parcels}
    if set(ids) - {p['id'] for p in parcels} or set(chosen) - catalog.keys():
        raise AccountError('La selección contiene parcelas o municipios desconocidos.', 400)
    if (mode == 'selected' and not ids) or (mode == 'municipalities' and not chosen):
        raise AccountError('Selecciona al menos una parcela o un municipio.', 400)
    return dict(name=name, phone=phone, active=form.get('active') == 'yes', access_mode=mode,
                parcel_ids=ids, municipalities=[catalog[key] for key in chosen])


def municipality_key(parcel):
    return json.dumps([parcel['state'], parcel['municipality']], ensure_ascii=False, separators=(',', ':'))


def allowed_parcels(profile, parcels):
    if profile['role'] == 'staff' or profile['access_mode'] == 'all':
        return parcels
    if profile['access_mode'] == 'selected':
        ids = set(profile['parcel_ids'])
        return [p for p in parcels if p['id'] in ids]
    if profile['access_mode'] == 'municipalities':
        places = {(m['state'], m['municipality']) for m in profile['municipalities']}
        return [p for p in parcels if (p['state'], p['municipality']) in places]
    return []


class NoRedirect(HTTPRedirectHandler):
    # Never forward a Supabase credential to a redirected host.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class SupabaseAccounts:
    def __init__(self, settings):
        self.url = settings.get('SUPABASE_URL', '').rstrip('/')
        self.public_key = settings.get('SUPABASE_PUBLISHABLE_KEY') or settings.get('SUPABASE_ANON_KEY', '')
        self.secret_key = settings.get('SUPABASE_SECRET_KEY') or settings.get('SUPABASE_SERVICE_ROLE_KEY', '')
        parsed = urlsplit(self.url)
        self.configured = bool(self.public_key and self.secret_key and parsed.scheme == 'https'
                               and parsed.hostname and not parsed.username and not parsed.password
                               and not parsed.query and not parsed.fragment and parsed.path in ('', '/'))
        self.http = build_opener(NoRedirect())

    def _request(self, method, path, body=None, *, token=None, admin=False, query=None):
        if not self.configured:
            raise AccountError('Falta configurar Supabase. Consulta docs/usuarios-supabase.md.')
        key = self.secret_key if admin else self.public_key
        headers = {'apikey': key, 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        elif admin and key.startswith('eyJ'):
            headers['Authorization'] = 'Bearer ' + key
        url = self.url + path + (('?' + urlencode(query)) if query else '')
        req = Request(url, data=json.dumps(body).encode('utf-8') if body is not None else None,
                      headers=headers, method=method)
        try:
            with self.http.open(req, timeout=12) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read())
            except (ValueError, OSError):
                payload = {}
            code = payload.get('error_code') or payload.get('code')
            if code in {'PGRST205', 'PGRST202', '42P01'}:
                raise AccountError('Falta ejecutar la migración de cuentas en el SQL Editor de Supabase: supabase/migrations/202610200001_accounts.sql.') from None
            if code in {'email_exists', 'email_exists_in_another_user', 'user_already_exists', '23505'}:
                raise AccountError('Ese correo ya está registrado.', 409) from None
            if code == 'weak_password':
                raise AccountError('Supabase rechazó la contraseña. Usa una contraseña más segura.', 400) from None
            if exc.code == 429:
                raise AccountError('Demasiados intentos. Espera unos minutos.', 429) from None
            if not admin and exc.code in (400, 401, 403, 422):
                raise AccountError('Correo, contraseña o sesión no válidos.', 401) from None
            raise AccountError('No se pudo completar la operación con Supabase. Revisa la configuración o inténtalo de nuevo.') from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise AccountError('Supabase no está disponible. Inténtalo de nuevo.') from None

    def sign_in(self, email, password):
        return self._request('POST', '/auth/v1/token', {'email': email, 'password': password},
                             query={'grant_type': 'password'})

    def refresh(self, refresh_token):
        return self._request('POST', '/auth/v1/token', {'refresh_token': refresh_token},
                             query={'grant_type': 'refresh_token'})

    def get_user(self, token):
        return self._request('GET', '/auth/v1/user', token=token)

    def sign_out(self, token):
        return self._request('POST', '/auth/v1/logout', token=token, query={'scope': 'local'})

    def profile(self, uid, token=None, admin=False):
        rows = self._request('GET', '/rest/v1/user_profiles', token=token, admin=admin,
                             query={'id': 'eq.' + user_id(uid), 'select': '*', 'limit': 1})
        return rows[0] if rows else None

    def list_profiles(self, offset=0, limit=51):
        return self._request('GET', '/rest/v1/user_profiles', admin=True,
                             query={'select': '*', 'order': 'created_at.desc,id.asc', 'offset': offset, 'limit': limit})

    def update_profile(self, uid, fields):
        self._request('PATCH', '/rest/v1/user_profiles', fields, admin=True,
                      query={'id': 'eq.' + user_id(uid)})

    def revoke_sessions(self, uid):
        self._request('POST', '/rest/v1/rpc/revoke_app_sessions', {'target_id': user_id(uid)}, admin=True)

    def create(self, email, password, fields, role='productor'):
        result = self._request('POST', '/auth/v1/admin/users',
                               {'email': email, 'password': password, 'email_confirm': True}, admin=True)
        uid = (result.get('user') or result)['id']
        try:
            self._request('POST', '/rest/v1/user_profiles',
                          {**fields, 'id': uid, 'email': email, 'role': role}, admin=True)
        except AccountError:
            # An identity without a profile has no app access. Remove the orphan when possible.
            try:
                self.delete(uid)
            except AccountError:
                raise AccountError('El alta quedó incompleta. No tiene acceso. Revisa Authentication → Users en Supabase antes de reintentar.') from None
            raise
        return uid

    def update_credentials(self, uid, email, password=''):
        # Revoke existing app sessions before changing credentials, including on remote failure.
        self.revoke_sessions(uid)
        fields = {'email': email, 'email_confirm': True}
        if password:
            fields['password'] = password
        self._request('PUT', '/auth/v1/admin/users/' + user_id(uid), fields, admin=True)
        # Email is synchronized transactionally by the auth.users trigger in the migration.

    def delete(self, uid):
        self.revoke_sessions(uid)
        self._request('DELETE', '/auth/v1/admin/users/' + user_id(uid), admin=True)


class SessionStore:
    """Opaque browser sessions and atomic login limits shared by local workers.

    Tokens remain in the private server instance directory, never in a Flask cookie.
    The SQLite transaction serializes refresh-token rotation across concurrent requests.
    """
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    sid TEXT PRIMARY KEY, user_id TEXT NOT NULL, access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL, token_expires REAL NOT NULL,
                    expires REAL NOT NULL, version INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS auth_session_user ON auth_sessions(user_id);
                CREATE TABLE IF NOT EXISTS login_attempts (bucket TEXT NOT NULL, stamp REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS login_attempt_bucket ON login_attempts(bucket, stamp);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=45)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode()).hexdigest()

    def reserve_attempt(self, address, email):
        now = time.time()
        buckets = [(self.digest('ip:' + address), 30), (self.digest('email:' + email), 10)]
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM login_attempts WHERE stamp < ?', (now - 300,))
            for bucket, maximum in buckets:
                count = db.execute('SELECT count(*) FROM login_attempts WHERE bucket=?', (bucket,)).fetchone()[0]
                if count >= maximum:
                    raise AccountError('Demasiados intentos. Espera cinco minutos.', 429)
            db.executemany('INSERT INTO login_attempts VALUES (?,?)', [(b, now) for b, _ in buckets])

    def create(self, tokens, profile):
        sid, now = secrets.token_urlsafe(48), time.time()
        with self.connect() as db:
            db.execute('DELETE FROM auth_sessions WHERE expires <= ?', (now,))
            db.execute('INSERT INTO auth_sessions VALUES (?,?,?,?,?,?,?)',
                       (self.digest(sid), profile['id'], tokens['access_token'], tokens['refresh_token'],
                        now + tokens.get('expires_in', 3600), now + 8 * 3600, profile['session_version']))
        return sid

    def resolve(self, sid, backend):
        if not sid:
            return None
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM auth_sessions WHERE sid=?', (self.digest(sid),)).fetchone()
            if not row:
                return None
            if row['expires'] <= time.time():
                db.execute('DELETE FROM auth_sessions WHERE sid=?', (row['sid'],))
                return None
            token = row['access_token']
            try:
                if row['token_expires'] <= time.time() + 60:
                    tokens = backend.refresh(row['refresh_token'])
                    token = tokens['access_token']
                    db.execute('UPDATE auth_sessions SET access_token=?,refresh_token=?,token_expires=? WHERE sid=?',
                               (token, tokens['refresh_token'], time.time() + tokens.get('expires_in', 3600), row['sid']))
            except AccountError as exc:
                if exc.status != 401:
                    raise
                db.execute('DELETE FROM auth_sessions WHERE sid=?', (row['sid'],))
                return None
        # Network identity/profile reads do not hold the shared SQLite write lock.
        # A completed refresh has already committed, even if the next call fails.
        try:
            identity = backend.get_user(token)
            profile = backend.profile(identity['id'], token=token)
        except AccountError as exc:
            if exc.status != 401:
                raise
            self.pop(sid)
            return None
        if (not profile or identity['id'] != row['user_id'] or not profile['active']
                or profile['role'] not in ('staff', 'productor') or profile['session_version'] != row['version']):
            self.pop(sid)
            return None
        return profile

    def pop(self, sid):
        if not sid:
            return None
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT access_token FROM auth_sessions WHERE sid=?', (self.digest(sid),)).fetchone()
            db.execute('DELETE FROM auth_sessions WHERE sid=?', (self.digest(sid),))
            return row['access_token'] if row else None

    def revoke_user(self, uid):
        with self.connect() as db:
            db.execute('DELETE FROM auth_sessions WHERE user_id=?', (uid,))
