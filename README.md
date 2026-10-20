# Reto FIRA · NAS (New Agro Speed)

Aplicación web con Python y Flask para consultar información de parcelas y resultados de AgroCebada. Incluye acceso para personal técnico y productores, administración de usuarios y un simulador de riesgo económico. La autenticación utiliza Supabase.

Esta guía explica cómo descargar, configurar y ejecutar la aplicación en tu equipo. Los resultados necesarios para consultar la plataforma ya están incluidos en el repositorio; no es necesario entrenar ni regenerar el Modelo.

Está dirigida al personal de FIRA que instalará y administrará la plataforma. La configuración inicial comprende el entorno Python, un proyecto de Supabase, el archivo privado `platform/.env` y las cuentas iniciales. Para consultar la aplicación, sigue los pasos 1 a 6; no ejecutes comandos de entrenamiento.

## Requisitos

- **Python 3.11 de 64 bits**: versión utilizada en el entorno de desarrollo del proyecto. Instálalo desde [Python](https://www.python.org/downloads/).
- **Git**, si vas a clonar el repositorio. Disponible en [Git](https://git-scm.com/downloads).
- Una cuenta y un proyecto en [Supabase](https://supabase.com/), con acceso a sus claves de API y al editor SQL.
- Conexión a internet para instalar las dependencias y utilizar la autenticación de Supabase.

Node.js es opcional: los recursos de interfaz necesarios para ejecutar la aplicación ya vienen incluidos.

## 1. Descargar el proyecto

### Con Git

Abre PowerShell en la carpeta donde quieras guardar el proyecto y ejecuta:

```powershell
git clone https://github.com/EnriqueLunaH/reto-fira.git
cd reto-fira
```

### Como archivo ZIP

En la [página del repositorio](https://github.com/EnriqueLunaH/reto-fira), selecciona **Code → Download ZIP**. Descomprime el archivo y abre una terminal en la carpeta extraída, donde se encuentran este `README.md` y la carpeta `platform`.

En ambos casos, conserva la estructura de carpetas del repositorio.

## 2. Crear el entorno virtual e instalar dependencias

Los siguientes pasos están escritos para **Windows con PowerShell**. Desde la raíz del proyecto:

```powershell
cd platform
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si no tienes el comando `py`, comprueba que `python --version` indique Python 3.11 y utiliza `python -m venv .venv` para crear el entorno.

Ejecuta la instalación desde `platform`: `requirements.txt` incluye una dependencia local ubicada en `vendor/`. Los comandos usan directamente el ejecutable del entorno virtual, por lo que no necesitas activarlo ni cambiar la política de ejecución de PowerShell.

**Desde este punto, todos los comandos de Windows se ejecutan dentro de `platform`.**

## 3. Configurar Supabase

### 3.1. Crear o seleccionar el proyecto

Entra al [panel de Supabase](https://supabase.com/dashboard), selecciona la organización que administrará FIRA y pulsa **New project**. Define el nombre y la contraseña de base de datos, selecciona la región y espera a que termine la creación. Si FIRA ya tiene un proyecto destinado a esta plataforma, utiliza ese proyecto y sus credenciales autorizadas.

Guarda la contraseña de base de datos en el gestor de secretos del administrador. La aplicación usa las API HTTPS de Supabase: **no necesita la contraseña de PostgreSQL ni una Connection string** como `postgresql://postgres:...@db....supabase.co:5432/postgres`. Tampoco necesitas instalar Agent Skills para configurar este proyecto.

### 3.2. Obtener la URL y las API keys

1. Abre **Connect** y copia la **Project URL**: debe tener un formato como `https://TU-PROYECTO.supabase.co`.
2. Abre **Settings → API Keys**. También puedes usar [API Keys](https://supabase.com/dashboard/project/_/settings/api-keys) y seleccionar tu proyecto.
3. En **Publishable and secret API keys**, copia la **Publishable key**, que empieza con `sb_publishable_`.
4. En **Secret keys**, crea una clave para el servidor si todavía no existe y copia su valor, que empieza con `sb_secret_`.
5. Guarda estos valores en el archivo `.env` del paso 4. Las dos claves deben pertenecer al mismo proyecto que la URL.

La **Secret key** permite administrar las cuentas y debe permanecer en el servidor. No la pegues en chats, capturas de pantalla, JavaScript del navegador ni commits. Consulta la [referencia oficial de API keys](https://supabase.com/docs/guides/getting-started/api-keys) si la organización usa claves antiguas.

### 3.3. Crear las tablas y políticas de seguridad

1. En el proyecto de Supabase, abre **SQL Editor → New query**.
2. Abre el archivo [202610200001_accounts.sql](platform/supabase/migrations/202610200001_accounts.sql) del repositorio y copia **todo su contenido** en la consulta.
3. Pulsa **Run**. El resultado esperado es **Success. No rows returned**: indica que el esquema se creó correctamente, aunque no haya filas para mostrar.
4. En **Table Editor** debe aparecer `public.user_profiles`. Las identidades de acceso se crearán después en **Authentication → Users** mediante el asistente del paso 5.

Ejecuta este archivo **una sola vez por proyecto de Supabase**. Si ya está aplicado, omite este paso; volver a ejecutarlo produce errores de objetos existentes. El SQL crea perfiles, asignaciones y políticas RLS; no modifica parcelas, predicciones ni el Modelo. No cambies las políticas ni desactives RLS para resolver errores de acceso.

### 3.4. Desactivar el registro público

Abre **Authentication → Sign In / Providers**, o entra a [Sign In / Providers](https://supabase.com/dashboard/project/_/auth/providers) y selecciona el proyecto:

1. Busca **Allow new users to sign up**, desactiva el interruptor y pulsa **Save**.
2. Deja **Allow anonymous sign-ins** desactivado.
3. Conserva habilitado el proveedor **Email**. En su configuración de contraseñas establece al menos **12 caracteres**, con mayúscula, minúscula, número y símbolo; la aplicación acepta hasta 128 caracteres.

El alta de productores desde staff seguirá funcionando: utiliza la API administrativa del servidor. Estas altas confirman el correo administrativamente y **no envían invitaciones por email**. El staff deberá entregar las credenciales al productor por un canal privado. La recuperación de acceso se gestiona desde el staff; esta versión no incluye recuperación automática por correo.

La ubicación de estos controles está descrita en la [configuración oficial de autenticación](https://supabase.com/docs/guides/auth/general-configuration).

## 4. Crear el archivo de configuración

Copia el ejemplo dentro de `platform` **solo en la primera instalación**. Si `.env` ya existe, edítalo conservando sus valores; no lo sobrescribas:

```powershell
Copy-Item .env.example .env
```

Genera una clave de sesión:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Abre `.env` en un editor de texto y completa los valores. Sustituye `SECRET_KEY` por el resultado del comando anterior:

```dotenv
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_REEMPLAZAR
SUPABASE_SECRET_KEY=sb_secret_REEMPLAZAR
SECRET_KEY=TU_CLAVE_DE_SESION_GENERADA
COOKIE_SECURE=0
PORT=5000
```

| Variable | Uso |
| --- | --- |
| `SUPABASE_URL` | URL del proyecto de Supabase. |
| `SUPABASE_PUBLISHABLE_KEY` | Clave pública del mismo proyecto. |
| `SUPABASE_SECRET_KEY` | Clave privada del servidor para administrar cuentas. |
| `SECRET_KEY` | Clave aleatoria y persistente para firmar las sesiones. |
| `COOKIE_SECURE` | Usa `0` para ejecutar en localhost mediante HTTP. Usa `1` en un despliegue con HTTPS. |
| `PORT` | Puerto local de la aplicación; por defecto, `5000`. |

Sustituye todos los ejemplos por valores reales del proyecto autorizado y guarda el archivo. No incluyas la contraseña de PostgreSQL. Las variables de entorno del proceso tienen prioridad sobre los valores de `.env`.

Si el panel solo ofrece **Legacy API Keys**, también se admiten `anon` y `service_role`: deja vacías `SUPABASE_PUBLISHABLE_KEY` y `SUPABASE_SECRET_KEY` y añade `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY`, respectivamente. La clave `service_role` es secreta y requiere el mismo cuidado que una Secret key. Para proyectos nuevos, utiliza las claves publicable y secreta.

El archivo `.env` contiene secretos y está excluido de Git. No lo publiques ni compartas sus valores.

## 5. Verificar la conexión y crear los usuarios iniciales

Primero comprueba la configuración:

```powershell
.\.venv\Scripts\python.exe manage_accounts.py check
```

El comando debe confirmar que la conexión con Supabase y la tabla `user_profiles` están disponibles. Comprueba también que indique que el registro público está deshabilitado.

La salida esperada es:

```text
Conexión con Supabase y tabla user_profiles disponibles.
Registro público de Supabase: deshabilitado.
```

Si indica que falta la migración, vuelve al paso 3.3. Si indica que el registro público está habilitado, completa el paso 3.4 y repite la comprobación antes de entregar el sistema a sus usuarios.

Después crea las cuentas iniciales:

```powershell
.\.venv\Scripts\python.exe manage_accounts.py bootstrap
```

El asistente solicita un correo y una contraseña para **staff** y otro correo y contraseña para **productor**. Usa correos distintos y contraseñas que cumplan los requisitos anteriores. Al escribir las contraseñas no se mostrarán caracteres en la terminal. Conserva los accesos en un lugar privado.

Para FIRA, escribe los correos autorizados del personal y del productor en vez de aceptar los correos de ejemplo que muestra el asistente. No crees la cuenta de staff mediante el registro público ni cambies su rol desde una sesión de productor.

Si una cuenta ya existe con el mismo correo y rol, se conserva. No hay contraseñas de demostración habilitadas. El productor inicial comienza sin parcelas asignadas.

**Alternativa para una demostración:** `manage_accounts.py bootstrap --generate-credentials` conserva los correos de ejemplo y genera contraseñas aleatorias en el archivo privado `.instance/initial-accounts.txt`. No es necesario para la instalación con correos institucionales. No publiques ese archivo; guarda las credenciales en el gestor autorizado y retira la copia local cuando termine su entrega.

## 6. Levantar el proyecto

Desde `platform`, ejecuta:

```powershell
.\.venv\Scripts\python.exe app.py
```

Mantén esa terminal abierta y visita [http://127.0.0.1:5000](http://127.0.0.1:5000). El servidor local utiliza Waitress.

- **Staff:** [http://127.0.0.1:5000/login/staff](http://127.0.0.1:5000/login/staff).
- **Productor:** [http://127.0.0.1:5000/login/productor](http://127.0.0.1:5000/login/productor).

Entra con la cuenta staff y abre **Usuarios y parcelas** (`/staff/usuarios`). Desde ahí puedes administrar productores y asignarles parcelas específicas, municipios completos o todas las parcelas disponibles. Después inicia sesión como productor para consultar sus asignaciones.

Para comprobar la instalación completa:

1. Como staff, edita el productor inicial y guarda el acceso a una parcela o a un municipio.
2. Cierra la sesión y entra por `/login/productor` con las credenciales de ese productor.
3. Verifica que **Tu cuenta** muestre su nombre y correo, y que el listado solo incluya las parcelas asignadas.
4. Cierra la sesión. Conserva el acceso de staff únicamente para el personal autorizado.

Si cambiaste `PORT`, utiliza ese puerto en las direcciones anteriores. Para detener el servidor, presiona **Ctrl+C** en la terminal.

## 7. Volver a iniciar en otra ocasión

Una vez completada la configuración inicial, abre PowerShell en la raíz del repositorio y ejecuta:

```powershell
cd platform
.\.venv\Scripts\python.exe app.py
```

Conserva tu `.env` y tu proyecto de Supabase. No necesitas repetir la migración ni crear de nuevo los usuarios. La aplicación crea sus archivos locales de sesión dentro de `platform/.instance/`, una carpeta privada excluida de Git.

## Linux y macOS

Los pasos de Supabase y configuración son los mismos. Desde la raíz del repositorio, crea el entorno e instala las dependencias con Python 3.11:

```bash
cd platform
python3.11 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
```

Completa `.env` y configura Supabase siguiendo los pasos 3 y 4. Después ejecuta:

```bash
./.venv/bin/python manage_accounts.py check
./.venv/bin/python manage_accounts.py bootstrap
./.venv/bin/python app.py
```

Abre las mismas direcciones del paso 6. En algunas distribuciones Linux, el paquete de creación de entornos virtuales de Python se instala por separado.

## Opcional: reconstruir los recursos de interfaz

Este paso solo se necesita si vas a editar los recursos de interfaz. Instala Node.js con npm y, desde `platform`, ejecuta en Windows:

```powershell
npm.cmd ci
npm.cmd run build:ui
```

En Linux o macOS utiliza `npm ci` y `npm run build:ui`. Para ejecutar la versión publicada, utiliza los recursos ya incluidos. `node_modules`, los entornos virtuales y las cachés de instalación están excluidos del repositorio.

## Solución de problemas

| Problema | Qué revisar |
| --- | --- |
| No se reconoce `py`, `python` o `python3.11`. | Comprueba que Python 3.11 esté instalado y disponible en la terminal. Vuelve a abrir la terminal después de instalarlo. |
| `pip` no encuentra el archivo local de OSBI. | Ejecuta la instalación dentro de `platform` y comprueba que exista `vendor/flask_osbi-0.1.0-py3-none-any.whl`. |
| Falla la instalación de dependencias. | Confirma que utilizas Python 3.11 de 64 bits y el ejecutable de `.venv`; conserva las versiones de `requirements.txt`. |
| `manage_accounts.py check` falla o el acceso devuelve 503. | Revisa internet, la URL y ambas claves de Supabase, y confirma que la migración esté aplicada en ese mismo proyecto. |
| Solo encuentras **Connection string**, host y puerto. | Estás viendo la conexión PostgreSQL. Obtén la **Project URL** y las claves en **Settings → API Keys**, como se explica en el paso 3.2. |
| **Falta ejecutar la migración de cuentas**. | Ejecuta el SQL completo del paso 3.3 en el proyecto al que apunta `SUPABASE_URL` y repite `manage_accounts.py check`. |
| La conexión funciona, pero el registro público sigue habilitado. | En **Authentication → Sign In / Providers**, desactiva **Allow new users to sign up**, guarda y repite la comprobación. |
| Aparece un error de tabla ya existente al ejecutar SQL. | Comprueba si la migración ya está aplicada; no la ejecutes otra vez ni borres tablas para repetirla. |
| No puedes iniciar sesión. | Usa los accesos creados mediante `bootstrap`; para HTTP local, conserva `COOKIE_SECURE=0` y reinicia el servidor tras editar `.env`. |
| Estás usando claves `anon` y `service_role`, pero falla la conexión. | Deja vacías las variables modernas; los valores de ejemplo `sb_publishable_REEMPLAZAR` y `sb_secret_REEMPLAZAR` no son claves válidas y tienen prioridad si no se sustituyen. |
| La clave de Auth existe, pero la cuenta no tiene acceso. | Las altas de **Authentication → Users** por sí solas no crean el perfil de la aplicación. Usa `bootstrap` para las cuentas iniciales o el CRUD del staff para productores. Solicita revisión al administrador si ya existe una identidad sin perfil. |
| Aparece **Demasiados intentos**. | Espera al menos cinco minutos antes de volver a intentar el acceso; también pueden aplicar los límites propios de Supabase. |
| El productor no ve parcelas. | Entra como staff y asigna permisos desde **Usuarios y parcelas**. |
| El puerto 5000 está ocupado. | Cambia `PORT` en `.env`, reinicia el servidor y abre la URL con el nuevo puerto. |

Consulta [Usuarios, autenticación y asignación de parcelas](platform/docs/usuarios-supabase.md) para más detalles sobre cuentas y permisos, y [la documentación de interfaz](platform/docs/ui-nas.md) para el mantenimiento de los recursos visuales.

## Entrega a operación de FIRA

- Para una instalación compartida, configura HTTPS y `COOKIE_SECURE=1`. La ejecución con `app.py` escucha solo en `127.0.0.1`; su dirección local no da acceso desde otros equipos. El área de infraestructura deberá definir el servicio y el proxy inverso del despliegue institucional.
- Conserva una `SECRET_KEY` persistente, el archivo `.env` y el directorio `.instance` como información privada del servidor. No adjuntes estos archivos a GitHub ni a paquetes de distribución; los instaladores reciben `.env.example` y generan sus propios valores.
- Las cuentas y asignaciones viven en Supabase. Las sesiones y los límites de intentos se guardan en `.instance/auth-sessions.sqlite3`. Para varios procesos del mismo servidor, usa el mismo volumen privado; desplegar en varios servidores requiere sustituir este almacenamiento por un almacén común.
- Las altas administrativas confirman el correo sin enviar mensajes. El personal autorizado entrega y recupera el acceso desde staff. Esta versión no incluye MFA ni recuperación automática por email.
- La puesta en marcha reutiliza los resultados incluidos. La documentación técnica del Modelo está separada en [platform/README.md](platform/README.md) y sus referencias; sus comandos de reproducción no forman parte de esta instalación.
