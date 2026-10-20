# AgroCebada · Reto FIRA

Aplicación local en Python, Flask, HTML, CSS y JavaScript para consultar las **59 predicciones de grano de cebada** del ciclo abril–octubre de 2025. Los datos reales y el modelo entrenado están en `artifacts/`. La autenticación y las cuentas de staff/productores usan Supabase.

## Iniciar en Windows

Desde `C:\dev\benchmarks\reto-fira\platform`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abrir http://127.0.0.1:5000. Si el entorno ya está instalado, ejecutar solo la última instrucción. `app.py` usa Waitress y no activa el depurador.

Antes del primer acceso, configurar Supabase y crear las cuentas con [la guía de usuarios](docs/usuarios-supabase.md). Los accesos de demostración embebidos ya no están habilitados. `manage_accounts.py bootstrap` crea el staff y el productor inicial con contraseñas propias; la opción `--generate-credentials` conserva los correos originales y guarda contraseñas aleatorias en el archivo privado `.instance/initial-accounts.txt`.

El staff administra productores desde `/staff/usuarios`: crear, editar, suspender, cambiar credenciales, eliminar y asignar parcelas específicas, municipios completos o todas las parcelas. El productor solo recibe por API los datos y geometrías autorizados. El personal técnico conserva el análisis de validación y la exportación CSV. Los roles y permisos se verifican en el servidor en cada solicitud.

## Reproducir el modelo

Los insumos deben permanecer en `../data/fira` y la bibliografía en `../data/libros`.

La versión activa, evaluada el 17 de octubre de 2026, combina **50% Ridge y 50% Random Forest**, ajustados con las **138 parcelas etiquetadas**. No publica intervalos de predicción. El MAE medio de cinco repeticiones anidadas pasó de 0.4018 a 0.3845 t/ha y el RMSE de 0.5578 a 0.5315 t/ha. Son métricas del procedimiento de selección; no miden el error desconocido de las 59 parcelas. El [reporte de implementación](../REPORTE_IMPLEMENTACION_PREDICCION.md) documenta las decisiones, las alternativas que no pasaron, las pruebas espaciales y las limitaciones.

```powershell
.\.venv\Scripts\python.exe scripts/refine_model.py --prepare
.\.venv\Scripts\python.exe scripts/refine_model.py --evaluate --workers 2
.\.venv\Scripts\python.exe scripts/refine_model.py --decide
.\.venv\Scripts\python.exe scripts/verify_refinement.py
.\.venv\Scripts\python.exe scripts/publish_refinement.py --build
.\.venv\Scripts\python.exe scripts/publish_refinement.py --activate
.\.venv\Scripts\python.exe -m pytest tests -q
```

El experimento guarda protocolo, huellas, respaldo y folds en `artifacts/model-refinement-v2/`. Reutiliza folds ya completados y rechaza entradas congeladas que hayan cambiado. `--build` prepara y comprueba una versión; `--activate` reemplaza los artefactos locales y sincroniza los CSV de entrega. Para evitar lecturas durante su reemplazo, detener el servidor antes de activar y reiniciarlo después. Ninguna de estas órdenes envía resultados a FIRA.

**`python -m pipeline.train` es el entrenador histórico de 110 parcelas de ajuste y 28 de calibración: no reproduce la versión activa y sobrescribe sus artefactos.** Se conserva para reproducir la referencia. Si se modifican los insumos, hay que regenerar características y abrir una versión nueva del experimento, sin mezclar los folds congelados. La extracción histórica `--force-features` recalcula las 146 capas; su caché por sí sola no comprueba cambios de origen.

Las 59 parcelas ocultas nunca aportan etiquetas. Se estima un ciclo ya concluido con información hasta octubre de 2025. La pantalla usa la repetición primaria 20261013 y el estrés espacial de 20 km; el reporte contiene las cinco repeticiones y ambas escalas de 10/20 km.

## Comparar las tres propuestas

La revisión histórica del 14 de octubre de 2026 conservó el modelo de entonces porque su alternativa compacta no mostró mejora consistente. Se mantiene como antecedente en [technical-documentation.md](technical-documentation.md). La propuesta del 17 de octubre, [PROPUESTA_AFINACION_PREDICCION.md](../PROPUESTA_AFINACION_PREDICCION.md), se implementó mediante el protocolo ampliado documentado en el [reporte actual](../REPORTE_IMPLEMENTACION_PREDICCION.md). `../comparisons/proposal.csv` y `../comparisons/predicciones_59.csv` son copias exactas de la entrega activa; los otros dos CSV permanecen intactos.

Desde `platform`, estas órdenes generan evidencia de auditoría sin reemplazar el modelo ni las predicciones de producción:

```powershell
.\.venv\Scripts\python.exe scripts/compare_predictions.py
.\.venv\Scripts\python.exe scripts/verify_citations.py
.\.venv\Scripts\python.exe scripts/diagnose_spatial_support.py
.\.venv\Scripts\python.exe scripts/diagnose_feature_recipes.py
.\.venv\Scripts\python.exe scripts/evaluate_refinements.py
```

Estas órdenes pertenecen a la auditoría histórica y sus resultados quedan en `artifacts/comparison-*`, `artifacts/citation-evidence.json` y `artifacts/refinement-audit/`; sus experimentos no sustituyen el protocolo actual. En la revisión nueva sí se inspeccionó el código de las otras propuestas. Se reutilizaron ideas y se evaluaron con extracción, particiones y selección comunes; no se atribuyen a esas implementaciones originales las métricas de las recetas nuevas. Sin rendimientos reales de las 59 ocultas, el desacuerdo entre entregas no determina cuál es más precisa.

## Archivos principales

- `artifacts/predicciones_59.csv`: entrega de dos columnas, ID_parcela y Rendimiento_predicho_t_ha, exactamente 59 filas, cuatro decimales.
- `artifacts/model.joblib`: mezcla entrenada, columnas, procedimiento y límites nulos; no tiene intervalo calibrado. Cargar únicamente el archivo producido por este proyecto.
- `artifacts/metrics.json`: selección, métricas, particiones, referencia e incertidumbre.
- `artifacts/validation-parcel.csv` y `validation-spatial.csv`: predicciones fuera de muestra auditables.
- `artifacts/environment.csv`: 146 variables extraídas por parcela.
- `artifacts/raster-coverage.csv` y `raster-audit.json`: cobertura válida de cada parcela y capa.
- `artifacts/features-cloud-*.csv`: variables por parcela para cada filtro de nubosidad.
- `artifacts/source-manifest.json`: rutas, tamaños y SHA-256 de los insumos.
- `../REPORTE_IMPLEMENTACION_PREDICCION.md`: metodología actual, comparación, selección, resultados, decisiones y citas explícitas.
- `artifacts/model-refinement-v2/`: protocolo congelado, OOF completos, dictamen, verificación y respaldo de la entrega anterior.
- `technical-documentation.md`: auditoría histórica del 14 de octubre; no describe el modelo activo.

La web consulta resultados precomputados del modelo congelado. No fabrica estimaciones en el navegador ni reentrena al abrir una página. Las cifras técnicas se sirven mediante API autenticada; las gráficas y los mapas SVG se generan localmente, sin CDN.

## Interfaz NAS

La interfaz usa la identidad NAS (New Agro Speed), temas claro/oscuro/Sistema y recursos locales de OSBI y GSAP. La instalación habitual de requisitos incluye el wheel de OSBI preparado desde el proyecto local. El diseño, alcance y mantenimiento de los recursos visuales están en [docs/ui-nas.md](docs/ui-nas.md). La vista pública `/timeline` contiene por ahora el texto solicitado de bienvenida.

## Riesgo económico para staff

La ruta `/staff/riesgo` compara el margen de una parcela de Hidalgo bajo el presupuesto de referencia de FIRA y un escenario de precio, costos directos y renta definido por el personal técnico. Reutiliza las predicciones congeladas y remuestrea los errores firmados de Hidalgo de la validación existente; ofrece la base por parcela y una alternativa por bloques espaciales como estrés. No modifica el modelo ni las 59 predicciones.

El cálculo se ejecuta en el servidor con 20,000 extracciones y semilla fija. Las frecuencias son escenarios experimentales, no probabilidades calibradas de pérdida futura ni de incumplimiento. Los rendimientos corresponden a 2025 y el presupuesto a PV 2026; el precio del presupuesto tiene base PV 2025. La aplicación exige confirmar que el perfil tecnológico sea aplicable y permite consultar el PDF original y descargar la documentación desde esa página.

Las fuentes científicas e institucionales, cifras del PDF, fórmulas, beneficios, límites y consideraciones están en [docs/riesgo-economico.md](docs/riesgo-economico.md). Las pruebas de finanzas, integridad de datos, validación de entradas y acceso staff están en `tests/test_risk.py` y se ejecutan con la orden habitual de pytest.

## Configuración

Variables de entorno o archivo local `.env`: `PORT`, `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `COOKIE_SECURE`. Usar `.env.example` como referencia. La clave secreta de Supabase permanece únicamente en el servidor. `COOKIE_SECURE=1` activa cookies exclusivamente HTTPS y HSTS; en localhost HTTP conservar `0`. Una clave de sesión local se genera en `.instance/session-key` si no se proporciona `SECRET_KEY`.

Las sesiones y los límites de intentos persisten en `.instance/auth-sessions.sqlite3`, compartido entre procesos del mismo host. Al desplegar, usar HTTPS, secretos persistentes y almacenamiento privado; para múltiples hosts sustituir SQLite por un almacén común. La recuperación de acceso se realiza mediante el staff; no existe registro público. La [guía de usuarios](docs/usuarios-supabase.md) detalla las políticas RLS, revocación, pruebas y límites.

## Docker

```powershell
docker build -f platform/Dockerfile -t agrocebada .
docker run --rm -p 127.0.0.1:5000:5000 --env-file platform/.env agrocebada
```

Ejecutar estas dos órdenes desde la raíz `C:\dev\benchmarks\reto-fira`. El contexto de construcción incluye únicamente los archivos permitidos por `.dockerignore`, incluido el PDF original necesario para el simulador.

El archivo `.env` debe contener las credenciales elegidas y SECRET_KEY y mantenerse fuera del control de versiones. El contenedor sirve los resultados existentes; el entrenamiento se ejecuta en el proyecto con los insumos. El Dockerfile se entrega como opción de portabilidad; revisar en la documentación si se pudo ejecutar en este entorno.
