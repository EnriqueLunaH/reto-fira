# Usuarios, autenticación y asignación de parcelas

## Alcance

Supabase Auth almacena las identidades y los hashes de las contraseñas. La tabla `public.user_profiles` almacena nombre, teléfono, correo sincronizado con Auth, rol, estado de cuenta y asignaciones. La aplicación conserva el catálogo de parcelas y los resultados existentes; este módulo no entrena, modifica ni reemplaza el Modelo ni sus datos.

Se retiran los usuarios de demostración embebidos. Sin Supabase configurado no hay acceso alternativo. El registro público no aprovisiona perfiles ni permite elegir un rol. El alta de productores se realiza desde `/staff/usuarios`, con un usuario staff autenticado; el staff inicial se crea mediante un comando privado de servidor.

## Configuración inicial

1. Crear un proyecto en Supabase. En Connect copiar Project URL; en Settings → API Keys copiar una Publishable key y una Secret key del servidor.
2. Copiar `platform/.env.example` a `platform/.env` y completar `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY` y una `SECRET_KEY` aleatoria. También se admiten las claves antiguas en `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY`. Las variables del proceso tienen precedencia sobre `.env`.
3. Ejecutar **una vez** `platform/supabase/migrations/202610200001_accounts.sql` en SQL Editor del proyecto. Se ejecuta dentro de una transacción. No volver a ejecutarlo sobre tablas ya creadas. No contiene datos ni cambios del Modelo.
4. En Authentication, desactivar **Allow new users to sign up** y el acceso anónimo. Mantener habilitado el proveedor Email y configurar contraseña de al menos 12 caracteres, mayúscula, minúscula, dígito y símbolo. El administrador crea cuentas con correo confirmado; no se envía correo de invitación. Si se requiere verificar el correo del destinatario, añadir posteriormente un flujo de invitación con SMTP.
5. Desde `platform`, ejecutar:

   ```powershell
   .venv\Scripts\python.exe manage_accounts.py check
   .venv\Scripts\python.exe manage_accounts.py bootstrap
   ```

   `bootstrap` pregunta correos y contraseñas de staff y productor. Las contraseñas no se imprimen. Conserva cuentas existentes con el mismo correo y rol. No usa las contraseñas antiguas de demostración.

   Para conservar los correos originales y generar contraseñas aleatorias, usar `bootstrap --generate-credentials`. Escribe las credenciales solamente en `.instance/initial-accounts.txt`, excluido del control de versiones; no imprime sus valores. Proteger este archivo y retirarlo cuando las credenciales se hayan guardado en el gestor de contraseñas. El productor inicial no tiene parcelas hasta que el staff las asigne.
6. Reiniciar el servidor con `.venv\Scripts\python.exe app.py`. Ingresar por `/login/staff` y abrir **Usuarios y parcelas**; acceso de productores por `/login/productor`.

No se necesita conexión PostgreSQL directa, contraseña de base de datos ni nuevas dependencias Python. El cliente usa HTTPS y las API de Auth y PostgREST de Supabase.

## Operación

La vista `/productor` muestra el nombre y correo del perfil autenticado en una tarjeta «Tu cuenta». Los valores se renderizan en el servidor, con escape HTML y distribución adaptable mediante utilidades OSBI. Las vistas de usuarios (listado, alta y edición) comparten el aside y la barra móvil del resto del staff; «Usuarios y parcelas» se marca como sección activa. El Drawer conserva su cierre con Escape, gestión de foco y navegación móvil. Se reutilizan los patrones Admin layout/Drawer de `components-v1.md` y las utilidades de `osbi-v1.md`.

- `/staff/usuarios`: muestra staff y productores, con paginación de 50 usuarios, estado y cantidad de parcelas disponibles.
- `/staff/usuarios/nuevo`: crea un productor con contraseña propia; no admite crear staff desde el navegador.
- `/staff/usuarios/<id>/editar`: guarda nombre, teléfono, cuenta activa y permisos en una sola actualización de la fila. La suspensión invalida las sesiones anteriores.
- **Credenciales de acceso**: cambia el correo y, opcionalmente, la contraseña en Auth Admin. Se invalidan las sesiones antes de solicitar el cambio; el correo se sincroniza desde `auth.users` mediante un trigger. Si Auth falla, el formulario avisa y las sesiones ya revocadas permanecen revocadas. Las asignaciones se guardan en su propio formulario.
- **Eliminar**: exige escribir el correo del productor; elimina la identidad de Auth y el perfil mediante `ON DELETE CASCADE`. No permite borrar staff por estas rutas. Si Auth rechaza la eliminación, se muestra el error y la cuenta permanece; sus sesiones anteriores ya fueron invalidadas.
- Recuperación de acceso: el productor contacta al staff, que establece una contraseña nueva. No se incluye recuperación por correo ni registro público en esta entrega.

Tipos de acceso:

| Modo | Resultado |
| --- | --- |
| Sin parcelas | Puede iniciar sesión, sin datos de parcelas disponibles. |
| Parcelas específicas | Una o varias parcelas seleccionadas por código. |
| Municipios completos | Todas las parcelas disponibles de uno o varios pares estado–municipio. |
| Todas | Todas las parcelas disponibles del catálogo. |

El modo municipio y el modo todas se aplican al catálogo vigente; si en el futuro se incorporan parcelas, quedan incluidas automáticamente. La selección individual conserva los códigos explícitos. El cambio de modo borra las asignaciones del modo anterior. Las asignaciones autorizan consulta; no acreditan propiedad.

## Seguridad

- Roles y estado se consultan en Supabase en cada solicitud protegida. No se acepta el rol de un formulario, de `user_metadata` ni de una cookie como autorización.
- Los productores solo pueden leer su perfil mediante RLS; no tienen permisos SQL de escritura. El rol `anon` no accede a la tabla. El secreto del servidor administra perfiles únicamente después de comprobar que el solicitante es staff. La función para invalidar sesiones solo puede ejecutarse con `service_role`.
- No hay perfil automático al registrarse con la API pública. Una identidad sin perfil no tiene acceso a la aplicación.
- La cookie contiene un identificador aleatorio de sesión; los tokens de Supabase están en `.instance/auth-sessions.sqlite3` del servidor. Se almacena un hash del identificador. La cookie está firmada, es HttpOnly, SameSite=Lax y tiene duración absoluta de ocho horas. Logout elimina la sesión del servidor y bloquea la reutilización de la cookie anterior. Los tokens se renuevan en servidor, con rotación serializada en SQLite.
- Cada lectura valida la identidad con Supabase Auth y vuelve a leer el perfil con el JWT del usuario. La revisión de `active`, rol y versión de sesión bloquea suspensión, borrado o credenciales revocadas sin esperar a que venza un JWT. Los permisos de parcelas se consultan de nuevo por solicitud.
- El listado, detalle/historial y GeoJSON se filtran en el servidor. Una parcela fuera del alcance devuelve 404. Dashboard, exportaciones y riesgo permanecen restringidos al staff.
- Formularios con CSRF, renderizado con escape HTML, CSP, bloqueo de iframes y respuestas privadas sin caché. Límite persistente y atómico de diez intentos por correo y treinta por IP cada cinco minutos; además aplican los límites de Supabase. No se usa un `X-Forwarded-For` proporcionado por el cliente como IP confiable.
- Errores remotos se traducen sin devolver contraseñas, claves ni tokens. El cliente HTTPS rechaza redirecciones para evitar reenviar credenciales a otro host. Una interrupción de Supabase bloquea el acceso y devuelve 503.

En producción usar HTTPS, `COOKIE_SECURE=1`, una `SECRET_KEY` persistente y un volumen privado para `.instance` con permisos exclusivos del servicio. Esta configuración habilita HSTS. `.env`, `.instance`, bases de sesiones, copias de seguridad y credenciales iniciales son secretos del servidor: no publicarlos ni montarlos como archivos estáticos.

SQLite comparte sesiones y límites entre procesos del **mismo host y volumen**. Un despliegue con varios hosts necesita sustituir este almacenamiento por Redis o un almacén transaccional común antes de escalar. Detrás de un proxy, configurar explícitamente sus saltos confiables si se necesita distinguir IP de usuarios; por defecto se cuenta la dirección del proxy. El sistema no incluye MFA, auditoría funcional de cambios ni pruebas de penetración externas.

## Verificación

```powershell
.venv\Scripts\python.exe -m pytest tests/test_accounts.py -q
node --test ui/producer.test.cjs ui/staff-motion.test.cjs
.venv\Scripts\python.exe verify_accounts_live.py
```

Las pruebas locales usan un servicio Supabase simulado e instancias SQLite temporales, sin acceso alternativo en producción. Comprueban roles, CRUD, CSRF, validación, cuatro tipos de asignación, consistencia lista/detalle/mapa, cambios de permisos en sesión, suspensión/borrado, revocación de credenciales, cookie replay, renovación, expiración, límites, escape HTML y transporte seguro.

`verify_accounts_live.py` usa el staff del archivo privado para crear **un productor temporal** con correo aleatorio de prueba, autenticarlo, verificar el CRUD real y las restricciones RLS con una clave pública/JWT, y eliminarlo al terminar. No envía emails, cambia contraseñas de usuarios existentes ni modifica parcelas o predicciones. Requiere conexión saliente al proyecto. Conservar los correos de las cuentas iniciales no implica reutilizar contraseñas antiguas.

Las pruebas históricas de integración que iniciaban sesión con las contraseñas de demostración deben migrarse a un proveedor simulado explícito antes de volver a ejecutarse completas. No se introduce una puerta de acceso con `TESTING=True`. Las pruebas históricas del Modelo y los cálculos permanecen sin editar.

Referencias oficiales: [gestión de usuarios](https://supabase.com/docs/guides/auth/managing-user-data), [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), [API keys](https://supabase.com/docs/guides/getting-started/api-keys), [contraseñas](https://supabase.com/docs/guides/auth/password-security).
