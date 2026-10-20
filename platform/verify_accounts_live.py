"""Exercise account CRUD and RLS against configured Supabase using one disposable user.

Never prints credentials or tokens. Does not read/write model code or recalculate data.
Requires the local credentials file created by manage_accounts bootstrap.
"""

from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
from uuid import uuid4

from accounts import AccountError, SupabaseAccounts, municipality_key, read_env
from app import create_app


BASE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def initial_staff():
    path = BASE / '.instance/initial-accounts.txt'
    lines = path.read_text(encoding='utf8').splitlines()
    index = lines.index('staff')
    return lines[index + 1].split(': ', 1)[1], lines[index + 2].split(': ', 1)[1]


def main():
    backend = SupabaseAccounts(read_env(BASE / '.env'))
    email, password = initial_staff()
    uid = None
    anonymous_or_user_tokens = []
    app = None
    try:
        with TemporaryDirectory(prefix='nas-accounts-') as temporary:
            app = create_app({'TESTING': True, 'SECRET_KEY': secrets.token_hex(32),
                              'AUTH_SESSION_DB': Path(temporary) / 'sessions.sqlite3', 'ACCOUNT_BACKEND': backend})
            staff = app.test_client()
            staff.get('/login/staff')

            def csrf(client):
                with client.session_transaction() as cookie:
                    return cookie['csrf_token']

            require(staff.post('/login/staff', data={'email': email, 'password': password,
                    'csrf_token': csrf(staff)}).status_code == 302, 'Falló el acceso real de staff.')
            require(staff.get('/staff/usuarios').status_code == 200, 'Falló el listado de usuarios.')
            catalog = staff.get('/api/parcels').json
            target = catalog[0]
            hidden = next(p for p in catalog if p['id'] != target['id'])
            test_email = 'nas-qa-' + uuid4().hex + '@example.com'
            test_password = secrets.token_urlsafe(24) + 'aA1!'
            payload = dict(csrf_token=csrf(staff), name='Prueba temporal de integración NAS', phone='',
                           email=test_email, password=test_password, active='yes',
                           access_mode='selected', parcel_ids=[target['id']])
            response = staff.post('/staff/usuarios/nuevo', data=payload)
            require(response.status_code == 303, 'Falló el alta de productor desde el formulario.')
            matches = backend._request('GET', '/rest/v1/user_profiles', admin=True,
                                        query={'email': 'eq.' + test_email, 'select': '*'})
            require(len(matches) == 1, 'No se encontró el productor creado.')
            uid = matches[0]['id']
            require(matches[0]['role'] == 'productor', 'Rol incorrecto en el alta.')

            def producer_login(client, supplied_password=test_password):
                client.get('/login/productor')
                require(client.post('/login/productor', data={'email': test_email, 'password': supplied_password,
                        'csrf_token': csrf(client)}).status_code == 302, 'Falló el acceso real del productor.')

            producer = app.test_client()
            producer_login(producer)
            require([p['id'] for p in producer.get('/api/parcels').json] == [target['id']], 'El listado filtró incorrectamente.')
            require(producer.get('/api/parcels/' + hidden['id']).status_code == 404, 'El detalle expuso una parcela ajena.')
            ids = {f['properties']['ID_POLIGONO'] for f in producer.get('/api/geometry').json['features']}
            require(ids == {target['id']}, 'La geometría expuso parcelas ajenas.')
            require(producer.get('/staff/usuarios').status_code == 403, 'El productor pudo abrir el CRUD.')

            direct = backend.sign_in(test_email, test_password)
            anonymous_or_user_tokens.append(direct['access_token'])
            token = direct['access_token']
            rows = backend._request('GET', '/rest/v1/user_profiles', token=token)
            require(len(rows) == 1 and rows[0]['id'] == uid, 'RLS permitió leer perfiles ajenos.')
            for method, path, body, request_token in [
                ('GET', '/rest/v1/user_profiles', None, None),
                ('PATCH', '/rest/v1/user_profiles?id=eq.' + uid, {'role': 'staff'}, token),
                ('POST', '/rest/v1/rpc/revoke_app_sessions', {'target_id': uid}, token),
            ]:
                try:
                    backend._request(method, path, body, token=request_token)
                except AccountError as error:
                    require(error.status == 401, 'RLS no respondió con denegación de permisos.')
                else:
                    raise RuntimeError('RLS permitió una operación sin privilegios.')

            edit = f'/staff/usuarios/{uid}/editar'
            for mode, extra, expected in [
                ('municipalities', {'municipalities': [municipality_key(target)]},
                 {p['id'] for p in catalog if (p['state'], p['municipality']) == (target['state'], target['municipality'])}),
                ('all', {}, {p['id'] for p in catalog}), ('none', {}, set()),
            ]:
                require(staff.post(edit, data={'csrf_token': csrf(staff), 'name': 'Prueba temporal actualizada',
                        'active': 'yes', 'access_mode': mode, **extra}).status_code == 303, 'Falló la actualización de permisos.')
                require({p['id'] for p in producer.get('/api/parcels').json} == expected,
                        'Los nuevos permisos no se aplicaron a una sesión existente.')

            new_password = secrets.token_urlsafe(24) + 'aA1!'
            require(staff.post(f'/staff/usuarios/{uid}/acceso', data={'csrf_token': csrf(staff),
                    'email': test_email, 'password': new_password}).status_code == 303, 'Falló el cambio de credenciales.')
            require(producer.get('/api/parcels').status_code == 401, 'El cambio de contraseña no invalidó la sesión.')
            producer_login(producer, new_password)
            require(staff.post(edit, data={'csrf_token': csrf(staff), 'name': 'Prueba temporal suspendida',
                    'access_mode': 'none'}).status_code == 303, 'Falló la suspensión.')
            require(producer.get('/api/parcels').status_code == 401, 'El usuario suspendido conservó acceso.')
            require(staff.post(f'/staff/usuarios/{uid}/eliminar', data={'csrf_token': csrf(staff),
                    'confirm_email': test_email}).status_code == 303, 'Falló la eliminación.')
            require(backend.profile(uid, admin=True) is None, 'Quedó un perfil después de eliminar.')
            uid = None
            staff.post('/logout', data={'csrf_token': csrf(staff)})
            print('OK: Supabase Auth real, CRUD, cuatro tipos de asignación, aislamiento de detalle/geometría, RLS y revocación de sesiones.')
            print('La cuenta temporal fue eliminada; las cuentas iniciales permanecen disponibles.')
    finally:
        if uid:
            backend.delete(uid)
        for token in anonymous_or_user_tokens:
            try:
                backend.sign_out(token)
            except AccountError:
                pass


if __name__ == '__main__':
    try:
        main()
    except (AccountError, RuntimeError, FileNotFoundError) as error:
        print(f'Verificación incompleta: {error}')
        raise SystemExit(1)
