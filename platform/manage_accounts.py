"""Provision initial accounts via Supabase Admin, without loading the application."""

import argparse
from getpass import getpass
from pathlib import Path
import secrets

from accounts import AccountError, SupabaseAccounts, check_password, email_address, read_env


def bootstrap(backend, generate=False):
    existing = []
    offset = 0
    while True:
        batch = backend.list_profiles(offset=offset, limit=1000)
        existing.extend(batch)
        if len(batch) < 1000:
            break
        offset += len(batch)
    planned = []
    for role, default_email, name in [('staff', 'ejemplotecnico@ejemplo.com', 'Staff inicial'),
                                      ('productor', 'ejemploproductor@ejemplo.com', 'Productor inicial')]:
        email = default_email if generate else email_address(input(f'Correo para {role} [{default_email}]: ').strip() or default_email)
        match = next((p for p in existing if p['email'].lower() == email), None)
        if match:
            if match['role'] != role:
                raise AccountError('El correo ya tiene un rol diferente. Usa otro correo.', 409)
            print(f'La cuenta de {role} ya existe; se conserva sin cambios.')
            continue
        password = secrets.token_urlsafe(24) + 'aA1!' if generate else check_password(getpass(f'Contraseña nueva para {role}: '))
        if not generate and password != getpass('Repite la contraseña: '):
            raise AccountError('Las contraseñas no coinciden.', 400)
        planned.append((role, email, password, name))
    if len({p[1] for p in planned}) != len(planned):
        raise AccountError('Staff y productor deben usar correos distintos.', 400)
    if generate and planned:
        destination = Path(__file__).resolve().parent / '.instance/initial-accounts.txt'
        destination.parent.mkdir(exist_ok=True)
        try:
            with destination.open('x', encoding='utf-8') as stream:
                stream.write('Credenciales iniciales NAS. Archivo privado: no publicar ni compartir.\n\n')
                for role, email, password, _ in planned:
                    stream.write(f'{role}\nCorreo: {email}\nContraseña: {password}\n\n')
                stream.write('El productor inicia sin asignaciones. Configúralas desde /staff/usuarios.\n')
        except FileExistsError:
            raise AccountError('Ya existe .instance/initial-accounts.txt. Consérvalo y usa bootstrap interactivo para completar altas pendientes.', 409) from None
        print(f'Credenciales guardadas únicamente en {destination}')
    for role, email, password, name in planned:
        backend.create(email, password, dict(name=name, phone='', active=True,
                       access_mode='none', parcel_ids=[], municipalities=[]), role=role)
        print(f'Cuenta {role} creada: {email}')
    print('Entra como staff a /staff/usuarios para asignar parcelas al productor.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'bootstrap'])
    parser.add_argument('--generate-credentials', action='store_true', help='Conserva los correos iniciales y genera contraseñas en .instance/initial-accounts.txt.')
    args = parser.parse_args()
    backend = SupabaseAccounts(read_env(Path(__file__).resolve().parent / '.env'))
    try:
        auth_settings = backend._request('GET', '/auth/v1/settings')
        backend._request('GET', '/auth/v1/admin/users', admin=True, query={'page': 1, 'per_page': 1})
        backend.list_profiles(limit=1)  # Validate credentials and migration before any writes.
        if args.command == 'check':
            print('Conexión con Supabase y tabla user_profiles disponibles.')
            print('Registro público de Supabase: ' + ('deshabilitado.' if auth_settings.get('disable_signup') else 'habilitado; desactívalo en Authentication.'))
        else:
            bootstrap(backend, generate=args.generate_credentials)
    except (AccountError, EOFError, KeyboardInterrupt) as exc:
        print(str(exc) if isinstance(exc, AccountError) else 'Operación cancelada.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
