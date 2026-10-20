# Riesgo económico de cebada para personal técnico

> **Actualización del modelo base, 17 de octubre de 2026:** la simulación conserva sus fórmulas y consume la nueva mezcla Ridge/Random Forest y sus errores externos. La validación por parcela utiliza la semilla 20261013 y el estrés espacial la cuadrícula de 20 km, con 36 observaciones únicas de Hidalgo en cada caso. Este predictor, ajustado con 138 etiquetas, no publica intervalos conformales. Consultar el [reporte de implementación](../../REPORTE_IMPLEMENTACION_PREDICCION.md).

## Propósito y decisión que apoya

La herramienta convierte el rendimiento estimado por el modelo en una comparación de márgenes económicos por parcela de Hidalgo. La pregunta que resuelve es: **¿cómo cambia el margen de esta parcela al cambiar el precio de venta, el costo directo o la renta, considerando los errores que el modelo ha cometido fuera de muestra?**

La simulación Monte Carlo es experimental. Su fuente de variación es una distribución empírica de errores predictivos existentes; el precio y la variación de costos son supuestos fijados por el personal técnico. Por tanto, las frecuencias mostradas describen el modelo de escenarios y no son probabilidades comprobadas de pérdidas futuras.

El valor para FIRA es hacer explícitos el punto de equilibrio, los supuestos presupuestales y la sensibilidad del margen antes de una revisión técnica. Facilita identificar qué cotización o dato conviene confirmar y conversar con el productor sobre la viabilidad económica. No autoriza financiamiento ni emite una calificación crediticia.

Esta aplicación es coherente con los Agrocostos, que relacionan tecnología, costos, rendimientos y precios para orientar el análisis de financiamiento. También conecta con las bases del Reto AgroCebada FIRA 2026: en la primera etapa, el desempeño y la justificación técnica pesan 70 % y la aplicación 30 %; en la segunda se valora la relación con la inclusión financiera y la viabilidad de las conclusiones. Añadir la simulación no mejora por sí mismo las métricas predictivas ni garantiza un resultado en el concurso [1, 2].

## Alcance y recursos reales

- Acceso exclusivo para el rol de personal técnico, con comprobación en el servidor.
- Evaluación individual de las 15 parcelas de predicción de Hidalgo presentes en los artefactos actuales. No se agrega una cartera ni se suman riesgos independientes entre parcelas.
- Se conserva el modelo de rendimiento y sus 59 predicciones. La simulación utiliza su estimación final y los artefactos de validación, sin reentrenar ni modificar la entrega.
- Se utiliza el presupuesto regional del PDF local de cebada, Hidalgo, Altiplano, modalidad Tradicional, ciclo PV 2026 y tecnología identificada como **TMF**. Se conserva esa denominación sin atribuirle una expansión que el documento no proporciona.
- El ejercicio combina estimaciones del ciclo abril-octubre de **2025** con costos cotizados en abril de **2026** y un precio base del ciclo PV **2025**. Es un **ejercicio retrospectivo revalorado con un presupuesto de 2026**, no un pronóstico de producción o rentabilidad del ciclo 2026.

Los insumos del proyecto se pueden inspeccionar en:

| Recurso | Uso |
| --- | --- |
| [`data/fira/context/Cebada_TMF_Hidalgo_PV_2026.pdf`](../../data/fira/context/Cebada_TMF_Hidalgo_PV_2026.pdf) | Presupuesto y supuestos regionales. Ver [3]. |
| [`artifacts/dashboard.json`](../artifacts/dashboard.json) | Fuente que consulta la API: rendimiento final con su precisión almacenada, superficie, municipio y estado de las parcelas de predicción. |
| [`artifacts/predicciones_59.csv`](../artifacts/predicciones_59.csv) | Entrega con cuatro decimales, conservada y verificada por las pruebas de integridad. No se reescribe al simular. |
| [`artifacts/parcels.csv`](../artifacts/parcels.csv) | Maestro de referencia para auditar estado, conjunto y superficie; esos datos están incorporados en el dashboard que lee la API. |
| [`artifacts/validation-parcel.csv`](../artifacts/validation-parcel.csv) | Predicciones fuera de muestra por partición aleatoria; 36 filas de Hidalgo. |
| [`artifacts/validation-spatial.csv`](../artifacts/validation-spatial.csv) | Predicciones fuera de muestra por partición espacial; 36 filas de Hidalgo para la opción de estrés. |
| [`artifacts/metrics.json`](../artifacts/metrics.json) | Procedencia del modelo y estado de incertidumbre (`not_estimated` en la versión activa); no se usa como distribución de simulación. |

## Cifras del PDF y tratamiento presupuestal

Las cantidades siguientes son las **publicadas**, en pesos mexicanos por hectárea salvo indicación distinta. Las páginas se refieren al orden físico del PDF: resumen en la página 1, memoria de cálculo en las páginas 2 y 3, y sensibilidad en la página 4 [3].

| Concepto | Valor publicado | Localización y significado |
| --- | ---: | --- |
| Preparación del terreno | $3,622 | Resumen y memoria de cálculo. |
| Siembra | $2,957 | Resumen y memoria de cálculo. |
| Fertilización | $5,706 | Resumen y memoria de cálculo. |
| Labores culturales | $383 | Resumen y memoria de cálculo. |
| Control de plagas, malezas y enfermedades | $2,965 | Resumen y memoria de cálculo. |
| Cosecha, selección y empaque | $3,004 | Resumen y memoria de cálculo. |
| Diversos | $2,867 | Incluye asistencia técnica y seguro agrícola. |
| **Costo directo / financiable total** | **$21,504** | No incluye la renta. Se usa el total publicado. |
| Asistencia técnica | $300 | Incluida en Diversos; no se vuelve a sumar. |
| Seguro agrícola | $2,567 | Incluido en Diversos; no se vuelve a sumar. |
| Rendimiento probable | 3.50 t/ha | Referencia regional, no etiqueta real de una parcela. |
| Precio probable | $7,375/t | Precio base promedio PV 2025, sin deducciones ni bonificaciones. |
| Ingreso probable | $25,813 | Redondeo publicado de 3.5 × 7,375 = $25,812.50. |
| Costo total del análisis financiero mostrado | $24,489 | Corresponde al total de la rama mayor a 160,000 UDIS. |
| Utilidad probable mostrada | $1,324 | Referencia publicada, sin renta. |
| Relación beneficio-costo mostrada | 1.05 | Referencia publicada. |
| Costo unitario mostrado | $6,997/t | Referencia publicada. |
| Punto de equilibrio mostrado | 3.32 t/ha | Referencia publicada. |
| Producción para cubrir avío más intereses | 2.74 t/ha | Referencia del PDF; no equivale a un flujo de caja completo. |
| Producción para cubrir costo directo | 2.92 t/ha | Referencia publicada. |
| Renta regional por hectárea y ciclo | $4,893 | Informada en el PDF, pero excluida de su análisis financiero. |
| Valor de compraventa de la tierra | $300,000/ha | Referencia patrimonial; no se suma como costo de este ciclo. |
| Subsidios | $0 | Supuesto publicado. |
| Rendimiento mínimo / probable / máximo de sensibilidad | 2.00 / 3.50 / 4.00 t/ha | Escenarios del PDF; no son una distribución de probabilidades. |
| Precio mínimo / probable / máximo de sensibilidad | $6,500 / $7,375 / $8,200 por t | Escenarios del PDF; no son una distribución de probabilidades. |

El PDF publica dos esquemas presupuestales. Se permite escoger el que corresponde al ejercicio, manteniendo sus etiquetas originales:

| Concepto | Hasta 160,000 UDIS (≤ 160,000) | Mayor a 160,000 UDIS (> 160,000) |
| --- | ---: | ---: |
| Costo financiable | $21,504 | $21,504 |
| Crédito total publicado | $19,353 | $17,203 |
| Aportación total publicada | $2,150 | $4,301 |
| Intereses totales publicados | $3,357 | $2,984 |
| No financiable | $0 | $0 |
| **Costo total publicado, con intereses y sin renta** | **$24,862** | **$24,489** |

La elección es un supuesto presupuestal del análisis. No convierte el umbral de UDIS a pesos, clasifica automáticamente al productor ni afirma que exista una oferta de crédito vigente con esas condiciones.

El calendario publicado contiene las siguientes ministraciones:

| Ministración | Fecha | Financiable | Crédito ≤ 160,000 UDIS | Aportación ≤ 160,000 UDIS | Intereses ≤ 160,000 UDIS | Total ≤ 160,000 UDIS | Crédito > 160,000 UDIS | Aportación > 160,000 UDIS | Intereses > 160,000 UDIS | Total > 160,000 UDIS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Abril de 2026 | $18,500 | $16,650 | $1,850 | $3,030 | $21,530 | $14,800 | $3,700 | $2,694 | $21,194 |
| 2 | Agosto de 2026 | $3,004 | $2,704 | $300 | $327 | $3,331 | $2,403 | $601 | $291 | $3,295 |

El vencimiento publicado es el 31 de marzo de 2027. La siembra está prevista entre mayo y junio de 2026 y la cosecha entre octubre de 2026 y enero de 2027. Son supuestos de ese presupuesto, no fechas observadas de las parcelas de 2025.

### Redondeo: conservar la fuente y hacer visible la diferencia

La portada financiera y la sensibilidad del PDF utilizan la rama **mayor a 160,000 UDIS**. Para contrastarlas con la interfaz hay que elegir ese perfil; el formulario propone inicialmente la rama hasta 160,000 UDIS.

Los importes impresos no reconstruyen siempre sus totales exactamente. Por ejemplo:

- $16,650 + $2,704 = $19,354, mientras el crédito total de la rama hasta 160,000 UDIS aparece como $19,353.
- $2,694 + $291 = $2,985, mientras los intereses totales de la rama mayor a 160,000 UDIS aparecen como $2,984.
- $21,504 + $3,357 = $24,861, frente al costo total publicado de $24,862; $21,504 + $2,984 = $24,488, frente a $24,489.
- $19,353 + $2,150 = $21,503, frente al costo financiable publicado de $21,504.

Las diferencias son de $1 y son compatibles con redondeos de cifras subyacentes no disponibles. No se corrige silenciosamente el documento ni se deduce una tasa de interés a partir de importes redondeados. La simulación toma el **costo total publicado de la rama elegida** como referencia y aplica a ese total solo el ajuste de costos directos y la renta descritos abajo. Se conserva precisión decimal durante el cálculo y se redondea al mostrar resultados.

Los ejes impresos de la sensibilidad también tienen precisión limitada. Por ejemplo, la celda de 3.83 t/ha y $8,200/t publica $6,945/ha, mientras que 3.83 × 8,200 − 24,489 produce $6,917/ha. El contraste de las 98 celdas arroja diferencias máximas de $28/ha en rendimiento/precio y $2/ha en costo/precio al utilizar literalmente sus etiquetas. Son compatibles con ejes subyacentes de mayor precisión, pero el PDF no entrega esa hoja de cálculo. No se alteran constantes para forzar coincidencias. La [verificación del 19 de octubre de 2026](verificacion-montecarlo.md) documenta la evidencia, las pruebas y la decisión sobre RabbitMQ.

El PDF señala que sus costos proceden de pocas observaciones y no son estadísticamente representativos por estado, cultivo, tecnología o ciclo. Es un presupuesto regional informativo, no el costo auditado de una parcela. También indica compras consolidadas, una cuota de asesoría de $30 por hectárea al mes durante diez meses y la inclusión de una cuota de seguro agrícola. Ninguno de estos datos acredita una póliza contratada o indemnizaciones observadas [3].

## Método Monte Carlo acordado

### 1. Errores fuera de muestra de Hidalgo

Para cada fila de validación de Hidalgo se calcula el error firmado:

**error = rendimiento observado − rendimiento predicho fuera de muestra.**

La base principal son los **36 errores** de `validation-parcel.csv`. La opción de estrés usa por separado los **36 errores** de `validation-spatial.csv`. No se mezclan estados, no se incluyen etiquetas de las 59 parcelas ocultas y no se combinan ambas bases como si fueran 72 observaciones independientes.

El signo se conserva: los errores positivos aumentan el rendimiento simulado y los negativos lo reducen. No se reemplazan por errores absolutos ni se centran artificialmente a cero. Si la base tiene sesgo, la media de la simulación puede diferir de la predicción final y debe poder explicarse.

### 2. Generación de escenarios

Se realizan **20,000 extracciones con reemplazo** de la base seleccionada, con **semilla fija 20261015**. Cada error disponible tiene la misma probabilidad de selección. Para cada extracción:

**rendimiento simulado = máximo(0, rendimiento final de la parcela + error extraído).**

El límite cero impide producciones negativas. Puede modificar la media y la cola inferior; debe mantenerse documentado y comprobarse si llega a activarse. La distribución tiene soporte empírico limitado: más extracciones estabilizan la representación computacional, pero no agregan años, productores ni evidencia sobre eventos extremos no observados.

Los 20,000 ensayos y la semilla son decisiones de ingeniería para reproducibilidad. No son tamaños de muestra observados ni evidencia de precisión estadística. El remuestreo reproduce una hipótesis explícita: que los errores de validación seleccionados resultan informativos al trasladarlos al rendimiento final de esta parcela.

### 3. Comparación económica con los mismos rendimientos simulados

El escenario de referencia utiliza el precio del PDF ($7,375/t), una variación de costos directos de 0 % y renta de $0/ha. El escenario del personal técnico permite fijar:

- Precio de venta por tonelada.
- Variación porcentual del costo directo agregado respecto de $21,504/ha.
- Renta de $0/ha, la referencia regional de $4,893/ha/ciclo o una cotización introducida por el usuario.
- Uno de los dos esquemas presupuestales publicados; la comparación debe identificar cuál usa cada resultado.

Precio, ajuste de costos y renta son entradas deterministas de cada escenario. No se les asigna una distribución normal, triangular u otra distribución sin datos que la justifiquen. Los mínimos y máximos de sensibilidad del PDF no bastan para estimar frecuencias. Los mismos rendimientos remuestreados se usan para ambas alternativas, para que la diferencia dependa de los supuestos económicos y no de muestras aleatorias distintas.

Si **δ** es la variación porcentual de costos directos, **R** la renta por hectárea y **T** el costo total publicado del esquema elegido:

**costo ajustado por hectárea = T + $21,504 × δ / 100 + R.**

Para cada extracción, con precio **P**, rendimiento simulado **Y** y superficie **A**:

- **Ingreso bruto por hectárea = P × Y.**
- **Margen por hectárea = P × Y − costo ajustado por hectárea.**
- **Margen por parcela = margen por hectárea × A.**
- **Rendimiento de equilibrio = costo ajustado por hectárea / P**, con precio positivo.
- **Precio de equilibrio a la predicción puntual = costo ajustado por hectárea / rendimiento final**, solo si ese rendimiento es positivo.

El ajuste porcentual aplica al agregado de costos directos, incluido el seguro de referencia. No afirma que cada insumo cambie igual en el mercado. Los intereses publicados se mantienen fijos en este ejercicio: cambiar el presupuesto directo no recalcula un préstamo ni sus ministraciones. Si cambian las condiciones financieras reales, se necesita un presupuesto actualizado.

El costo de acarreo y el flete del PDF están presupuestados para 3.5 t/ha. En esta primera versión permanecen dentro del presupuesto fijo; no se conoce un calendario real de costos variables por tonelada de cada parcela. Esta simplificación puede afectar los márgenes de rendimientos alejados de la referencia.

### 4. Resultados e interpretación

La salida debe mostrar primero el margen y su sensibilidad: media, mediana, percentiles bajos y altos del margen simulado, frecuencia de simulaciones con margen menor a cero y puntos de equilibrio. Las unidades deben distinguir pesos por hectárea, pesos por parcela y toneladas por hectárea.

La frecuencia de margen negativo significa: **porcentaje de extracciones de la base de errores seleccionada que generan un margen negativo bajo estos supuestos**. No se denomina probabilidad de incumplimiento ni pérdida futura garantizada. Los percentiles son cuantiles del remuestreo experimental y no intervalos de confianza de la rentabilidad real.

La opción espacial sirve para comprobar cuánto cambia la conclusión frente a una base de errores obtenida con una separación geográfica más exigente. No es una campaña climática adversa estimada ni una probabilidad de sequía. Se muestra como alternativa de estrés metodológico, sin atribuirle una garantía de ser siempre más conservadora [6].

## Diferencia frente al intervalo conformal de la versión anterior

El modelo anterior informaba un intervalo split conformal nominal de 90 %, con 28 parcelas de calibración y radio de aproximadamente 0.698210 t/ha. Ese radio procedía de un cuantil de errores absolutos; no era una desviación estándar ni definía una función de distribución acumulada. La versión activa utiliza las 138 etiquetas para ajustar el predictor y no conserva una muestra de calibración separada: no publica ese intervalo ni lo traslada alrededor de las estimaciones nuevas.

La cobertura conformal es marginal y requiere condiciones como la intercambiabilidad entre calibración y nuevas observaciones. No garantiza cobertura de 90 % en cada parcela o municipio, ni convierte los extremos del intervalo en percentiles económicos. La dependencia espacial y el cambio entre campañas requieren evaluación específica [5, 6].

La simulación usa errores **firmados de validación fuera de muestra**, no el radio conformal, para evitar convertir un intervalo en una distribución inventada. Aun así, el remuestreo no adquiere por ello una garantía conformal: trasladar errores entre parcelas y desde modelos de cada partición al modelo final sigue siendo un supuesto experimental.

## Límites financieros, agronómicos y de uso

1. **Margen antes que deuda.** El total presupuestal incluye los intereses publicados. El préstamo financia parte de los costos y no se resta otra vez como gasto. La aportación del productor tampoco se suma como un costo adicional al presupuesto ya contabilizado.
2. **Sin evaluación de cobertura de deuda en este alcance.** La utilidad contable no es caja disponible. Faltan fechas de cobro, efectivo inicial, otros ingresos y gastos, otras obligaciones y condiciones contractuales. La cifra del PDF de 2.74 t/ha para avío más intereses es una referencia bruta y no demuestra suficiencia de caja, cumplimiento ni elegibilidad crediticia.
3. **Seguro como costo presupuestado.** Los $2,567/ha ya están incluidos. No se simulan indemnizaciones ni se afirma que una pérdida esté cubierta: faltan póliza, riesgos cubiertos, suma asegurada, deducible, exclusiones y momento de pago.
4. **Sin aprendizaje causal.** Modificar costos, precio o renta no cambia el rendimiento estimado. El sistema no ha aprendido una respuesta causal a fertilización, prácticas de cultivo o contratación de seguro. No prescribe dosis ni promete rendimiento adicional por gastar más.
5. **Una campaña no describe todos los años.** Los errores son de parcelas de 2025; no son una serie interanual de clima, rendimientos o precios. No permiten calibrar la frecuencia futura de sequías, heladas u otros extremos ni las colas de una pérdida rara.
6. **Sin cartera.** Las parcelas pueden compartir clima, mercado y errores. Sumar simulaciones independientes ocultaría dependencia y concentración. La literatura confirma que modelar dependencias puede cambiar materialmente el riesgo agregado; se necesitarían datos y validación adicionales para ese uso [7].
7. **Sin precio maltero garantizado.** El precio base no incluye deducciones ni bonificaciones. La aceptación, proteína y calidad pueden afectar la venta; aquí no existe una base local para estimar esas probabilidades. El precio fijado por el personal técnico puede representar una hipótesis de descuento, pero no una predicción de rechazo [8].
8. **Sin representatividad económica individual.** Que una parcela sea de Hidalgo no demuestra que utilice el paquete, las compras consolidadas, el arrendamiento o los costos del presupuesto. El resultado debe conservar visibles la fuente y las sustituciones introducidas por el usuario.
9. **Sin dictamen crediticio.** La herramienta no calcula PD, LGD, reservas, tarifa de seguro, monto máximo otorgable ni una garantía FIRA. Su uso es exploratorio y requiere revisión técnica y datos reales antes de una decisión financiera.

## Cómo comprobar el comportamiento

La verificación debe cubrir coherencia económica, trazabilidad y aislamiento del modelo de rendimiento:

| Comprobación | Resultado que se espera |
| --- | --- |
| Acceso por rol | La página y la API rechazan consultas sin sesión de personal técnico, aunque se invoque la URL directamente. |
| Estado y conjunto | Solo se aceptan parcelas de predicción de Hidalgo existentes en los artefactos. No se usa el presupuesto para Puebla o Tlaxcala por defecto. |
| Base residual | Cada modo contiene exactamente 36 errores finitos, calculados como observado menos predicho. Se conserva el signo y no se mezclan ambos archivos. |
| Reproducibilidad | Mismos artefactos, parcela, entradas y modo producen los mismos resultados y la misma semilla registrada. |
| Comparación pareada | Escenarios económicos idénticos producen resultados idénticos. Una variación económica usa exactamente los mismos rendimientos simulados. |
| Identidades monetarias | Subir la renta $100/ha reduce cada margen $100/ha; subir el costo directo 1 % reduce cada margen $215.04/ha; cambiar el precio modifica cada ingreso en cambio de precio × rendimiento simulado. |
| Ejemplo del PDF | Con rendimiento fijo de 3.5 t/ha, precio $7,375/t, rama mayor a 160,000 UDIS, sin variación ni renta, el ingreso es $25,812.50/ha y el margen $1,323.50/ha, mostrados como $25,813 y $1,324 con redondeo a pesos. Este ejemplo no es la media Monte Carlo de una parcela. |
| Renta regional | Al añadir $4,893/ha al ejemplo anterior, el costo es $29,382/ha y el margen −$3,569.50/ha. |
| Rama hasta 160,000 UDIS | El mismo ejemplo con costo total publicado de $24,862 produce margen de $950.50/ha, antes de renta. |
| Sensibilidad publicada | Con 3.5 t/ha y precio $6,500/t, la rama mayor arroja −$1,739/ha; con 3.0 t/ha y $7,375/t arroja −$2,364/ha. |
| Valores físicos | Ningún rendimiento simulado es negativo. Si se activa el límite cero, se identifica su efecto. No se divide entre rendimiento o precio cero. |
| Entradas inválidas | Se rechazan valores no finitos, precio no positivo, renta negativa y ajustes fuera del rango permitido por el servidor. |
| Consistencia de indicadores | La frecuencia de margen negativo queda entre 0 y 100 % y los percentiles aparecen ordenados. La escala de parcela usa la superficie real del artefacto. |
| Redondeo y doble conteo | Se conservan los costos totales publicados; seguro, principal del crédito y aportación no se suman nuevamente. Se explican diferencias de $1. |
| Persistencia de la entrega | La consulta no reentrena, no escribe artefactos y no cambia `predicciones_59.csv` ni `model.joblib`. |
| Etiquetas | Se identifica el ejercicio 2025 revalorado con costos 2026, la base residual, la rama presupuestal y los supuestos. Ninguna frecuencia se presenta como PD o pronóstico validado para 2026. |

Estas comprobaciones verifican la implementación de las fórmulas y las restricciones; no prueban calibración de probabilidades económicas futuras. Esa validación requeriría rendimientos y cuentas económicas posteriores, separados del desarrollo del modelo.

## Acceso, trazabilidad y verificación de la implementación

- Página: `/staff/riesgo`. Contexto: `GET /api/risk/context`. Cálculo: `POST /api/risk/simulate`, con sesión staff, formulario y token CSRF.
- Desde la página se pueden descargar el PDF original y este documento, ambos protegidos por el mismo rol.
- El cálculo registra la semilla, cantidad de sorteos, identificadores de la muestra residual, huella SHA-256 del CSV utilizado y huella de la parcela que recibió. La huella del presupuesto se verifica contra el original revisado: `ac1166eb9af0416871ec661cef61f5ef5c39a6ebd0b35c60788c26cd8de4b5b8`. Si cambia el PDF, se detiene el cálculo hasta revisar las constantes económicas.
- El servidor exige al menos diez residuos válidos, únicos y finitos; los archivos actuales tienen 36 por base. Ese mínimo es una restricción operativa, no un umbral de suficiencia estadística. Los límites de formulario (precio $0.01–$100,000/t, renta $0–$100,000/ha y variación directa de −100% a +300%) son protecciones de entrada, no rangos económicos estimados con datos.
- El resultado identifica cuántos sorteos se limitaron a cero t/ha. Una frecuencia de pérdida de 0% no descarta riesgos fuera del soporte de los residuos observados. El error Monte Carlo de la frecuencia disponible en la API mide solo variación numérica del remuestreo, no incertidumbre del modelo ni de los datos.
- Al editar la configuración, la interfaz marca los resultados anteriores como desactualizados hasta volver a calcular. Los histogramas comparados comparten intervalos y la tabla conserva las unidades por hectárea y por parcela.
- Verificación del 15 de octubre de 2026: 66 pruebas automatizadas aprobadas, incluidas 60 del módulo económico. Cubren cuentas del PDF, pérdidas con resultados conocidos, entradas no finitas, muestras dañadas, permisos, CSRF, reproducibilidad y conservación de los artefactos originales. También se revisaron interacción y presentación en el navegador local.
- El empaquetado Docker incluye el PDF original y la documentación; se construye desde la raíz según el README. No se pudo ejecutar la construcción en este entorno porque el motor de Docker Desktop no estaba iniciado.

## Ampliaciones que requieren evidencia adicional

El siguiente paso defendible es incorporar históricos oficiales de rendimiento, precio medio rural y superficie siniestrada de cebada para Hidalgo, distinguiendo municipio, ciclo PV y temporal. El SIAP publica esas variables y ofrece datos municipales; todavía no se incorporan ni se ajusta una distribución con ellos en este módulo [4].

Antes de utilizar esos históricos se deben revisar cambios de definición, inflación, años disponibles, observaciones faltantes y grano geográfico. Un promedio municipal no equivale al riesgo de una finca. Se debe separar tendencia y variación, evaluar dependencia precio-rendimiento y probar fuera del tiempo de entrenamiento. Un panel de varias campañas también permitiría verificar el transporte de los residuos predictivos actuales.

Para agregar flujo de caja y cobertura bruta del avío se necesitarían fechas de ministración, gasto y cobro; saldo y efectivo inicial; otras deudas y fuentes de ingreso; condiciones del crédito y póliza. Habría que distinguir los gastos operativos ya pagados con el crédito del principal que se devuelve, para evitar doble conteo. Aun con ese flujo, incumplimiento efectivo y calificación crediticia requerirían datos y validación propios.

La literatura de cebada respalda usar simulación para comparar márgenes y alternativas de comercialización, pero sus parámetros extranjeros no se importan a Hidalgo. Un estudio irlandés construye presupuestos estocásticos por finca a partir de rendimientos y precios y compara contratos anticipados; su utilidad aquí es metodológica [9]. Calidad, estrategias productivas y dependencias entre fincas solo se agregarán cuando existan fuentes locales compatibles [7, 8].

## Fuentes y bibliografía primaria

Consulta de enlaces y documentos: 15 de octubre de 2026. Las referencias explican el fundamento y las limitaciones; no implican que sus conjuntos de datos externos ya hayan sido incorporados al simulador.

1. **FIRA (2026).** *Reto AgroCebada FIRA 2026. Bases de participación*, página 4 para ponderaciones y vínculo con inclusión financiera. [PDF oficial](https://www.fira.gob.mx/Nd/Reto%20Agrocebada%20Bases.pdf).
2. **FIRA.** *Agrocostos*. Portal oficial con la finalidad y el alcance de los presupuestos regionales, sus ministraciones y análisis de sensibilidad. [Agrocostos](https://www.fira.gob.mx/Nd/Agrocostos.jsp).
3. **FIRA (PV 2026).** *Sistema de costos agrícolas: Cebada, Hidalgo, Altiplano, modalidad Tradicional, tecnología TMF*. Archivo local original: [`Cebada_TMF_Hidalgo_PV_2026.pdf`](../../data/fira/context/Cebada_TMF_Hidalgo_PV_2026.pdf). Responsable de elaboración: Itzel Evelyn Sánchez Camacho; autorizado por Ariadna Lavariega Martínez. Insumos cotizados en abril de 2026; precio base de PV 2025. Fuente de las cifras de este documento, no una serie estadística.
4. **Dirección General del SIAP (2026).** *Cierre de la Producción Agropecuaria*, comunicado del 13 de agosto de 2026. [Descripción oficial de variables](https://www.gob.mx/agricultura/dgsiap/prensa/cierre-de-la-produccion-agropecuaria?idiom=es), [Anuario Estadístico de la Producción Agrícola](https://nube.agricultura.gob.mx/cierre_agricola/) y [datos abiertos agrícolas](https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php). Fuentes para una ampliación futura, no datos ya cargados.
5. **Romano, Y., Patterson, E. y Candès, E. J. (2019).** *Conformalized Quantile Regression*. NeurIPS 2019. [Artículo completo del congreso](https://papers.nips.cc/paper/8613-conformalized-quantile-regression.pdf). Explica cobertura marginal, intercambiabilidad y diferencia entre intervalos y estimación de cuantiles condicionales.
6. **Roberts, D. R. et al. (2017).** *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*. Ecography, 40(8), 913-929. DOI: [10.1111/ecog.02881](https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.02881). Sustenta evaluar dependencias espaciales y temporales al estimar el error de generalización.
7. **Goodwin, B. K. y Hungerford, A. (2015).** *Copula-Based Models of Systemic Risk in U.S. Agriculture: Implications for Crop Insurance and Reinsurance Contracts*. American Journal of Agricultural Economics, 97(3), 879-896. DOI: 10.1093/ajae/aau086. [Registro y acceso al artículo en USDA](https://research.fs.usda.gov/treesearch/48029). Sustenta la relevancia de dependencias entre fuentes de riesgo; no proporciona correlaciones locales para este proyecto.
8. **Smith, E. G. et al. (2012).** *Net Return Risk for Malting Barley Production in Western Canada as Influenced by Production Strategies*. Agronomy Journal, 104, 1374-1382. DOI: [10.2134/agronj2011.0416](https://acsess.onlinelibrary.wiley.com/doi/10.2134/agronj2011.0416). El resumen del editor describe simulación conjunta de rendimiento, proteína, calibre y precio con experimentos de temporal. Evidencia de que calidad y aceptación comercial importan; no estima sus parámetros para México.
9. **Loughrey, J., Thorne, F. y Hennessy, T. (2016).** *A microsimulation model for risk in Irish tillage farming*. International Journal of Microsimulation, 9(2), 41-76. DOI: 10.34196/ijm.00135. [Artículo abierto](https://www.microsimulation.pub/articles/00135). Antecedente de simulación Monte Carlo del margen de cebada y comercialización; distingue margen bruto de neto y subraya heterogeneidad entre fincas.
