---
name: refactoring-ui
description: Diseña, revisa y mejora interfaces aplicando Refactoring UI de Adam Wathan y Steve Schoger. Se utiliza al crear o refactorizar pantallas, formularios, dashboards, tablas, tarjetas, navegación y páginas web; al revisar capturas o código; y al resolver problemas de jerarquía visual, espaciado, tipografía, color, profundidad, imágenes y acabado. Conserva el PDF original y referencias completas para consultar ejemplos y detalles bajo demanda.
---

# Refactoring UI

Convertir los principios del libro en decisiones concretas de diseño e implementación. Adaptar las decisiones a la tarea, el contenido, la marca y los componentes existentes.

## Fuente y conservación de información

Mantener el PDF original Refactoring-UI.pdf, de Adam Wathan y Steve Schoger, como fuente íntegra adicional. Sus 252 páginas conservan texto, imágenes, comparaciones, fórmulas y composición original. Las instrucciones siguientes son una adaptación operativa; no sustituyen esa fuente. Consultar [origen y acceso al documento](references/source-document.md) para recuperar el archivo original y verificar su identidad.

Consultar las referencias completas por tema y examinar las páginas del PDF cuando una decisión dependa de un ejemplo visual. La extracción de texto conserva el texto extraíble de cada página, pero no reproduce imágenes ni garantiza su orden visual.

| Tema | Páginas del PDF | Referencia completa | Consultar cuando |
| --- | --- | --- | --- |
| Inicio y personalidad | 7–34; portada e índice 1–6 | [Starting from Scratch](references/01-starting-from-scratch.md) | Se inicia una funcionalidad o se definen restricciones visuales. |
| Jerarquía | 35–64 | [Hierarchy is Everything](references/02-hierarchy.md) | Compiten datos, etiquetas, títulos, iconos o acciones. |
| Distribución y espaciado | 65–100 | [Layout and Spacing](references/03-layout-spacing.md) | Hay problemas de densidad, agrupación, anchura o adaptación. |
| Tipografía | 101–136 | [Designing Text](references/04-designing-text.md) | Se ajustan escalas, fuentes, lectura o alineación. |
| Color | 137–170 | [Working with Color](references/05-working-with-color.md) | Se construyen paletas, tonos, estados o contraste. |
| Profundidad | 171–198 | [Creating Depth](references/06-creating-depth.md) | Se definen elevación, sombras, relieves o capas. |
| Imágenes | 199–218 | [Working with Images](references/07-working-with-images.md) | Hay fotografías, iconos, capturas o contenido subido. |
| Acabado | 219–248 | [Finishing Touches](references/08-finishing-touches.md) | Se pulen controles, fondos, estados vacíos o componentes. |
| Aprendizaje | 249–252 | [Leveling Up](references/09-leveling-up.md) | Se estudian referencias y se desarrolla criterio visual. |

Buscar términos originales mediante `rg -n 'line-height|saturation|shadows' references/*.md`; buscar `## Página N` para localizar una página. Renderizar el PDF cuando la extracción omita la información necesaria. Usar un visor de PDF disponible; para renderizado local, comprobar primero la disponibilidad de Poppler o de una biblioteca adecuada. La aplicación de las reglas en Markdown no requiere paquetes adicionales.

En ChatGPT, recuperar el PDF por el identificador del archivo original indicado en source-document.md mediante las capacidades disponibles de archivos; seguir la skill de archivos correspondiente. En otros entornos, proporcionar ese PDF como archivo de entrada. Conservar todas las referencias junto a SKILL.md. Un SKILL.md aislado no conserva todo el libro. Si falta el PDF, las reglas y el texto extraído siguen disponibles, pero comunicar la limitación para comparaciones visuales y no afirmar que se consultó la fuente íntegra.

## Flujo de trabajo

1. Identificar funcionalidad, público, acción principal, contenido real y restricciones. Reutilizar el sistema de diseño existente. Preguntar solo por información que cambie materialmente la solución; declarar los supuestos restantes.
2. Elegir la ruta: para una interfaz nueva, comenzar por una funcionalidad mínima; para una existente, inspeccionar pantalla, captura o código y registrar problemas observables; para una consulta puntual, responder con la regla y un ejemplo.
3. Consultar las referencias pertinentes. En una auditoría completa, recorrer todos los temas y justificar los no aplicables.
4. Resolver estructura, contenido, jerarquía y espaciado en baja fidelidad o escala de grises. Definir después tipografía, color y personalidad; terminar con profundidad, imágenes y acabado.
5. Seleccionar tokens para tamaños, pesos, interlineado, colores, márgenes, padding, anchuras, alturas, sombras, radios, bordes y opacidad. Comparar valores vecinos antes de inventar otros.
6. Implementar o proponer cambios concretos según lo solicitado. Trabajar en ciclos cortos: diseñar → construir → observar con contenido real → corregir. No presentar funcionalidad pendiente como operativa.
7. Revisar con la lista de verificación final. Corregir fallos y repetir las comprobaciones afectadas. Distinguir verificaciones realizadas de pendientes.

Tratar las cifras del libro como puntos de partida, no como obligaciones universales. Mantener libertad en decisiones estéticas y rigor en comprobaciones de contenido, funcionalidad y legibilidad. No sacrificar accesibilidad para reproducir un efecto visual.

## 1. Comenzar desde cero

### 1.1. Empezar por una funcionalidad — pp. 8–11

- Diseñar primero una tarea real; decidir navegación y estructura global después de conocer varias funcionalidades.
- Para buscar vuelos, comenzar con origen, destino, salida, regreso y búsqueda; decidir después logo, sidebar o anchura global.

### 1.2. Dejar los detalles para después — pp. 12–15

- Explorar estructura con bocetos simples y trazos gruesos para evitar decisiones prematuras de fuentes, sombras e iconos.
- Diseñar en escala de grises para sostener la jerarquía con tamaño, contraste y espacio; incorporar color después.
- Usar bocetos y wireframes como herramientas desechables de decisión; avanzar pronto a una interfaz funcional.

### 1.3. No diseñar demasiado por adelantado — pp. 16–19

- Diseñar y construir una versión simple de la siguiente funcionalidad; iterar sobre problemas reales antes de pasar a otra.
- Probar casos como muchos contactos, errores o eventos simultáneos en la implementación, sin intentar imaginarlo todo previamente.
- Separar lo esencial de lo opcional: comentarios sin adjuntos pueden ser una primera versión útil. No bloquearla por una ampliación costosa ni insinuar capacidades que no se construirán.

### 1.4. Elegir una personalidad — pp. 20–27

- Coordinar tipografía, color, radios y lenguaje: serif para carácter clásico; sans serif redondeada para uno juguetón; sans serif neutra para discreción.
- Usar azul/familiaridad, dorado/sofisticación y rosa/diversión como asociaciones contextuales, sin convertirlas en leyes psicológicas.
- Elegir radios pequeños para neutralidad, grandes para amabilidad y esquinas rectas para formalidad; mantener coherencia entre componentes.
- Alinear el tono formal o cercano con el público. Estudiar sitios que utiliza sin imitar excesivamente a competidores directos.

### 1.5. Limitar las opciones — pp. 28–34

- Definir conjuntos reducidos y perceptiblemente distintos para decisiones recurrentes; evitar ajustes arbitrarios píxel a píxel.
- Comparar un candidato con sus vecinos: para un icono de 16 px, probar 12 y 24 px; si gana un extremo, repetir desde allí.
- Crear sistemas conforme aparezcan necesidades; no exigir definirlos todos previamente ni repetir la misma decisión menor.

## 2. Jerarquía visual

### 2.1. Distinguir importancia — pp. 36–37

- Clasificar contenido y acciones como principales, secundarios y terciarios. Evitar igual énfasis para todo.
- Destacar lo que permite reconocer, comprender y completar la tarea; suavizar el contenido de apoyo.

### 2.2. No depender solo del tamaño — pp. 38–41

- Combinar tamaño, peso y color. Dar peso al contenido principal antes de agrandarlo; suavizar el secundario antes de volverlo diminuto.
- Comenzar con dos o tres colores de texto y dos pesos: 400/500 para texto normal y 600/700 para énfasis, según la fuente.
- Evitar pesos inferiores a 400 en texto pequeño; reservarlos, si funcionan, para títulos grandes.

### 2.3. Adaptar el texto al fondo de color — pp. 42–45

- Reducir contraste aproximando texto y fondo, conservando legibilidad. Elegir un tono relacionado mediante matiz, saturación y luminosidad.
- Evitar gris neutro indiscriminado o blanco de opacidad reducida: puede parecer deshabilitado y dejar que patrones atraviesen las letras.

### 2.4. Destacar reduciendo la competencia — pp. 46–47

- Si el foco no destaca, suavizar sus competidores: navegación inactiva, paneles secundarios o fondo de sidebar.
- Evitar añadir más énfasis al foco cuando el problema está alrededor.

### 2.5. Usar etiquetas cuando aporten claridad — pp. 48–53

- En datos presentados, omitir etiquetas redundantes cuando formato y contexto identifican correo, teléfono, precio o departamento.
- Combinar aclaración y valor: «12 unidades disponibles» o «3 habitaciones».
- Conservar etiquetas para métricas similares; normalmente enfatizar el dato y suavizar la etiqueta.
- En especificaciones donde se busca «profundidad» o «dimensiones», destacar la etiqueta sin volver ilegible el valor.
- Mantener etiquetas accesibles en formularios: esta simplificación corresponde a presentación de datos.

### 2.6. Separar semántica y apariencia — pp. 54–55

- Elegir h1–h6 por estructura documental y ajustar el estilo por importancia visual; no hacer enorme un título por ser h1.
- Tratar ciertos títulos como etiquetas de apoyo. Si se ocultan visualmente por redundancia, conservar su utilidad para tecnologías de asistencia.

### 2.7. Equilibrar peso y contraste — pp. 56–59

- Reducir contraste de iconos sólidos que pesan más que el texto contiguo.
- Para un borde fino demasiado tenue, probar mayor grosor con color suave antes de oscurecerlo.
- Evaluar la superficie visual ocupada, además de las dimensiones nominales.

### 2.8. Jerarquizar acciones además de su significado — pp. 60–64

- Hacer evidente la acción primaria con fondo sólido contrastante; usar tratamientos menos prominentes para secundarias y discretos para terciarias.
- No convertir automáticamente acciones destructivas en dominantes. En la pantalla habitual pueden ser secundarias; en su confirmación, principales con énfasis de peligro.
- Comunicar claramente la consecuencia y conservar la semántica del control.

## 3. Distribución y espaciado

### 3.1. Comenzar con espacio abundante — pp. 66–69

- Probar más espacio del necesario y reducirlo hasta equilibrar, en lugar de añadir solo lo mínimo para evitar estrechez.
- Evaluar el componente dentro de la pantalla. Elegir densidad compacta deliberadamente si la tarea requiere información simultánea.

### 3.2. Establecer una escala de espacio y tamaño — pp. 70–75

- Evitar escalas lineales interminables: pocos píxeles importan en tamaños pequeños y apenas se perciben en grandes.
- Buscar diferencias relativas cercanas al 25 % o superiores entre vecinos; ampliar saltos conforme aumenta el tamaño.
- Usar la escala visual de la p. 73 como referencia: `4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 640, 768 px`.
- Partir de una base útil, como 16 px, y reutilizar factores y múltiplos; probar el siguiente valor cuando el actual resulte insuficiente.

### 3.3. Usar solo la anchura necesaria — pp. 76–83

- No estirar formularios para llenar la pantalla: si funcionan con 600 px, conservar esa anchura aunque la navegación sea mayor.
- Comenzar con un lienzo móvil de unos 400 px si cuesta diseñar contenido estrecho en un lienzo amplio; ampliar después.
- Separar texto de apoyo y formulario en columnas cuando mejore el equilibrio sin ensanchar campos.
- Permitir más anchura cuando la tarea la necesite; no comprimir sin motivo.

### 3.4. Usar la retícula con criterio — pp. 84–91

- Usar retículas para orden, sin forzar todas las anchuras a porcentajes.
- Dar a la sidebar una anchura ajustada a su contenido y dejar flexible el área principal; 25 % puede crecer o encogerse inconvenientemente.
- Para una tarjeta óptima de 500 px, usar max-width y reducirla solo cuando falte espacio. Evitar que cambios de columnas la hagan mayor en tablet que en escritorio.

### 3.5. Ajustar tamaños independientemente — pp. 92–95

- No reducir toda la interfaz en la misma proporción. En móvil, los elementos grandes suelen reducirse más que los pequeños.
- Interpretar los ejemplos contextualmente: cuerpo de 18 px y título de 45 px en escritorio; cuerpo de 14 px y título de 20–24 px en móvil. Evitar una relación permanente de 2.5 veces.
- Ajustar fuente y padding por separado en variantes de botón; dar más aire proporcional a los grandes y menos a los pequeños. Evitar simples cambios de zoom.

### 3.6. Evitar agrupaciones ambiguas — pp. 96–100

- Mantener menos espacio dentro de un grupo que entre grupos. Acercar etiqueta y campo; separar más el siguiente campo.
- Dar más espacio antes que después de un encabezado que pertenece al contenido siguiente; diferenciar separación entre viñetas de su interlineado.
- Aplicar el mismo criterio horizontalmente.

## 4. Tipografía

### 4.1. Establecer una escala tipográfica — pp. 102–107

- Restringir tamaños; evitar todos los valores de 10 a 24 px sin sistema.
- Usar la escala visual de la p. 105 como referencia: `12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72 px`.
- Si se usa escala modular, redondear valores y comprobar tamaños intermedios útiles; una razón matemática no garantiza adecuación a interfaces.
- Definir tamaños en rem o px para evitar acumulación de em anidados: 1.25em seguido de .875em termina en 17.5 px con base de 16 px.

### 4.2. Elegir buenas fuentes — pp. 108–113

- Comenzar con una sans serif neutra o la fuente del sistema si no existe una razón clara para otra elección.
- Usar variedad de pesos como señal orientativa de calidad: cinco o más pesos, o unos diez estilos contando cursivas, ayudan a filtrar opciones.
- Priorizar altura de x y espaciado adecuados a tamaños reales; evitar fuentes condensadas de titular para texto pequeño.
- Consultar popularidad y tipografía de buenos referentes como filtros. Verificar disponibilidad y licencia de la fuente elegida.
- Conservar recomendaciones históricas en las referencias; no presentar cifras antiguas de disponibilidad en catálogos como actuales.

### 4.3. Controlar longitud de línea — pp. 114–117

- Apuntar a 45–75 caracteres por línea; comenzar con unos 20–35em de anchura y comprobar con la fuente real.
- Limitar párrafos aunque imágenes u otros componentes necesiten una región mayor. Superar 75 caracteres solo por una razón comprobada.
- Distinguir em para anchura de párrafo de em para tamaños tipográficos anidados.

### 4.4. Alinear por línea base — pp. 118–121

- Alinear textos de tamaños distintos por su línea base al compartir fila; evitar centrar sus cajas y desalinear las letras.

### 4.5. Ajustar interlineado al contexto — pp. 122–125

- Usar 1.5 como inicio, no como valor universal; líneas largas pueden requerir cerca de 2.
- Dar más ayuda de interlineado al texto pequeño y menos al grande; un título puede funcionar cerca de 1. Revisar saltos reales.

### 4.6. No colorear intensamente cada enlace — pp. 126–127

- Hacer reconocibles enlaces en párrafos. Donde casi todo sea enlace, usar peso, tono oscuro o indicaciones discretas de interacción.
- En enlaces auxiliares, considerar subrayado o cambio de color en hover; añadir indicación equivalente en foco y asegurar descubrimiento sin ratón.

### 4.7. Alinear para facilitar lectura — pp. 128–131

- Seguir la dirección del idioma; en español, alinear normalmente texto largo a la izquierda.
- Centrar titulares o bloques breves; para más de dos o tres líneas, alinear al inicio o acortar el contenido.
- Alinear números de tablas a la derecha y facilitar comparación decimal.
- Si se justifica texto editorial, activar separación silábica e idioma adecuado para evitar huecos irregulares.

### 4.8. Ajustar espaciado entre letras con propósito — pp. 132–136

- Conservar normalmente el espaciado de la fuente; reducirlo moderadamente en titulares hechos con una fuente de texto abierta.
- Aumentarlo en etiquetas completamente en mayúsculas.
- No convertir una fuente de titulares en fuente de texto pequeño solo aumentando espaciado.

## 5. Color

### 5.1. Trabajar con HSL — pp. 138–141

- Ajustar matiz en grados, saturación y luminosidad en porcentajes.
- Recordar rojo 0°, verde 120°, azul 240°; saturación 0 % elimina matiz; luminosidad 0 % es negro y 100 % blanco.
- No confundir HSL con HSB: en HSB, brillo 100 % produce blanco solo con saturación 0 %; con saturación plena produce color puro.
- Usar HSL para construir paletas; conservar otros formatos si el proyecto los necesita. No interpretar la recomendación como prohibición de otros espacios de color.

### 5.2. Preparar una paleta suficiente — pp. 142–147

- Definir neutros para la mayor parte de la interfaz, uno o dos colores principales para acciones y marca, y acentos para estados y categorías.
- Preparar unos 8–10 neutros y 5–10 tonos por color principal o acento; ampliar solo según necesidad.
- Comenzar con gris muy oscuro en vez de negro puro si resulta más natural; usar extremos claros para fondos y oscuros para texto.
- Reservar acentos para advertencias, peligro, tendencias, novedades, gráficos, calendarios o etiquetas. Una interfaz compleja puede necesitar unas diez familias; una sencilla no necesita todas.

### 5.3. Definir tonos antes de usarlos — pp. 148–151

- Evitar variaciones aisladas mediante lighten/darken en cada componente.
- Elegir un tono base útil para un botón y extremos según usos reales: texto oscuro y fondo claro de una alerta.
- Para nueve tonos, fijar 900 oscuro, 500 base y 100 claro; completar 700 y 300, después 800, 600, 400 y 200.
- Para neutros, comenzar por texto oscuro y fondo casi blanco. Ajustar visualmente al probar componentes; no confiar solo en interpolación ni añadir tonos casi idénticos.

### 5.4. Conservar intensidad al variar luminosidad — pp. 152–157

- Aumentar saturación hacia extremos de luminosidad cuando sea posible para evitar tonos deslavados.
- Distinguir luminosidad HSL y brillo percibido: amarillo puede parecer más brillante que azul con idéntica luminosidad.
- Conservar la fórmula ilustrativa de la p. 153: `brillo ≈ sqrt(0.299*r² + 0.587*g² + 0.114*b²) / 255`, con RGB entre 0 y 255. No usarla para validar contraste WCAG.
- Para aclarar manteniendo intensidad, desplazar ligeramente matiz hacia 60°, 180° o 300°; para oscurecer, hacia 0°, 120° o 240°. Por ejemplo, llevar amarillo hacia naranja en tonos oscuros.
- Combinar matiz y luminosidad; limitar normalmente rotación a unos 20–30° para conservar identidad. Confirmar visualmente.

### 5.5. Dar temperatura a neutros — pp. 158–161

- Añadir azul para neutros fríos, amarillo o naranja para cálidos; ajustar intensidad a la personalidad.
- Aumentar saturación en extremos claros y oscuros cuando haga falta para mantener temperatura coherente.

### 5.6. Mantener accesibilidad y personalidad — pp. 162–165

- Conservar la recomendación del libro: contraste 4.5:1 para texto normal y 3:1 para grande. Su referencia aproximada a 18 px no define correctamente por sí sola texto grande.
- Para implementar, aplicar la precisión complementaria del [criterio 1.4.3 de W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html): texto grande desde 18 pt, equivalentes a 24 CSS px, o 14 pt en negrita, aproximadamente 18.67 CSS px. No redondear un contraste insuficiente para hacerlo pasar.
- Si blanco sobre un fondo intenso obliga a oscurecer demasiado un elemento secundario, invertir: texto oscuro de color sobre fondo claro tintado.
- En paneles oscuros, probar pequeños giros hacia matices más brillantes para diferenciar texto secundario sin hacerlo todo blanco. Medir contraste con luminancia relativa.

### 5.7. No transmitir significado solo con color — pp. 166–170

- Añadir signos, flechas, texto o iconos que permitan entender estados y tendencias sin distinguir rojo y verde.
- En gráficos, aprovechar diferencias de luminosidad y complementar con etiquetas, patrones o trazos cuando sea necesario.
- Comprobar que el color refuerza un mensaje ya comprensible.

## 6. Profundidad

### 6.1. Simular una luz coherente — pp. 172–179

- Usar luz conceptual desde arriba: para relieve, iluminar borde superior y añadir sombra corta debajo.
- Para hundimiento, iluminar borde inferior y usar sombra interior arriba; aplicar a campos o casillas cuando encaje.
- Elegir a mano las luces para evitar desaturación por blanco superpuesto. Mantener sombras de borde nítidas y discretas; evitar fotorrealismo que añada ruido.

### 6.2. Comunicar elevación con sombras — pp. 180–185

- Relacionar sombra con altura y atención: pequeña para botones, intermedia para desplegables, mayor para modales.
- Definir una escala finita, por ejemplo cinco niveles; comenzar por extremos y completar intermedios.
- Elevar elementos al arrastrarlos y reducir sombra al presionar botones. Elegir la altura conceptual antes de sus valores.

### 6.3. Combinar dos sombras con funciones distintas — pp. 186–189

- Combinar sombra amplia y suave de luz directa con otra pequeña y oscura de contacto u oclusión ambiental.
- Atenuar la sombra de contacto al aumentar elevación; puede casi desaparecer en el nivel superior.
- Evitar una misma combinación rígida para todas las alturas.

### 6.4. Dar profundidad a un diseño plano — pp. 190–193

- Usar superficies más claras que su fondo para sugerir cercanía y más oscuras para hundimiento, especialmente dentro de una familia cromática.
- Considerar sombras sólidas, cortas y sin desenfoque si son coherentes con la estética.

### 6.5. Superponer para crear capas — pp. 194–198

- Cruzar transiciones de fondo con tarjetas, extender elementos fuera de contenedores o superponer controles cuando aporte profundidad.
- Separar imágenes superpuestas con un borde del color del fondo para evitar choques.
- Comprobar recortes, orden de capas y adaptación móvil.

## 7. Imágenes

### 7.1. Utilizar buena fotografía — pp. 200–201

- Trabajar con imágenes finales de calidad o representativas del material disponible. Considerar fotografía profesional para necesidades específicas y bancos adecuados para genéricas.
- No depender de una imagen provisional excelente que se sustituirá por material inferior. Evaluar luz, composición y color además de resolución.

### 7.2. Mantener contraste consistente sobre imágenes — pp. 202–207

- Examinar zonas claras y oscuras bajo el texto; cambiar solo las letras no resuelve un fondo variable.
- Usar overlay negro para texto claro o blanco para oscuro; ajustar intensidad con imágenes reales.
- Alternativamente, reducir contraste y compensar brillo. Para teñir: reducir contraste → desaturar → aplicar color con mezcla multiply.
- Para conservar detalle, combinar moderación del contraste con sombra difusa de texto sin desplazamiento, semejante a un halo.
- Comprobar variantes y recortes; el efecto visual no garantiza contraste suficiente.

### 7.3. Respetar el tamaño previsto de cada recurso — pp. 208–213

- Evitar ampliar mapas de bits más allá de su resolución útil.
- No ampliar automáticamente SVG de 16–24 px tres o cuatro veces: mantienen nitidez, pero pueden verse pobres o gruesos. Elegir variante adecuada o mantener el icono pequeño dentro de una forma mayor.
- Evitar capturas complejas reducidas hasta volver ilegible el texto. Capturar una interfaz más estrecha, reservar espacio, recortar una región o simplificar detalles y sustituir texto minúsculo por líneas.
- Preparar un favicon simplificado a 16 px, en vez de reducir un logotipo complejo; revisar también iconos grandes reducidos.

### 7.4. Contener imágenes subidas por usuarios — pp. 214–218

- Establecer contenedores de forma, tamaño y proporción coherentes; centrar y recortar con cover u object-fit sin deformar.
- Evitar que imágenes claras se fundan con el fondo mediante sombra interior sutil o borde interior semitransparente; un borde externo rígido puede chocar con sus colores.
- Probar imágenes claras, oscuras, horizontales y verticales; conservar el sujeto relevante al recortar.

## 8. Acabado

### 8.1. Mejorar elementos existentes — pp. 220–223

- Sustituir viñetas por iconos relacionados, destacar comillas en testimonios o refinar enlaces con peso, color y subrayado.
- Aplicar color de marca a estados seleccionados de radios y casillas cuando aporte coherencia.
- Conservar nombre, estado, foco, teclado y área utilizable al personalizar controles. Evitar adornos que compitan con la tarea.

### 8.2. Añadir bordes de acento — pp. 224–227

- Considerar acentos arriba de tarjetas, en navegación activa, al lado de alertas, bajo titulares o arriba del sitio.
- Usarlos para atención o identidad, sin decorar indiscriminadamente todo.

### 8.3. Decorar fondos con moderación — pp. 228–233

- Diferenciar paneles o secciones con color; comenzar degradados discretos con matices separados como máximo unos 30°.
- Añadir patrones suaves en una zona o en su borde, con bajo contraste.
- Usar formas geométricas, fragmentos de patrón o ilustraciones discretas, como un mapa simplificado, si mejoran la composición.

### 8.4. Diseñar estados vacíos — pp. 234–237

- Tratar ausencia de contenido como una primera experiencia importante en funciones dependientes de datos del usuario.
- Explicar el siguiente paso y destacar la acción que genera contenido; añadir ilustración si ayuda.
- Ocultar filtros o pestañas todavía inútiles. Distinguir ausencia de contenido de ausencia de resultados filtrados.

### 8.5. Usar menos bordes — pp. 238–241

- Probar separación mediante espacio, fondos diferentes o sombras sutiles.
- Retirar bordes redundantes con fondos diferenciados. Una sombra delimita mejor cuando superficie y fondo tienen colores distintos.
- Mantener bordes que realmente comuniquen límites o estados.

### 8.6. Reconsiderar convenciones de componentes — pp. 242–248

- Crear desplegables con secciones, columnas, iconos o texto de apoyo cuando mejore la elección.
- Combinar datos relacionados en celdas cuando no requieran ordenación independiente; introducir jerarquía, imágenes o estados sin perjudicar comparación.
- Usar tarjetas seleccionables para opciones importantes cuando convenga, conservando semántica y comportamiento de selección única.
- Adoptar variantes por mejoras de comprensión, no solo por novedad.

## 9. Desarrollar criterio — pp. 250–252

- Estudiar decisiones que no se habrían tomado espontáneamente: invertir fondo de calendario, integrar botón en input o usar dos tonos en un titular.
- Recrear una interfaz sin consultar primero sus estilos; comparar discrepancias para descubrir interlineado, espaciado de mayúsculas, sombras y otros detalles.
- Extraer principios transferibles y probarlos en el contexto propio.

## Ejemplos de aplicación

| Solicitud | Aplicación concreta | Verificación |
| --- | --- | --- |
| «Este dashboard se ve saturado». | Priorizar cifras, suavizar etiquetas, destacar Guardar, reducir Eliminar a su nivel y añadir texto o signos a tendencias. | Revisar escala de grises, prioridad de acciones y contraste. |
| «El formulario cambia de tamaño de forma extraña». | Limitar anchura óptima con max-width, reducirlo solo cuando no quepa y separar más grupos que etiqueta y campo. | Revisar móvil, tablet, escritorio y contenido largo. |
| «El hero es ilegible y sus iconos se ven pobres». | Regular fondo bajo texto, medir contraste y usar iconos adecuados o contenedores mayores. | Probar fotos y recortes alternativos; revisar a tamaño real. |

## Lista de verificación y ciclo de corrección

- [ ] La funcionalidad y acción principal son claras; no se promete una capacidad inexistente.
- [ ] La jerarquía distingue niveles sin tamaños extremos ni texto ilegible.
- [ ] La separación entre grupos supera la interna y evita asociaciones ambiguas.
- [ ] Anchuras y adaptación responden al contenido; no se escala todo indiscriminadamente.
- [ ] Tipografía y espaciado usan tokens coherentes; párrafos y alineación facilitan lectura.
- [ ] La paleta es finita; estados y categorías se entienden sin color.
- [ ] Se mide contraste cuando hay colores verificables; se distingue estimación de medición.
- [ ] Sombras, luz y superposición comunican capas sin ruido ni recortes.
- [ ] Fotografías, iconos, capturas y contenido subido funcionan a sus tamaños finales.
- [ ] Se revisaron estados vacíos y, cuando existen, error, carga, selección, foco y contenido extremo.
- [ ] Se ejecutaron las comprobaciones posibles; se corrigieron y revisaron los fallos.
- [ ] Se consultó la referencia pertinente y se identificaron aportaciones complementarias al libro.

Si falla una comprobación, identificar elemento y regla afectados, corregir y repetir la revisión correspondiente. No afirmar que se probaron interacciones, contraste, otros modelos o tamaños si no se hizo.

## Entrega de resultados

Para una revisión, presentar propuestas priorizadas con `Elemento → problema observado → cambio concreto → criterio de verificación`. Citar páginas cuando se explique una regla específica. Evitar diagnosticar partes no vistas.

Para implementar, entregar código o artefacto solicitado, explicar brevemente qué cambió y qué se comprobó, y conservar contenido, semántica y comportamiento necesarios. Para consultas conceptuales, responder con la regla y un ejemplo sin convertirlas automáticamente en una auditoría.
