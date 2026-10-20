# Reto FIRA · NAS (New Agro Speed)

Aplicación web con Python y Flask para consultar información de parcelas y resultados de AgroCebada. Incluye acceso para personal técnico y productores, administración de usuarios y un simulador de riesgo económico. La autenticación utiliza Supabase.

Esta guía explica cómo descargar, configurar y ejecutar la aplicación en tu equipo. Los resultados necesarios para consultar la plataforma ya están incluidos en el repositorio; no es necesario entrenar ni regenerar el Modelo.

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

1. Crea un proyecto en Supabase y espera a que esté disponible.
2. Copia la **Project URL**, una **Publishable key** y una **Secret key** del servidor. Las necesitarás en el siguiente paso.
3. En el **SQL Editor** del proyecto, abre una consulta y pega el contenido completo de [202610200001_accounts.sql](platform/supabase/migrations/202610200001_accounts.sql). Ejecútalo **una sola vez** para crear las tablas y políticas de las cuentas. Si el proyecto ya tiene esta migración aplicada, omite su ejecución.
4. En **Authentication**, conserva habilitado el proveedor de correo electrónico y desactiva el registro público (**Allow new users to sign up**) y el acceso anónimo. Las cuentas se crearán desde el servidor.
5. Configura contraseñas de al menos 12 caracteres, con mayúscula, minúscula, número y símbolo.

La aplicación usa las API HTTPS de Supabase; no necesitas una conexión PostgreSQL directa ni la contraseña de la base de datos.

## 4. Crear el archivo de configuración

Copia el ejemplo:

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
SUPABASE_PUBLISHABLE_KEY=TU_CLAVE_PUBLICA
SUPABASE_SECRET_KEY=TU_CLAVE_SECRETA_DEL_SERVIDOR
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

Guarda el archivo antes de continuar. Las variables de entorno del proceso tienen prioridad sobre los valores de `.env`. Si utilizas claves antiguas de Supabase, la aplicación también admite `SUPABASE_ANON_KEY` y `SUPABASE_SERVICE_ROLE_KEY` como alternativas a las claves pública y secreta, respectivamente.

El archivo `.env` contiene secretos y está excluido de Git. No lo publiques ni compartas sus valores.

## 5. Verificar la conexión y crear los usuarios iniciales

Primero comprueba la configuración:

```powershell
.\.venv\Scripts\python.exe manage_accounts.py check
```

El comando debe confirmar que la conexión con Supabase y la tabla `user_profiles` están disponibles. Comprueba también que indique que el registro público está deshabilitado.

Después crea las cuentas iniciales:

```powershell
.\.venv\Scripts\python.exe manage_accounts.py bootstrap
```

El asistente solicita un correo y una contraseña para **staff** y otro correo y contraseña para **productor**. Usa correos distintos y contraseñas que cumplan los requisitos anteriores. Al escribir las contraseñas no se mostrarán caracteres en la terminal. Conserva los accesos en un lugar privado.

Si una cuenta ya existe con el mismo correo y rol, se conserva. No hay contraseñas de demostración habilitadas. El productor inicial comienza sin parcelas asignadas.

## 6. Levantar el proyecto

Desde `platform`, ejecuta:

```powershell
.\.venv\Scripts\python.exe app.py
```

Mantén esa terminal abierta y visita [http://127.0.0.1:5000](http://127.0.0.1:5000). El servidor local utiliza Waitress.

- **Staff:** [http://127.0.0.1:5000/login/staff](http://127.0.0.1:5000/login/staff).
- **Productor:** [http://127.0.0.1:5000/login/productor](http://127.0.0.1:5000/login/productor).

Entra con la cuenta staff y abre **Usuarios y parcelas** (`/staff/usuarios`). Desde ahí puedes administrar productores y asignarles parcelas específicas, municipios completos o todas las parcelas disponibles. Después inicia sesión como productor para consultar sus asignaciones.

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
| Aparece un error de tabla ya existente al ejecutar SQL. | Comprueba si la migración ya está aplicada; no la ejecutes otra vez ni borres tablas para repetirla. |
| No puedes iniciar sesión. | Usa los accesos creados mediante `bootstrap`; para HTTP local, conserva `COOKIE_SECURE=0` y reinicia el servidor tras editar `.env`. |
| El productor no ve parcelas. | Entra como staff y asigna permisos desde **Usuarios y parcelas**. |
| El puerto 5000 está ocupado. | Cambia `PORT` en `.env`, reinicia el servidor y abre la URL con el nuevo puerto. |

Consulta [Usuarios, autenticación y asignación de parcelas](platform/docs/usuarios-supabase.md) para más detalles sobre cuentas y permisos, y [la documentación de interfaz](platform/docs/ui-nas.md) para el mantenimiento de los recursos visuales.
