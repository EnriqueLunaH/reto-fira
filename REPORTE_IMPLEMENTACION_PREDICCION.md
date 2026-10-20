# Implementación y evaluación de la afinación de `reto-fira`

**Reto AgroCebada FIRA 2026 · Rendimiento de grano en toneladas por hectárea**  
**Población:** 138 parcelas etiquetadas y 59 parcelas de PREDICCION.  
**Alcance:** implementación, experimentos reproducibles, selección y verificación de la entrega. No se conocen los rendimientos reservados de las 59 parcelas.

<!-- RESULTADO_INICIO -->
**Resultado: se activó `point_extended`, un procedimiento que selecciona dentro del entrenamiento entre regresiones regularizadas, árboles y mezclas acotadas.** Al reajustarlo con las 138 etiquetas eligió **50% Ridge + 50% Random Forest**. Se generaron y verificaron las 59 predicciones, y se sincronizó `comparisons/proposal.csv`. Activación: 17 de octubre de 2026, 23:00:30 de Ciudad de México / 18 de octubre, 05:00:30 UTC. [E10]; [E12]; [E13].

En cinco repeticiones de validación anidada por parcela, el MAE del procedimiento pasó de **0.4018 a 0.3845 t/ha** (−4.30%) y el RMSE de **0.5578 a 0.5315 t/ha** (−4.71%). La alternativa cumplió las cinco condiciones de promoción fijadas antes de observar sus resultados. También mejoró los agregados espaciales frente a la referencia, aunque falló en una repetición y en varios grupos espaciales individuales. [E7]–[E10].

**Alcance de la mejora:** evidencia de validación sobre datos reutilizados, no medición del error en las 59 parcelas ocultas. La validación evalúa el procedimiento de selección completo; sus modelos varían entre folds. No demuestra que la mezcla final fija hubiera obtenido exactamente esas métricas si se la hubiese preseleccionado. Se informa incluso el diagnóstico Ridge, cuyo MAE aleatorio resultó menor, sin cambiar retrospectivamente las reglas para promoverlo.
<!-- RESULTADO_FIN -->

## 1. Problema que se resolvió y criterio de éxito

El objetivo es producir una predicción puntual por parcela oculta. No es reproducir el promedio de tres CSV ni demostrar que una familia de algoritmos es superior por definición. Las etiquetas disponibles corresponden al ciclo 2025; las series de imágenes de otros años no constituyen otros ciclos etiquetados. La autoridad para los IDs, conjuntos y rendimientos es el maestro de FIRA; la segunda sesión de preguntas confirma los límites de información y solicita un valor puntual con cuatro decimales. [F1], §1; [F4], preguntas 7, 9 y 10; [F8].

Se implementaron experimentos que permiten distinguir dos hipótesis:

1. **Cantidad de información para ajustar:** reservar 28 etiquetas exclusivamente para calibrar intervalos puede perjudicar la predicción puntual. Se compara el procedimiento original con el mismo conjunto de 18 candidatos usando todo el entrenamiento permitido en cada fold.
2. **Representación y familia:** las regresiones regularizadas, los árboles y unos resúmenes compactos pueden aprovechar mejor la información disponible. Se amplía un selector interno acotado y se evalúa el procedimiento completo, incluida una posible mezcla.

La bibliografía justifica realizar esas pruebas, no anticipa su resultado. ISLP explica la regularización y el reajuste después de seleccionar el modelo; ESL exige aplicar la validación a toda la secuencia de modelado. [B2], PDF 252 y 260; [B9], PDF 241 y 265. El artículo de Cawley y Talbot muestra que el sobreajuste del criterio de selección puede tener un efecto comparable a las diferencias entre algoritmos. [W7].

El éxito operativo consiste en aceptar solamente un reemplazo que satisfaga los criterios fijados antes de los nuevos resultados. Si ninguna alternativa los cumple, el resultado correcto es conservar la entrega y registrar el conocimiento obtenido. Una mejora en validación no garantiza menor error en las 59 etiquetas ocultas. [B2], PDF 39; [W1], p. 4.

## 2. Evidencia reutilizada y preservación de la referencia

Se conservaron la extracción sobre la malla nativa de los rasters, las intersecciones ponderadas por área y la regla de cobertura del 80%. No se cambiaron las etiquetas, geometrías ni los archivos originales. Antes de reutilizar las características se cotejaron las huellas de las fuentes con el manifiesto que produjo los artefactos y se comparó el maestro original con los metadatos usados para entrenar. El detalle verificable está en [E2] y [E3].

La carpeta `platform/artifacts/model-refinement-v2/incumbent/` contiene copias anteriores de modelo, métricas, dashboard, CSV, validaciones y código de entrenamiento. También conserva las copias de comparación existentes. [E4] identifica sus hashes. Se evita así confundir la evaluación de una receta nueva con el comportamiento de la versión entregable anterior.

Se reutilizan los siguientes hallazgos de la revisión previa, con su alcance:

| Propuesta | Información útil | Limitación que no se traslada |
|---|---|---|
| `proposal-01` | Ridge como hipótesis estadística y control de complejidad. | Su tabla pierde las 84 columnas climáticas en 196/197 parcelas; no es una prueba justa contra un modelo que sí recibe clima. |
| `proposal-02` | Resúmenes climáticos/satelitales y posibilidad de combinar predictores complementarios. | Selección supervisada antes de CV, reutilización de las particiones de búsqueda y falta de evaluación externa propia del ensamble. |
| `reto-fira` original | Extracción nativa y preparación aprendida dentro del entrenamiento; selección anidada. | 110 parcelas de ajuste y 28 de calibración final; la reserva para intervalos se evalúa como posible coste para la predicción puntual. |

Fuentes: [P1], `zonal_features` y `evaluate_models`; [P1f]; [P2b]; [P2c]; [R1]. La revisión detallada y sus evidencias están en [ANT], sección 3. Las otras dos propuestas permanecen como antecedentes: no se usan sus 59 salidas como etiquetas ni se reescriben como supuestos modelos FAO.

## 3. Implementación de los candidatos

### 3.1 Un mismo contrato de datos

`pipeline/refinement.py` reúne las tres tablas de nube 20%, 40% y 60%, cada una con 181 variables, alineadas por identificador. El contenedor de entrada tiene 543 columnas, pero cada candidato individual utiliza solo su umbral y su receta. La combinación permite que un ensamble tenga dos miembros con filtros distintos sin confundir las columnas. Los IDs, estado, conjunto, coordenadas y rendimiento quedan fuera de los predictores. El estado se utiliza exclusivamente para evaluar subgrupos y una referencia descriptiva. [I1], `load_data` y `RecipeTransformer`; [F2]; [R2].

Todas las transformaciones nuevas son locales a cada fila: no calculan estadísticas poblacionales ni utilizan etiquetas. Las medianas de imputación, eliminación de constantes, escalado y selección supervisada sí se aprenden, pero únicamente al ajustar cada entrenamiento. Se preserva un indicador de ausencia y no se interpreta un dato faltante como ausencia física de lluvia o vegetación. [I1], `make_model`; [B5], PDF 70; [B7], PDF 400; [B8], PDF 225; [B9], PDF 265.

### 3.2 Recetas predefinidas

| Receta | Variables | Decisión implementada |
|---|---:|---|
| Original | 181 | Representación actual y selección univariante interna de 30, 35, 40 o 60 variables, según algoritmo. |
| Ambiente | 43 | Las 40 variables climáticas actuales más elevación, pendiente y superficie. Solo nube 20 porque estas variables no dependen del filtro satelital; duplicar nubes sería repetir el mismo candidato. |
| Vigor | 26 | Tres sumas de lluvia; temperatura media y amplitud de abril–junio, julio–agosto y septiembre–octubre; relieve y superficie; NDVI/EVI medio, máximo y cambio tardío de Sentinel-2 y Planet; cobertura mensual de ambos sensores. |
| Humedad y trayectoria | 42 | Las 26 anteriores, resúmenes NDWI/MSI/DSWI2 de Sentinel-2 y MSAVI de Planet; media, dispersión y cobertura NDVI mayo–octubre; cambio mayo–junio a julio–agosto. |

Los nombres, columnas y reglas exactas se congelan en [E1], `feature_columns`. En las recetas compactas se conservan todas las columnas no constantes después de imputar; no se impone un filtro marginal de correlación antes de Ridge o de árboles. La regularización limita los coeficientes de Ridge y el tamaño de hojas limita los árboles. Son mecanismos distintos que se comparan dentro del mismo protocolo. [B2], §6.2; [B9], §7.10.2.

Las ventanas son meses del calendario, no etapas fenológicas observadas. Las medias de temperatura por ventana requieren todos sus meses. La media y dispersión NDVI de mayo–octubre requieren al menos cuatro de los seis meses; el cambio entre ventanas de dos meses exige ambos valores en cada ventana. La cobertura faltante se mantiene como dato ausente. El mínimo de cuatro meses es una especificación operativa fijada antes de evaluar, no una regla agronómica universal. [I1], `feature_recipe`; [F4], pregunta 2; [F6].

Se respetan los sensores: no se intercambian fórmulas de índices ni se presenta LAI como biomasa medida. Las recetas nuevas no requieren interpolar huecos largos ni suponer una fecha de siembra. No se añadió una integral temporal ni índices nuevos fuera del conjunto probado: ampliar simultáneamente todas las alternativas habría aumentado la búsqueda con solo 138 etiquetas. [F2]; [F3], pp. 1–2; [B1], PDF 3; [B6], PDF 1; [W7].

### 3.3 Algoritmos y presupuesto de búsqueda

Se conservan los 18 candidatos originales como control: seis familias/configuraciones por tres filtros de nube. Son Ridge con alpha 10/100 y selección de 30 variables; Extra Trees con 180 árboles, hoja mínima 3 y 60 variables; Random Forest con 180 árboles, hoja mínima 4 y 60 variables; HistGradientBoosting con 120 iteraciones, 7 hojas, hoja mínima 12, regularización L2 de 10, tasa 0.05 y 35 variables; SVR con C=5, epsilon=0.15 y 40 variables. Los árboles aleatorios usan fracción de características 0.8. [R1], `candidates`; [I1], `specifications`.

Las recetas nuevas prueban cinco configuraciones: Ridge alpha 1, 10 y 100; Random Forest moderado; HistGradientBoosting moderado. Los parámetros de árboles se mantienen iguales a sus contrapartes anteriores, excepto que la receta compacta conserva todas sus columnas después de eliminar constantes. Se obtienen **35 candidatos nuevos**: 5 de ambiente, 15 de vigor y 15 de humedad/trayectoria. En total son **53 candidatos individuales**. Esta es una búsqueda deliberadamente acotada, no un reclamo de optimización exhaustiva. [E1]; [I1].

La revisión de Clark et al. justifica considerar varias familias y combinar información agroclimática y satelital. No permite concluir que ML supere siempre a la estadística; además, la mayoría de sus modelos son de trigo y a escalas superiores a la parcela. Por eso la implementación deja a Ridge competir con los árboles y utiliza los resultados de este conjunto para decidir. [W8].

### 3.4 Mezcla pequeña, seleccionada dentro del entrenamiento

Se obtiene el mejor Ridge y el mejor Random Forest usando exclusivamente las predicciones internas fuera de muestra. Se prueban pesos de Ridge 0.25, 0.50 y 0.75; los extremos ya están representados por los candidatos individuales. La mezcla entra en el mismo selector y no se fuerza su uso. No se calculan pesos a partir del error de entrenamiento ni se ajustan contra los CSV ocultos. [I1], `select_models` y `WeightedPredictor`; [B9], PDF 265.

Seleccionar primero los componentes y después los pesos puede sobreajustar la validación interna. Precisamente por eso la evaluación externa abarca ambas decisiones. No se presenta la mejor métrica interna como desempeño de entrega. Tampoco se usa SHAP de un RF para explicar una mezcla diferente. [W7]; [B4], PDF 163 y 208.

## 4. Evaluación común y prevención de fuga

### 4.1 Procedimientos que se comparan

- **`incumbent`:** reproduce el procedimiento anterior, incluida reserva del 20% del entrenamiento externo para calibración; la predicción se ajusta con el resto.
- **`point_original`:** usa los mismos 18 candidatos, pero permite ajustar y seleccionar con todo el entrenamiento externo.
- **`point_extended`:** usa los 53 candidatos y las tres mezclas, con todo el entrenamiento externo.
- **Diagnósticos:** mejor Ridge, mejor RF, mejor boosting, mejor candidato por receta y selector ampliado sin mezcla; todos se seleccionan internamente. También mediana global y mediana por estado, aprendidas en cada entrenamiento.

Solo `point_original` y `point_extended` pueden sustituir al original por la regla congelada. Los mejores resultados de familia o receta son diagnósticos: escoger uno de ellos después de observar sus errores externos sería otra selección no evaluada. [E1]; [I2], `evaluate_job` y `decide`; [B9], PDF 241.

### 4.2 Particiones

Se ejecutan cinco repeticiones por parcela, con semillas **20261013, 20261014, 20261015, 20261016 y 20261017**. Cada repetición contiene cinco folds externos y cada selección tres folds internos. En cada repetición, las 138 parcelas reciben exactamente una predicción externa por procedimiento. Se comparten las mismas parcelas de evaluación: la comparación es pareada. [E5]; [W9], §2.4.

Se añaden dos pruebas espaciales: cuadrículas de **10 km y 20 km**, sobre coordenadas EPSG:6372 y origen fijo (0,0), cinco folds agrupados en cada escala, semilla 20261013 para aleatoriedad de modelos y reserva de calibración. No hay grupos espaciales compartidos entre entrenamiento y evaluación; la selección interna también respeta esos grupos. Los tamaños de cuadrícula son análisis de sensibilidad predefinidos, no una distancia de independencia espacial estimada. [E1]; [I2]; [B3], PDF 166 y 348.

Esto produce **35 evaluaciones externas**: 25 por parcela y 10 espaciales. Son 7,455 ajustes internos de candidatos individuales, antes de los reajustes de ganadores: 35 × (18 × 3 + 53 × 3). Las mezclas reutilizan predicciones internas. Cada fold conserva IDs de entrenamiento, calibración, validación, particiones internas, puntuaciones y selección. [E6].

La cercanía de las parcelas ocultas a las conocidas hace pertinente evaluar interpolación local, mientras las cuadrículas describen la dificultad de transferir a otras zonas. Agrupar por ID no basta para eliminar la proximidad entre parcelas distintas. El estudio de Habibi et al. evalúa transferencia a campos independientes de soja y respalda comprobar la separación espacial para ese objetivo; no determina una cuadrícula universal para FIRA. [ANT], §4.3; [W10].

### 4.3 Métricas y unidades

Para cada repetición se calculan las métricas sobre las 138 predicciones externas juntas:

- **MAE:** media de |observado − predicho|, en t/ha; criterio primario.
- **RMSE:** raíz de la media de errores cuadrados, en t/ha; control de errores grandes.
- **R² predictivo:** 1 − SSE/SST; puede ser negativo.
- **Sesgo:** media de predicho − observado, en t/ha; positivo significa sobreestimación.

Entre repeticiones, el MAE se promedia; el RMSE agregado es la raíz de la media de los MSE de las repeticiones. **No se promedian las predicciones de las cinco repeticiones para atribuir al modelo una métrica artificialmente más favorable.** Las métricas se desglosan también por estado y por esquema. [E7]; [E8]; [E9]. FIRA menciona RMSE, MAE, r² u otras medidas del comité, sin fijar aquí una fórmula exclusiva; elegir MAE como principal es una política del experimento. [W1], p. 5.

El NSE estándar y el R² definido por 1 − SSE/SST coinciden sobre las mismas observaciones; no se agregan como votos independientes. La correlación de Pearson al cuadrado no es esa misma medida y no sustituye la magnitud del error en t/ha. [W11]; [W12].

### 4.4 Regla congelada de sustitución

Antes de los resultados nuevos se exigió a cada alternativa elegible:

1. Reducir el MAE medio al menos **0.01 t/ha**, equivalente a 10 kg/ha.
2. Reducir MAE en al menos **cuatro de cinco** repeticiones.
3. No incrementar el RMSE agregado.
4. No empeorar simultáneamente MAE y RMSE en **ambas** escalas espaciales.
5. Tener por debajo de cero el límite superior del intervalo descriptivo de diferencias de MAE obtenido por bootstrap pareado de parcelas.

Si ambas pasan, se prefiere `point_original`, salvo que el selector ampliado reduzca su MAE al menos otras 0.01 t/ha. Esto limita la complejidad sin afirmar que los dos procedimientos sean estadísticamente equivalentes. Los umbrales son decisiones operativas del equipo, explícitas y previas; **no proceden de FIRA ni son constantes científicas**. [E1], `promotion`; [B2], PDF 248; [W9], §2.5.

Para el bootstrap se promedia primero la diferencia de pérdidas de cada parcela entre las cinco repeticiones; después se remuestrean las 138 parcelas 5,000 veces. También se remuestrean bloques de 20 km como sensibilidad. No se tratan 690 predicciones como 690 parcelas independientes. Los intervalos son descriptivos: no corrigen toda la dependencia de CV, ni el desarrollo previo con las mismas etiquetas, ni la selección entre procedimientos. El intervalo por bloques se informa aunque incluya cero; su límite superior no es una condición adicional de promoción. [I2], `paired_bootstrap`; [E10].

## 5. Resultados ejecutados

<!-- METRICAS_INICIO -->
### 5.1 Comparación anidada por parcela

Cada cifra resume cinco repeticiones sobre las mismas 138 parcelas, no cinco conjuntos independientes. R² se promedia entre repeticiones; MAE y sesgo tienen unidades t/ha. [E7]; [E8].

| Procedimiento | MAE (t/ha) | RMSE (t/ha) | R² medio | Sesgo (t/ha) |
| --- | --- | --- | --- | --- |
| Referencia con reserva de calibración | 0.4018 | 0.5578 | 0.5675 | 0.0148 |
| Puntual, candidatos originales | 0.3860 | 0.5388 | 0.5964 | 0.0066 |
| Puntual ampliado — promovido | 0.3845 | 0.5315 | 0.6073 | -0.0030 |
| Ampliado sin mezclas — diagnóstico | 0.3889 | 0.5423 | 0.5912 | 0.0015 |
| Ridge — diagnóstico | 0.3756 | 0.5187 | 0.6259 | -0.0019 |
| Random Forest — diagnóstico | 0.3953 | 0.5484 | 0.5818 | 0.0002 |
| Boosting — diagnóstico | 0.4128 | 0.5695 | 0.5490 | -0.0044 |
| Ambiente — diagnóstico | 0.3828 | 0.5348 | 0.6023 | -0.0038 |
| Vigor — diagnóstico | 0.4175 | 0.5628 | 0.5596 | -0.0226 |
| Humedad/trayectoria — diagnóstico | 0.4064 | 0.5589 | 0.5658 | -0.0165 |
| Mediana por estado | 0.4404 | 0.6255 | 0.4560 | -0.0088 |
| Mediana global | 0.7566 | 0.9464 | -0.2453 | 0.3389 |

El selector ampliado reduce el MAE frente a la referencia en **0.017265 t/ha**, aproximadamente **17.3 kg/ha**. Frente al selector puntual original la diferencia es solo **0.001494 t/ha**: no se atribuye toda la mejora a los nuevos índices. Buena parte de la señal favorable aparece al eliminar la reserva para intervalos. La ampliación aporta la estabilidad exigida por la regla de promoción, pero esta ronda no identifica causalmente la aportación aislada de cada cambio.

**Resultado incómodo que se conserva:** Ridge obtiene MAE 0.3756 y RMSE 0.5187 en el diagnóstico aleatorio, inferiores a los del procedimiento promovido. No se lo declara perdedor. No era elegible como procedimiento de reemplazo en el protocolo y seleccionarlo ahora explotaría el mismo resultado externo usado para evaluarlo. Además, su MAE espacial es 0.5514 a 10 km y 0.6110 a 20 km, mayor que el del selector ampliado en ambos casos. Queda como hipótesis prioritaria para otra evaluación con evidencia independiente, no como permiso para seguir buscando hasta obtener la cifra mínima. [E1]; [E8]; [W7].

### 5.2 Consistencia entre particiones

| Semilla | MAE anterior | MAE nuevo | Δ MAE | RMSE anterior | RMSE nuevo |
| --- | --- | --- | --- | --- | --- |
| 20261013 | 0.4077 | 0.3902 | -0.0175 | 0.5613 | 0.5297 |
| 20261014 | 0.3841 | 0.3731 | -0.0111 | 0.5324 | 0.5215 |
| 20261015 | 0.4159 | 0.3851 | -0.0308 | 0.5820 | 0.5290 |
| 20261016 | 0.4213 | 0.3729 | -0.0484 | 0.5810 | 0.5293 |
| 20261017 | 0.3798 | 0.4013 | 0.0214 | 0.5298 | 0.5476 |

La semilla 20261017 empeora: **no hubo una mejora universal**. `point_original` mejora solo en tres de cinco semillas, por lo que no se promueve aunque su promedio sea favorable. `point_extended` mejora en cuatro y satisface las demás condiciones. Los intervalos descriptivos del cambio de MAE (nuevo − anterior) son **[−0.032044, −0.002555] t/ha** por parcelas y **[−0.029894, −0.006818] t/ha** por bloques de 20 km. Para `point_original`, el intervalo por bloques incluye cero: **[−0.025101, +0.007155]**. No son pruebas independientes de significación ni intervalos para las 59 predicciones. [E10].

### 5.3 Transferencia espacial y heterogeneidad

| Esquema | Procedimiento | MAE | RMSE | R² | Sesgo |
| --- | --- | --- | --- | --- | --- |
| spatial10 | incumbent | 0.5467 | 0.7275 | 0.2641 | 0.1791 |
| spatial10 | point_extended | 0.5201 | 0.7085 | 0.3021 | 0.1671 |
| spatial10 | point_original | 0.4899 | 0.6957 | 0.3271 | 0.1533 |
| spatial20 | incumbent | 0.8048 | 0.9555 | -0.2694 | -0.3589 |
| spatial20 | point_extended | 0.5977 | 0.8090 | 0.0901 | 0.2941 |
| spatial20 | point_original | 0.5390 | 0.7495 | 0.2189 | 0.2659 |

El modelo promovido mejora frente a la referencia en las dos escalas. Sin embargo, `point_original` presenta mejores agregados espaciales que el ampliado. Por tanto, la decisión final responde a la regla conjunta predefinida y al objetivo de parcelas del mismo conjunto; **no demuestra superioridad del nuevo modelo para toda región desconocida**. A 20 km el sesgo nuevo es +0.2941 t/ha y el R² apenas 0.0901: sigue existiendo una debilidad importante de transferencia.

Los resultados por fold revelan cuánto depende el promedio de grupos grandes y difíciles:

| Esquema | Fold | n | MAE anterior | MAE nuevo | Δ MAE |
| --- | --- | --- | --- | --- | --- |
| spatial10 | 1 | 29 | 0.5178 | 0.4318 | -0.0860 |
| spatial10 | 2 | 28 | 0.4040 | 0.4507 | 0.0467 |
| spatial10 | 3 | 27 | 0.5701 | 0.3806 | -0.1896 |
| spatial10 | 4 | 27 | 0.3414 | 0.3890 | 0.0476 |
| spatial10 | 5 | 27 | 0.9074 | 0.9575 | 0.0501 |
| spatial20 | 1 | 58 | 1.1726 | 0.3645 | -0.8081 |
| spatial20 | 2 | 27 | 0.4115 | 0.4269 | 0.0154 |
| spatial20 | 3 | 21 | 0.4691 | 0.8444 | 0.3754 |
| spatial20 | 4 | 16 | 1.0453 | 1.4125 | 0.3672 |
| spatial20 | 5 | 16 | 0.3353 | 0.5928 | 0.2576 |

El fold con más parcelas de evaluación a 20 km mejora mucho, mientras cuatro de los cinco folds empeoran su MAE. Los folds contienen grupos completos, pero tienen tamaños desiguales. La métrica agregada pondera parcelas, no folds por igual. No se reinterpretan estos resultados como una garantía de extrapolación. [E5]; [E6]; [W10].

### 5.4 Errores por estado y parcela

| Estado | Procedimiento | Parcelas únicas | MAE medio | Sesgo medio |
| --- | --- | --- | --- | --- |
| Hidalgo | incumbent | 36 | 0.3395 | 0.0326 |
| Hidalgo | point_extended | 36 | 0.3197 | -0.0142 |
| Puebla | incumbent | 71 | 0.4438 | -0.0199 |
| Puebla | point_extended | 71 | 0.4262 | -0.0255 |
| Tlaxcala | incumbent | 31 | 0.3777 | 0.0733 |
| Tlaxcala | point_extended | 31 | 0.3642 | 0.0615 |

Se reduce el MAE medio en los tres estados; eso no implica mejorar cada parcela ni elimina los errores grandes. Estas son las ocho parcelas con mayor error absoluto medio nuevo entre las cinco repeticiones:

| ID | Estado | Observado | MAE anterior | MAE nuevo | Δ MAE |
| --- | --- | --- | --- | --- | --- |
| AGC_015 | Puebla | 2.6400 | 2.3114 | 2.2307 | -0.0807 |
| AGC_171 | Puebla | 2.1500 | 2.3298 | 2.2220 | -0.1078 |
| AGC_034 | Hidalgo | 2.0000 | 1.2777 | 1.3081 | 0.0303 |
| AGC_024 | Puebla | 3.0300 | 1.2534 | 1.2663 | 0.0130 |
| AGC_166 | Hidalgo | 2.5000 | 1.4075 | 1.2132 | -0.1943 |
| AGC_160 | Puebla | 3.6200 | 1.2658 | 1.2036 | -0.0622 |
| AGC_162 | Puebla | 5.5900 | 1.1203 | 1.1284 | 0.0081 |
| AGC_127 | Puebla | 5.5700 | 0.9382 | 0.9273 | -0.0110 |

Se conserva el detalle completo en [E15]. No se retiran estas observaciones ni se corrigen sus etiquetas para mejorar las métricas; requerirían evidencia independiente de un error de medición. [B5], PDF 70; [E5].

### 5.5 Estabilidad de selección e interpretación

| Selección interna | Folds / 25 |
| --- | --- |
| blend_ridge_0.5 | 9 |
| blend_ridge_0.75 | 7 |
| original_c60_gradient_boosting | 3 |
| environment_c20_ridge_10 | 2 |
| original_c40_extra_trees | 1 |
| original_c60_random_forest | 1 |
| original_c60_ridge_10 | 1 |
| environment_c20_gradient_boosting | 1 |

La mezcla se elige en 16 de 25 folds aleatorios. Los componentes concretos también pueden variar: no se debe confundir estabilidad de familia con estabilidad exacta de variables o pesos. En los otros folds compiten configuraciones individuales, incluido boosting. La selección final sobre 138 etiquetas se realiza de nuevo con el mismo procedimiento interno. [E16]; [E12].

La importancia se recalculó con modelos de cada fold externo de la semilla primaria 20261013 y diez permutaciones por grupo. Una fila nunca se explica con un modelo ajustado usando su etiqueta. Las variables del mismo grupo se permutan juntas y de forma consistente entre filtros de nube. Los aumentos de MAE se ponderan por número de parcelas:

| Grupo permutado | Aumento medio de MAE (t/ha) |
| --- | --- |
| Lluvia | 0.260160 |
| Temperatura | 0.105438 |
| Superficie | -0.000812 |
| Señal Landsat | -0.002246 |
| Vegetación Planet | -0.007628 |
| Vegetación Sentinel-2 | -0.009669 |
| Relieve | -0.013130 |

La lluvia y temperatura dominan este diagnóstico. Los valores negativos pequeños de otros grupos no demuestran que carezcan de valor en toda configuración: hay redundancia, ruido y variación de selección. No se volvieron a eliminar grupos a partir de este diagnóstico externo. El resultado respalda evitar el relato de que agregar satélites siempre mejora; las recetas de vigor y humedad, evaluadas por separado, no superan a la referencia en MAE aleatorio. [E14]; [W13].
<!-- METRICAS_FIN -->

## 6. Qué se conservó, qué se descartó y qué quedó sin probar

| Decisión de la propuesta original | Aplicación y fundamento |
|---|---|
| D1–D3: comparación honesta y aprovechamiento de propuestas | Se reutilizan ideas, no sus etiquetas inexistentes ni sus errores de extracción/validación. [P1f]; [P2b]; [B9]. |
| D4–D9: protocolo, particiones, promoción y extracción | Implementados en el manifiesto, folds comunes, pruebas espaciales, regla de decisión y comprobación de fuentes. [E1]–[E6]. |
| D10: todas las etiquetas para la estimación puntual | Evaluado directamente en `point_original` frente a `incumbent`; no se presume mejor por tener más datos. [E7]; [B2]. |
| D11 y D14: representaciones compactas y algoritmos moderados | Comparación explícita de Ridge, RF y boosting; representación original como control. [I1]; [E1]. |
| D12–D13: trayectoria y nubosidad | Se prueban resúmenes mayo–octubre con cobertura mínima, manteniendo los tres filtros. No se añadió nube 100%, integral temporal o nuevas fuentes en esta ronda. [F2]; [I1]. |
| D15: ensamble | Solo tres pesos internos; los candidatos individuales siguen compitiendo. No se impone una mezcla. [I1]. |
| D16: revisión de errores e interpretación | Errores por ID y estado; se mantienen extremos legítimos. No se reajusta el modelo después de mirar los errores externos. [E5]; [E9]; [B4]; [B5]. |
| D17–D19: FAO, componentes de rendimiento y GDD | No incorporados: faltan insumos o introducirían supuestos no contrastados. No son métodos inútiles en general; quedan fuera de la entrega actual. [F4]; [F6]; [W3]. |
| D20: evidencia y entrega verificable | Protocolo, respaldo, hashes, OOF, métricas, decisiones y pruebas automatizadas; conclusión final condicionada a esta evidencia. [E1]–[E10]; [I3]. |

No se borran archivos de antecedentes ni datos originales con el argumento de que no aportan. El descarte se aplica a la receta de predicción y a hipótesis que no superan la evaluación. Preservar experimentos fallidos permite revisar la decisión y evita volver a seleccionar el resultado favorable de una búsqueda anterior. [B9], §7.2; [W7].

No se incorporan redes neuronales, correcciones manuales por parcela, recorte al rango histórico, multiplicadores Kc/HI, descuentos automáticos por trilla ni pseudoetiquetas del consenso entre CSV. Tampoco se interpreta la anomalía respecto de 2022–2024 como una normal climatológica de largo plazo. La disponibilidad de esas fórmulas o técnicas no prueba su pertinencia para estos datos. [ANT], §§5–6; [F4]; [W3].

## 7. Modelo entregado, incertidumbre y aplicación

<!-- ENTREGA_INICIO -->
### 7.1 Configuración final

El selector interno sobre las 138 etiquetas eligió `blend_ridge_0.5`:

| Miembro | Peso | Variables y parámetros |
|---|---:|---|
| Ridge | 0.50 | Nube 60%; receta original de 181 variables, imputación y selección interna de 30, alpha 10. |
| Random Forest | 0.50 | Nube 60%; receta humedad/trayectoria de 42 variables antes de indicadores de ausencia, 180 árboles, hoja mínima 4, fracción de características 0.8. |

Ambos se reajustan con **138 parcelas** después de elegir la configuración. El CSV usa la mezcla de las predicciones, limitadas inferiormente a cero por la misma política usada al evaluar. No se aplican ajustes manuales a las 59 salidas. [I1]; [I4]; [E12].

La puntuación interna final es MAE **0.362012** y RMSE **0.513399**. Son valores utilizados para seleccionar, y **no sustituyen** las métricas externas de la sección 5. La diferencia entre ambas estimaciones es esperable por reutilización de la validación interna y tamaños de entrenamiento distintos. [E12]; [W7].

### 7.2 Entrega y cambios

Se verificaron exactamente 59 IDs únicos correspondientes a PREDICCION, sin valores ausentes o no finitos, con las dos columnas requeridas y cuatro decimales. Media **3.9185 t/ha**, mínimo **2.8003**, máximo **4.7358**. Respecto del CSV anterior, el cambio medio es **+0.0205 t/ha** y el cambio absoluto medio **0.1107 t/ha**. Estas diferencias describen salidas; no miden un error verdadero. [E17]; [E18].

| ID | Predicción anterior | Predicción nueva | Cambio (t/ha) |
| --- | --- | --- | --- |
| AGC_183 | 3.2283 | 2.9164 | -0.3119 |
| AGC_190 | 4.6650 | 4.3695 | -0.2955 |
| AGC_095 | 4.2359 | 4.5148 | 0.2789 |
| AGC_120 | 3.1274 | 3.4029 | 0.2755 |
| AGC_129 | 3.1438 | 3.3850 | 0.2412 |
| AGC_088 | 4.5177 | 4.2868 | -0.2309 |
| AGC_039 | 3.0688 | 2.8410 | -0.2278 |
| AGC_192 | 4.9140 | 4.6998 | -0.2142 |

Las tres copias de entrega son idénticas: `platform/artifacts/predicciones_59.csv`, `comparisons/predicciones_59.csv` y `comparisons/proposal.csv`. Los CSV de `proposal-01` y `proposal-02` permanecen intactos. Hash SHA-256 nuevo:

`3391c573da2588cbc6eb6c939e66513c8794df8a0b0a45c275bda3705357687b`

El anterior está respaldado con hash `53b1b2fe8f46c66814a12d036826bca80e5a5c4cbdd529a43358cef83ce665ff`. [E4]; [E12]; [E13]. La activación es local: **no se envió la entrega a FIRA**.

### 7.3 Coherencia de la aplicación

Se actualizaron conjuntamente modelo, CSV, dashboard, métricas y archivos OOF. La aplicación muestra **intervalo no disponible** para este predictor puntual; conserva límites nulos en lugar de reutilizar los conformales anteriores o convertirlos en cero. La metodología identifica ajuste con 138 etiquetas y cero de calibración.

Las gráficas de validación y el simulador económico usan una sola predicción externa por parcela: semilla primaria **20261013** para validación por parcela y cuadrícula de **20 km** para estrés espacial. Por ello, la pantalla puede mostrar MAE 0.3902 por parcela y 0.5977 espacial; el 0.3845 del reporte es el promedio de cinco repeticiones. No se multiplican las 36 observaciones de Hidalgo por cinco para aparentar una muestra mayor. Se conservan las fórmulas económicas y sus límites; ahora consumen las predicciones y errores de la versión nueva. [I4]; [E5]; [E19].

La importancia global usa OOF, mientras la sensibilidad individual sustituye grupos por las medianas del entrenamiento del modelo final. Esta última es una perturbación descriptiva, no un intervalo ni una estimación causal de manejo. Los rangos de características se recalcularon para las representaciones realmente usadas. [I4]; [B4].
<!-- ENTREGA_FIN -->

Los intervalos del modelo anterior pertenecen al predictor ajustado con 110 parcelas y calibrado con otras 28. No pueden trasladarse alrededor de un predictor que ya utilizó esas 28 etiquetas para ajustarse. Si se promueve un predictor puntual de 138 etiquetas, la ausencia de un intervalo validado debe mostrarse explícitamente; el reporte no presenta dispersión entre árboles como cobertura predictiva. FIRA considera los rangos un complemento del valor puntual. [F4], pregunta 7; [W6], §§1.1 y 2.3.

La evaluación y cualquier importancia por permutación describen el procedimiento predictivo y asociaciones, no los efectos causales de cambiar riego, clima o manejo. La permutación de grupos correlacionados es un diagnóstico del uso de la información, no una recomendación agronómica causal. [B4], PDF 163, 208 y 216; [W13].

## 8. Verificación y reproducción

<!-- VERIFICACION_INICIO -->
Se completaron las siguientes verificaciones:

| Comprobación | Resultado y evidencia |
|---|---|
| Fuentes y maestro | 156 archivos fuente cotejados con el manifiesto; metadatos concordantes; no se modificaron insumos. [E3]. |
| Reproducción de la referencia | Predicciones de referencia reconciliadas con tolerancia absoluta 1e−10 en los esquemas comparables. [E10]. |
| Particiones | 35 folds externos, separación de IDs y grupos también en selección interna; 966 filas OOF equivalen a 138 × 7 esquemas/repeticiones. [E11]. |
| Métricas independientes | 84 filas recalculadas mediante fórmulas NumPy; máxima discrepancia 4.44e−16. No se depende solo de la misma función que generó las métricas. [I5]; [E11]. |
| Evidencia preservada | Huellas de entradas congeladas y respaldo anterior sin cambios. [E11]. |
| Modelo persistido | Recarga del archivo y comparación de predicciones con CSV a tolerancia 0.00005 t/ha, acorde con cuatro decimales. [E12]. |
| Entrega | 59 IDs exactos y únicos, valores finitos, esquema y cuatro decimales; tres copias idénticas y otras propuestas intactas. [I3]. |
| Pruebas de aplicación y pipeline | **71 pruebas aprobadas**; 21 advertencias de deprecación de Rasterio, sin fallos. Incluyen fuga por etiquetas externas, separación espacial, faltantes, integridad, autenticación y riesgo económico. [I3]; [E20]. |
| JavaScript | Comprobación sintáctica de `charts.js`, `staff.js`, `producer.js` y `risk.js` sin errores. [E20]. |
| Revisión visual | **No completada**: el navegador local no pudo conectarse y la comprobación de socket fue bloqueada por permisos del entorno. Las pruebas con el cliente Flask pasaron; no se afirma una inspección visual de las pantallas. [E20]. |

El registro `decision.json` conserva `production_modified: false` porque la evaluación y el dictamen no escribían producción. La activación posterior está documentada por separado en `activation.json`; no es una contradicción. [E10]; [E13].

La ausencia de intervalos es deliberada y se prueba. La batería conserva compatibilidad con el formato anterior cuando un modelo sí declara calibración, pero para esta versión exige 138 IDs de ajuste, ningún ID de calibración y límites nulos.
<!-- VERIFICACION_FIN -->

Las órdenes se ejecutan desde `C:\dev\benchmarks\reto-fira\platform`, con el entorno existente y las versiones fijadas en `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe scripts/refine_model.py --prepare
.\.venv\Scripts\python.exe scripts/refine_model.py --evaluate --workers 2
.\.venv\Scripts\python.exe scripts/refine_model.py --decide
.\.venv\Scripts\python.exe scripts/verify_refinement.py
.\.venv\Scripts\python.exe scripts/publish_refinement.py --build
.\.venv\Scripts\python.exe scripts/publish_refinement.py --activate
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe scripts/complete_refinement_report.py
```

`--prepare` guarda las fuentes y el protocolo; una preparación posterior comprueba las huellas sin reemplazar el respaldo. `--evaluate` reutiliza folds completos ya guardados; `--decide` exige todos los resultados esperados y reconcilia la referencia con el OOF anterior. Cambiar archivos congelados bloquea la reanudación: debe abrirse una versión nueva del experimento, no mezclar resultados. Esas tres órdenes evalúan sin activar producción. [I2].

`verify_refinement.py` comprueba particiones y cálculos de forma independiente. `publish_refinement.py --build` reajusta y prepara la versión aceptada; `--activate` comprueba sus hashes y reemplaza los artefactos locales. Detener la aplicación antes de activar y reiniciarla después evita servir archivos de dos versiones durante el reemplazo. El generador del reporte solo recompone tablas y registros descriptivos, sin entrenar ni seleccionar. El entrenador histórico `python -m pipeline.train` **no reproduce esta versión** y puede sobrescribirla con la referencia antigua. [I4]; [I5]; [I6].

## 9. Límites de la conclusión

1. **Sin verdad oculta:** no se puede medir la precisión real de los 59 CSV contra su rendimiento verdadero.
2. **Desarrollo previo:** estas 138 etiquetas ya influyeron en el proyecto. Las nuevas particiones mejoran la comparación, pero no crean una prueba ciega independiente.
3. **Un solo ciclo:** no se valida predicción de campañas futuras, heladas extremas ni sequías no observadas.
4. **Dependencia espacial:** los datos comparten clima y proximidad. Hay pocos bloques, con tamaños desiguales; los resultados espaciales y sus intervalos necesitan ese contexto.
5. **Medición del objetivo:** los rendimientos proceden principalmente de comercializadores y, en menor proporción, productores. No se dispone de una medida parcelaria de su error. [F4], pregunta 5.
6. **Búsqueda limitada:** se evaluaron los candidatos definidos, no todos los algoritmos y variables posibles. “Perfeccionar” significa mejorar con evidencia y trazabilidad, no certificar un óptimo universal.
7. **Posselección:** decidir qué procedimiento desplegar utilizando estas comparaciones introduce incertidumbre adicional. Las métricas externas de cada procedimiento y el carácter exploratorio permanecen visibles después de la decisión.

## 10. Referencias explícitas y evidencias

### Documentación FIRA y bibliografía local

Las páginas siguientes corresponden al índice físico del PDF, contando desde 1; se conservaron los localizadores de la revisión inicial. No se afirma una lectura integral de los libros.

| Ref. | Fuente y pasaje que respalda la decisión |
|---|---|
| [F1] | Descripción general, §§1–4: ciclo, fuentes y variables. |
| [F2] | Diccionario de índices, estadísticos y consideraciones: sensores, cobertura e interpretación. |
| [F3] | Ecuaciones oficiales, pp. 1–2: fórmulas y diferencias por sensor. |
| [F4] | Segunda sesión, preguntas 2, 5–10, 12–14: fechas, etiquetas, muestra, entrega y datos ausentes. |
| [F5] / [F6] / [F7] | LEEME de precipitación, temperatura y relieve: unidades, resolución, CRS y NoData. |
| [B1] | Radočaj et al., `02.pdf`, pp. 1 y 3: integración de datos para estimación de rendimiento. |
| [B2] | ISLP, PDF 39, 211, 248, 252 y 260: error externo, variabilidad, regularización y reajuste. |
| [B3] | Geographic Data Science, PDF 166 y 348: dependencia espacial y errores. |
| [B4] | Molnar, PDF 163, 208 y 216: causalidad, permutación externa y variables correlacionadas. |
| [B5] | Introduction to Data Mining, PDF 70 y 180: faltantes, atípicos y separación de evaluación. |
| [B6] | Shawon et al., `last.pdf`, p. 1: familias y métricas; no garantiza un ganador. |
| [B7] | VanderPlas, `Python_Datascience.pdf`, PDF 400: pipelines y evaluación separada. |
| [B8] | McKinney, PDF 225, §7.1: tratamiento de faltantes. |
| [B9] | ESL, PDF 241, §7.2, y 265, §7.10.2: selección/evaluación y validación del proceso entero. |

### Fuentes de internet

| Ref. | Fuente y alcance |
|---|---|
| [W1] | Bases FIRA, pp. 4–6: evaluación oculta, criterios y entrega. |
| [W3] | FAO AquaCrop: insumos requeridos; justifica no simular procesos con insumos inventados. |
| [W6] | Angelopoulos y Bates, tutorial de conformal prediction: separación de ajuste/calibración y límites. |
| [W7] | Cawley y Talbot (2010), JMLR 11:2079–2107: sobreajuste en selección de modelos. |
| [W8] | Clark et al. (2023), Agricultural Systems 211:103749: adecuar método a datos; revisión heterogénea, no prueba parcelaria FIRA. |
| [W9] | Schrauf et al. (2021), Frontiers, §§2.3–2.5: validación pareada, uso real y relevancia práctica. |
| [W10] | Habibi et al. (2024), Journal of Agriculture and Food Research 16:101096: validación para transferencia espacial en soja. |
| [W11] / [W12] | Definiciones de R² predictivo y NSE; igualdad algebraica bajo esas definiciones. |
| [W13] | Documentación de importancia por permutación: utilidad predictiva en observaciones apartadas. |

Los artículos y libros respaldan principios y motivan candidatos. Las cifras de desempeño y el dictamen de este proyecto se respaldan en sus artefactos ejecutados, no en mejoras publicadas para otros cultivos o conjuntos.

[ANT]: <C:/dev/benchmarks/reto-fira/PROPUESTA_AFINACION_PREDICCION.md>
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
[W1]: https://www.fira.gob.mx/Nd/Reto%20Agrocebada%20Bases.pdf
[W3]: https://www.fao.org/aquacrop/overview/input-requirements/
[W6]: https://arxiv.org/html/2107.07511v6
[W7]: https://jmlr.org/papers/v11/cawley10a.html
[W8]: https://www.sciencedirect.com/science/article/pii/S0308521X23001543
[W9]: https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2021.734512/full
[W10]: https://pure.au.dk/portal/en/publications/critical-evaluation-of-the-effects-of-a-cross-validation-strategy/
[W11]: https://scikit-learn.org/stable/modules/model_evaluation.html#r2-score
[W12]: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/optimization/goodness-of-fit-indices
[W13]: https://scikit-learn.org/stable/modules/permutation_importance.html
[P1]: <C:/dev/benchmarks/proposal-01/reto-fira-v0/src/pipeline.py>
[P1f]: <C:/dev/benchmarks/proposal-01/reto-fira-v0/outputs/features.csv>
[P2b]: <C:/dev/benchmarks/proposal-02/pipeline/04_correlacion_seleccion.py>
[P2c]: <C:/dev/benchmarks/proposal-02/pipeline/05_entrenamiento.py>
[R1]: <C:/dev/benchmarks/reto-fira/platform/pipeline/train.py>
[R2]: <C:/dev/benchmarks/reto-fira/platform/pipeline/features.py>
[I1]: <C:/dev/benchmarks/reto-fira/platform/pipeline/refinement.py>
[I2]: <C:/dev/benchmarks/reto-fira/platform/scripts/refine_model.py>
[I3]: <C:/dev/benchmarks/reto-fira/platform/tests/test_refinement.py>
[I6]: <C:/dev/benchmarks/reto-fira/platform/scripts/complete_refinement_report.py>
[E1]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/protocol.json>
[E2]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/input-hashes.json>
[E3]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/source-check.json>
[E4]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/incumbent-hashes.json>
[E5]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/paired-oof.csv>
[E6]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/folds>
[E7]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/metrics-by-seed.csv>
[E8]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/metrics-aggregate.csv>
[E9]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/metrics-by-state.csv>
[E10]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/decision.json>

[I4]: <C:/dev/benchmarks/reto-fira/platform/scripts/publish_refinement.py>

[I5]: <C:/dev/benchmarks/reto-fira/platform/scripts/verify_refinement.py>

[E11]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/verification.json>

[E12]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/release-manifest.json>

[E13]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/activation.json>

[E14]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/permutation-oof.csv>

[E15]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/error-review-by-plot.csv>

[E16]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/selections.csv>

[E17]: <C:/dev/benchmarks/reto-fira/platform/artifacts/predicciones_59.csv>

[E18]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/prediction-changes.csv>

[E19]: <C:/dev/benchmarks/reto-fira/platform/docs/riesgo-economico.md>

[E20]: <C:/dev/benchmarks/reto-fira/platform/artifacts/model-refinement-v2/completion.json>
