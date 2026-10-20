# UI del productor: decisiones, fuentes y verificación

Fecha: 18 de octubre de 2026 (hora de México). Ruta: `/productor`.

## Propósito y alcance

La interfaz ayuda a una persona no técnica a identificar una parcela, interpretar la cantidad de grano estimada y reconocer los límites de esa cifra. Es una consulta retrospectiva de cebada de temporal del ciclo abril–octubre de 2025. No presenta seguimiento en tiempo real ni una predicción de la próxima campaña.

Se modificaron exclusivamente la plantilla del productor y su JavaScript de presentación; se añadió una hoja de estilos específica, pruebas de UI y esta documentación. No se cambiaron predicciones, entrenamiento, variables, algoritmos, API, reglas de acceso, exportaciones ni el dashboard de staff. El servidor local se reinició con el mismo entorno virtual y `app.py` para liberar la plantilla anterior almacenada en memoria.

## Información que se prioriza

| Pregunta del productor | Información existente | Decisión de presentación |
| --- | --- | --- |
| ¿Qué parcela estoy viendo? | Código, municipio, estado, superficie y polígono | Identificación junto al resultado, búsqueda por código o municipio y dibujo del límite registrado. No se atribuye propiedad: el acceso de demostración permite consultar las 59 parcelas. |
| ¿Cuánto grano se estima en toda la parcela? | `parcel.total_t` | Cifra principal en toneladas, rotulada como estimación y cantidad aproximada. Un decimal facilita la lectura; el valor original permanece intacto. |
| ¿Cuánto corresponde a una hectárea? | `parcel.yield` | Toneladas por hectárea en palabras y equivalencia aproximada en kilogramos. Dos decimales para toneladas y ninguno para kg son reglas de formato, no modificaciones al modelo. |
| ¿Qué superficie se consideró? | `parcel.area_ha` | Hectáreas junto al rendimiento, explicando que se usan para obtener el total. Se consume el total ya suministrado por la API, sin recalcularlo a partir de cifras redondeadas. |
| ¿Qué tan segura es la cifra? | `metadata.interval`, límites existentes | Aviso visible junto al resultado. La implementación actual declara que no existe un rango validado. No se inventan bandas, porcentajes de confianza ni probabilidades de éxito. |
| ¿Qué se observó en ese ciclo? | Historia de NDVI, lluvia, altitud, inclinación | Detalles opcionales con títulos en forma de preguntas, unidades y explicaciones. No compiten visualmente con la estimación de grano. |
| ¿Cómo puedo usarla? | Alcance retrospectivo de los datos | Comparar con registros propios del ciclo y revisar discrepancias con un asesor. No se generan recomendaciones de fertilizante, riego, crédito o ventas. |

Esta selección es una hipótesis de diseño basada en el objetivo expresado por el usuario y en los campos disponibles, no el resultado de entrevistas con productores. La relevancia de cada bloque deberá contrastarse con ellos.

Se retiró de esta vista la presentación de sensibilidad con flechas y diferencias en t/ha. Esas asociaciones podían interpretarse como instrucciones para aumentar la cosecha, aunque no establecen causalidad. La información técnica permanece disponible en su espacio correspondiente; sus cálculos no se modificaron. También se evita mostrar precisión del modelo, rankings regionales o simulaciones económicas como si describieran la cosecha individual.

## Fuentes consultadas y aplicación concreta

**Medium, publicación Microsoft Power BI.** El artículo recomienda partir de las necesidades del público, simplificar las visualizaciones, usar jerarquía y acompañar la información con contexto. Se aplicó mediante un resultado principal, etiquetas comprensibles, pocos controles y diseño apilado en móvil. Es una publicación de un autor en Medium; no se presenta como una norma oficial de Microsoft ni como un estudio específico de agricultores. [How to Design Data Dashboards for Non-Technical Users](https://medium.com/microsoft-power-bi/how-to-design-data-dashboards-for-non-technical-users-963bb08b2d50).

**Nielsen Norman Group.** Su discusión de atributos preatentivos explica por qué la posición y la longitud permiten comparar cantidades mejor que el área o el ángulo, y por qué el color sirve para destacar. Se conserva una serie temporal con ejes, sin medidores circulares ni gráficos decorativos; la cifra principal destaca por tamaño, posición y espacio. Las series también se distinguen por trazo continuo/discontinuo, no solo por color. [Dashboards: Making Charts and Graphs Easier to Understand](https://www.nngroup.com/articles/dashboards-preattentive/).

**UX Pilot.** Se aplicó su orientación de vincular información con tareas, adaptar la profundidad al rol, priorizar indicadores y ofrecer detalles progresivamente. La pantalla inicial responde cuánto y dónde; los detalles de vegetación, terreno y método se abren a demanda. La gráfica tiene contexto visible y una tabla, sin exigir pasar el cursor para obtener valores. No se trasladan al proyecto los porcentajes de mejora comercial mencionados por el artículo. [12 Dashboard Design Principles For Better UX](https://uxpilot.ai/blogs/dashboard-design-principles).

**LinkedIn.** Se intentó acceder al enlace indicado; el servicio de consulta devolvió un error y no permitió recuperar el texto. No se atribuye ninguna decisión a esa página ni se afirma haber aplicado contenido no verificable. [Designing dashboards for non-expert users](https://www.linkedin.com/top-content/design/dashboard-design-principles/designing-dashboards-for-non-expert-users/).

**Referencias locales.** [components-v1.md](../components-v1.md), apartados Text field, Button, Card grid y Accordion, guía los controles y la composición. Se reutilizan las macros `accordion` y `accordion_item` de Flask-OSBI, sus relaciones ARIA y su comportamiento de apertura. [osbi-v1.md](../osbi-v1.md) aporta las utilidades de grid/flex, espaciado, bordes, radios, anchura y foco. Los selectores nativos se conservan por su soporte de teclado y selector móvil. [refactoring-ui.md](../skill/refactoring-ui.md) orienta jerarquía, espaciado, contraste y revisión con contenido real; esta referencia local no equivale a haber consultado íntegramente el libro.

## Comportamiento y accesibilidad

- La búsqueda combina estado con código o municipio, ignora mayúsculas y acentos y muestra el número de coincidencias. Conserva la selección si sigue disponible; de lo contrario, muestra la primera coincidencia e identifica claramente su código y localidad.
- Mientras carga otra selección se oculta el resultado anterior. Un identificador de solicitud impide que respuestas tardías lo sustituyan. La búsqueda espera 180 ms tras escribir para evitar consultas innecesarias.
- Los estados de carga, ausencia de resultados y error tienen mensajes. Se ofrecen limpieza de filtros, reintento y retorno al acceso. El estado se anuncia mediante una región viva, sin anunciar continuamente toda la ficha.
- Un fallo al obtener el dibujo no impide consultar la estimación. Los valores ausentes se muestran como «Sin dato» y los ceros se conservan como ceros.
- La gráfica se dibuja cuando se abre su panel y se adapta a cambios de ancho. Se preservan los meses sin medición; la tabla muestra «Sin medición», no cero. No se promedian ni se fusionan los sensores.
- Las etiquetas permanecen visibles, los controles tienen al menos 44–48 px de altura y el foco es visible. Los desplegables OSBI se activan con teclado; las tablas tienen encabezados y título.
- En móvil, «Ver estimación» lleva al resultado. Los datos se apilan y la explicación de incertidumbre permanece junto a las cifras.
- La entrada de secciones dura 300 ms, con un desplazamiento de 6 px, y empieza al entrar en el viewport. Ocurre una vez por sección, respeta movimiento reducido y termina si se oculta la pestaña. No se animan cifras intermedias: el productor siempre ve el valor final. Los efectos no son necesarios para acceder al contenido.
- Se reutilizan los SVG existentes y los tokens de tema de NAS. No fue necesario instalar D3, incorporar servicios externos ni modificar el renderizador compartido con staff.

## Verificaciones realizadas

1. Pruebas automatizadas de UI: `node --test ui/producer.test.cjs`, ejecutadas desde `platform`, **7 pruebas aprobadas**. Cubren números/cero/ausencias, ausencia de rango, fallo opcional del mapa, respuestas fuera de orden, búsqueda y recuperación, reintento de carga y gráfica diferida.
2. Revisión en navegador con datos existentes: 59 parcelas iniciales; 15 al filtrar Hidalgo; búsqueda sin coincidencias y limpieza; selección AGC_120 con nombre municipal largo; desplegables por teclado; tabla de siete meses y contexto de terreno.
3. Lectura visual en escritorio de 1280 px y móvil de 390 px, sin desbordamiento horizontal de la página. Revisión de temas oscuro y claro; se restauró el tema oscuro al terminar.
4. Verificación en la URL solicitada, `http://127.0.0.1:5000/productor`, después de reiniciar el servicio que retenía la plantilla anterior. La vista muestra los datos de AGC_003: aproximadamente 61.9 toneladas totales, 3.31 toneladas por hectárea y 18.68 hectáreas.
5. Evidencia visual y manifiesto de integridad en `platform/work/ui-review/producer-v1/`. Las comprobaciones de integridad se limitan al conjunto de archivos explícitamente listado en ese manifiesto.

No se realizaron pruebas de comprensión con agricultores, auditoría WCAG completa, pruebas con un lector de pantalla real ni ensayos en teléfonos físicos o redes de baja velocidad. Las comprobaciones de concurrencia y errores usan respuestas simuladas en memoria. La revisión visual y de teclado no sustituye esas evaluaciones.

## Archivos de implementación

- `platform/templates/producer.html`: contenido, jerarquía y componentes.
- `platform/static/css/producer.css`: estilos acotados a la vista del productor.
- `platform/static/js/producer.js`: presentación, filtros, estados, detalles y microinteracciones.
- `platform/ui/producer.test.cjs`: regresiones del comportamiento de UI.

Para evaluar la siguiente iteración con productores, pedirles localizar una parcela, explicar la diferencia entre total y rendimiento por hectárea, identificar el ciclo y describir qué significa «sin rango validado». Registrar sus errores y dudas antes de añadir nuevos indicadores.
