"""Authorization regressions with a simulated Supabase service; no model writes."""

from copy import deepcopy
import io
import json
from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest

from accounts import (AccountError, SessionStore, SupabaseAccounts, allowed_parcels,
                      check_password, municipality_key, read_env)
from app import BASE, create_app


PASSWORD = 'PruebaSegura2026!'
STAFF_ID = '11111111-1111-4111-8111-111111111111'
PRODUCER_ID = '22222222-2222-4222-8222-222222222222'


class FakeSupabase:
    def __init__(self):
        self.profiles = {}
        self.credentials = {}
        self.tokens = {}
        self.created = []
        self.available = True
        for uid, role in [(STAFF_ID, 'staff'), (PRODUCER_ID, 'productor')]:
            self.profiles[uid] = dict(id=uid, role=role, email=role + '@example.com', name=role,
                phone='', active=True, access_mode='none', parcel_ids=[], municipalities=[],
                session_version=1, created_at='2026-10-20T00:00:00Z')
            self.credentials[uid] = PASSWORD

    def check(self):
        if not self.available:
            raise AccountError('Servicio no disponible.')

    def issue(self, uid):
        access, refresh = 'access-' + str(uuid4()), 'refresh-' + str(uuid4())
        self.tokens[access] = self.tokens[refresh] = uid
        return dict(access_token=access, refresh_token=refresh, expires_in=3600)

    def sign_in(self, email, password):
        self.check()
        uid = next((u for u, p in self.profiles.items() if p['email'] == email), None)
        if not uid or self.credentials[uid] != password:
            raise AccountError('Correo o contraseña incorrectos.', 401)
        return self.issue(uid)

    def refresh(self, token):
        self.check()
        if token not in self.tokens:
            raise AccountError('Sesión inválida.', 401)
        return self.issue(self.tokens[token])

    def get_user(self, token):
        self.check()
        uid = self.tokens.get(token)
        if uid not in self.profiles:
            raise AccountError('Sesión inválida.', 401)
        return {'id': uid}

    def sign_out(self, token):
        self.tokens.pop(token, None)

    def profile(self, uid, token=None, admin=False):
        self.check()
        if not admin:
            assert self.tokens.get(token) == uid  # User reads must carry the user's JWT.
        return deepcopy(self.profiles.get(uid))

    def list_profiles(self, offset=0, limit=51):
        self.check()
        return deepcopy(list(self.profiles.values())[offset:offset + limit])

    def create(self, email, password, fields, role='productor'):
        if any(p['email'] == email for p in self.profiles.values()):
            raise AccountError('Ese correo ya está registrado.', 409)
        uid = str(uuid4())
        self.created.append(uid)
        self.profiles[uid] = dict(id=uid, email=email, role=role, session_version=1,
                                  created_at='2026-10-20T00:00:00Z', **deepcopy(fields))
        self.credentials[uid] = password
        return uid

    def update_profile(self, uid, fields):
        if self.profiles[uid]['active'] != fields['active']:
            self.revoke_sessions(uid)
        self.profiles[uid].update(deepcopy(fields))

    def revoke_sessions(self, uid):
        self.profiles[uid]['session_version'] += 1

    def update_credentials(self, uid, email, password=''):
        self.revoke_sessions(uid)
        self.profiles[uid]['email'] = email
        if password:
            self.credentials[uid] = password

    def delete(self, uid):
        del self.profiles[uid]


@pytest.fixture
def setup(tmp_path):
    backend = FakeSupabase()
    app = create_app({'TESTING': True, 'SECRET_KEY': 'account-test-secret',
                      'ACCOUNT_BACKEND': backend, 'AUTH_SESSION_DB': tmp_path / 'sessions.sqlite3'})
    catalog = json.loads((BASE / 'artifacts/dashboard.json').read_text(encoding='utf8'))['parcels']
    return app, backend, catalog


def csrf(client):
    with client.session_transaction() as cookie:
        return cookie['csrf_token']


def login(client, role='staff', email=None, password=PASSWORD):
    client.get('/login/' + role)
    return client.post('/login/' + role, data={'email': email or role + '@example.com',
                                             'password': password, 'csrf_token': csrf(client)})


def fields(client, **kwargs):
    return {**dict(csrf_token=csrf(client), name='Productor actualizado', phone='5551231234',
                   active='yes', access_mode='none'), **kwargs}


def test_no_demo_fallback_or_forged_role(setup):
    app, backend, _ = setup
    client = app.test_client()
    assert client.get('/api/parcels').status_code == 401
    with client.session_transaction() as cookie:
        cookie['role'] = 'staff'
    assert client.get('/api/dashboard').status_code == 401
    assert login(client, 'staff', 'ejemplotecnico@ejemplo.com', '123Tecnico#').status_code == 401
    assert login(client, 'staff').status_code == 302
    backend.available = False
    assert client.get('/api/parcels').status_code == 503


def test_login_csrf_wrong_role_disabled_unknown_user(setup):
    app, backend, _ = setup
    client = app.test_client()
    assert client.post('/login/staff', data={'email': 'staff@example.com', 'password': PASSWORD}).status_code == 400
    assert login(client, 'staff', 'productor@example.com').status_code == 401
    backend.profiles[PRODUCER_ID]['active'] = False
    assert login(client, 'productor').status_code == 401
    assert client.get('/login/admin').status_code == 404


@pytest.mark.parametrize('mode', ['none', 'selected', 'municipalities', 'all'])
def test_parcel_list_detail_geometry_have_same_authorization(setup, mode):
    app, backend, catalog = setup
    profile = backend.profiles[PRODUCER_ID]
    profile.update(access_mode=mode, parcel_ids=[catalog[0]['id']],
                   municipalities=[{k: catalog[1][k] for k in ('state', 'municipality')}])
    expected = {p['id'] for p in allowed_parcels(profile, catalog)}
    client = app.test_client()
    assert login(client, 'productor').status_code == 302
    assert {p['id'] for p in client.get('/api/parcels').json} == expected
    assert {f['properties']['ID_POLIGONO'] for f in client.get('/api/geometry').json['features']} == expected
    for p in catalog:
        response = client.get('/api/parcels/' + p['id'])
        assert response.status_code == (200 if p['id'] in expected else 404)
        if response.status_code == 200:
            assert all(h['id'] == p['id'] for h in response.json['history'])
    assert {p['id'] for p in client.get('/api/parcels?search=AGC').json} <= expected
    for path in ['/staff', '/staff/usuarios', '/api/dashboard', '/api/risk/context', '/export/predictions.csv']:
        assert client.get(path).status_code == 403


def test_municipality_scope_also_checks_state():
    rows = [dict(id='A', state='Estado A', municipality='San Pedro'),
            dict(id='B', state='Estado B', municipality='San Pedro')]
    profile = dict(role='productor', access_mode='municipalities',
                   municipalities=[dict(state='Estado A', municipality='San Pedro')])
    assert [p['id'] for p in allowed_parcels(profile, rows)] == ['A']


def test_staff_keeps_full_catalog_and_existing_views(setup):
    app, _, catalog = setup
    client = app.test_client()
    login(client)
    assert len(client.get('/api/parcels').json) == len(catalog)
    assert len(client.get('/api/dashboard').json['parcels']) == len(catalog)
    assert len(client.get('/api/geometry').json['features']) == len(catalog)
    assert client.get('/export/predictions.csv').status_code == 200
    for section in ['', '/predicciones', '/riesgo', '/validacion', '/factores', '/metodologia']:
        response = client.get('/staff' + section)
        assert response.status_code == 200
        assert '/staff/usuarios' in response.text


def test_permissions_updated_during_existing_session(setup):
    app, backend, catalog = setup
    client = app.test_client()
    login(client, 'productor')
    assert client.get('/api/parcels').json == []
    profile = backend.profiles[PRODUCER_ID]
    profile.update(access_mode='selected', parcel_ids=[catalog[0]['id']])
    assert [p['id'] for p in client.get('/api/parcels').json] == [catalog[0]['id']]
    profile.update(access_mode='none', parcel_ids=[])
    assert client.get('/api/parcels/' + catalog[0]['id']).status_code == 404
    profile['active'] = False
    assert client.get('/api/parcels').status_code == 401


def test_roles_are_revalidated_without_trusting_cookie(setup):
    app, backend, _ = setup
    client = app.test_client()
    login(client)
    backend.profiles[STAFF_ID]['role'] = 'productor'
    assert client.get('/staff/usuarios').status_code == 403


def test_crud_with_assignments_and_no_role_escalation(setup):
    app, backend, catalog = setup
    client = app.test_client()
    login(client)
    assert client.get('/staff/usuarios').status_code == 200
    assert client.get('/staff/usuarios/nuevo').status_code == 200
    response = client.post('/staff/usuarios/nuevo', data=fields(client, email='nuevo@example.com',
        password=PASSWORD, role='staff', parcel_ids=[catalog[0]['id']], access_mode='selected'))
    assert response.status_code == 303
    uid = backend.created[0]
    assert backend.profiles[uid]['role'] == 'productor'
    assert backend.profiles[uid]['parcel_ids'] == [catalog[0]['id']]
    place = municipality_key(catalog[1])
    response = client.post(f'/staff/usuarios/{uid}/editar', data=fields(client,
        access_mode='municipalities', municipalities=[place], parcel_ids=[catalog[0]['id']]))
    assert response.status_code == 303
    assert backend.profiles[uid]['parcel_ids'] == []
    assert backend.profiles[uid]['municipalities'] == [
        {'state': catalog[1]['state'], 'municipality': catalog[1]['municipality']}]
    response = client.post(f'/staff/usuarios/{uid}/editar', data=fields(client, access_mode='all'))
    assert response.status_code == 303
    assert backend.profiles[uid]['municipalities'] == []
    assert client.post(f'/staff/usuarios/{uid}/eliminar', data={
        'csrf_token': csrf(client), 'confirm_email': 'wrong@example.com'}).status_code == 303
    assert uid in backend.profiles
    assert client.post(f'/staff/usuarios/{uid}/eliminar', data={
        'csrf_token': csrf(client), 'confirm_email': 'nuevo@example.com'}).status_code == 303
    assert uid not in backend.profiles


@pytest.mark.parametrize('extra', [dict(access_mode='selected', parcel_ids=['UNKNOWN']),
    dict(access_mode='municipalities', municipalities=['unknown']), dict(access_mode='all-evil'),
    dict(access_mode='selected'), dict(access_mode='municipalities'), dict(name='')])
def test_invalid_profile_and_assignments_are_rejected(setup, extra):
    app, backend, _ = setup
    client = app.test_client()
    login(client)
    payload = fields(client, email='new@example.com', password=PASSWORD)
    payload.update(extra)
    assert client.post('/staff/usuarios/nuevo', data=payload).status_code == 400
    assert not backend.created


def test_duplicate_email_does_not_create_another_user(setup):
    app, backend, _ = setup
    client = app.test_client()
    login(client)
    assert client.post('/staff/usuarios/nuevo', data=fields(client,
        email='productor@example.com', password=PASSWORD)).status_code == 409
    assert not backend.created


@pytest.mark.parametrize('suffix', ['/editar', '/acceso', '/eliminar'])
def test_staff_accounts_cannot_be_changed_via_producer_routes(setup, suffix):
    app, _, _ = setup
    client = app.test_client()
    login(client)
    assert client.post(f'/staff/usuarios/{STAFF_ID}{suffix}', data=fields(client)).status_code == 404
    assert client.post(f'/staff/usuarios/not-a-uuid{suffix}', data=fields(client)).status_code == 404


@pytest.mark.parametrize('path', ['/staff/usuarios/nuevo', f'/staff/usuarios/{PRODUCER_ID}/editar',
    f'/staff/usuarios/{PRODUCER_ID}/acceso', f'/staff/usuarios/{PRODUCER_ID}/eliminar'])
def test_all_account_mutations_require_csrf_and_staff(setup, path):
    app, backend, _ = setup
    client = app.test_client()
    login(client)
    assert client.post(path, data={'csrf_token': 'forged'}).status_code == 400
    producer_client = app.test_client()
    login(producer_client, 'productor')
    assert producer_client.post(path, data=fields(producer_client)).status_code == 403
    assert not backend.created


def test_credentials_change_revokes_existing_sessions(setup):
    app, backend, _ = setup
    producer_client, client = app.test_client(), app.test_client()
    login(producer_client, 'productor')
    login(client)
    response = client.post(f'/staff/usuarios/{PRODUCER_ID}/acceso', data={
        'csrf_token': csrf(client), 'email': 'changed@example.com', 'password': 'NuevaSegura2026!'})
    assert response.status_code == 303
    assert producer_client.get('/api/parcels').status_code == 401
    assert login(producer_client, 'productor').status_code == 401
    assert login(producer_client, 'productor', 'changed@example.com', 'NuevaSegura2026!').status_code == 302


def test_deletion_and_suspension_revoke_sessions(setup):
    app, backend, _ = setup
    producer_client, staff_client = app.test_client(), app.test_client()
    login(producer_client, 'productor')
    login(staff_client)
    payload = fields(staff_client)
    payload.pop('active')
    assert staff_client.post(f'/staff/usuarios/{PRODUCER_ID}/editar', data=payload).status_code == 303
    assert producer_client.get('/api/parcels').status_code == 401
    backend.profiles[PRODUCER_ID]['active'] = True
    login(producer_client, 'productor')
    assert staff_client.post(f'/staff/usuarios/{PRODUCER_ID}/eliminar', data={
        'csrf_token': csrf(staff_client), 'confirm_email': 'productor@example.com'}).status_code == 303
    assert producer_client.get('/api/parcels').status_code == 401


def test_logout_blocks_cookie_replay_and_tokens_are_server_side(setup):
    app, _, _ = setup
    client = app.test_client()
    login(client)
    cookie = client.get_cookie('session').value
    with client.session_transaction() as values:
        assert set(values) == {'auth_sid', 'csrf_token', 'role', '_permanent'}
    assert client.post('/logout', data={'csrf_token': csrf(client)}).status_code == 302
    client.set_cookie('session', cookie)
    assert client.get('/api/parcels').status_code == 401


def test_session_refresh_and_absolute_expiration(setup):
    app, backend, _ = setup
    client = app.test_client()
    login(client)
    store = app.extensions['account_sessions']
    with store.connect() as db:
        before = db.execute('SELECT access_token FROM auth_sessions').fetchone()[0]
        db.execute('UPDATE auth_sessions SET token_expires=0')
    assert client.get('/api/parcels').status_code == 200
    with store.connect() as db:
        assert db.execute('SELECT access_token FROM auth_sessions').fetchone()[0] != before
        db.execute('UPDATE auth_sessions SET expires=0')
    assert client.get('/api/parcels').status_code == 401


def test_login_limit_persists_across_app_instances(setup):
    app, backend, _ = setup
    client = app.test_client()
    for _ in range(10):
        assert login(client, password='incorrect').status_code == 401
    other = create_app({'TESTING': True, 'SECRET_KEY': 'other', 'ACCOUNT_BACKEND': backend,
                        'AUTH_SESSION_DB': app.extensions['account_sessions'].path}).test_client()
    assert login(other).status_code == 429


def test_security_headers_and_template_escaping(setup):
    app, backend, _ = setup
    backend.profiles[PRODUCER_ID]['name'] = '<script>alert(1)</script>'
    client = app.test_client()
    login(client)
    response = client.get('/staff/usuarios')
    assert '<script>alert(1)</script>' not in response.text
    assert '&lt;script&gt;' in response.text
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert "default-src 'self'" in response.headers['Content-Security-Policy']
    assert 'HttpOnly' in response.headers.get('Set-Cookie', '')


def test_password_validation():
    for invalid in ['123Abc!', 'a' * 20, 'A' * 20, 'Abcdefghijk123', 'aA1!' * 40]:
        with pytest.raises(AccountError):
            check_password(invalid)
    assert check_password(PASSWORD) == PASSWORD


def test_env_is_literal_and_environment_wins(tmp_path, monkeypatch):
    path = tmp_path / '.env'
    path.write_text('SUPABASE_URL="https://example.supabase.co"\nX_LITERAL=$(evil)\n', encoding='utf8')
    monkeypatch.setenv('SUPABASE_URL', 'https://other.supabase.co')
    assert read_env(path)['SUPABASE_URL'] == 'https://other.supabase.co'
    assert read_env(path)['X_LITERAL'] == '$(evil)'


def test_transport_uses_correct_key_scope_and_never_echoes_secrets():
    backend = SupabaseAccounts(dict(SUPABASE_URL='https://example.supabase.co',
                                   SUPABASE_PUBLISHABLE_KEY='sb_publishable_TEST', SUPABASE_SECRET_KEY='sb_secret_TEST'))
    calls = []

    class HTTP:
        def open(self, req, timeout):
            calls.append(req)
            return io.BytesIO(b'[]')

    backend.http = HTTP()
    backend.profile(PRODUCER_ID, token='user-jwt')
    req = calls[-1]
    assert req.get_header('Apikey') == 'sb_publishable_TEST'
    assert req.get_header('Authorization') == 'Bearer user-jwt'
    backend.list_profiles()
    assert calls[-1].get_header('Apikey') == 'sb_secret_TEST'
    assert calls[-1].get_header('Authorization') is None


@pytest.mark.parametrize('error, status', [
    (HTTPError('https://example.supabase.co', 400, 'bad', {}, io.BytesIO(b'{"error_code":"invalid_credentials","message":"sb_secret_DO_NOT_ECHO"}')), 401),
    (HTTPError('https://example.supabase.co', 404, 'missing', {}, io.BytesIO(b'{"code":"PGRST205"}')), 503),
    (URLError('sb_secret_DO_NOT_ECHO'), 503)])
def test_transport_errors_are_sanitized(error, status):
    backend = SupabaseAccounts(dict(SUPABASE_URL='https://example.supabase.co',
                                   SUPABASE_PUBLISHABLE_KEY='public', SUPABASE_SECRET_KEY='secret'))

    class HTTP:
        def open(self, *args, **kwargs):
            raise error

    backend.http = HTTP()
    with pytest.raises(AccountError) as result:
        backend.sign_in('user@example.com', 'password')
    assert result.value.status == status
    assert 'DO_NOT_ECHO' not in str(result.value)


def test_unconfigured_supabase_fails_closed():
    with pytest.raises(AccountError) as result:
        SupabaseAccounts({}).sign_in('user@example.com', PASSWORD)
    assert result.value.status == 503
