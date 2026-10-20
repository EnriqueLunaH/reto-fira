# Módulos de interfaz OSBI para NAS

Copias sin modificaciones de `C:/dev/osbi-v1/src/js`, paquete local `osbi` 1.0.0:
`SelectMenu`, `Drawer`, `FloatingManager` y las constantes `drawer` y `breakpoints`.
`sources.json` registra la ruta y SHA-256 de cada archivo para contrastarlos con
la biblioteca proporcionada. El `package.json` original declara licencia ISC;
no había un archivo LICENSE independiente en su raíz.

Se utilizan los contratos de **Admin layout**, **Select menu** y **Sidebar layout**
de `components-v1.md`. NAS adapta el breakpoint a `lg` (64rem) para conservar
el aside en equipos de escritorio desde 1024px. El runtime Flask de OSBI incluye
acordeones; estos dos módulos se empaquetan aparte porque no se inicializan allí.

La integración propia está en `ui/staff.js`: transmite la selección al filtro
existente, sincroniza el botón de restablecer, adapta el teclado del listbox y
gestiona foco y contenido inerte al abrir la navegación móvil. No contiene
cálculos, consultas adicionales ni cambios de datos.

Dependencias fijadas: `@floating-ui/dom` 1.7.4, la misma versión declarada por OSBI,
y `esbuild` 0.25.8 como herramienta de compilación. Las licencias MIT de Floating UI
se conservan en `licenses/`.

Desde `platform`, ejecutar `npm.cmd ci` y `npm.cmd run build:ui`. El resultado
`static/js/staff-ui.js` se sirve localmente y se entrega precompilado; ejecutar la
aplicación no requiere Node, acceso a npm ni una instalación externa de OSBI JS.

El mismo comando construye `static/js/risk-ui.js` desde `ui/risk-selects.js`.
Este adaptador utiliza SelectMenu para las opciones recibidas por los selects
existentes del simulador. Conserva nombres, valores, `required`, validación y
FormData; sincroniza selección y deshabilitado sin consultas de datos nuevas.
Los controles originales siguen disponibles si no se activa la mejora. Los
acordeones metodológicos usan directamente las macros y el runtime Flask-OSBI.
