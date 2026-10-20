# Verificación del Sistema Montecarlo de riesgo económico

Fecha: **19 de octubre de 2026**, America/Mexico_City. Aplicación: `reto-fira/platform`, ruta `/staff/riesgo`.

## Dictamen y alcance

El simulador reproduce los costos, intereses, renta opcional y fórmulas económicas del presupuesto FIRA revisado. Funciona con las **15 parcelas disponibles de Hidalgo**, las dos bases de errores y los dos perfiles financieros. Los resultados son escenarios experimentales: este PDF no permite certificar probabilidades futuras de pérdida ni de incumplimiento.

Se revisaron visualmente las **cuatro páginas completas** de [Cebada_TMF_Hidalgo_PV_2026.pdf](../../data/fira/context/Cebada_TMF_Hidalgo_PV_2026.pdf), incluidas memoria, ministraciones, sensibilidad y notas. Su SHA-256 coincide con el registrado por el simulador: `ac1166eb9af0416871ec661cef61f5ef5c39a6ebd0b35c60788c26cd8de4b5b8`.

**El código del Modelo, su entrenamiento, sus insumos, sus artefactos y las predicciones permanecieron intactos.** Tampoco se cambió `risk.py`, su fórmula económica ni su método de remuestreo. La intervención productiva se limita al tiempo de espera de las solicitudes en `static/js/risk.js` y a una aclaración en `templates/risk.html`. Se actualizaron exclusivamente las pruebas de riesgo y su documentación.

## Contraste con el PDF

Importes por hectárea, en MXN, salvo indicación contraria. Páginas físicas: resumen en 1; memoria en 2 y 3; sensibilidad en 4.

| Concepto | PDF e implementación | Comprobación |
| --- | ---: | --- |
| Costos directos financiables | $21,504 | Los siete rubros suman exactamente este total. |
| Seguro agrícola | $2,567 | Ya incluido; no se agrega de nuevo. |
| Asistencia técnica | $300 | Ya incluida; no se agrega de nuevo. |
| Precio de referencia | $7,375/t | Base PV 2025; no cotización garantizada de 2026. |
| Rendimiento regional probable | 3.50 t/ha | Ejemplo presupuestal; no sustituye el rendimiento de una parcela. |
| Intereses, hasta / mayor a 160,000 UDIS | $3,357 / $2,984 | Se mantienen fijos según el perfil elegido. |
| Costo total publicado, hasta / mayor a 160,000 UDIS | $24,862 / $24,489 | Se preservan los totales impresos. |
| Renta regional opcional | $4,893 | Se suma una sola vez cuando corresponde. |
| Ingreso con 3.5 t/ha | $25,812.50 | Compatible con $25,813 publicados. |
| Margen con perfil mayor y sin renta | $1,323.50 | Compatible con $1,324 publicados. |
| Margen con perfil mayor y renta regional | -$3,569.50 | Costo de $29,382; la renta cambia el margen en -$4,893. |
| Margen con perfil hasta 160,000 UDIS y sin renta | $950.50 | Utiliza el otro total publicado. |
| Equilibrio con perfil mayor | 3.320542 t/ha | Compatible con 3.32 t/ha publicados. |

La fórmula verificada es:

`margen/ha = precio × rendimiento simulado − (total publicado del perfil + 21,504 × cambio directo/100 + renta)`.

El crédito y la aportación describen cómo se financia el presupuesto. No se vuelven a restar como gastos. La variación porcentual afecta el costo directo; no recalcula intereses ni determina una respuesta agronómica del rendimiento.

### Por qué se aclaró el perfil financiero

La portada y la sensibilidad del PDF corresponden a **Mayor a 160,000 UDIS**; la interfaz propone inicialmente **Hasta 160,000 UDIS**. Ambos presupuestos existen en la fuente. Se agregó esta aclaración junto al selector para que la comparación no atribuya los $373 de diferencia entre totales a una falla de cálculo. Se conservó la elección explícita del usuario. Fuente: PDF local, páginas 1 y 4.

### Por qué se preservan los redondeos

El PDF contiene diferencias internas de $1: por ejemplo, 21,504 + 2,984 = 24,488, frente al total impreso de 24,489. No se conoce la precisión de la hoja original. Es correcto mantener el total presupuestal publicado y documentarlo, como ya hacía el módulo.

Se contrastaron también las **98 celdas** de sensibilidad. Los ejes impresos están redondeados: 3.83 × 8,200 − 24,489 = 6,917, mientras la celda publica 6,945. La diferencia máxima al utilizar literalmente las etiquetas es **$28/ha** en rendimiento/precio y **$2/ha** en costo/precio. Es compatible con ejes subyacentes de mayor precisión; el PDF no los confirma. Se documentó esta limitación en la metodología y no se alteraron constantes para forzar una coincidencia artificial. Fuente: PDF local, página 4; [comparación completa](../work/montecarlo-audit/pdf-sensitivity-audit.json).

## Corrección de recuperación de solicitudes

**Problema comprobado:** `fetch` no tenía límite de espera. Si la conexión o la lectura de la respuesta quedaba pendiente, el formulario podía permanecer bloqueado en «Calculando…» hasta recargar la página.

**Cambio:** un plazo único de **15 segundos** cubre la conexión y la lectura JSON. Al agotarse, la interfaz cancela mediante `AbortController`, muestra un mensaje que permite reintentar y entra en los manejadores existentes de recuperación. El temporizador se limpia tanto al completar como al fallar. Una respuesta anterior no sustituye un cálculo nuevo después de vencer el plazo. En la carga inicial se ofrece «Volver a cargar»; al simular se recuperan los controles y se conservan los resultados anteriores marcados como desactualizados.

**Por qué:** se evita un bloqueo indefinido sin cambiar ninguna fórmula, muestra de errores, predicción ni condición financiera. Los 15 segundos son un límite operativo de interfaz, no un umbral estadístico. Cancelar la solicitud del navegador no garantiza detener un cálculo que ya empezó en el servidor. No se incorpora un reintento automático de POST.

**Respaldo:** [documentación de AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController), que cubre la cancelación de solicitudes y consumo de cuerpos. Las pruebas ejecutan la función productiva con reloj controlado: no esperan 15 segundos reales ni requieren servidor externo.

## Pruebas y evidencia

La ejecución original de las pruebas de riesgo y cuentas dio **94 aprobadas y 4 fallidas**. Tres fallos dependían de credenciales de demostración ya retiradas y de Supabase; el otro consumía el token CSRF al rechazar una petición anónima y luego esperaba alcanzar la autenticación en el POST.

Se corrigieron las pruebas de riesgo para usar el proveedor simulado ya existente en `test_accounts.py`, cuentas sintéticas y una base temporal de sesiones. El caso anónimo ahora envía primero el POST con CSRF válido. Se comprueba la autorización real de las rutas, sin modificar la autenticación productiva ni utilizar credenciales reales. Esto verifica la integración local; no prueba disponibilidad o configuración de Supabase en un despliegue externo.

| Verificación | Evidencia |
| --- | --- |
| Pruebas Python de riesgo y cuentas | 110 aprobadas: 72 de riesgo y 38 de cuentas. |
| Recuperación HTTP y timeout en JavaScript | 13 aprobadas: éxito, demora válida, conexión detenida, JSON detenido, plazo compartido, sesión, red, HTTP y limpieza. |
| Matriz completa de datos actuales | 60 combinaciones: 15 parcelas × 2 bases × 2 perfiles; 60 repeticiones idénticas y 60 escenarios adversos adicionales. |
| Integridad matemática | Histogramas suman 20,000; cuantiles ordenados; frecuencias entre 0 y 1; importes finitos; escala de superficie correcta; comparación pareada. |
| Fuentes y acceso | Staff/anonimato/productor, CSRF, campos duplicados, PDF con huella distinta, errores de fuentes y ambas bases/perfiles. |
| Soporte de los datos | 36 errores de Hidalgo en cada base; no se mezclan como si fueran 72 observaciones independientes. |
| Límite físico de rendimiento | Cero sorteos recortados en las 60 combinaciones de referencia actuales. La implementación conserva el límite cero. |
| Navegador local | AGC_003, perfil hasta 160,000 UDIS y base por parcela: margen medio -$426.53/ha sin renta y -$5,319.53/ha con renta; cambio exacto -$4,893/ha. La edición marca resultados desactualizados; el recálculo termina y recupera controles. Sin errores o advertencias de consola en la consulta revisada. |
| Conservación del Modelo | Comparación SHA-256 de código, artefactos, insumos y entregas; sin cambios fuera de la lista explícita de interfaz y pruebas. |

La auditoría de ejecución está en [runtime-audit.json](../work/montecarlo-audit/runtime-audit.json). El manifiesto anterior se conserva en [integrity-before.json](../work/montecarlo-audit/integrity-before.json); la [comparación final](../work/montecarlo-audit/integrity-after.json) verifica 316 archivos, con 313 idénticos y únicamente tres cambios permitidos en interfaz y pruebas. La revisión de las cuatro páginas está en [revision-presupuesto-pdf.md](../work/montecarlo-audit/revision-presupuesto-pdf.md).

Comandos desde `reto-fira/platform`:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_risk.py tests/test_accounts.py -q -p no:cacheprovider
node --test tests/test_risk_ui.cjs
.\.venv\Scripts\python.exe -B work/montecarlo-audit/verify_runtime.py
```

La auditoría adicional escribe solamente su evidencia en `work/montecarlo-audit`. Nunca importa entrenamiento ni ejecuta predicciones nuevas. La prueba de permisos usa autenticación simulada.

## Decisión sobre RabbitMQ

**No integrar RabbitMQ para la carga actual.** Esta es una decisión de ingeniería basada en mediciones, no un requisito del PDF.

En una ejecución local se midieron 60 cálculos: media **5.35 ms**, p95 **7.43 ms**, máximo **34.84 ms**. En 30 solicitudes completas con el cliente de prueba Flask: media **18.54 ms**, p95 **30.39 ms**, máximo **39.90 ms**. Son mediciones del entorno revisado, con lectura de archivos, serialización, CSRF y autenticación simulada; excluyen la red y la latencia real de Supabase. No son una prueba de carga concurrente ni una promesa de rendimiento en producción. Las repeticiones pueden variar.

RabbitMQ distribuye trabajos entre procesos y permite gestionar confirmaciones y durabilidad; no mejora las ecuaciones, la fidelidad al PDF ni la validez estadística. Introducirlo ahora añadiría un broker, trabajadores y seguimiento de resultados a una operación corta que el usuario espera recibir inmediatamente. La [documentación oficial de RabbitMQ](https://www.rabbitmq.com/tutorials/tutorial-two-python) describe las colas para trabajos que consumen tiempo; [Flask](https://flask.palletsprojects.com/en/stable/patterns/celery/) recomienda tareas en segundo plano cuando el trabajo prolongado impide responder a la petición.

Reevaluarlo si aparecen lotes persistentes, trabajos que deban sobrevivir reinicios o latencias/concurrencia medidas que excedan el presupuesto de respuesta. Antes habría que medir autenticación, E/S y saturación por separado. Si se introduce, requerirá resultados asociados al usuario, idempotencia, estados, límites de cola, reintentos y confirmaciones; no basta instalar el paquete.

## Límites y mejoras que no se aplicaron

1. **Calibración financiera.** El PDF es un presupuesto regional con pocas observaciones y declara que no es estadísticamente representativo. Los 20,000 sorteos remuestrean 36 errores de una campaña; no agregan historia ni garantizan riesgo de sequía, impago o siniestros. Se conservan esas advertencias. Fuente: PDF local, notas de las páginas 2 y 3; [FIRA Agrocostos](https://www.fira.gob.mx/Nd/Agrocostos.jsp).
2. **Precios y costos fijos por escenario.** Los extremos de sensibilidad del PDF no definen una distribución. No se agregaron distribuciones normales o triangulares ni correlaciones sin datos. Seguro y acarreo/flete se mantienen dentro del presupuesto fijo; no se simulan indemnizaciones. Fuente: PDF y [metodología del módulo](riesgo-economico.md).
3. **Ruido numérico del remuestreo.** Frente a evaluar exactamente los 36 errores con igual peso, la mayor diferencia observada de frecuencia fue **0.5462 puntos porcentuales** entre las 60 combinaciones. Es variación computacional, no evidencia de incertidumbre futura. Evaluar exactamente el soporte empírico sería una alternativa futura si se quiere eliminar ese ruido; no se cambió el motor. [NumPy 2.4 documenta](https://numpy.org/doc/2.4/reference/random/generated/numpy.random.Generator.choice.html) el muestreo uniforme y con reemplazo utilizado.
4. **Defensa frente a artefactos alterados.** En pruebas únicamente en memoria, un identificador nulo o un booleano usado como superficie/rendimiento puede atravesar conversiones numéricas; metadatos `lower=NaN` causan una excepción no controlada y magnitudes finitas extremas pueden desbordar importes. **No están presentes en las entradas actuales**, que producen JSON finito en toda la matriz. Conviene reforzar validación de tipo, identificadores y finitud de resultados si se permite sustituir fuentes. No se editó el consumidor de salidas ni ningún artefacto del Modelo, respetando la restricción del usuario. Estas observaciones impiden afirmar tolerancia perfecta a datos arbitrariamente dañados; no invalidan las cuentas verificadas del PDF.

Las fuentes web se consultaron el 19 de octubre de 2026. Sus recomendaciones de arquitectura y APIs no cambian la fuente económica: las cifras provienen exclusivamente del PDF local identificado por su huella.
