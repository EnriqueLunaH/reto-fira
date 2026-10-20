# AgroCebada: comparación y afinación de la predicción

> **Documento histórico del 14 de octubre de 2026.** El dictamen y las cifras siguientes corresponden a la versión anterior. La implementación del 17 de octubre sí sustituyó el modelo tras otra evaluación predefinida; consultar el [reporte vigente](../REPORTE_IMPLEMENTACION_PREDICCION.md). Los artefactos de la versión descrita aquí están preservados en [model-refinement-v2/incumbent](artifacts/model-refinement-v2/incumbent/); los enlaces a artefactos de producción pueden mostrar la versión nueva.

Fecha de revisión: **14 de octubre de 2026**. Unidad: parcela; objetivo: rendimiento de **grano, t/ha**, ciclo abril-octubre de 2025.

## Dictamen y cambios realizados

**No se puede declarar qué CSV predice mejor las 59 parcelas ocultas.** Sus rendimientos reales no están disponibles. Los tres archivos tienen exactamente los mismos 59 identificadores válidos, sin predicciones ausentes, infinitas o duplicadas. Las diferencias entre ellos no son errores frente a la verdad. [F1, F4, B2]

**Se conserva el modelo y sus 59 predicciones actuales.** Se encontró fundamento para probar una alternativa más compacta y regularizada, pero la evaluación pareada no mostró mejora consistente. El candidato baja ligeramente el error en una partición, no lo confirma en otra y empeora ambos ensayos espaciales. Cambiar los valores de entrega con esa evidencia no cumpliría el criterio de mejora sustentada solicitado.

La revisión sí endurece la propuesta: audita los CSV, reproduce nuestras métricas y el modelo guardado, añade una referencia regional, documenta limitaciones, deja un experimento anidado reproducible, verifica citas directamente en los originales y proporciona particiones comunes para comparar a los tres equipos. Se crea este documento, que el README anunciaba pero que no existía al comenzar.

Se agregó `../comparisons/predicciones_59.csv` como **copia exacta** de `artifacts/predicciones_59.csv`, sin cambiar sus valores. SHA-256 de ambos: `53b1b2fe8f46c66814a12d036826bca80e5a5c4cbdd529a43358cef83ce665ff`. No se alteraron los archivos de los compañeros, `pipeline/train.py`, `pipeline/features.py`, `model.joblib`, `metrics.json` ni `dashboard.json` durante esta revisión.

Los resultados siguientes son una auditoría y experimentos exploratorios sobre las mismas 138 etiquetas disponibles; **no son una validación ciega nueva ni una garantía de precisión futura**. [B2, B9]

## 1. Fuentes y autoridad de la evidencia

Se consultaron las secciones pertinentes de **todos los nueve PDF bibliográficos**, el PDF de ecuaciones FIRA y los tres DOCX solicitados, además de los CSV originales, los tres LEEME, los inventarios y los dos MD de comparación. No se afirma una lectura integral de todos los libros.

La tabla maestra oficial controla IDs, áreas, partición y rendimientos observados. Los documentos FIRA controlan el significado y los requisitos de entrega; los metadatos e inventarios de los archivos entregados controlan su resolución efectiva. Los libros justifican principios y ensayos, mientras que los errores fuera de muestra deciden si una modificación merece adoptarse. Las cifras de los compañeros se atribuyen a sus MD: sus códigos, folds y predicciones OOF no se incluyen aquí y **no pudieron reproducirse**.

La sección 8 contiene citas literales breves, páginas y límites de interpretación. `scripts/citation-specification.json` y `artifacts/citation-evidence.json` guardan los extractos y SHA-256. `scripts/verify_citations.py` vuelve a abrir los PDF/DOCX originales; ya no depende de transcripciones en `work/`. Verificar que una cita existe no demuestra automáticamente que apoye cualquier conclusión.

## 2. Qué datos y procedimiento se auditaron

### Parcela, periodo y verdad observada

El maestro `data/fira/CSV-files/ID_area_rendimiento_70_30_Reto_AgroCebada.csv` contiene 197 parcelas: 138 de ENTRENAMIENTO con rendimiento observado y 59 de PREDICCION con rendimiento vacío. Las observaciones satelitales repetidas no son nuevas etiquetas de rendimiento. La división se hace por parcela, evitando repartir fechas de una parcela entre ajuste y evaluación. [F1, B9]

La predicción usa información hasta octubre de 2025: es una estimación retrospectiva del ciclo terminado, **no un pronóstico disponible al sembrar**. No existen etiquetas anuales de rendimiento para validar generalización temporal. El historial climático 2022-2024 representa ambiente; no supone cebada continua, pues el organizador desconoce la rotación de cultivos. No se inventan fechas exactas de siembra, variedad ni manejo por parcela. [F1, F4]

### Variables y controles conservados

El procedimiento actual construye **181 predictores** por parcela, de los que 40 son climáticos. Se conservaron las siguientes decisiones existentes; su presencia no se presenta como una mejora nueva:

| Componente | Tratamiento actual y razón | Sustento y límite |
|---|---|---|
| Ráster | Media ponderada por el área de intersección parcela-celda, reproyección al CRS de cada fuente; NoData enmascarado. Cobertura válida mínima 80%; menor cobertura pasa a ausente. | F1, T1-T3 y auditorías `raster-coverage.csv`/`raster-audit.json`. El 80% es una elección del proyecto, no un umbral óptimo demostrado por un libro. |
| Precipitación | Suma mensual y acumulados de abril-octubre, periodos inicial/medio/final e historia/anomalía. | T1: acumulado mensual en mm/mes. No interpretar la media mensual como precipitación diaria. |
| Temperatura | Tmin/Tmax mensuales, medias de temporada, amplitud e historia/anomalía. | T2: promedios mensuales en °C. No llamarlos grados-día medidos ni inferir heladas diarias con medias mensuales. |
| Satélite | Sensores separados; mediana por mes, media/pico/dispersión y cambio tardío por índice. Igual peso por mes al resumir la temporada. | F2: sensores no equivalentes. La ponderación mensual es una decisión metodológica, no una superioridad probada frente a toda alternativa. |
| Nubes y faltantes | Comparar filtros 20/40/60% dentro de CV interna; 0% es válido, 100% se excluye; no imputar satélite ausente como vegetación cero. | F1-F2, B5 y B8. Ninguna fuente fija un umbral universal óptimo. |
| Índices | Se usan las columnas suministradas; NDVI/NDWI fuera de [-1,1] pasan a ausentes. No se aplica ese límite a EVI/LAI/ratios ni a VI6T. | F2-F3: formulaciones por proveedor, VI6T espectral-térmico y variantes `resampled` de 8 bits. No recomputar índices con una fórmula ajena. |
| Transformaciones aprendidas | Imputación por mediana, indicadores de ausencia, filtro de varianza, escalado y selección supervisada `f_regression`, ajustados dentro del entrenamiento de cada fold. | B7 y B9. El pipeline facilita aplicar transformaciones, pero la separación por folds es lo que evita contaminación. La mediana no se declara universalmente óptima. |
| IDs y geografía | ID, estado y coordenadas quedan como metadatos; no se usan como predictores del modelo. | F1 y B3. Estado se usa adicionalmente como referencia diagnóstica, sin introducirlo de forma automática al modelo. |

**Discrepancia resuelta:** F1 cita CEM de 15 m como fuente general. Los ráster entregados se llaman `Elevacion_INEGI_CEM4_120m.tif` y `Pendiente_INEGI_CEM4_120m_grados.tif`; el LEEME, inventario y metadatos indican **120 m**, CRS EPSG:6372, pendiente en grados. Se documenta la resolución entregada de 120 m. La lluvia y temperaturas tienen 0.05° (aproximadamente 5 km), EPSG:4326. No se atribuye resolución de parcela fina a una cuadrícula climática compartida. [T1-T3, F1]

### Validación y ajuste final existentes

La selección interna ordena por **MAE**, después por RMSE, nombre y filtro de nubes. Este es el criterio actual de nuestra propuesta; las fuentes consultadas no establecen una métrica oficial única del concurso. Se conservó para evitar elegir el criterio después de ver qué modelo gana. Se reportan también RMSE y R². [B6, B9]

Se evalúan 18 configuraciones: seis familias/configuraciones (Ridge α=10/100 con k=30, ExtraTrees y Random Forest con k=60, HistGradientBoosting con k=35 y SVR con k=40), cada una bajo tres filtros de nubes. Las transformaciones y la selección se reajustan en cada entrenamiento interno. Los modelos predicen valores no negativos.

La CV aleatoria externa usa KFold de cinco partes, mezcladas con semilla 20261013. De cada entrenamiento externo se reserva 20% para calibración; el ajuste/selección usa 88 parcelas y la calibración 22-23. Dentro del ajuste se elige el modelo con tres folds internos. Las 138 predicciones externas se reúnen una sola vez por parcela para calcular métricas globales. **No se detectó fuga directa de etiquetas en este flujo.** La agregación temporal por parcela previa al split no utiliza rendimientos. [B9]

El estrés espacial usa GroupKFold(5) sobre bloques de 20 km. La calibración también aparta bloques completos y la selección interna usa GroupKFold. Son solo seis bloques etiquetados, de tamaños 58, 27, 21, 16, 14 y 2; los folds de prueba contienen 58, 27, 21, 16 y 16 parcelas. Los tamaños efectivos de ajuste varían de 53 a 120. Esta prueba mide traslado geográfico y es muy sensible a qué bloques quedan para calibración. No es comparable directamente con KMeans o celdas CHIRPS de otros proyectos. [B3]

Para la entrega, una partición fija separa **110 para ajuste/selección y 28 para calibración**. Sobre las 110 se ejecuta selección interna de cinco folds; gana Random Forest con nubosidad 60%, k=60. Se predicen las 59 sin usar sus etiquetas. Los otros compañeros declaran reajustar su predictor puntual con las 138; esa diferencia debe explicitarse al comparar procedimientos.

## 3. Resultados propios verificados

Se recalcularon desde los CSV OOF con fórmulas explícitas independientes de los helpers del entrenamiento:

`MAE = mean(abs(predicho-real))`; `RMSE = sqrt(mean((predicho-real)^2))`; `R² = 1-sum((predicho-real)^2)/sum((real-media(real))^2)`; `sesgo = mean(predicho-real)`.

El MAE está en t/ha; RMSE penaliza más los errores grandes. R² depende de la variación del objetivo de la población evaluada y no es un porcentaje de exactitud. Se calcula sobre todas las predicciones OOF reunidas, no como promedio simple de R² por fold. [B2, B6]

<!-- RESULTS_START -->
| Evaluación actual | n | MAE (t/ha) | RMSE (t/ha) | R² |
|---|---:|---:|---:|---:|
| CV anidada aleatoria por parcela | 138 | 0.407694 | 0.561318 | 0.561921 |
| Referencia mediana global, mismos folds | 138 | 0.724420 | 0.911897 | -0.156184 |
| CV anidada por bloques de 20 km | 138 | 0.804789 | 0.955497 | -0.269388 |
| Referencia mediana global, bloques | 138 | 1.344565 | 1.424477 | -1.821279 |
| Calibración del ajuste final, muestra distinta | 28 | 0.329741 | 0.405251 | 0.604299 |

El mínimo interno del ganador final es MAE **0.386266** sobre 110 casos internos; no sustituye la estimación externa. La métrica de las 28 parcelas de calibración tampoco reemplaza la OOF de 138. El radio de intervalo final es **0.698210 t/ha**.
<!-- RESULTS_END -->

La concordancia de las métricas con `metrics.json` se verificó con tolerancia de 1e-12. Se cargó exclusivamente el `model.joblib` de este proyecto y se reprodujeron sus predicciones finales a tolerancia de redondeo de 0.00005 t/ha; se verificaron IDs de ajuste/calibración disjuntos y excluyentes de las 59 ocultas.

### Señal regional, contracción y errores grandes

| Estado, CV aleatoria | n | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| Hidalgo | 36 | 0.293742 | 0.411980 | 0.711303 |
| Puebla | 71 | 0.475637 | 0.659517 | -0.291815 |
| Tlaxcala | 31 | 0.384414 | 0.457488 | -0.529525 |

Una referencia adicional de **mediana de rendimiento por estado**, calculada únicamente con el ajuste de cada fold externo original, obtiene MAE **0.432210**, RMSE **0.617521**, R² **0.469800**. Nuestra ventaja de MAE frente a ella es solo **0.024516 t/ha**. El avance frente a la mediana global no demuestra por sí mismo precisión fina dentro de cada región. Es una referencia diagnóstica incorporada al informe, no un cambio de predictor. [B3; `scripts/diagnose_spatial_support.py`]

El cuartil inferior de rendimiento observado presenta sesgo OOF +0.45447 t/ha y el superior -0.46925: hay contracción hacia el centro. Entre los errores grandes están AGC_171 (real 2.15, predicho 4.81091) y AGC_015 (real 2.64, predicho 5.04462). No existe evidencia de que sus etiquetas sean incorrectas: no se eliminaron ni se estiraron las predicciones para corregir el patrón después de ver la evaluación. [F4, B9]

Hay 85 pares de predictores con correlación absoluta superior a 0.98. Esto motiva ensayar regularización/compactación, pero no demuestra que quitar variables aumente precisión. La importancia por permutación es dependencia predictiva, no causa agronómica; una importancia negativa de un grupo en solo 28 casos no demuestra que ese grupo sea inútil. [B4]

### Geografía e incertidumbre

Las 59 ocultas tienen una parcela etiquetada a entre 67 y 1909 m de su centroide (mediana 349 m), y **49/59 comparten exactamente el vector de 40 variables climáticas** con alguna parcela etiquetada en las features guardadas a seis decimales. Las 138 etiquetas contienen solo 43 vectores climáticos distintos. Esto refleja soporte ambiental compartido y ayuda a explicar correlaciones entre propuestas; no prueba exactitud ni implica uso de etiquetas ocultas. El reto oculto se parece más a interpolar en estas zonas que a extrapolar una región entera. Es una inferencia del soporte observado y del muestreo aleatorio estratificado declarado, cuyos estratos exactos se desconocen. [B3, F4]

Por ello se conserva CV aleatoria como estimación principal del problema disponible y CV espacial como estrés; no se elige la validación que más favorece al modelo. No hay prueba temporal con un solo ciclo etiquetado.

La cobertura nominal de los intervalos actuales es 90%. En OOF aleatorio se observó **128/138 = 92.75%**, ancho medio 1.76109 t/ha. En espacial, la cobertura con límites finitos es **95/95 = 100%**, ancho medio 4.46601 t/ha, **más 43 casos con intervalo no acotado**: dos folds calibran con solo dos parcelas y su cuantil corregido es infinito. No se presenta ese 100% como cobertura finita de las 138.

El código usa split-conformal, orden estadístico `ceil((n_cal+1)*0.9)`, devolviendo infinito si supera `n_cal`. En el ajuste final son 28 residuos y rango 27. Se conserva como complemento existente y se informa su cobertura observada. **Los libros suministrados no contienen una justificación específica suficiente para prometer una garantía conformal/CV+ aquí**; no se les atribuye tal garantía. La intercambiabilidad no está asegurada bajo dependencia espacial, y las etiquetas de calibración ya se inspeccionaron para explicar/auditar. No se reutilizaría sin revisión el mismo radio si se reajustara el modelo con esas etiquetas. [B3, B9]

## 4. Qué dicen las tres propuestas y por qué no hay un ranking justo

| Propuesta y evaluación declarada | MAE | RMSE | R² | Estado de la evidencia |
|---|---:|---:|---:|---|
| Nuestra, OOF aleatorio anidado, 138 | 0.4077 | 0.5613 | 0.5619 | Recalculada desde OOF y código local |
| agrocebada_hidden, 5 folds × 10 repeticiones, por evaluación | 0.3778 | 0.5284 | 0.6118 | Reportada en su MD; corrida quick/experimental |
| agrocebada_hidden, promedio de 10 predicciones OOF por parcela | 0.3682 | 0.5196 | 0.6246 | Misma corrida; predictor agregado diferente |
| Predicciones-agroceba, selector anidado, 138 | 0.4190 | 0.5519 | 0.5765 | Reportada en su MD; reconoce uso previo de evaluación externa |

Las cifras nominales favorecen al primer compañero en CV aleatoria, pero no acreditan una victoria sobre las 59. Las 1380 evaluaciones repetidas del primer MD siguen correspondiendo a **138 parcelas**, no 1380 unidades independientes. Promediar diez predicciones OOF por parcela cambia el predictor evaluado; no debe compararse sin matiz con una sola predicción OOF o con el modelo final entrenado una vez.

Frente al segundo compañero, nuestro MAE es numéricamente menor y nuestro RMSE mayor. Elegir después la métrica favorable sería improcedente. Además, cambian semilla, cantidad de entrenamiento efectiva, selección por MAE/RMSE, grupos espaciales, complejidad del selector y reutilización de folds. La validación anidada protege decisiones internas, pero no elimina optimismo si se adopta una receta después de mirar sus resultados externos. [B2, B6, B9]

Las métricas espaciales declaradas tampoco son intercambiables: primer compañero MAE 0.7277/RMSE 0.8925/R² -0.1076 con cinco clusters KMeans; segundo 0.6390/0.7775/0.1594 con celdas CHIRPS; nosotros 0.8048/0.9555/-0.2694 con bloques de 20 km y reserva de calibración. No se ordenan como si fueran el mismo problema.

### Desacuerdo de las 59 salidas

| Par | Diferencia absoluta media (t/ha) | Máxima diferencia absoluta | Correlación Pearson |
|---|---:|---:|---:|
| Nuestra / agrocebada_hidden | 0.09955 | 0.29071 | 0.98768 |
| Nuestra / Predicciones-agroceba | 0.12540 | 0.42226 | 0.97251 |
| agrocebada_hidden / Predicciones-agroceba | 0.11267 | 0.54605 | 0.97908 |

El mayor rango entre las tres propuestas está en AGC_118: 2.85446 a 3.40051 t/ha. No sabemos cuál extremo se acerca al rendimiento real. Correlación alta, consenso, menor dispersión y cercanía a la media de entrenamiento no equivalen a precisión. No se copiaron valores, no se ajustó sesgo hacia un compañero y no se promediaron entregas sin residuos comunes para validar pesos. [B2, B9]

Para comparar mejor, `artifacts/comparison-common-folds.csv` deja dos asignaciones KFold(5), semillas **20261013 y 20261014**, sobre el orden maestro de las 138 etiquetas (276 filas largas). Son particiones propuestas para una comparación común, **no una reconstrucción de las usadas por los compañeros**. Cada proyecto tendría que producir OOF `ID, semilla, fold, observado, predicho`, sin usar su validación externa en ninguna selección, y se compararían errores por las mismas parcelas. Mantener MAE primario actual, RMSE como control, R², sesgo y sensibilidad espacial definida de forma idéntica. Las repeticiones se mantienen por separado y la incertidumbre se agrupa por parcela; no se cuentan como etiquetas nuevas. Si esos folds ya influyeron en las recetas, la comparación sigue siendo exploratoria. Una evaluación final oficial con las 59 etiquetas sería la prueba independiente disponible para el reto.

## 5. Ensayos de afinación y decisión

### Hipótesis sustentada y diagnóstico previo

Con 181 variables para 138 etiquetas, redundancia fuerte, varios ganadores externos y un empate interno de solo 0.000591 MAE entre RF y Ridge, se probó **reducir complejidad mediante Ridge y un grupo climático compacto**. ISLP describe el beneficio de regularizar estimaciones con alta varianza; ESL exige evaluar toda la secuencia, incluida selección de grupo. Son razones para hacer el ensayo, no pruebas de que vaya a ganar. [B2, B9]

También se examinó la reserva de calibración. ISLP describe reajustar tras selección con todos los datos disponibles, y FIRA solicita un punto por parcela. Se hicieron diagnósticos de cuatro recetas fijas (RF actual, Ridge actual, Ridge climático y RF climático), cinco folds y dos semillas **20261013/20261114**, con y sin reserva de calibración: 80 ajustes. Los IC descriptivos de las diferencias frente a RF con reserva cruzan cero; ajustar con más etiquetas no ayuda uniformemente. Por ejemplo, RF actual con todas las etiquetas del entrenamiento externo empeora bajo la segunda semilla. Este diagnóstico no ejecuta selección interna de recetas, por lo que **no valida el reemplazo del selector completo**. Comparte la semilla 20261013 con el ensayo anidado siguiente, pero usa 20261114 como segunda semilla en lugar de 20261014. [B2, F4; `scripts/diagnose_feature_recipes.py`]

### Comparación anidada del procedimiento completo

Se mantuvieron los 18 candidatos originales y se añadieron solo dos: Ridge α=10/100 usando los **40 predictores climáticos**, sin filtro supervisado adicional. Como ese grupo no cambia con la nube, se evalúa una vez por α, evitando triplicar candidatos equivalentes. El grupo se elige dentro de cada entrenamiento interno; también ahí se ajustan imputación, varianza y escalado. No se usa ni el rendimiento externo ni las salidas de los compañeros para elegirlo.

Ambos procedimientos comparten las mismas parcelas externas, ajuste/calibración, métrica MAE, predicción no negativa y semilla en cada ensayo. Se evaluaron las semillas 20261013/20261014 en aleatorio y espacial: **20 folds externos pareados**, cada uno con las mismas 138 etiquetas repartidas en su esquema. En espacial los bloques externos no cambian al cambiar semilla; sí cambian la asignación de bloques a calibración y la aleatoriedad del ajuste. No son dos particiones geográficas independientes.

Antes de ejecutar la comparación anidada se dejó `artifacts/refinement-audit/protocol.json`. Se fijó una regla conservadora: MAE menor en ambas semillas, RMSE sin empeorar, ausencia de deterioro espacial y límites superiores de los IC pareados de MAE negativos. El script aplica como control espacial la versión estricta de MAE y RMSE sin incremento. La comparación se diseñó tras inspeccionar datos/resultados previos; **no se llama preregistro independiente**. Los IC bootstrap percentiles (3000 remuestreos por parcela y por los seis bloques) son descriptivos y condicionales a los OOF, sin reajuste ni corrección por selección o dependencia de CV. No hay soporte para presentarlos como prueba confirmatoria; el resultado se evalúa principalmente por consistencia del error observado.

| Esquema y semilla | MAE actual | MAE candidato | RMSE actual | RMSE candidato | R² actual | R² candidato |
|---|---:|---:|---:|---:|---:|---:|
| Aleatorio 20261013 | 0.407694 | 0.402329 | 0.561318 | 0.547601 | 0.561921 | 0.583070 |
| Aleatorio 20261014 | 0.384118 | 0.384269 | 0.532401 | 0.538780 | 0.605893 | 0.596394 |
| Espacial 20261013 | 0.804789 | 0.823393 | 0.955497 | 0.988831 | -0.269388 | -0.359501 |
| Espacial 20261014 | 0.448702 | 0.509733 | 0.612419 | 0.733182 | 0.478527 | 0.252590 |

El cambio de MAE, candidato menos actual, en aleatorio es **-0.005365** y **+0.000152** t/ha. Los IC descriptivos por parcela son respectivamente [-0.02718, +0.01701] y [-0.01244, +0.01353]; por bloque [-0.02750, +0.03730] y [-0.01248, +0.00882]. La ganancia inicial no se reproduce, el RMSE empeora en la segunda semilla y ambos resultados espaciales empeoran. La fuerte variación del propio modelo espacial entre semillas ilustra sensibilidad de calibración/selección con muy pocos grupos; no se escoge la semilla favorable como nuevo resultado oficial.

**Decisión: descartar la promoción del candidato y conservar producción.** `artifacts/refinement-audit/decision.json` registra los controles incumplidos y `paired-oof.csv` permite recalcular las diferencias por parcela. El rechazo no prueba que toda regularización o compactación sea inútil; indica que esta modificación concreta no tiene apoyo suficiente para sustituir la propuesta actual. Tampoco se afirma que el modelo actual sea óptimo.

### Decisiones que no se implementaron

| Cambio considerado | Decisión y evidencia |
|---|---|
| Eliminar todo satélite por su importancia pequeña/negativa | No. La importancia con 28 casos y predictores correlacionados no demuestra inutilidad; el ensayo anidado compacto no mejora consistentemente. [B4] |
| Reajustar inmediatamente con 138 conservando el intervalo actual | No. Los diagnósticos de tamaño no prueban mejora uniforme y el radio corresponde a otro modelo ajustado con 110. Si se ensaya un predictor puntual con 138, hay que evaluar toda esa receta y separar/revalidar incertidumbre. [B2, B9, F4] |
| Seleccionar por RMSE porque cambia el ganador | No. Se mantuvo el criterio MAE actual y se reportó RMSE como control. No se identificó una métrica oficial única en las fuentes. [B6, B9] |
| Mezclar o copiar las 59 predicciones de compañeros | No. No hay verdad oculta ni OOF comunes para aprender/validar pesos. El desacuerdo no proporciona ese sustento. [B2, B9] |
| Corregir contracción estirando extremos o quitar AGC_171/015 | No. Sería adaptación a errores externos y no existe validación de etiqueta errónea. [B9, F4] |
| Añadir ventanas fenológicas exactas, manejo o variedad | No. No existen esas observaciones por parcela; mayo es referencia aproximada, no fecha exacta. [F4] |
| Añadir múltiples índices, familias o cientos de hiperparámetros | No en esta revisión. Un mayor espacio de búsqueda no demuestra ganancia y aumenta selección adaptativa con pocas etiquetas. Solo se probó la hipótesis compacta explícita. [B2, B9] |

## 6. Mejoras futuras que sí tienen una pregunta y una prueba definida

1. **Comparación común de los tres proyectos:** requiere sus OOF/código, mismos folds y definición métrica. Es el paso prioritario para resolver qué procedimiento generaliza mejor; los archivos entregados no permiten ejecutarlo por los compañeros. No se enviaron mensajes ni se modificaron sus proyectos.
2. **Precisión dentro de región:** buscar señal que supere de forma consistente la referencia regional, especialmente Puebla. Requiere nuevos predictores observados o ingeniería acotada con selección interna; se conserva un procedimiento congelado para evaluación. No añadir estado o rendimientos vecinos por intuición. [B3, B9]
3. **Uso de las 138 etiquetas para el punto:** evaluar un procedimiento que use todas las etiquetas del entrenamiento de cada fold externo, sin reserva de calibración, y después reajuste el punto final con 138; revalidar o separar explícitamente la estrategia de incertidumbre. Es una hipótesis apoyada metodológicamente, aún no una mejora aprobada por los resultados. [B2, F4]
4. **Datos para reducir incertidumbre agronómica:** fechas de siembra, variedad, manejo y eventos adversos medidos por parcela, si el organizador los aporta. La literatura motiva integrarlos y validarlos; no se inventan ni se asegura cuánto mejorarían. [B1, F4]

Estas líneas son oportunidades condicionadas a evidencia adicional, no una lista de cambios aplicados ni una promesa de exactitud a cuatro decimales. Los cuatro decimales son un formato de entrega, no resolución demostrada del error.

## 7. Reproducción, artefactos y verificaciones

Desde `C:\dev\reto-fira\platform`, con el entorno que contiene `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe scripts/compare_predictions.py
.\.venv\Scripts\python.exe scripts/verify_citations.py
.\.venv\Scripts\python.exe scripts/diagnose_spatial_support.py
.\.venv\Scripts\python.exe scripts/diagnose_feature_recipes.py
.\.venv\Scripts\python.exe scripts/evaluate_refinements.py
.\.venv\Scripts\python.exe -m pytest tests -q
```

Los scripts de auditoría no reentrenan ni reemplazan producción. Sus salidas permanentes son:

| Archivo/carpeta en `platform/` | Uso |
|---|---|
| `artifacts/comparison-summary.json` | Comprobaciones, procedencia y huellas de las entradas; diferencia medición reproducida de cifra ajena reportada. |
| `artifacts/comparison-input-audit.csv`, `comparison-predictions.csv`, `comparison-pairwise.csv` | Integridad de 59 IDs y desacuerdos por parcela/pares. |
| `artifacts/comparison-validation-metrics.csv`, `comparison-validation-slices.csv`, `comparison-largest-oof-errors.csv` | Métricas propias recalculadas, desgloses y errores grandes, además de cifras reportadas de compañeros con marca explícita. |
| `artifacts/comparison-common-folds.csv` | Asignaciones comunes propuestas, 276 filas. |
| `scripts/citation-specification.json`, `artifacts/citation-evidence.json` | 28 extractos de los 13 documentos originales, ubicaciones, hashes y comprobación literal. |
| `artifacts/refinement-audit/protocol.json`, `results.json`, `paired-oof.csv`, `decision.json`, `input-hashes.json` | Ensayo anidado completo y decisión de conservar producción. |
| `artifacts/refinement-audit/fixed-recipe-*` | Diagnóstico previo de recetas fijas/tamaño, distinto del selector anidado. |
| `artifacts/refinement-audit/support-summary.json`, `state-baseline-oof.csv` | Redundancia, soporte geográfico y referencia regional. |

Se verificaron **29 controles** de comparación: IDs/particiones/etiquetas, metadatos, áreas y producción del compañero que las incluye, intervalos ordenados, OOF completos, métricas, separación espacial externa, ajuste/calibración y reproducción del modelo final. Pasaron las **seis pruebas existentes** de la app/pipeline; aparecen avisos de deprecación de Rasterio/Affine. No se añadieron pruebas que solo repitan el cálculo del experimento. Las comprobaciones y huellas hacen revisables los resultados, sin convertir una auditoría en medición de verdad oculta.

No se reejecutó extracción de las 146 capas ni se sustituyeron sus features; se reutilizaron los artefactos actuales, cotejando su procedencia y soporte. El caché ambiental existente no invalida automáticamente por hash si cambian los insumos; para un reentrenamiento con fuentes modificadas se requiere `python -m pipeline.train --force-features`, como advierte el README. Esa orden **sí reemplaza resultados de producción** y no forma parte de esta comparación. No se declara validación visual nueva de la app ni prueba Docker, porque no se realizaron en esta auditoría.

## 8. Citas verificadas y alcance de cada decisión

Las páginas PDF son físicas, contadas desde 1; la página impresa se indica cuando pudo identificarse. Los párrafos DOCX se cuentan desde 1 incluyendo vacíos, como `python-docx`. Se normalizaron Unicode NFKC y espacios al verificar; no se reescribieron los extractos. Las citas apoyan el principio indicado y refutan inferencias excesivas: ninguna certifica nuestros valores ocultos.

### Bibliografía solicitada

| Clave y archivo original (ruta desde la raíz) | Ubicación y extracto literal breve | Decisión apoyada y límite |
|---|---|---|
| **B1** `data/libros/02.pdf`, Radočaj et al., revisión de predicción de rendimiento con satélite | PDF p.3: “management variables would provide a more detailed representation of crop yield dynamics” | Motiva combinar satélite con contexto ambiental/manejo observado. No demuestra que agregar variables ausentes o cualquier índice mejore estos datos. |
| **B2** `data/libros/An Introduction to Statistical Learning with Applications in Python.pdf` | PDF p.39, impresa29: “previously unseen test observation not used to train the statistical learning method” | Exigir etiquetas y evaluación fuera de ajuste; acuerdo entre CSV no mide exactitud. |
| B2, mismo libro | PDF p.211, impresa203: “the test error rate can be highly variable” | Medir sensibilidad a particiones; no contar repeticiones como nuevos sujetos. |
| B2, mismo libro | PDF p.252, impresa244: “ridge regression works best in situations where the least squares estimates have high variance.” | Sustenta probar regularización en un diseño redundante; no garantiza que Ridge gane aquí. |
| B2, mismo libro | PDF p.260, impresa252: “the model is re-fit using all of the available observations” | Motiva evaluar el punto con todos los datos después de selección; no autoriza reciclar la calibración independiente de otro ajuste. |
| **B3** `data/libros/Geographic Data Science with Python.pdf` | PDF p.166, impresa133: “the similarity in values between observations in a dataset is related to the similarity in locations” | Examinar dependencia y soporte espacial. No fija 20 km como bloque óptimo ni convierte estrés de transferencia en estimación exacta del split oculto. |
| B3, mismo libro | PDF p.348, impresa315: “The spatial error model includes a spatial lag in the error term” | Distinguir dependencia de errores y predictores. Una caída espacial de R² no prueba por sí sola fuga de etiquetas. |
| **B4** `data/libros/Interpretable Machine Learning - Christoph Molnar.pdf` | PDF p.208, §8.5.2: “You should probably use test data.” | Medir importancia en observaciones apartadas del ajuste; no elegir nuevas features con la misma prueba sin evaluar de nuevo el proceso. |
| B4, mismo libro | PDF p.216: “it makes the interpretation of the feature importance considerably more difficult” | Predictores correlacionados complican atribuir importancia; no eliminar automáticamente un grupo por importancia pequeña. |
| B4, mismo libro | PDF p.163: “but not necessarily for the real world!” | La explicación del modelo no establece causalidad agronómica; no prometer un aumento de rendimiento al modificar una variable. |
| **B5** `data/libros/Introduction to Data Mining.pdf` | PDF p.70, impresa46: “missing values should be taken into account during the data analysis” | Auditar faltantes y distinguirlos de cero; no prescribe mediana universal óptima. |
| B5, mismo libro | PDF p.180, impresa156: “a separate validation set that is not used for training the model.” | Separación evaluación/ajuste; el contexto original es clasificación, no una métrica de regresión transferible literalmente. |
| **B6** `data/libros/last.pdf`, Shawon et al., revisión sistemática de predicción de rendimiento | PDF p.1, resumen: “RMSE, R-square, and MAE are found to be the mostly favored.” | Reportar las tres métricas habituales; no establece métrica oficial FIRA ni algoritmo vencedor. |
| **B7** `data/libros/Python_Datascience.pdf`, VanderPlas | PDF p.400, impresa382: “All the steps of the model are applied automatically.” | Encapsular transformaciones; el ejemplo de esa página predice entrenamiento, por lo que un pipeline solo no prueba generalización. |
| **B8** `data/libros/Python-for-Data-Analysis.pdf`, McKinney | PDF p.225, impresa207: “Calling fillna with a constant replaces missing values with that value:” | Describe el mecanismo; no justifica que cero sea una medición física ni que la mediana sea la mejor estrategia. |
| **B9** `data/libros/The Elements of Statistical Learning.pdf` | PDF p.241, impresa222: “set error of the final chosen model will underestimate the true test error” | El contexto trata de elegir repetidamente modelos con el test; sustenta reconocer selección posterior a mirar errores como exploratoria. |
| B9, mismo libro | PDF p.265, impresa246, §7.10.2: “cross-validation must be applied to the entire sequence of modeling steps.” | Selección supervisada, grupo, nube, pesos y correcciones deben evaluarse dentro de todo el procedimiento. Refuta filtrar con todo y validar después. |

### Documentos FIRA solicitados

| Clave y original | Ubicación y extracto | Decisión y límite |
|---|---|---|
| **F1** `data/fira/context/Descripcion_general_variables_DataSet.docx` | §1, pára.7: “El rendimiento estará disponible para 138 parcelas del conjunto de ENTRENAMIENTO” | 138 etiquetas; el resto del párrafo especifica 59 ocultas. No imputar verdad ni medir precisión sobre ellas. |
| F1 | §1, pára.7: “el rendimiento proporcionado corresponde al ciclo de producción de abril - octubre de 2025” | Validación de un ciclo; no afirmar transferencia temporal ni pronóstico temprano con información de octubre. |
| F1 | §2, pára.14: “La selección de periodos, sensores, índices, criterios de nubosidad” | El resto del párrafo deja esas decisiones al equipo. No es una instrucción para elegir un umbral concreto. |
| **F2** `data/fira/context/Diccionario_de_indices_satelitales.docx` | Dataset PRO, pára.13: “no deben fusionarse automáticamente como si fueran mediciones equivalentes” | Conservar sensores separados y evitar mezclar índices con el mismo nombre como escala idéntica. |
| F2 | Consideraciones, pára.15: “No existen umbrales universales aplicables a todas las parcelas, fechas y etapas fenológicas.” | Refuta reglas fijas de productividad basadas en un corte arbitrario. |
| **F3** `data/fira/context/Ecuaciones_indices_AgroCebada_FIRA_2026.pdf` | PDF p.2, Landsat: “(B3 - ST_B10) / (B3 + ST_B10)” | VI6T usa señal térmica; no sustituir su fórmula por NDVI. |
| F3 | PDF p.1: “resampled corresponde a datos remuestreados a enteros de 8 bits.” | No equiparar automáticamente variantes del proveedor a fórmulas en índices float. |
| **F4** `data/fira/context/Segunda_Sesion_Preguntas_Reto.docx` | Pregunta2, pára.7: “No se dispone de la fecha exacta de siembra de cada parcela.” | No inventar alineación fenológica real. |
| F4 | Pregunta7, pára.17: “un valor puntual de rendimiento por parcela, expresado en t/ha y con cuatro decimales.” | Punto de entrega y formato; incertidumbre complementaria, no precisión demostrada a 0.0001. |
| F4 | Pregunta9, pára.21: “Las parcelas se seleccionaron mediante un muestreo aleatorio estratificado.” | CV por parcela pertinente al reto, con estratos exactos desconocidos y estrés espacial adicional. |
| F4 | Pregunta10, pára.23: “Por el momento no se cuenta con el historial de cultivos de cada parcela para ese periodo.” | No atribuir cebada a todos los años ni presentar historia ambiental como rendimiento etiquetado multianual. |

F4, preguntas5,12,14, añade procedencia mixta de rendimiento (comercializadora/productor) y falta de siniestros/variedad por parcela; se leyó como contexto de medición, no como motivo para borrar extremos ni causa demostrada de los errores observados.

### Textos, inventarios y CSV solicitados

| Clave / archivo | Evidencia consultada y uso |
|---|---|
| **T1** `data/fira/precipitation/LEEME.txt` y `annual-precipitation-inventory.csv` | “Precipitación acumulada mensual.”; unidad mm/mes, 0.05°, 48 capas. Inventario con mes, días esperados/encontrados, CRS y NoData. Control de unidades/agregación y resolución. |
| **T2** `data/fira/temperatures/LEEME_.txt` y `inventario_temperatura_2022_2025.csv` | “Tmin: promedio mensual de temperatura mínima diaria.”; Tmax análoga; °C, 96 capas, NoData -9999. No sumar temperaturas como GDD diarios observados. |
| **T3** `data/fira/INEGI-topography/LEEME.txt` y `inventario_topografia.csv` | “Resolución de entrega: 120 m.”; pendiente en grados; EPSG:6372 y NoData. Resuelve discrepancia de resolución frente a la referencia general. |
| Maestro de ID/área/rendimiento | 197 IDs únicos, 138 etiquetas/59 nulos; autoridad para uniones 1:1 y todas las evaluaciones propias. Se ignora la columna final enteramente vacía. |
| `Conjunto_datos_BASICO_AgroCebada2026.csv`, `Conjunto_datos_PRO_AgroCebada.csv` | Se revisaron sensor/fecha/nubes, columnas de índices y tratamiento vigente. Sus filas repetidas no aumentan n de etiquetas; los faltantes estructurales entre sensores no son ceros físicos. |
| `comparisons/agrocebada_hidden.csv` y `.md` | Entrega de 59 e información reportada de nested repetida, quick/experimental, promedio OOF, estrés KMeans y ajuste final138. Cifras atribuidas, sin código ni OOF ajenos verificables. |
| `comparisons/Predicciones-agroceba.csv` y `.md` | Entrega de 59 y cifras reportadas de selector anidado, separación por celda climática, selección interna RMSE y ajuste final138; el MD declara adaptación después de ver evaluaciones previas. |
| `platform/artifacts/predicciones_59.csv`, métricas, features, parcel metadata y ambos CSV de validación | Procedencia local comprobable, métricas recalculadas y modelo guardado reproducido. Copia exacta en `comparisons/predicciones_59.csv`. |

La trazabilidad de todas las entradas de la comparación está en `artifacts/comparison-summary.json`; los insumos generales del proyecto conservan su manifiesto original. Esta documentación distingue requisitos, principios bibliográficos, hipótesis y resultados: **no se aplicó una mejora de predicción que los datos no sostuvieran**.
