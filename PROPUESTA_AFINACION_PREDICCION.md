# Propuesta fundamentada para afinar la predicción de `reto-fira`

> **Estado: implementada y evaluada el 17 de octubre de 2026.** Este documento conserva la propuesta previa a los nuevos experimentos; las expresiones «actual» y «no se entrenaron modelos nuevos» describen ese momento. El [reporte de implementación](REPORTE_IMPLEMENTACION_PREDICCION.md) contiene el dictamen vigente, la mezcla Ridge/Random Forest, las métricas verificadas y las 59 predicciones actualizadas. Las referencias a las métricas y entrega anteriores apuntan ahora al respaldo preservado.

**Reto AgroCebada FIRA 2026 · Revisión del 17 de octubre de 2026**  
**Objetivo:** mejorar la estimación del rendimiento de grano, en t/ha, de las 59 parcelas de `PREDICCION`.  
**Alcance:** propuesta metodológica y revisión de evidencia existente. No se generó código, no se entrenaron modelos nuevos y no se modificaron las predicciones.

## 1. Respuesta a la pregunta principal

**Todavía no se puede saber cuál de los tres CSV es más preciso en las 59 parcelas.** Sus rendimientos reales están ocultos y reservados para la evaluación del organizador. La cercanía entre predicciones, su apariencia agronómica o la sofisticación del algoritmo no sustituyen la comparación contra valores observados. La comparación defendible consiste en simular esa situación con las 138 parcelas etiquetadas: ocultar sus rendimientos durante el ajuste, predecirlas y medir el error mediante un protocolo común. [F1], §1; [W1], p. 4; [B2], §2.2, p. impresa 29 / PDF 39.

**Recomendación:** conservar `reto-fira` como referencia y candidato de entrega mientras se comprueban mejoras. Tiene una separación entre selección y evaluación más rigurosa que las otras dos implementaciones. Aprovecharía de `proposal-01` la comparación con Ridge y de `proposal-02` la idea de resúmenes agronómicos compactos y de un ensamble pequeño, pero sometería todo a validación anidada. No copiaría sus predicciones ni sus procedimientos de evaluación. Esto favorece la calidad de la evidencia; **no demuestra que el CSV actual gane en las parcelas ocultas**. [R1], funciones `pipeline`, `select_model` y `evaluate`; [P1]; [P2b]; [P2c]; [B9], §7.10.2, PDF 265.

La primera hipótesis que probaría es **ajustar el predictor puntual final con las 138 etiquetas, en lugar de reservar 28 exclusivamente para calibrar intervalos**. La segunda es reducir redundancia y mejorar los resúmenes temporales, comparando regresión regularizada y árboles moderados. Son hipótesis, no mejoras demostradas. La literatura respalda seleccionar la configuración y después reajustar con las observaciones disponibles; FIRA solicita un valor puntual y considera complementaria la incertidumbre. [B2], §6.2.3, PDF 260; [F4], pregunta 7.

## 2. Qué se verificó y qué significa la evidencia

Se revisaron los tres CSV actuales, las implementaciones que los producen, sus métricas guardadas, los tres DOCX oficiales, el PDF de ecuaciones, los tres LEEME de los insumos y pasajes pertinentes de los nueve PDF bibliográficos solicitados. Las páginas bibliográficas citadas se extrajeron de los PDF originales; los DOCX se cotejaron con su contenido original. No se afirma una lectura íntegra de todos los libros.

En este documento:

- **Hecho observado** significa comprobado en los archivos actuales o en una fuente oficial.
- **Resultado existente** significa obtenido en ejecuciones anteriores y guardado en el proyecto; se identifica cuando solo se transcribe.
- **Decisión propuesta** significa un criterio de trabajo recomendado aquí. Las citas justifican el principio, pero no prueban que la decisión reduzca el error de estas 59 parcelas.
- **Hipótesis** significa una modificación que requiere evaluación antes de adoptarse.

Los identificadores de referencia, como [F4] o [B9], son enlaces. La sección 10 identifica cada fuente y su ubicación. En los PDF, «PDF» cuenta páginas físicas desde 1; «impresa» corresponde a la numeración del libro.

### 2.1 Correspondencia de archivos y datos

La tabla oficial contiene 197 parcelas: 138 con etiqueta y 59 de predicción. Los tres CSV de comparación tienen exactamente esos 59 identificadores, sin duplicados, valores numéricos ausentes, infinitos o no positivos. Sus encabezados difieren, pero declaran rendimiento en t/ha. Cada archivo coincide byte por byte, mediante SHA-256, con la salida correspondiente de su proyecto. [F8]; [C0]; [C1]; [C2]; salidas identificadas en la sección 10.4.

Los tres CSV originales de insumos —maestro de rendimientos, Básico y PRO— tienen hashes idénticos entre los tres proyectos. Esto confirma que comparten esos datos originales. **No implica que los modelos reciban la misma información después de extraer, filtrar, agregar e imputar.** No se realizó una comparación de hashes de todos los GeoTIFF.

| Archivo actual | Propuesta | Media predicha | Mínimo | Máximo |
|---|---|---:|---:|---:|
| `proposal.csv` | `reto-fira` | 3.8980 | 2.8941 | 4.9140 |
| `proposal-01.csv` | `proposal-01` | 3.8764 | 2.4755 | 5.3221 |
| `proposal-02.csv` | `proposal-02` | 3.9193 | 2.9096 | 4.9825 |

Unidades: t/ha. Cálculos descriptivos sobre los 59 valores de [C0], [C1] y [C2], sin usar etiquetas ocultas.

| Par de propuestas | Diferencia absoluta media | Raíz de diferencia cuadrática media |
|---|---:|---:|
| `reto-fira` frente a `proposal-01` | 0.3503 | 0.4731 |
| `reto-fira` frente a `proposal-02` | 0.1748 | 0.2246 |
| `proposal-01` frente a `proposal-02` | 0.3225 | 0.3933 |

Estas son **diferencias entre predicciones**, calculadas al unir por identificador; no son MAE o RMSE contra la verdad. Por ejemplo, `AGC_031` recibe 4.4444, 2.9888 y 4.2317 t/ha, respectivamente: un desacuerdo de 1.4556 t/ha que merece revisar sus insumos, pero que no indica qué valor corregir. [C0]; [C1]; [C2]; [B2], PDF 39.

**Decisión D1.** Utilizar el desacuerdo para priorizar revisión de datos —`AGC_031`, `AGC_118`, `AGC_065`, `AGC_003` y `AGC_091` presentan los cinco mayores rangos—, sin ajustar manualmente sus rendimientos hacia el promedio de las propuestas. Si se detecta un error verificable de extracción, se corrige la regla general y se reevalúa; no se inventa una corrección parcelaria. [C0]; [C1]; [C2]; [B5], cap. 2, PDF 70; [B9], PDF 265.

### 2.2 No reutilizar una comparación anterior como si fuera esta

El proyecto contiene una [auditoría anterior de comparación][R8] que usa las denominaciones `agrocebada_hidden` y `Predicciones-agroceba`. Sus diferencias entre CSV no corresponden a los archivos actuales `proposal-01.csv` y `proposal-02.csv`. Esta propuesta recalculó los descriptivos anteriores con los archivos indicados en la solicitud. Los experimentos previos de `reto-fira` sí pueden aportar antecedentes, siempre identificados como resultados existentes y sin atribuirlos a los otros proyectos.

## 3. Diagnóstico de las tres implementaciones

### 3.1 `proposal-01`: Ridge es una idea aprovechable, pero su extracción climática limita la comparación

La implementación construye 203 predictores, conserva observaciones de abril a octubre de 2025 y separa sensores. Su configuración guardada admite nubosidad de hasta 100%. Compara mediana, Ridge, Random Forest y Gradient Boosting en cinco folds espaciales sobre 12 bloques de 10 km. Selecciona Ridge con `alpha=10` y lo reajusta con las 138 etiquetas. La imputación y el escalado están dentro del ajuste de cada fold. [P1], funciones `satellite_features`, `evaluate_models` y `main`; [P1m].

**Hallazgo crítico observado:** en su tabla de características hay 84 columnas climáticas; **196 de las 197 parcelas carecen de valores en todas ellas**. Solo `AGC_101` tiene valores climáticos extraídos. La media topográfica tiene datos para 180 parcelas en elevación y 179 en pendiente. [P1f], columnas con prefijos `precip_`, `tmin_`, `tmax_` y `topo_`.

El código utiliza una máscara con `all_touched=False`: selecciona píxeles cuyo centro está dentro de la parcela. Con clima de aproximadamente 5 km y parcelas pequeñas, muchas geometrías no contienen ningún centro, aunque estén dentro de la cobertura del raster. El patrón observado es consistente con ese mecanismo; no representa ausencia real de lluvia o temperatura en 196 parcelas. [P1], `zonal_features`, línea 72; [F5]; [F6].

En contraste, `reto-fira` pondera las intersecciones entre parcela y celda por su área. Su tabla ambiental tiene valores de precipitación, Tmin y Tmax de abril de 2025 para las 197 parcelas; conserva faltantes de relieve cuando no supera su cobertura mínima. Esta es una ventaja de integración que conviene preservar. [R2], `zonal_mean` y `extract_environment`; [R5].

**Decisión D2.** No trasladar la extracción de `proposal-01`. Recuperar su hipótesis de un modelo lineal regularizado y probarla sobre las características correctamente extraídas de `reto-fira`. Si se quiere evaluar la metodología de `proposal-01`, distinguir su versión original de una versión corregida; la segunda produciría otro modelo y otro CSV. [P1f]; [R2]; [B2], §6.2.1, PDF 248 y 252.

**Límite de sus métricas:** los mismos folds sirven para escoger la familia y comunicar el error del ganador. Además, reporta medias de métricas por fold, no métricas globales sobre todas las predicciones fuera de muestra. No equivalen a una evaluación externa del proceso completo de selección. [P1], `evaluate_models`; [B9], §7.2, PDF 241.

### 3.2 `proposal-02`: buenos candidatos de variables, evaluación optimista y ensamble sin evaluación externa propia

Esta propuesta genera resúmenes climáticos y satelitales, usa nubosidad de 20%, selecciona 12 variables y combina RF, XGBoost y Ridge. Los pesos guardados son aproximadamente 0.3423, 0.3385 y 0.3192, obtenidos como el inverso normalizado del RMSE de cada modelo. Los modelos finales se ajustan con 138 etiquetas. [P2a]; [P2b]; [P2c]; [P2m].

Hay cuatro problemas que impiden trasladar sus resultados como evidencia de superioridad:

1. **Selección supervisada antes de validar.** Calcula correlación con el rendimiento sobre las 138 parcelas y selecciona variables antes de ejecutar la CV. Las etiquetas de las futuras validaciones ya influyeron en qué predictores entran. Es el tipo de procedimiento que ESL exige repetir dentro de cada partición. [P2b], líneas 159–168 y 217–228; [B9], §7.10.2, PDF 265.
2. **Reutilización de CV para optimización y evaluación.** Busca hiperparámetros y después evalúa los ganadores sobre los mismos folds, sin una capa externa que evalúe la búsqueda. El mínimo obtenido puede ser optimista. [P2c], funciones `train_random_forest`, `train_xgboost`, `train_ridge` y bloque de línea 253; [B9], PDF 241.
3. **Falta una evaluación externa del ensamble entregado.** El archivo de metadatos guarda métricas de los tres componentes; el error del ensamble calculado en el código es sobre entrenamiento. No equivale al error del CSV combinado en parcelas no vistas. El peso inverso del RMSE tampoco incorpora por sí solo la correlación entre errores de modelos. [P2c], `compute_ensemble_weights` y bloque de línea 269; [P2m]; [B2], PDF 39.
4. **La incertidumbre y la explicación corresponden a otro objeto.** El intervalo se construye con ±1.96 desviaciones entre árboles del RF alrededor del ensamble; SHAP se calcula para RF. Esa dispersión no demuestra cobertura predictiva del ensamble, ni las contribuciones de un componente explican por sí solas toda la mezcla. [P2d], líneas 48–65 y 127–135; [W6], §§2.3 y 3; [B4], §8.5.

La imputación también está definida antes de CV y calcula las medianas de predicción por separado. Es una regla que se debe corregir al reutilizar el procedimiento. **Matiz:** en las tablas actuales no encontré celdas vacías en las 12 variables finalmente seleccionadas, ni en entrenamiento ni en predicción. Por tanto, no atribuyo a esa imputación un efecto numérico demostrado en este CSV; la fuga observada está en la selección con las etiquetas y en la evaluación de la búsqueda. [P2b], `impute_median`; [P2x]; [B7], PDF 400; [B9], PDF 265.

**Decisión D3.** Retomar los resúmenes de temperatura, distribución mensual de lluvia, vigor y humedad como candidatos; volver a seleccionar su utilidad dentro de CV. No declarar universales el corte de correlación 0.30, VIF 10, nube 20% ni las 12 variables actuales. De hecho, varias de estas últimas tienen correlación absoluta menor que 0.30, por la salvaguarda de selección del código. [P2b]; [P2s]; [F2], «Consideraciones para el análisis»; [B9], PDF 265.

### 3.3 `reto-fira`: conservar la separación de datos y medir dónde aporta señal

El modelo actual selecciona entre seis familias y tres umbrales de nube, es decir, 18 combinaciones. La imputación con indicadores, eliminación de constantes, estandarización y selección supervisada están dentro del pipeline. La selección de familia y nubosidad se realiza en CV interna, y la evaluación externa separa parcelas completas. El modelo final guardado es Random Forest, nube ≤60%, selección de 60 características; ajusta con 110 parcelas y reserva 28 para calibración. [R1]; [R3].

No encontré en ese código la selección global de predictores con las etiquetas de validación que sí aparece en `proposal-02`. Tampoco hay fundamento para afirmar que corregir ese problema mejorará `reto-fira`: la protección ya existe. Su CV externa selecciona con tres folds internos; la selección final usa cinco. Para el nuevo estudio conviene fijar y describir el número de folds internos de cada procedimiento, evitando presentar variantes como idénticas. [R1], `select_model`, `evaluate` y `run`.

Los MAE y RMSE siguientes se recalcularon directamente desde las 138 predicciones OOF guardadas, verificando unicidad y correspondencia de identificadores. R² se transcribe de los metadatos correspondientes. OOF significa que cada parcela fue predicha sin usar su etiqueta en ese ajuste. [R3]; [R4a]; [R4b].

| Procedimiento existente | MAE (t/ha) | RMSE (t/ha) | R² | Interpretación |
|---|---:|---:|---:|---|
| `reto-fira`, CV anidada por parcela | 0.4077 | 0.5613 | 0.5619 | Referencia principal disponible; no error observado de las 59 ocultas. |
| `reto-fira`, CV anidada espacial de 20 km | 0.8048 | 0.9555 | −0.2694 | Estrés de transferencia geográfica, con solo seis bloques. |
| `proposal-01`, Ridge; medias de folds espaciales de 10 km | 0.5757 | 0.6967 | −1.2720 | Valores guardados; selección y evaluación sobre los mismos folds. |
| `proposal-02`, RF optimizado; medias de folds aleatorios | 0.4090 | 0.5422 | 0.5561 | Valores guardados, con selección global y CV reutilizada; RF es solo un componente. |

**Esta tabla no es un ranking.** Cambian extracción, particiones, tamaños de ajuste, selección y agregación de métricas. En particular, 0.5422 de `proposal-02` no prueba que su ensamble supere a `reto-fira`. [P1m]; [P2m]; [R1]; [B9], §§7.2 y 7.10.2.

Un diagnóstico previo de `reto-fira` aporta dos advertencias útiles: una mediana por estado obtiene MAE OOF 0.4322 frente a 0.4077 del modelo, y hay 181 características para 138 etiquetas, con 85 pares de correlación absoluta >0.98. Son resultados existentes, no recalculados en esta revisión. Sugieren comprobar cuánto valor añadido existe dentro de cada región y si la redundancia perjudica la estabilidad; no prueban que deba eliminarse el satélite. [R6]; [B2], PDF 252; [B4], PDF 216.

**Decisión D4.** Conservar referencias globales y añadir una referencia por estado aprendida únicamente con el entrenamiento de cada fold, con respaldo global si un estado no está representado. Reportar MAE, RMSE y sesgo por estado, número de parcelas y cobertura de insumos. La referencia regional ayuda a distinguir predicción entre regiones de discriminación entre parcelas vecinas. [R6]; [F1]; [B3], cap. 6, PDF 166. El uso concreto de esa referencia es una decisión diagnóstica de esta propuesta.

## 4. Protocolo para saber qué procedimiento predice mejor

### 4.1 Definir la tarea y la métrica antes de comparar

Aquí se estima una **cantidad continua de un ciclo ya ocurrido**, abril–octubre de 2025. No se necesita convertir el rendimiento en clases ni predecir una probabilidad de evento futuro. Regresión estadística y aprendizaje automático se solapan: Ridge aprende de los datos, y los árboles también pueden hacer regresión. Un método flexible no es automáticamente más preciso con 138 etiquetas. [F1], §1; [B2], §§2.2 y 6.2; [B6], resumen.

**Decisión D5.** Mantener **MAE como criterio primario provisional** por su interpretación directa en t/ha y su continuidad con el selector actual; usar **RMSE como salvaguarda frente a errores grandes**, y reportar R² y sesgo. No se afirma que MAE sea la métrica oficial exclusiva: las bases mencionan RMSE, MAE, r² u otras que defina el Comité. Si existe una comunicación oficial adicional con fórmula de puntuación, debe sustituir esta prioridad antes de la selección. [R1], ordenación de `scores`; [W1], p. 5, «Criterios de evaluación»; [B6], PDF 1.

Definiendo el error como predicción menos rendimiento observado, MAE es la media de su valor absoluto; RMSE es la raíz de la media de su cuadrado; el sesgo es la media del error con signo. Sesgo positivo significa sobreestimación. R² compara la suma de errores cuadrados con la variación del rendimiento observado respecto de su media. **R²=0.56 no significa “56% de precisión”.** Las métricas deben calcularse sobre el mismo conjunto de predicciones fuera de muestra. [R1], `metrics`; [B2], §2.2.

Cada parcela tendrá el mismo peso en la métrica principal propuesta. Ponderar por área cambiaría el objetivo hacia producción agregada y requeriría una justificación adicional. No confundir t/ha con toneladas totales, que resultan de multiplicar por hectáreas. [F4], preguntas 6–8; decisión de evaluación propuesta.

### 4.2 Comparación común, anidada y por parcela

**Decisión D6.** Preparar un protocolo congelado con estas condiciones:

1. **Unidad independiente de partición: la parcela.** Todas sus fechas y sensores permanecen del mismo lado. Las muchas filas satelitales no aumentan el número de etiquetas independientes por encima de 138. La agregación fija por parcela puede preceder a CV si no aprende de los rendimientos ni de las otras parcelas. [F1], §§1–2; [B9], PDF 265.
2. **Cinco folds externos compartidos.** En cada repetición, cada una de las 138 parcelas tiene una predicción externa. Los modelos candidatos reciben exactamente los mismos IDs externos. Comparar procedimientos completos, incluyendo selección, transformaciones y, si corresponde, reserva de calibración. [B9], §§7.2 y 7.10.2.
3. **Cinco repeticiones predefinidas como presupuesto de estabilidad.** Conservar las semillas existentes 20261013 y 20261014 y añadir 20261015, 20261016 y 20261017 antes de ejecutar. Cinco repeticiones es una decisión operativa, no una regla del libro ni 690 parcelas independientes. [B2], §5.1.1, PDF 211; [R7p].
4. **Selección interna de tres folds**, idéntica para los nuevos candidatos y congelada también para su selección final. Dentro se eligen grupo de variables, nube, regularización, familia y cualquier peso de ensamble. Imputación, escalado y filtros aprendidos se recalculan sin observar la validación interna. [B9], PDF 265; [B7], PDF 400.
5. **Separar auditoría original de comparación corregida.** La sección 3 documenta las implementaciones originales y sus limitaciones. La nueva comparación de precisión debe ejecutar sus procedimientos corregidos bajo el protocolo común; no conservar la fuga de selección para fabricar un ranking. Reparar `proposal-01` o `proposal-02` produce variantes cuyos resultados ya no validan retrospectivamente sus CSV originales. [P1]; [P2b]; [P2c]; [B9], PDF 241.
6. **Recalcular métricas globales por repetición a partir de las 138 OOF.** Reportar además dispersión entre repeticiones. No promediar RMSE o R² de folds y llamarlos métricas globales. No evaluar la media de cinco OOF por parcela como si fuera una única predicción del mismo procedimiento: ese promedio corresponde a un ensamble distinto. [R1], contraste con [P1] y [P2c]; definiciones de métricas anteriores.

Para evitar optimismo adicional, el conjunto de recetas a seleccionar debe entrar en la selección interna. Si después de observar errores externos se cambia el conjunto de candidatos, el resultado pasa a ser de desarrollo exploratorio. Repetir semillas no vuelve a hacer vírgenes las 138 etiquetas. Con los datos disponibles, la evaluación externa final realmente reservada sigue siendo la del organizador. [B9], PDF 241 y 265; [W1], p. 4.

### 4.3 Papel de la validación espacial

**Decisión D7.** Usar la CV por parcela como aproximación principal al reto, y acompañarla de una prueba espacial común de 20 km y sensibilidad de 10 km. Los tamaños se proponen por continuidad con las implementaciones existentes; ningún libro establece que sean universalmente correctos ni que eliminen toda dependencia. Mantener los bloques fuera del ajuste, selección y calibración del fold espacial. [P1]; [R1]; [B3], PDF 166.

La justificación es específica: FIRA informa muestreo aleatorio estratificado, sin publicar aquí los estratos. Además, el diagnóstico espacial existente sitúa todas las parcelas ocultas a menos de 1.91 km del centroide de alguna parcela etiquetada; 49/59 comparten un vector de 40 variables climáticas con alguna etiqueta. Esto sugiere interpolación dentro de zonas conocidas, sin demostrar independencia ni revelar cómo se hizo la partición oficial. [F4], pregunta 9; [R6].

Si se equilibra por estado, declararlo como aproximación del equipo, no como reconstrucción de los estratos oficiales. Registrar tamaños de bloques, distancias al entrenamiento y errores dentro de cada estado. Un peor resultado espacial informa sobre transferencia a zonas no vistas; no es por sí solo prueba de fuga de etiquetas. Tampoco debe ocultarse porque la entrega sea local. [F4], pregunta 9; [B3], caps. 6 y 11, PDF 166 y 348.

No construir una validación temporal ficticia de 2022–2024 asignando a esos años el rendimiento de 2025. Existe un solo ciclo etiquetado y se desconoce la rotación anterior. [F1], §1; [F4], pregunta 10.

### 4.4 Regla para promover una mejora

**Decisión D8.** Antes de ejecutar, fijar una regla conservadora de sustitución:

- Comparar pérdidas pareadas sobre los mismos IDs: para cada parcela, restar el error absoluto actual al error absoluto nuevo. Una diferencia negativa favorece al nuevo procedimiento.
- Exigir menor MAE agregado de las repeticiones y que el signo de la mejora no dependa de una sola partición. Reportar todas las repeticiones, no solo la favorable.
- Exigir que el RMSE agregado no aumente. Reportar cualquier deterioro por estado y en cada esquema espacial; para esta iteración se propone no promover un candidato que empeore sistemáticamente ambos esquemas espaciales.
- Examinar intervalos descriptivos de las diferencias mediante remuestreo pareado de parcelas y, como sensibilidad, de bloques. Con pocos bloques y etiquetas reutilizadas, no tratarlos como prueba definitiva ni usar las repeticiones como observaciones independientes.
- Si la ventaja es pequeña, inestable o compatible con ausencia de mejora, mantener la entrega actual. Dentro del selector, una preferencia por menor complejidad debe quedar fijada antes de evaluar; la regla de un error estándar puede inspirar esa preferencia, pero no certifica equivalencia estadística entre algoritmos.

La separación entre selección y evaluación se sustenta en [B9], PDF 241 y 265; la variabilidad de particiones y la preferencia por modelos sencillos en [B2], PDF 211 y 248; la sensibilidad a dependencia espacial en [B3], PDF 166. La combinación concreta de requisitos anterior es una **política operativa propuesta**, no un umbral de FIRA ni una garantía bibliográfica.

## 5. Qué afinar: decisiones técnicas ordenadas por prioridad

### 5.1 Preservar la extracción geográfica y auditar la cobertura

**Decisión D9.** Mantener el cálculo de `reto-fira` por intersección y área en el CRS del raster. Conservar el diagnóstico de cobertura, NoData y número de celdas. No cambiarlo por la máscara de centros de `proposal-01`, ni asumir que reproyectar y luego incluir todos los píxeles tocados, como en `proposal-02`, recupera la misma estadística. Son operaciones distintas y pueden alterar los predictores. [R2]; [P1], `zonal_features`; [P2e]; [F1], «Consideraciones para los participantes».

Los LEEME especifican lluvia acumulada mensual en mm/mes, Tmin/Tmax como promedios mensuales de extremos diarios en °C, clima de 0.05° y relieve entregado de 120 m, con pendiente en grados. La referencia general a CEM de 15 m no transforma los archivos entregados en datos de esa resolución. Los metadatos guardados del raster confirman 120 m. No interpretar interpolación como información nueva a escala parcelaria. [F5]; [F6]; [F7]; [R5a].

**Criterio de aceptación:** una fila por parcela, máscara válida, unidades explícitas y trazabilidad del faltante. La cobertura mínima de 80% del código actual es una regla del proyecto, no un mandato oficial; conservarla inicialmente y cambiarla solo como experimento identificado. [R2], `extract_environment`; [B5], PDF 70.

### 5.2 Separar precisión puntual de calibración de intervalos

**Decisión D10.** Comparar el procedimiento actual con una variante que use todo el entrenamiento disponible de cada fold para ajustar el punto. En la entrega final, esa variante usaría las 138 etiquetas después de seleccionar su configuración. La comparación debe respetar tamaños reales: el procedimiento actual suele ajustar 88 parcelas en los folds externos aleatorios; la variante sin reserva ajustaría 110 o 111, según el fold. [R1]; [R7r]; [B2], PDF 211 y 260.

**Criterio de aceptación:** mejora según D8, conservando la misma extracción y el mismo presupuesto de selección para aislar el cambio. No presuponer que más observaciones garantizan menor error en toda partición.

Si gana la variante puntual, **no trasladar el radio conformal anterior al modelo reajustado**. Se puede explicar incertidumbre mediante errores OOF y limitaciones, sin prometer cobertura parcelaria. Si se necesitan intervalos calibrados, evaluar un procedimiento compatible, como CV+/jackknife+, con sus supuestos y coste propios. [F4], pregunta 7; [W6], §§1.1, 3 y 6.2.

La cobertura existente al 90% es 128/138 en CV por parcela. La espacial tiene 95 intervalos finitos que cubren 95/95 casos, más 43 casos sin intervalo acotado. Esas cifras no deben resumirse como “100% de cobertura espacial” omitiendo los 43. Son resultados guardados del modelo actual, no propiedades de un eventual modelo afinado. [R3]; [R4b].

### 5.3 Reducir redundancia mediante grupos interpretables

**Decisión D11.** Comparar pocas representaciones predefinidas, seleccionadas internamente:

| Grupo candidato | Contenido y propósito | Fundamento y límite |
|---|---|---|
| Clima + relieve | Lluvia del ciclo y por ventanas; temperatura media, amplitud; elevación y pendiente. | [F1], §§3–4; [F5]; [F6]; [F7]. Referencia ambiental, no sustituto automático del satélite. |
| Clima + relieve + vigor | Añadir resúmenes separados por sensor de NDVI/EVI y LAI o MSAVI. | [F2]; [F3]; [B1], PDF 3. Evaluar aporte incremental y redundancia. |
| Anterior + humedad/senescencia | Un conjunto pequeño de NDWI, MSI, DSWI2/DSWI5 y, como ensayo, NDSVI o CRC. | [F2]; [P2s]. La selección global previa de CRC/DSWI2 en `proposal-02` genera una hipótesis; no valida su utilidad. |
| Representación actual | Mantener las 181 columnas como control, con su selección interna vigente. | [R2]; [R6]. Permite comprobar si reducir variables realmente ayuda. |

No obligar a todo algoritmo a usar el mismo filtro univariante. Probar Ridge regularizado sobre el conjunto definido, con y sin la selección actual, permite evaluar el coste de descartar variables por asociación marginal. Los árboles pueden captar interacciones que una correlación individual no revela. Todos los filtros aprendidos siguen dentro de los folds. [B2], §6.2; [B9], PDF 265.

La anomalía climática actual compara 2025 con la media de 2022–2024. Mantenerla rotulada como **referencia de tres años**, no como normal climatológica de largo plazo. Comparar con/sin ese contexto para comprobar su aporte. La lluvia de agosto–octubre de 2024 de `proposal-02` tampoco mide directamente humedad de suelo al sembrar en 2025. [R2], `climate_features`; [P2a], `prec_ant_fin_ciclo`; [F5]; [F4], pregunta 10.

**Criterio de aceptación:** mejora externa del procedimiento que selecciona el grupo y resultados estables por región. No adoptar el grupo que luce mejor únicamente después de mirar toda la OOF.

### 5.4 Mejorar la señal temporal sin inventar fenología

**Decisión D12.** Mantener abril–octubre de 2025 como ventana principal, medianas mensuales y sensores separados. Comparar una alternativa mayo–octubre y unos pocos resúmenes de trayectoria: nivel máximo robusto, cambio entre ventanas, dispersión temporal y área bajo la curva de vigor. Son características candidatas motivadas por la evolución del cultivo, no fechas agronómicas observadas. [F1], §§1–2; [F2], «Consideraciones»; [F4], pregunta 2; [B1], introducción.

Para una integral temporal propuesta, definir la unidad como índice × día, usar diferencias reales entre fechas y normalizar por duración si se comparan periodos distintos. No sumar observaciones como si todas cubrieran el mismo intervalo; no unir huecos largos sin una regla de cobertura fijada antes de validar. Si no hay cobertura suficiente, conservar ausencia y su indicador. Estas son especificaciones metodológicas del ensayo basadas en la desigual frecuencia de sensores y el tratamiento explícito de faltantes. [F2]; [B5], PDF 70; [B8], §7.1.

No llamar automáticamente “floración” a julio–agosto. `proposal-02` usa ese nombre en configuración, pero la fecha exacta de siembra y la variedad por parcela no están disponibles. Las ventanas deben nombrarse por sus meses; cualquier interpretación fenológica será aproximada. [P2cfg]; [F4], preguntas 2 y 14.

**Criterio de aceptación:** las mejoras persisten al controlar cobertura y no se explican solo por el número de adquisiciones. Distinguir la desviación espacial `_std` entregada por fecha de una desviación temporal calculada entre fechas: representan variaciones diferentes. [F2], definiciones de estadísticos; [R2], `satellite_features`; [P2a], `safe_agg`.

### 5.5 Tratar nubosidad, fórmulas y ausencias como parte del modelo

**Decisión D13.** Conservar inicialmente los cortes candidatos 20%, 40% y 60% de `reto-fira`, seleccionados en CV interna. Usar 100% solo como sensibilidad explícita a la política de `proposal-01`, sin asumir que más observaciones equivalen a mejor señal. Registrar meses útiles por sensor, vacíos estructurales y observaciones descartadas. Ningún documento oficial fija un umbral universal. [R2]; [P1m]; [F1], §2; [F2].

Mantener separados Sentinel-2, Planet y Landsat. El PDF oficial define NDWI de Sentinel-2 mediante B08 y B11; VI6T combina B3 y ST_B10; NDDI/ENDDI utilizan índices remuestreados a enteros de 8 bits. No sustituirlos por fórmulas de otro proveedor ni tratar VI6T como temperatura en °C. En Planet el PDF denomina la fórmula foliar `LAI2`, mientras el CSV usa `lai`: conservar esa discrepancia documentada, sin reinterpretar el índice como biomasa medida. [F2], advertencia final; [F3], pp. 1–2.

La lluvia mensual se suma para obtener acumulados. NoData y falta de observaciones se mantienen como ausencia, no como cero de lluvia, vegetación o temperatura. Exigir meses suficientes antes de acumular; evitar que una suma que ignora todos los faltantes produzca cero aparentemente observado. La imputación debe aprenderse únicamente con el entrenamiento y aplicarse igual a validación y predicción. [F5]; [F6]; [B5], PDF 70; [B7], PDF 400; [B8], PDF 225; [B9], PDF 265.

### 5.6 Probar modelos moderados y un ensamble solo si hay complementariedad

**Decisión D14.** Priorizar Ridge y los árboles ya disponibles; mantener fuera las redes neuronales conforme al alcance solicitado. Para una primera ronda acotada, probar Ridge con regularizaciones 1, 10 y 100 y conservar un RF/boosting de complejidad moderada como contraparte. Esos valores forman un presupuesto de búsqueda propuesto, no parámetros óptimos establecidos por una fuente. Ridge ya es una hipótesis razonable por la redundancia y por su presencia en las tres implementaciones. [P1m]; [P2m]; [R1]; [B2], PDF 248, 252 y 260.

La elección de grupos, regularización y familias deberá resolverse dentro del selector. No ampliar simultáneamente a cientos de hiperparámetros, numerosos índices, múltiples métodos de corrección y docenas de semillas: aumenta la oportunidad de seleccionar ruido en una muestra pequeña. [B9], §§7.2 y 7.10.2; [B2], PDF 248.

**Decisión D15.** Evaluar, como último candidato, una mezcla de dos modelos complementarios, por ejemplo Ridge y RF. Considerar solo pesos 0, 0.25, 0.5, 0.75 y 1, elegidos con predicciones internas fuera de muestra. Los extremos permiten elegir un solo modelo. Conservar el ensamble únicamente si mejora la evaluación externa del procedimiento completo. Este pequeño conjunto de pesos es una decisión operativa. [P2c], antecedente de mezcla; [B9], PDF 265.

La justificación matemática es que, para errores eₐ y eᵦ, el error cuadrático esperado de una mezcla de peso w es **w² E[eₐ²] + (1−w)² E[eᵦ²] + 2w(1−w) E[eₐeᵦ]**. Por ello, dos modelos individualmente buenos no garantizan que la mezcla mejore: importa si se equivocan en las mismas parcelas. Es una expansión algebraica del cuadrado, no una ganancia estimada para estos datos. Con MAE primario, elegir el peso por MAE interno y revisar RMSE; no deducir pesos óptimos solo de esta fórmula.

No usar los tres CSV ocultos como si fueran etiquetas, ni entrenar un modelo para imitarlos. Un ensamble de propuestas necesita predicciones internas y externas alineadas de sus procedimientos reproducibles. [B2], PDF 39; [B9], PDF 265.

### 5.7 Revisar errores sin borrar casos difíciles ni exagerar explicaciones

**Decisión D16.** Revisar los mayores errores OOF y las parcelas con poco soporte, verificando identificador, unidad, cobertura y fuente. Mantener los rendimientos extremos salvo evidencia independiente de un error de dato. No corregir el sesgo de extremos, recortar al rango histórico o eliminar parcelas porque empeoran el RMSE. Si se ensaya una calibración de sesgo, se aprende internamente y se evalúa como parte de la receta. [B5], PDF 70, distinción entre ruido y valores atípicos; [F4], preguntas 5 y 12; [B9], PDF 265.

Para explicar el modelo entregado, calcular importancia por permutación en observaciones no utilizadas en su ajuste, preferiblemente por grupos de variables correlacionadas, y mostrar estabilidad entre particiones. Si se entrega un ensamble, explicar el ensamble. Una contribución predictiva de lluvia no identifica el efecto causal de aumentar el riego o de cambiar prácticas de manejo. [B4], PDF 163, 208 y 216; [F4], pregunta 13.

## 6. Cómo utilizar el fundamento agronómico aportado

### 6.1 FAO, coeficientes de cultivo y AquaCrop

**Decisión D17.** Usar la agronomía para proponer variables y revisar coherencia; no reemplazar ahora el predictor por una fórmula FAO sin insumos y calibración parcelaria.

Gómez Mercado et al. estudian el método de zonas agroecológicas de FAO, no AquaCrop. Su estudio de 2006, con otros genotipos, advierte limitaciones para captar variación local y parte de ausencia de limitación hídrica. No trasladaría esas condiciones a las parcelas de temporal del reto. [W2], resumen y «Materiales y métodos»; [F4], preguntas 1 y 14.

AquaCrop requiere, además del clima, características calibradas del cultivo, suelo y manejo. Faltan en el dataset varios de esos insumos parcelarios. FAO permite estimaciones de ET0 con información meteorológica incompleta, por lo que no sería correcto decir que su cálculo es imposible; sí añadiría aproximaciones que necesitan evaluación. No es la mejora prioritaria para esta entrega. [W3]; [W5]; [F1]; [F4].

Los valores Kc ≈ 0.30 inicial y Kc ≈ 1.15 intermedio tienen contexto en FAO-56: coeficientes para estimar evapotranspiración del cultivo bajo condiciones especificadas. **No son multiplicadores directos que conviertan NDVI, precipitación o temperatura en toneladas por hectárea.** Tampoco fijan el calendario de cada parcela. [W4], cap. 6, ecuación 58 y tabla 12.

No asignar HI de 0.35–0.45 universalmente: el artículo presenta condiciones experimentales específicas y faltan biomasa calibrada y variedad parcelaria para trasladar ese cálculo. [W2], cuadros 3–5; [F4], pregunta 14.

### 6.2 Componentes de rendimiento

**Decisión D18.** No aplicar la fórmula de espigas × granos × peso de grano porque esos conteos no están disponibles en los insumos revisados. LAI satelital no equivale a espigas por m² ni a peso de grano. [F1]; [F2]; [W2], metodología de muestreo.

La conversión planteada sí es dimensionalmente correcta: 1 g/m² equivale a 0.01 t/ha, por lo que se divide entre 100. Por ejemplo, 500 g/m² equivalen a 5 t/ha. Es un cálculo de unidades; no aporta los componentes que faltan. No descontar automáticamente 5–10% por cosecha/trilla: no se verificó un factor universal aplicable a estas parcelas y la etiqueta ya corresponde a rendimiento reportado de grano. [F4], preguntas 5–6; cálculo dimensional propio.

### 6.3 Grados-día y riesgo climático

**Decisión D19.** Considerar GDD mensual únicamente como una característica aproximada y opcional, después de los ensayos prioritarios. Las Tmin/Tmax son medias mensuales; no permiten reconstruir exactamente días de helada, máximos diarios, rachas secas ni fenología. La truncación por umbrales y el promedio mensual no conmutan en general, por lo que no se obtiene el GDD diario exacto aplicando umbrales al promedio. [F6]; [P2a], `gdd`; razonamiento matemático sobre la agregación.

No asumir madurez universal a 1200–1400 GDD ni usar ese rango para fijar una fecha de cosecha: debe precisarse temperatura base, techo, variedad y fecha inicial, y validarse su pertinencia. `proposal-02` propone base 0°C y techo 30°C, pero esas decisiones no convierten su aproximación en una medición fenológica. [P2cfg]; [F4], preguntas 2 y 14.

Si se desea incorporar climatología diaria, suelo u otras fuentes públicas, documentar procedencia, resolución y fecha de disponibilidad, y hacer un experimento separado. FIRA permite información pública adicional; esa autorización no demuestra que agregarla mejore la precisión. [F1], párrafo introductorio; [B1], PDF 3.

## 7. Experimentos concretos y orden de ejecución propuesto

Esta sección describe trabajo futuro; **ninguno de estos experimentos nuevos se ejecutó para redactar este documento**. El orden prioriza cambios con una hipótesis identificable y evidencia verificable.

| Prioridad | Experimento | Qué se conserva para comparar | Condición para seguir |
|---|---|---|---|
| 0 | Congelar archivos, IDs, protocolo y referencia actual; separar versiones originales/corregidas de las propuestas. | Etiquetas, mismos folds, métrica y trazabilidad. | Reproducir estructura y errores de referencia; resolver extracción defectuosa antes de interpretar familias. D1–D9. |
| 1 | Evaluar predictor puntual con todo el entrenamiento frente a reserva de calibración. | Variables y presupuesto de selección. | Cumplir D8 y diseñar una comunicación de incertidumbre compatible. D10. |
| 2 | Comparar representaciones compactas con la actual y Ridge frente a árboles moderados. | Extracción nativa, particiones y disponibilidad temporal. | Selección interna completa y estabilidad regional; no escoger una ablación mirando toda la OOF. D11 y D14. |
| 3 | Probar la pequeña alternativa temporal y calidad de observación. | Mismas familias y comparación externa. | Aporte adicional con cobertura suficiente; sin fechas agronómicas inventadas. D12–D13. |
| 4 | Probar mezcla de dos modelos. | Candidatos ya definidos y pesos seleccionados dentro del entrenamiento. | Complementariedad de errores y mejora externa de la mezcla. D15. |
| Posterior | GDD aproximado, clima diario, suelo o un modelo de procesos. | Protocolo independiente documentado. | Insumos suficientes y beneficio validado; no necesario para completar la entrega actual. D17–D19. |

Los candidatos de las prioridades que se decida ejecutar deben quedar definidos antes de observar la evaluación externa. Si se amplían adaptativamente después, se conserva una bitácora y se declara el carácter exploratorio. El orden de trabajo no autoriza selección repetida sobre un mismo test. [B9], PDF 241 y 265.

### 7.1 Un ensayo previo que ya aconseja prudencia

El proyecto ya comparó añadir dos Ridge de clima al selector original. No debe proponerse como una mejora inédita ni volver a anunciarse como ganadora por una sola semilla. [R7p]; [R7r]; [R7d].

| CV por parcela, resultado existente | MAE original → ampliado | RMSE original → ampliado |
|---|---:|---:|
| Semilla 20261013 | 0.4077 → 0.4023 | 0.5613 → 0.5476 |
| Semilla 20261014 | 0.3841 → 0.3843 | 0.5324 → 0.5388 |

La ganancia no se sostiene en ambas particiones; los intervalos descriptivos pareados incluyen cero y la decisión guardada es conservar el original. La recomendación nueva debe evaluar hipótesis distintas o un protocolo conjunto más sólido; no seleccionar ex post la cifra más favorable. Estas mismas etiquetas ya participaron en desarrollo, por lo que no se presentan como evidencia ciega. [R7r]; [R7d]; [B9], PDF 241.

## 8. Evidencia que debe producir la futura afinación

**Decisión D20.** Para que una modificación sea revisable, exigir estos productos de evaluación antes de reemplazar `proposal.csv`:

| Evidencia | Contenido mínimo | Por qué es necesaria |
|---|---|---|
| Protocolo congelado | IDs, folds, semillas, métricas, recetas, hiperparámetros candidatos y regla de promoción. | Separa decisiones previas de ajustes motivados por resultados. [B9], §7.2. |
| Tabla OOF común | ID, etiqueta observada, repetición, fold, predicción de cada procedimiento y tamaño efectivo de ajuste. | Permite comparar pérdidas pareadas sin confundir poblaciones. [B2], §2.2; [B9], §7.10.2. |
| Auditoría de insumos | Sensor, ventana, cobertura, NoData, unidades y faltantes por parcela. | Detecta pérdida de información como la observada en `proposal-01`. [F1]; [F5]; [F6]; [F7]; [P1f]. |
| Resultados de ablación | Mismas métricas con/sin cada grupo, estabilidad y coste de complejidad. | Distingue motivación agronómica de utilidad predictiva comprobada. [B1]; [B4], PDF 216. |
| Diagnóstico regional | Errores, sesgo, tamaños y soporte geográfico, junto a referencias simples. | Evita esconder diferencias locales tras el promedio global. [B3], cap. 6; [R6]. |
| Incertidumbre coherente | Qué predictor se calibra, supuestos, cobertura observada, anchura y casos no acotados. | No equipara dispersión de árboles con cobertura garantizada. [W6], §§2.3 y 3. |
| Entrega verificada | Los 59 IDs, t/ha, cuatro decimales, valores finitos y correspondencia entre modelo, CSV y aplicación. | Satisface el objetivo parcelario y previene errores de exportación. [F4], preguntas 6–8. |

No hay en los documentos revisados una plantilla de encabezados de CSV que permita certificar como oficial uno de los tres esquemas actuales. Verificar la plantilla del portal antes del envío, manteniendo el valor puntual y cuatro decimales que sí están documentados. [F4], pregunta 7; [C0]; [C1]; [C2].

## 9. Recomendación de entrega y límite de la conclusión

**Mantendría `proposal.csv` como versión de respaldo y no lo reemplazaría hasta que un procedimiento evaluado de forma común supere la regla D8.** El mejor primer experimento es liberar todas las etiquetas para el predictor puntual, seguido de regularización y representaciones compactas con señal temporal. Las otras propuestas aportan hipótesis; sus CSV y métricas actuales no demuestran una mejora transferible. [R1]; [P1f]; [P2b]; [P2c]; [B2], PDF 260; [B9], PDF 265.

Si no hay una mejora estable antes del cierre, entregar el modelo actual con sus limitaciones explícitas es una decisión técnicamente más defendible que cambiar valores por consenso o adoptar el mínimo de una búsqueda extensa. Esto no certifica que el actual sea óptimo: significa que no se ha demostrado un reemplazo mejor con la evidencia disponible. [B9], PDF 241; [R7d].

La convocatoria consultada publica cierre el **19 de octubre de 2026 a las 23:59**. Ese plazo favorece concentrar la evaluación en pocas hipótesis comprobables. Ningún resultado de CV permitirá garantizar que se alcanzó la máxima precisión posible en las 59 parcelas: esa exactitud solo podrá medirse cuando FIRA confronte las estimaciones con sus rendimientos reservados. [W0]; [W1], pp. 4 y 6.

## 10. Fuentes y localizadores de las decisiones

### 10.1 Documentación oficial e insumos locales

| Ref. | Fuente | Localizador y uso |
|---|---|---|
| [F1] | FIRA, *Descripción general del conjunto de datos*. | §§1–4 y consideraciones: población, ciclo 2025, fuentes y decisiones de integración. |
| [F2] | FIRA, *Diccionario de índices satelitales*. | Estadísticos, Dataset PRO, consideraciones y tablas: sensores, significado y límites de interpretación. |
| [F3] | FIRA, *Ecuaciones de índices satelitales*. | PDF pp. 1–2: fórmulas por sensor, `resampled`, VI6T y LAI2. |
| [F4] | FIRA, *Segunda sesión de preguntas y respuestas*, 9 de octubre de 2026. | Preguntas 1–14, especialmente 2, 5–10 y 12–14: temporal, etiquetas, siembra, muestra, formato y ausencias. |
| [F5] | Precipitación, `LEEME.txt`. | VARIABLE, UNIDAD y RESOLUCIÓN: acumulados mensuales, mm/mes y 0.05°. |
| [F6] | Temperaturas, `LEEME_.txt`. | VARIABLES, UNIDADES, RESOLUCIÓN y NODATA: medias mensuales, °C y −9999. |
| [F7] | Topografía, `LEEME.txt`. | PRODUCTOS ENTREGADOS: resolución 120 m, elevación, pendiente en grados y CRS. |
| [F8] | Maestro de identificador, área y rendimiento. | Campos `ID_POLIGONO`, `AREA_HA`, `RENDIMIENTO_T_HA`, `CONJUNTO`. Autoridad para las etiquetas y los 59 IDs. |

### 10.2 Los nueve PDF bibliográficos solicitados

| Ref. | Obra identificada | Pasaje consultado y alcance |
|---|---|---|
| [B1] | Radočaj et al. (2026), *Satellite Remote Sensing for Crop Yield Prediction: A Review*, archivo `02.pdf`. DOI: 10.3390/agriculture16040417. | PDF pp. 1 y 3. Integración de meteorología, suelo y manejo con satélite. Revisión bibliométrica; no un experimento que demuestre qué algoritmo gana aquí. |
| [B2] | James et al., *An Introduction to Statistical Learning with Applications in Python*. | PDF 39 / impresa 29: error en observaciones no vistas; PDF 211 / 203: variación de validación; PDF 248 / 240: regularización y regla de un error estándar; PDF 252 / 244: Ridge y varianza; PDF 260 / 252: selección de regularización y reajuste. |
| [B3] | Rey, Arribas-Bel y Wolf, *Geographic Data Science with Python*. | PDF 166 / impresa 133, cap. 6: autocorrelación espacial; PDF 348 / 315, §11.4.3.2: dependencia en los errores. Motiva sensibilidad geográfica, no un tamaño universal de bloque. |
| [B4] | Christoph Molnar, *Interpretable Machine Learning*. | PDF 163, §8.1: interpretación del predictor frente a causalidad real; PDF 208, §8.5.2: importancia en datos apartados; PDF 216: dificultades con predictores correlacionados. |
| [B5] | Tan et al., *Introduction to Data Mining*. | PDF 70 / impresa 46: faltantes y diferencia entre ruido y atípicos; PDF 180 / 156, §3.5.1: separación de validación. Esta última sección trata clasificación; se utiliza su principio de separación, no sus métricas. |
| [B6] | Shawon et al. (2025), *Crop yield prediction using machine learning: An extensive and systematic literature review*, archivo `last.pdf`. DOI: 10.1016/j.atech.2024.100718. | PDF 1, resumen: variables, familias y métricas frecuentes. Frecuencia de uso no implica superioridad ni define la puntuación de FIRA. |
| [B7] | Jake VanderPlas, *Python Data Science Handbook*, archivo `Python_Datascience.pdf`. | PDF 400 / impresa 382: pipelines y advertencia sobre evaluar datos de entrenamiento. Sustenta transformaciones consistentes; no prueba que un tipo de imputación sea óptimo. |
| [B8] | Wes McKinney, *Python for Data Analysis*, archivo `Python-for-Data-Analysis.pdf`. | PDF 225 / impresa 207, §7.1: eliminación y relleno de faltantes. Describe operaciones; no otorga significado físico a un cero imputado. |
| [B9] | Hastie, Tibshirani y Friedman, *The Elements of Statistical Learning*. | PDF 241 / impresa 222, §7.2: selección frente a evaluación y reutilización de test; PDF 265 / impresa 246, §7.10.2: validar la secuencia completa de modelado. |

Dos pasajes especialmente relevantes son: ESL indica “cross-validation must be applied to the entire sequence of modeling steps” ([B9], PDF 265); ISLP señala que, tras seleccionar la regularización, “the model is re-fit using all of the available observations” ([B2], PDF 260). El primero fundamenta reparar la comparación; el segundo motiva evaluar el reajuste con 138 etiquetas. Ninguno promete una ganancia en las parcelas ocultas.

### 10.3 Fuentes de internet y tratamiento de los enlaces aportados

| Ref. | Fuente | Uso y estado de acceso |
|---|---|---|
| [W0] | FIRA, página de la convocatoria 2026. | Objetivo y fecha de entrega. Consultada el 17 de octubre de 2026, fecha local de esta revisión. |
| [W1] | FIRA, *Reto AgroCebada. Bases*. | PDF p. 4: etiquetas reservadas; p. 5: métricas y evaluación; p. 6: calendario. Se obtuvo desde la convocatoria. |
| [W2] | Gómez Mercado et al. (2009), *Estimación del rendimiento de cebada (Hordeum vulgare L.) maltera con el método FAO*, *Agricultura Técnica en México* 35(1), 13–23. | Texto completo accesible en ResearchGate, depositado por un autor. Resumen, metodología y cuadros 3–5. El enlace [SciELO aportado][WS] no pudo recuperarse; no se finge una segunda lectura ni se cuentan ambos enlaces como dos estudios distintos. |
| [W3] | FAO, *AquaCrop input requirements*. | Insumos de clima, cultivo, suelo y manejo. Fuente primaria para requisitos. |
| [W4] | FAO-56, capítulo 6, *ETc – Single crop coefficient*. | Ecuación 58 y tabla 12: significado y condiciones de coeficientes Kc. |
| [W5] | FAO, *ETo Calculator*. | Posibilidad de estimar ET0 con datos meteorológicos incompletos y medias mensuales, con aproximaciones documentadas. |
| [W6] | Angelopoulos y Bates, *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, arXiv:2107.07511v6. | §§1.1, 2.3, 3 y 6.2: calibración separada, evaluación de incertidumbre y alternativas CV+/jackknife+. Las garantías requieren supuestos; no se prometen bajo dependencia espacial arbitraria. |
| [WC] | Colektia, *Modelo predictivo: qué es, tipos y cómo funciona*. | Enlace consultado como contexto divulgativo del planteamiento. No se usa su tabla estadística/ML para seleccionar algoritmos ni justificar reglas agronómicas. |
| [WI] | IBM, *¿Qué es el pronóstico predictivo?* | Enlace consultado como contexto general. Las decisiones de validación se sustentan en los libros y en la documentación del reto. |

### 10.4 Evidencia de las implementaciones y salidas

| Ref. | Archivo / artefacto | Localizador |
|---|---|---|
| [C0] | `reto-fira/comparisons/proposal.csv` | Los 59 valores actuales de `reto-fira`; idéntico a [su salida de producción][C0o]. |
| [C1] | `reto-fira/comparisons/proposal-01.csv` | Los 59 valores actuales de `proposal-01`; idéntico a [su salida][C1o]. |
| [C2] | `reto-fira/comparisons/proposal-02.csv` | Los 59 valores actuales de `proposal-02`; idéntico a [su salida][C2o]. |
| [P1] | `proposal-01/.../src/pipeline.py` | `zonal_features`, `satellite_features`, `evaluate_models`, `main`. |
| [P1f] | `proposal-01/.../outputs/features.csv` | 197 filas, 203 predictores; ausencia de los 84 predictores climáticos en 196 filas. |
| [P1m] | `proposal-01/.../outputs/metrics.json` | Validación, modelo elegido, número de predictores, nubosidad y métricas. |
| [P2a] | `proposal-02/pipeline/03_feature_engineering.py` | `gdd`, `safe_agg` y `build_climate_features`. |
| [P2b] | `proposal-02/pipeline/04_correlacion_seleccion.py` | Selección global, VIF, imputación y generación de matrices. |
| [P2c] | `proposal-02/pipeline/05_entrenamiento.py` | Optimización, evaluación, pesos y error de entrenamiento del ensamble. |
| [P2d] | `proposal-02/pipeline/06_prediccion.py` | Mezcla, recorte a 0.5–8 t/ha, dispersión de árboles y SHAP de RF. |
| [P2e] | `proposal-02/pipeline/02_extraccion_zonal.py` | `zonal_extract`, `all_touched=True`; se combina con [reproyección bilineal previa][P2re]. |
| [P2cfg] | `proposal-02/pipeline/config.py` | Ventanas, nubosidad y constantes de GDD. |
| [P2m] | `proposal-02/models_saved/model_meta.json` | Las 12 características, pesos y métricas de componentes. |
| [P2s] | `proposal-02/features/selected_features.json` | Variables y correlaciones guardadas. |
| [P2x] | `proposal-02/features/master_train.csv` | Revisión de vacíos en las características seleccionadas, junto con [master_pred.csv][P2xp]. |
| [R1] | `reto-fira/platform/pipeline/train.py` | Pipeline, selección interna, evaluación externa y calibración. |
| [R2] | `reto-fira/platform/pipeline/features.py` | Extracción por intersección, ventanas, sensores, cobertura y agregación. |
| [R3] | `reto-fira/platform/artifacts/metrics.json` | Selección final, tamaños, métricas e intervalos actuales. |
| [R4a] / [R4b] | OOF por parcela / espacial. | 138 predicciones externas por archivo; base del recálculo de MAE y RMSE. |
| [R5] / [R5a] | Tabla ambiental / auditoría raster. | Cobertura de variables y resolución de archivos entregados. |
| [R6] | `refinement-audit/support-summary.json` | Referencia estatal, distancias, patrones climáticos y redundancia. Resultados anteriores. |
| [R7p] / [R7r] / [R7d] | Protocolo / resultados / decisión del ensayo previo. | Ampliación de 18 a 20 candidatos; resultado exploratorio y decisión de conservar original. |
| [R8] | Auditoría anterior de comparación. | Se usa únicamente para identificar que comparó otras entregas. |

Hashes SHA-256 de los CSV revisados, para identificar esta versión de la propuesta:

| Archivo | SHA-256 |
|---|---|
| `proposal.csv` | `53B1B2FE8F46C66814A12D036826BCA80E5A5C4CBDD529A43358CEF83CE665FF` |
| `proposal-01.csv` | `ADEE78579E942C6D9D33C0E3E5578AA378DECCB6DC46918C5DE3E2E1D2597EE9` |
| `proposal-02.csv` | `C07C896DA0A82AC0FE305AFBE8747E78631860B20FD8BD7B64E4ED39C3B27432` |

[F1]: <C:/dev/benchmarks/reto-fira/data/fira/context/Descripcion_general_variables_DataSet.docx>
[F2]: <C:/dev/benchmarks/reto-fira/data/fira/context/Diccionario_de_indices_satelitales.docx>
[F3]: <C:/dev/benchmarks/reto-fira/data/fira/context/Ecuaciones_indices_AgroCebada_FIRA_2026.pdf>
[F4]: <C:/dev/benchmarks/reto-fira/data/fira/context/Segunda_Sesion_Preguntas_Reto.docx>
[F5]: <C:/dev/benchmarks/reto-fira/data/fira/precipitation/LEEME.txt>
[F6]: <C:/dev/benchmarks/reto-fira/data/fira/temperatures/LEEME_.txt>
[F7]: <C:/dev/benchmarks/reto-fira/data/fira/INEGI-topography/LEEME.txt>
[F8]: <C:/dev/benchmarks/reto-fira/data/fira/CSV-files/ID_area_rendimiento_70_30_Reto_AgroCebada.csv>
[B1]: <C:/dev/benchmarks/reto-fira/data/libros/02.pdf>
[B2]: <C:/dev/benchmarks/reto-fira/data/libros/An Introduction to Statistical Learning with Applications in Python.pdf>
[B3]: <C:/dev/benchmarks/reto-fira/data/libros/Geographic Data Science with Python.pdf>
[B4]: <C:/dev/benchmarks/reto-fira/data/libros/Interpretable Machine Learning - Christoph Molnar.pdf>
[B5]: <C:/dev/benchmarks/reto-fira/data/libros/Introduction to Data Mining.pdf>
[B6]: <C:/dev/benchmarks/reto-fira/data/libros/last.pdf>
[B7]: <C:/dev/benchmarks/reto-fira/data/libros/Python_Datascience.pdf>
[B8]: <C:/dev/benchmarks/reto-fira/data/libros/Python-for-Data-Analysis.pdf>
[B9]: <C:/dev/benchmarks/reto-fira/data/libros/The Elements of Statistical Learning.pdf>
[W0]: https://www.fira.gob.mx/Nd/Convocatoria-2026.html
[W1]: https://www.fira.gob.mx/Nd/Reto%20Agrocebada%20Bases.pdf
[W2]: https://www.researchgate.net/publication/262502093_Estimacion_del_rendimiento_de_cebada_Hordeum_vulgare_L_maltera_con_el_metodo_FAO
[WS]: https://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S0568-25172009000100002
[W3]: https://www.fao.org/aquacrop/overview/input-requirements/
[W4]: https://www.fao.org/4/X0490E/x0490e0b.htm
[W5]: https://www.fao.org/land-water/resources/tools/software/eto-calculator/en
[W6]: https://arxiv.org/html/2107.07511v6
[WC]: https://colektia.com/blog/que-es-un-modelo-predictivo
[WI]: https://www.ibm.com/mx-es/think/topics/predictive-forecasting
[C0]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/incumbent/comparisons-proposal.csv>
[C1]: <C:/dev/benchmarks/reto-fira/comparisons/proposal-01.csv>
[C2]: <C:/dev/benchmarks/reto-fira/comparisons/proposal-02.csv>
[C0o]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/incumbent/predicciones_59.csv>
[C1o]: <C:/dev/benchmarks/proposal-01/reto-fira-v0/outputs/predicciones_59.csv>
[C2o]: <C:/dev/benchmarks/proposal-02/predictions/predicciones_AgroCebada2026.csv>
[P1]: <C:/dev/benchmarks/proposal-01/reto-fira-v0/src/pipeline.py>
[P1f]: <C:/dev/benchmarks/proposal-01/reto-fira-v0/outputs/features.csv>
[P1m]: <C:/dev/benchmarks/proposal-01/reto-fira-v0/outputs/metrics.json>
[P2a]: <C:/dev/benchmarks/proposal-02/pipeline/03_feature_engineering.py>
[P2b]: <C:/dev/benchmarks/proposal-02/pipeline/04_correlacion_seleccion.py>
[P2c]: <C:/dev/benchmarks/proposal-02/pipeline/05_entrenamiento.py>
[P2d]: <C:/dev/benchmarks/proposal-02/pipeline/06_prediccion.py>
[P2e]: <C:/dev/benchmarks/proposal-02/pipeline/02_extraccion_zonal.py>
[P2re]: <C:/dev/benchmarks/proposal-02/pipeline/01_alineacion_crs.py>
[P2cfg]: <C:/dev/benchmarks/proposal-02/pipeline/config.py>
[P2m]: <C:/dev/benchmarks/proposal-02/models_saved/model_meta.json>
[P2s]: <C:/dev/benchmarks/proposal-02/features/selected_features.json>
[P2x]: <C:/dev/benchmarks/proposal-02/features/master_train.csv>
[P2xp]: <C:/dev/benchmarks/proposal-02/features/master_pred.csv>
[R1]: <C:/dev/benchmarks/reto-fira/platform/pipeline/train.py>
[R2]: <C:/dev/benchmarks/reto-fira/platform/pipeline/features.py>
[R3]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/incumbent/metrics.json>
[R4a]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/incumbent/validation-parcel.csv>
[R4b]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/incumbent/validation-spatial.csv>
[R5]: <C:/dev/benchmarks/reto-fira/platform/artifacts/environment.csv>
[R5a]: <C:/dev/benchmarks/reto-fira/platform/artifacts/raster-audit.json>
[R6]: <C:/dev/benchmarks/reto-fira/platform/artifacts/refinement-audit/support-summary.json>
[R7p]: <C:/dev/benchmarks/reto-fira/platform/artifacts/refinement-audit/protocol.json>
[R7r]: <C:/dev/benchmarks/reto-fira/platform/artifacts/refinement-audit/results.json>
[R7d]: <C:/dev/benchmarks/reto-fira/platform/artifacts/refinement-audit/decision.json>
[R8]: <C:/dev/benchmarks/reto-fira/platform/work/prediction-comparison-audit.md>
