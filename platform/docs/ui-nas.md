# NAS: identidad y experiencia de interfaz

Fecha: 16 de octubre de 2026.

## Alcance

Este cambio corresponde a presentación e interacción: plantillas, estilos, iconos, navegación, temas y animaciones. En Python solo se registra la extensión de interfaz Flask-OSBI y se agrega la vista pública `/timeline`, cuyo contenido principal es un `h1` con el texto `hola`. No se alteran el entrenamiento, las API existentes, autenticación, CSRF, predicciones ni fórmulas del simulador.

## Dirección visual

- **NAS / New Agro Speed:** monograma propio, tipografía Inter local, composición editorial y vocabulario centrado en comprender la parcela.
- **Material:** vidrio esmerilado, bordes discretos, reflejos y capas translúcidas, inspirados en la [Daily Hydration Bottle de The Ordinary](https://theordinary.com/en-us/daily-hydration-bottle-100742.html). La ilustración se construye en CSS/SVG y representa conceptualmente información; no es un mapa ni una predicción real.
- **Estilo:** contraste y contención visual de [Vercel](https://vercel.com/); controles compactos y jerarquía de [shadcn/ui](https://ui.shadcn.com/); espacios de trabajo con navegación lateral inspirados en [Notion](https://www.notion.com/). No se incorporan bibliotecas de esos productos ni sus marcas a NAS.
- **Criterio:** se aplicó la guía local [`refactoring-ui.md`](../../skill/refactoring-ui.md), especialmente jerarquía, escala tipográfica, espaciado entre grupos, contraste y función de las superficies. Se consultó la guía Markdown proporcionada, no el PDF completo del libro ni referencias complementarias no incluidas.

## Tokens y temas

Los tokens de NAS están en `static/css/nas.css`. Se enlazan a los colores semánticos de OSBI mediante sus variables RGB documentadas.

| Función | Oscuro | Claro |
| --- | --- | --- |
| Fondo | `#0a0a0a` | `#fafaf8` |
| Superficie | `#111111` | `#ffffff` |
| Superficie elevada | `#191919` | `#f0f0ed` |
| Texto principal | `#ededeb` | `#20221f` |
| Texto secundario | `#a1a1a1` | `#61635e` |
| Acento agrícola | `#bfd3ae` | `#45663b` |

Contraste calculado con luminancia relativa WCAG sobre los tokens del fondo: texto principal 16.89:1 oscuro y 15.34:1 claro; texto secundario 7.66:1 y 5.82:1; texto tenue 5.37:1 y 4.88:1; acento 12.39:1 y 6.25:1. Estas cifras corresponden a colores sólidos, no a cualquier composición translúcida arbitraria.

El tema inicial es oscuro. El usuario puede elegir Claro, Oscuro o Sistema; la preferencia se conserva en almacenamiento local cuando está disponible. Sistema sigue la preferencia del dispositivo y responde a sus cambios. Un script local pequeño establece el tema antes de cargar estilos para reducir destellos. Los gráficos utilizan colores CSS semánticos para actualizarse sin cambiar los datos.

Inter se sirve desde OSBI, sin Google Fonts. Se emplean principalmente pesos 400–600 y tamaños de 12, 14, 16, 20, 24, 30, 36, 48, 60 y 76 px, con tamaños fluidos en los titulares y ajustes independientes para móvil. Los párrafos se limitan a anchuras de lectura; los valores numéricos usan una jerarquía propia.

## Recorrido y contenido

1. Navegación flotante: marca NAS, proyecto, Agrocostos, FIRA y Timeline, seguida de las acciones de acceso técnico y agricultor. En móvil se utiliza un menú desplegable con las mismas rutas.
2. Hero con propuesta de valor y capas de información ilustrativas.
3. Relato de los problemas: información dispersa, interpretación del rendimiento y diferencia entre producción y margen económico.
4. Vista conceptual del espacio de trabajo y accesos diferenciados por rol.
5. Relación complementaria con FIRA, enlaces a sus servicios y preguntas frecuentes.

La relación se presenta como una propuesta para el Reto AgroCebada, no como una alianza formal o como evidencia de que FIRA carezca de herramientas analíticas. El contenido institucional se contrastó con [FIRA](https://www.fira.gob.mx/Nd/index.jsp), [Quiénes somos](https://www.fira.gob.mx/Nd/AcercadeNosotros.jsp), [Agrocostos](https://www.fira.gob.mx/Nd/Agrocostos.jsp) y [Crédito FIRA](https://www.fira.gob.mx/Nd/FondeoFira.jsp). Se conservan los límites del periodo 2025 y del simulador experimental.

## OSBI y dependencias

Se instaló el paquete desde el entorno virtual de la aplicación mediante:

```powershell
.\.venv\Scripts\python.exe -m pip install "C:\dev\osbi-v1"
```

Se conservó el wheel construido por esa instalación en `vendor/flask_osbi-0.1.0-py3-none-any.whl`. El archivo de requisitos y Docker lo utilizan para reproducir la instalación sin una ruta absoluta de Windows ni un paquete publicado en PyPI. La extensión se registra una sola vez por aplicación. Se usan sus recursos completos, fuente Inter, utilidades documentadas, macros de campos/botones y acordeones, según los archivos `flask.md`, `osbi-v1.md` y `components-v1.md` proporcionados.

La distribución actual de OSBI incluye unos 15.7 MB de CSS sin comprimir y unos 757 KB precomprimidos. Se utiliza la negociación gzip incluida por la extensión. Este cambio no modifica ni purga la biblioteca del usuario; conviene evaluar su coste de análisis CSS con dispositivos de producción reales antes de un despliegue amplio.

GSAP se instaló con npm y quedó fijado en la versión 3.15.0 en `package.json` y `package-lock.json`. Se sirven localmente el núcleo y ScrollTrigger; no se requieren CDN para ejecutar la interfaz. Para actualizar esos recursos desde el paquete instalado:

```powershell
npm.cmd ci
npm.cmd run build:ui
```

El script copia los archivos distribuidos y el README del proveedor a `static/vendor/gsap`. Los encabezados de autoría y enlace de licencia de los archivos originales se conservan.

## Movimiento y accesibilidad

- CSS nativo: progreso de lectura con `animation-timeline: scroll()` y aparición de elementos seleccionados con `animation-timeline: view()`, protegidos con `@supports`.
- GSAP: entrada escalonada del hero, profundidad del conjunto de vidrio, apariciones por sección, énfasis de los capítulos y desplazamiento suave del bloque tipográfico FIRA × NAS. ScrollTrigger coordina el movimiento sin interceptar rueda o gestos ni forzar posiciones de scroll.
- Se respeta `prefers-reduced-motion`: se desactivan los movimientos decorativos y GSAP revierte las animaciones de los contextos que dejan de cumplir su media query. El contenido existe y es visible sin la capa de animación.
- La navegación incluye salto al contenido. Menús y tema usan controles nativos, nombres accesibles, Escape y cierre exterior. Los desplegables móviles se excluyen mutuamente. Los campos conservan etiquetas y el acceso permite mostrar/ocultar la contraseña.
- Las tablas conservan desplazamiento local en pantallas pequeñas. El panel técnico usa el layout administrativo descrito más abajo; las vistas públicas mantienen su navegación flotante y espacio reservado para títulos y anclas.
- El histograma económico adapta su lienzo y la cantidad de etiquetas al ancho disponible para evitar texto diminuto en móvil. Al cambiar de tamaño se redibuja la misma respuesta; no se ejecuta otra simulación ni se altera su contenido.

## Verificación

Se ejecutaron las 66 pruebas existentes del proyecto después de integrar OSBI y la nueva vista. También se revisaron en navegador la landing en ambos temas, las transiciones al desplazarse, Timeline, los accesos de ambos roles, el panel técnico, el simulador y la navegación móvil. Se verificaron el acordeón de OSBI, mostrar/ocultar contraseña, la persistencia de tema entre vistas, la resolución de Sistema, el fondo oscuro neutro y la ausencia de desbordamiento horizontal en las vistas móviles examinadas. El resultado económico se conservó al redimensionar el gráfico.

Las vistas públicas, las seis secciones técnicas y once recursos locales de la landing respondieron correctamente en una prueba de renderizado. El CSS de OSBI se entregó con gzip (757,349 bytes) y `pip check` no encontró incompatibilidades. Las capturas de revisión están en `work/ui-review/`, fuera de los artefactos del modelo. La revisión de colores se realiza sobre tokens concretos, no por apreciación visual solamente.

La prueba automatizada de las fórmulas y datos originales no equivale a una medición de rendimiento en teléfonos reales. No se modificaron los datos para producir las capturas o la presentación.

## Actualización 1/6: espacio técnico

Se eliminó el encabezado superior del espacio técnico en escritorio. Aside y main
ocupan `100dvh`, con desplazamiento independiente y `overscroll-behavior: contain`.
El cambio se aplica a las seis secciones que comparten la plantilla. La marca NAS,
la fuente Inter y los tokens de color coinciden con la landing en claro y oscuro.
Tema y cierre de sesión se agrupan al pie del aside; se conserva el formulario
POST con CSRF existente. En móvil, un pequeño control dentro del main abre la
navegación lateral, con foco contenido, fondo inerte y cierre mediante Escape,
botón o clic exterior.

El filtro «Estado de las parcelas» usa **SelectMenu de OSBI**, con un campo oculto
que conserva el contrato de la interfaz anterior. El adaptador emite `change`
para el controlador existente y sincroniza valor, etiqueta y selección al
restablecer. Las flechas, Inicio/Fin y escritura de letras mueven el foco;
Enter/Espacio confirma y Escape cierra. Se conservan los datos, cálculos, API,
autenticación, exportación y lógica de negocio.

Fuentes locales de diseño: [Admin layout, Sidebar layout y Select menu](../../components-v1.md),
[utilidades OSBI](../../osbi-v1.md) y la [guía Refactoring UI proporcionada](../../skill/refactoring-ui.md).
Se aplicaron jerarquía, anchuras ajustadas al contenido, escala de espaciado,
tipografía neutra y acciones secundarias discretas. No se consultaron el PDF
íntegro ni las referencias complementarias ausentes de esa guía.
La procedencia y las huellas de los módulos se documentan en
[vendor/osbi-ui](../vendor/osbi-ui/README.md).

Validación de esta actualización: las 66 pruebas existentes pasan; renderizado
correcto de las seis secciones; encabezado público preservado; módulos OSBI
contrastados con sus SHA-256. En navegador se comprobaron ambos temas, estados
Hidalgo (15), Puebla (29) y Tlaxcala (15), restablecimiento a 59, teclado del
selector, navegación móvil y recuperación del foco. En escritorio de 1280×420,
el aside se desplazó aproximadamente 281px manteniendo el main en 304px y el
documento en 0; desplazar después el main a 0 conservó la posición del aside.
Las capturas se guardan en `work/ui-review/staff-update1-*.jpg`.

## Actualización 2/6: predicciones por parcela

La vista `/staff/predicciones` mantiene la navegación lateral de la actualización
anterior y presenta una superficie única para filtros y tabla. Reutiliza Inter,
los neutros minerales y el acento vegetal de la landing. El encabezado distingue
la tarea, el conjunto PREDICCIÓN, el cultivo, el ciclo y la descarga. Los cambios
de esta entrega son exclusivamente de presentación e interacción.

Se aplicaron la guía local [Refactoring UI](../../skill/refactoring-ui.md), en
particular jerarquía, agrupación, alineación de cifras y estados vacíos, y los
contratos [Text field, Button, Admin layout y Select menu](../../components-v1.md).
Los componentes se apoyan en las [utilidades OSBI](../../osbi-v1.md); el selector
conserva el módulo OSBI ya integrado. La tabla usa HTML semántico propio: el
catálogo proporcionado no incluye un componente de tabla. No se añadió otra
biblioteca ni se consultó el PDF íntegro del libro.

Las cifras se alinean a la derecha con dígitos tabulares. Se preservan cuatro
decimales de rendimiento y el formato existente de superficie, rango y cosecha.
Los encabezados mantienen las unidades; el rendimiento estimado recibe el
énfasis visual. El identificador permanece visible al desplazar horizontalmente
y los encabezados permanecen visibles dentro del scroll vertical de la tabla.
La región tiene foco de teclado y el orden activo se comunica con `aria-sort`,
flechas y texto. Cambiar filtros u orden vuelve al inicio vertical de la tabla;
redimensionar conserva su posición cuando la selección no cambia.

Los contadores y el contexto de filtros usan las filas existentes. El estado sin
coincidencias incluye una acción que invoca el restablecimiento existente; en
una sola coincidencia se muestra «1 parcela». La carga y los errores tienen
mensajes de estado y `aria-busy`. Las aclaraciones explican el carácter nominal
del rango y las dos columnas del CSV, sin agregar conclusiones analíticas.

Archivos: `templates/staff.html`, `templates/_icons.html`,
`static/css/predictions.css` y únicamente el renderizado y los estados de interfaz
de `static/js/staff.js`. Las comparaciones SHA-256 confirman que `app.py`,
`risk.py`, `artifacts/dashboard.json` y `artifacts/predicciones_59.csv` permanecen
idénticos a los anteriores a esta actualización.

Verificación: las 66 pruebas existentes pasan; las seis secciones técnicas renderizan correctamente y el CSS
nuevo solo se carga en predicciones. En navegador se revisaron los temas claro
y oscuro, la ordenación ascendente y descendente, la combinación Hidalgo +
AGC_003 (una parcela), el estado vacío y su restablecimiento a 59. El CSV filtrado
conserva exactamente `AGC_003,3.1624` después de su encabezado. En 390px y 320px
no hay desbordamiento horizontal del documento; el desplazamiento pertenece a
la tabla. Se comprobó la posición fija de encabezados e identificador al
desplazarla, conservando la posición del main. Capturas:
`work/ui-review/predictions-update2-*.jpg`.

## Actualización 3/6: riesgo económico

La ruta `/staff/riesgo` comparte Inter, los colores, las superficies y los
controles de NAS. La configuración se organiza en tres secciones enlazadas:
parcela, referencia y escenario. La ficha elegida ocupa el espacio junto al
selector; presupuesto y bases de errores se agrupan sin dejar una tarjeta
vacía de altura innecesaria. Los campos muestran unidades, mantienen sus
límites originales y separan la acción principal del restablecimiento.

Se aplicaron las pautas de jerarquía, agrupación, anchura, alineación de cifras,
color y tipografía de la [guía Refactoring UI](../../skill/refactoring-ui.md),
las [utilidades OSBI](../../osbi-v1.md) y los contratos de
[Select menu, Text field, Button, Checkbox group y Accordion](../../components-v1.md).
Los tres selectores usan el módulo real SelectMenu con un adaptador de interfaz
en `ui/risk-selects.js`. Sus opciones proceden de los selects que ya llena el
controlador original: no hay listas inventadas, consultas adicionales ni valores
alternativos. Los controles originales conservan sus nombres, valores,
validación y participación en FormData. La mejora añade teclado, búsqueda por
letras, sincronización de deshabilitado y presentación del error obligatorio.
Los triggers se exponen como comboboxes; los controles fuente se retiran de la
navegación y del árbol accesible mientras está activa la mejora.

Las explicaciones y fuentes usan las macros Accordion del runtime Flask-OSBI.
Los resultados mantienen los cuatro indicadores, el histograma y las 17 filas
de comparación existentes. Se mejoraron tipografía, contraste, unidades,
alineación numérica, encabezados de tabla e identificación de cada serie. El
enlace «Ajustar escenario» vuelve al formulario sin ejecutar un cálculo. El
aviso de resultado pendiente continúa ligado al último cálculo. Se conserva la
distinción entre estimaciones de 2025 y presupuesto de 2026, así como todos los
límites metodológicos y enlaces originales.

El cuerpo de esta vista se fija al viewport para que el foco en controles y
acordeones lejanos desplace solamente el main. La corrección responde a un
desplazamiento del documento detectado durante la revisión; queda acotada a la
presencia de `.risk-page`. El aside y el main mantienen su altura y scroll
independiente. En móvil se apilan los campos y la referencia; la tabla conserva
su scroll local y el histograma usa su adaptación existente.

Archivos modificados: `templates/staff.html`, `templates/risk.html`,
`static/css/risk.css`, el nuevo adaptador y su bundle `static/js/risk-ui.js`, el
script de construcción y la documentación del proveedor. **`static/js/risk.js`
permanece íntegro**, al igual que `app.py`, `risk.py` y los artefactos: se
compararon las huellas SHA-256 de 41 archivos protegidos. La respuesta JSON
completa de la simulación de referencia también coincide exactamente. No se
agregaron dependencias ni se cambió el cálculo del histograma o del simulador.

Verificación: 66 pruebas existentes aprobadas, seis secciones renderizadas y
enlaces al PDF y a la metodología operativos. En navegador se revisaron los
temas claro y oscuro, la validación de parcela, selección con teclado y Escape,
el cambio de perfil y presupuesto, base espacial, confirmación, cálculo y aviso
de resultados pendientes. En 390px y 320px no hay desbordamiento horizontal del
documento; los indicadores conservan el mismo contenido después de redimensionar.
Se comprobó la apertura de ambos acordeones y que
el documento permanece en scroll 0 al llevar el foco a ellos. Las capturas se
guardan como `work/ui-review/risk-update3-*.jpg`. Se consultó la guía Markdown
proporcionada; no el PDF completo ni sus referencias complementarias ausentes.

## Actualización 4/6: validación

La ruta `/staff/validacion` adopta las superficies neutras, Inter, los tamaños
tipográficos y el acento verde de NAS. El encabezado identifica la evaluación
como retrospectiva e indica el ciclo de los datos; ofrece acceso directo a la
metodología. El filtro OSBI se agrupa con el tamaño de la muestra seleccionada
y una explicación de su efecto sobre los indicadores y las dos gráficas.
El contador reutiliza el texto que ya produce el controlador original.

Se aplicaron las pautas de jerarquía, proximidad, tipografía, color y anchura de
la [guía Refactoring UI](../../skill/refactoring-ui.md), las
[utilidades OSBI](../../osbi-v1.md) y los contratos Select menu y Accordion de
[components-v1.md](../../components-v1.md). Los indicadores conservan sus
etiquetas, valores, unidades y notas. Las gráficas distinguen la evaluación por
parcela de la prueba por bloques, muestran sus unidades y explican la diagonal
de coincidencia. La leyenda geográfica solo muestra el estado seleccionado.
Las definiciones y el alcance se consultan en dos acordeones reales de
Flask-OSBI, sin dependencias adicionales.

Las explicaciones proceden de la vista y la metodología existentes: no se
introducen nuevas métricas, umbrales de aprobación ni conclusiones sobre la
calidad del modelo. Se conserva la advertencia sobre generalización entre años
y la posibilidad de R² negativo. En móvil las gráficas usan el ancho disponible;
las etiquetas de las barras se colocan encima de cada barra en contenedores
estrechos. Esta adaptación de geometría se limita a `validation-chart` y
`spatial-chart` y mantiene los valores, escalas, colores y títulos originales.
El documento se fija al viewport únicamente en esta vista para que llevar el
foco a contenido lejano desplace el main sin arrastrar el aside.

Archivos de interfaz: `templates/staff.html`, el nuevo parcial
`templates/validation.html`, `static/css/validation.css`,
`static/js/validation-ui.js` y la adaptación de presentación en
`static/js/charts.js`. **`static/js/staff.js` permanece íntegro**, junto con
`app.py`, `risk.py`, el controlador de riesgo y todos los artefactos: se
compararon las huellas SHA-256 de 42 archivos protegidos.

Verificación: 66 pruebas existentes aprobadas; seis secciones staff renderizadas
sin errores y carga de los recursos nuevos limitada a validación. En navegador,
las métricas completas, los títulos de las gráficas, cada punto y cada barra
coinciden exactamente con la versión anterior en los cuatro filtros:
138 parcelas en total, 36 de Hidalgo, 71 de Puebla y 31 de Tlaxcala. Se conservan
los valores negativos de R². Se revisaron temas claro y oscuro, navegación por
teclado y Escape en el selector, restablecimiento, acordeones y menú móvil.
En 390px y 320px no hay desbordamiento horizontal del documento; el documento
mantiene scroll 0 al enfocar los acordeones. En escritorio, aside y main
conservan su altura y desplazamiento independiente. No se registraron errores
de consola. Las comparaciones y capturas están en
`work/ui-review/update4-*.json` y `work/ui-review/validation-update4-*.jpg`.

## Actualización 5/6: factores del modelo

La ruta `/staff/factores` comparte Inter, los fondos neutros, el acento verde y
la jerarquía del resto de NAS. El encabezado identifica el método de importancia
y el ciclo de los datos, con un acceso a la metodología. La gráfica ocupa una
anchura legible y comparte espacio con una guía de valores positivos, cercanos
a cero y negativos. Se mantiene visible el alcance global sobre 28 parcelas de
calibración, sin filtro geográfico, y la advertencia de que no mide causalidad.
El método y sus límites se amplían en un Accordion real de Flask-OSBI.

Se aplicaron las pautas de jerarquía, agrupación, anchura, espaciado, tipografía
y color de la [guía Refactoring UI](../../skill/refactoring-ui.md), las
[utilidades OSBI](../../osbi-v1.md) y los patrones de composición y
[Accordion](../../components-v1.md#accordion). Se reutilizaron el shell, el
Drawer, los iconos y el selector de tema existentes. No se agregaron dependencias.
Se consultó la guía Markdown proporcionada; sus referencias complementarias y
el PDF completo no están presentes en la carpeta de la guía.

Los siete grupos, su orden, los valores, el signo y los tres decimales se
conservan. Los textos explicativos reorganizan el contenido y el método ya
documentados en la vista original; no se crean indicadores ni recomendaciones
agronómicas. La fuente de los valores sigue siendo `artifacts/dashboard.json`,
servida por el controlador existente. No se añaden consultas ni cálculos de
importancia en la interfaz.

La adaptación en `static/js/charts.js` se limita a la geometría y los rótulos de
`importance-chart`: máximo de 720px, uso del ancho disponible en móvil,
etiquetas encima de las barras cuando el contenedor mide menos de 480px y
dos decimales en los rótulos del eje para hacer legible su extremo negativo.
La escala numérica original permanece igual. Una línea de referencia y su
etiqueta identifican el cero. Los textos SVG llevan un contorno del color de
la superficie para que las líneas de la cuadrícula no dificulten su lectura.
En pantallas intermedias la guía pasa debajo de la gráfica; en móvil se apila.
El cuerpo se fija al viewport únicamente en esta vista para mantener el scroll
del main independiente del aside al enfocar contenido lejano.

Archivos de interfaz: `templates/staff.html`, el parcial `templates/factors.html`,
`static/css/factors.css`, `static/js/factors-ui.js` y la adaptación de dibujo en
`static/js/charts.js`. El adaptador solo presenta la carga y los errores del
controlador original. **`static/js/staff.js` permanece íntegro**, junto con
`app.py`, `risk.py`, el controlador de riesgo y los artefactos; las huellas
SHA-256 de los 42 archivos protegidos coinciden con las iniciales.

Verificación: 66 pruebas existentes aprobadas y seis secciones staff renderizadas
sin errores. CSS y adaptador nuevos se cargan únicamente en factores. En
navegador, los títulos, valores y siete barras coinciden exactamente con la
versión anterior; los indicadores, puntos y barras de validación también se
conservan tras la adaptación del dibujado. Se revisaron temas claro y oscuro,
menú móvil, acordeón, foco y scroll independiente. En 320px, 390px y 1024px no
hay desbordamiento horizontal del documento. El viewport final vuelve a su
tamaño original. No se registraron errores de consola.

Se midió contraste entre los colores calculados por el navegador: texto de
apoyo sobre tarjeta 6.08:1 en claro y 7.31:1 en oscuro; texto tenue 5.10:1 y
5.12:1; distintivo verde sobre su fondo 5.62:1 y 10.32:1. Estas mediciones
corresponden a esos pares, no a una auditoría integral de accesibilidad.
Evidencias: `work/ui-review/update5-*.json` y
`work/ui-review/factors-update5-*.jpg`.

## Actualización 6/6: metodología y límites

La ruta `/staff/metodologia` adopta Inter, la escala tipográfica, los neutros y
el acento verde de NAS. La información deja de ser un bloque continuo y se
organiza en cuatro secciones: fuentes, métricas agregadas, ajuste y límites.
Un índice con enlaces nativos permite ir directamente a cada sección y mueve
el foco al destino. El acceso a validación conecta la explicación con los
resultados ya disponibles en la aplicación.

Las fuentes se agrupan por datos de parcela, geometrías, clima y topografía.
Las dos fórmulas existentes tienen etiquetas y unidades separadas; se conserva
la advertencia sobre la imposibilidad de sumar incertidumbre individual para
crear un intervalo regional. El proceso distingue selección, preparación y
modelo final. El resumen dinámico conserva íntegro el texto que genera el
controlador original, incluyendo coberturas, tamaños de muestra, casos sin
rango finito y la advertencia de que no son garantías individuales.

Los límites temporal, espacial y de información disponible permanecen visibles
en su sección. Solo la referencia al detalle técnico del proyecto se coloca
en un Accordion real de Flask-OSBI. Los nombres `technical-documentation.md` y
`artifacts` se presentan como referencias de archivos del proyecto: no se
crearon enlaces a rutas de descarga inexistentes.

Se aplicaron las pautas de jerarquía, agrupación, anchura de lectura,
espaciado, tipografía y color de la
[guía Refactoring UI](../../skill/refactoring-ui.md), las
[utilidades OSBI](../../osbi-v1.md) y los contratos de composición, Admin layout,
Button, Card grid y [Accordion](../../components-v1.md#accordion). Se reutilizan
el shell y los controles de navegación y apariencia. Se consultó la guía
Markdown; sus referencias complementarias y el PDF completo no están presentes
en su carpeta. No se agregaron dependencias ni fuentes externas.

En móvil, índice y contenido se reorganizan sin reducir proporcionalmente toda
la página; las fórmulas, los nombres de fuentes y los archivos pueden ajustarse
al ancho disponible. Los destinos respetan el espacio de la barra móvil
mediante el scroll-padding existente. El cuerpo se fija al viewport solo en
esta vista para que el foco y las anclas desplacen el main y conserven el scroll
independiente del aside. El resumen técnico es texto normal para evitar nuevas
notificaciones accesibles cada vez que el controlador lo repinta al redimensionar.

Archivos de interfaz: `templates/staff.html`, el parcial
`templates/methodology.html`, `static/css/methodology.css` y
`static/js/methodology-ui.js`. Este último solo presenta estados de carga y
error observando el texto existente, sin analizarlo ni recalcular métricas.
**Todos los JavaScript preexistentes permanecen íntegros**, al igual que
`app.py`, `risk.py` y los artefactos: las huellas SHA-256 de 51 archivos protegidos
coinciden con las iniciales. La información procede de la vista original y
del resumen que ya genera `staff.js`.

Verificación: 66 pruebas existentes aprobadas; las seis rutas staff renderizan
sin errores. Los recursos nuevos solo se cargan en metodología. El HTML
renderizado de las otras cinco rutas coincide con el anterior, normalizando
únicamente espacios. En navegador, el resumen del modelo coincide exactamente
con la versión anterior, también tras redimensionar. Se revisaron ambos temas,
las cuatro anclas, activación con teclado, acordeón y menú móvil. El documento
mantiene scroll 0 y no presenta desbordamiento horizontal en 320px, 390px y
1024px. En escritorio, aside y main conservan la altura del viewport.

Contraste medido con los colores calculados por el navegador: texto de apoyo
sobre tarjeta 6.08:1 en claro y 7.31:1 en oscuro; texto tenue 5.10:1 y 5.12:1;
distintivo verde sobre su fondo 5.62:1 y 10.32:1. Son mediciones de esos pares,
no una auditoría integral de accesibilidad. Evidencias en
`work/ui-review/update6-*.json` y `work/ui-review/methodology-update6-*.jpg`.
