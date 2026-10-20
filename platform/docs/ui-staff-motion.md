# Staff: jerarquía visual y movimiento al entrar en pantalla

Actualización: 18 de octubre de 2026. Alcance exclusivo de la UI de staff.

## Qué cambia

El resumen distingue la acción principal «Explorar parcelas», los filtros, la selección activa y los indicadores. El rendimiento tiene un acento discreto; los otros indicadores mantienen menor énfasis. Las dos gráficas tienen títulos, unidades y contexto separados. La búsqueda sin resultados incluye una acción para recuperar el conjunto completo.

Se reutilizan el Admin layout, Drawer y SelectMenu existentes de OSBI; no se reemplazan sus controladores. La plantilla usa las utilidades documentadas de flex, espaciado, bordes, radios y foco. Las reglas adicionales están en un CSS exclusivo de staff y usan los tokens de NAS.

Fuentes aplicadas:

- [osbi-v1.md](../../osbi-v1.md): contrato de nombres, flex, espaciado, bordes, foco y movimiento reducido.
- [components-v1.md](../../components-v1.md): Admin layout, Button, Card grid y contratos de Drawer/SelectMenu. Las rutas de navegación siguen siendo enlaces reales.
- [refactoring-ui.md](../../skill/refactoring-ui.md): jerarquía y énfasis (pp. 36–64), agrupación y espaciado (66–100), números y alineación (128–131), estados vacíos y bordes (234–241). Se aplicó la guía Markdown; el PDF y las referencias complementarias citadas por ella no están en esa carpeta y no se afirma haberlos revisado.

## Cuándo comienza el movimiento

`staff-motion.js` utiliza el núcleo local de GSAP y un `IntersectionObserver` cuyo contenedor es `.staff-main`, no la ventana. Así reconoce el desplazamiento real del panel y el recorte de los contenedores de tabla. Se exige un 12% de intersección, con margen superior para la barra móvil y 24 px de margen inferior.

| Elemento | Tratamiento |
|---|---|
| Indicadores numéricos | Conteo de cero al valor presentado, 750 ms, conservando decimales, signo, moneda y porcentaje. Se reserva el ancho final para evitar saltos de la unidad. |
| Barras | Crecimiento desde cero, 650 ms. Los valores negativos crecen hacia la izquierda. Ejes, etiquetas y cifras finales permanecen legibles. |
| Puntos de gráficas y mapa | Aparición por radio y opacidad, 420 ms; desfase total limitado a 220 ms. No cambian coordenadas ni valores. |
| Filas de tabla | Entrada individual de 360 ms al aparecer en la zona visible, con desplazamiento de 6 px y opacidad moderada. |
| Selección del mapa | Contorno de selección y foco, `aria-pressed` y detalle anunciado como estado. |
| Botones y filas | Respuesta breve al pasar el puntero, presionar o enfocar. Sin bucles decorativos. |

Las animaciones en curso se pausan al salir de vista, al ocultarse la pestaña o al abrir el Drawer modal sobre el contenido. El foco por teclado completa inmediatamente la presentación del elemento enfocado. Al filtrar o reemplazar una gráfica se liberan los nodos retirados. Las entradas completadas no vuelven a reproducirse para el mismo contenido durante esa visita.

El controlador existente de staff conserva todos sus cálculos. Solo avisa a la capa visual después del render y agrupa los eventos de cambio de ancho para evitar redibujos continuos. Un redibujo por tamaño no vuelve a iniciar entradas. Las otras vistas dinámicas de staff se detectan por inserción de nodos; no se observan atributos animados ni cada actualización del contador.

## Accesibilidad y funcionamiento sin animación

- `prefers-reduced-motion` elimina las transiciones CSS y el movimiento GSAP. Si cambia durante una animación, se completa y restaura el estado final.
- No existe una regla CSS que oculte inicialmente los datos. Si GSAP o IntersectionObserver no están disponibles, los valores siguen visibles.
- Los lectores de pantalla reciben el número final; la copia visual animada tiene `aria-hidden`. No se anuncian los valores intermedios del contador como datos nuevos.
- No se anima el número dentro de las celdas: se conserva la precisión necesaria para comparar parcelas.
- Se mantienen nombres accesibles, foco visible, navegación con teclado, semántica de tablas y exportación con filtros.
- La impresión completa las animaciones activas y conserva los números finales.

## Archivos

- `templates/staff.html`: carga de recursos solo en staff, jerarquía del resumen y estado vacío.
- `static/css/staff-experience.css`: presentación y microinteracciones limitadas a `body[data-page="staff"]`.
- `static/js/staff-motion.js`: observación, movimiento y accesibilidad de números, SVG y filas.
- `static/js/staff.js`: información de selección y coordinación del render; fórmulas existentes intactas.
- `ui/staff-motion.test.cjs`: pruebas del ciclo de vida de la capa visual, sin modelos ni datos.

No se modificaron Python, entrenamiento, características, modelos guardados, métricas, CSV, API, fórmulas económicas, gráficos compartidos del productor ni recursos públicos. Las huellas previas de backend, pipeline, artefactos de primer nivel y entregas se conservan en `work/ui-review/staff-motion-v1/protected-hashes.json` para comprobar este límite.

## Verificación

- 10 pruebas Node aprobadas: aislamiento de staff, umbral de visibilidad, pausa/reanudación, pestaña oculta, Drawer, movimiento reducido, ausencia de GSAP, limpieza de nodos, foco y redibujos sin animación.
- 2 pruebas existentes de autenticación/roles/CSRF y exportación filtrada aprobadas.
- Revisión real en navegador a 1280 × 720 y 390 × 844: resumen, contador fuera de pantalla, gráficas pendientes antes del scroll, activación al entrar, tabla y filas pendientes, navegación móvil, filtros y estado vacío/restablecimiento.
- Se revisaron las vistas de validación y factores, incluidos los valores negativos, y la carga de los controles económicos. No se ejecutó una nueva simulación económica para esta revisión.
- Sin errores de consola en las vistas inspeccionadas. El movimiento reducido se verificó en las pruebas de ciclo de vida; no se cambió la preferencia del sistema operativo.

Órdenes desde `platform`:

```powershell
node --check static/js/staff-motion.js
node --check static/js/staff.js
node --test ui/staff-motion.test.cjs
.\.venv\Scripts\python.exe -m pytest tests/test_integrity.py -k "authentication_roles or export_filters" -q
```

La vista previa requirió ejecutar el servidor de desarrollo fuera del aislamiento de sockets del entorno, enlazado únicamente a `127.0.0.1`. No se cambió el servidor de producción ni su configuración.
