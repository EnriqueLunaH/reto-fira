"""Render the implementation report from frozen experiment and release evidence.

Does not train, select or modify predictions. Tables retain diagnostic failures.
"""
from pathlib import Path
import json
import re

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
AUDIT = BASE / 'artifacts/model-refinement-v2'
REPORT = BASE.parent / 'REPORTE_IMPLEMENTACION_PREDICCION.md'


def table(frame, decimals=4):
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return f'{v:.{decimals}f}'
        return str(v).replace('|', '/')
    return '\n'.join(['| ' + ' | '.join(map(str, frame.columns)) + ' |',
                      '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |'] +
                     ['| ' + ' | '.join(fmt(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None)])


def main():
    metrics = pd.read_csv(AUDIT / 'metrics-aggregate.csv')
    seeds = pd.read_csv(AUDIT / 'metrics-by-seed.csv')
    oof = pd.read_csv(AUDIT / 'paired-oof.csv')
    decision = json.loads((AUDIT / 'decision.json').read_text())
    assert decision['selected_procedure'] == 'point_extended'
    old, new = [metrics.loc[(metrics.scheme == 'parcel') & (metrics.procedure == p)].iloc[0]
                for p in ('incumbent', 'point_extended')]
    gain_mae, gain_rmse = (old.mae-new.mae)/old.mae*100, (old.rmse-new.rmse)/old.rmse*100
    result = f'''**Resultado: se activó `point_extended`, un procedimiento que selecciona dentro del entrenamiento entre regresiones regularizadas, árboles y mezclas acotadas.** Al reajustarlo con las 138 etiquetas eligió **50% Ridge + 50% Random Forest**. Se generaron y verificaron las 59 predicciones, y se sincronizó `comparisons/proposal.csv`. Activación: 17 de octubre de 2026, 23:00:30 de Ciudad de México / 18 de octubre, 05:00:30 UTC. [E10]; [E12]; [E13].

En cinco repeticiones de validación anidada por parcela, el MAE del procedimiento pasó de **{old.mae:.4f} a {new.mae:.4f} t/ha** (−{gain_mae:.2f}%) y el RMSE de **{old.rmse:.4f} a {new.rmse:.4f} t/ha** (−{gain_rmse:.2f}%). La alternativa cumplió las cinco condiciones de promoción fijadas antes de observar sus resultados. También mejoró los agregados espaciales frente a la referencia, aunque falló en una repetición y en varios grupos espaciales individuales. [E7]–[E10].

**Alcance de la mejora:** evidencia de validación sobre datos reutilizados, no medición del error en las 59 parcelas ocultas. La validación evalúa el procedimiento de selección completo; sus modelos varían entre folds. No demuestra que la mezcla final fija hubiera obtenido exactamente esas métricas si se la hubiese preseleccionado. Se informa incluso el diagnóstico Ridge, cuyo MAE aleatorio resultó menor, sin cambiar retrospectivamente las reglas para promoverlo.'''
    order = ['incumbent', 'point_original', 'point_extended', 'point_extended_single', 'ridge', 'random_forest',
             'gradient_boosting', 'environment', 'vigor', 'water_temporal', 'state_median', 'median']
    labels = {'incumbent':'Referencia con reserva de calibración', 'point_original':'Puntual, candidatos originales',
              'point_extended':'Puntual ampliado — promovido', 'point_extended_single':'Ampliado sin mezclas — diagnóstico',
              'ridge':'Ridge — diagnóstico', 'random_forest':'Random Forest — diagnóstico',
              'gradient_boosting':'Boosting — diagnóstico', 'environment':'Ambiente — diagnóstico',
              'vigor':'Vigor — diagnóstico', 'water_temporal':'Humedad/trayectoria — diagnóstico',
              'state_median':'Mediana por estado', 'median':'Mediana global'}
    comparison = metrics[metrics.scheme.eq('parcel')].set_index('procedure').loc[order].reset_index()
    comparison['procedure'] = comparison.procedure.map(labels)
    comparison = comparison[['procedure','mae','rmse','r2','bias']]
    comparison.columns = ['Procedimiento','MAE (t/ha)','RMSE (t/ha)','R² medio','Sesgo (t/ha)']
    perseed = seeds[(seeds.scheme == 'parcel') & seeds.procedure.isin(['incumbent','point_extended'])]
    perseed = perseed.pivot(index='seed', columns='procedure', values=['mae','rmse'])
    st = pd.DataFrame({'Semilla':perseed.index, 'MAE anterior':perseed.mae.incumbent,
                       'MAE nuevo':perseed.mae.point_extended, 'Δ MAE':perseed.mae.point_extended-perseed.mae.incumbent,
                       'RMSE anterior':perseed.rmse.incumbent, 'RMSE nuevo':perseed.rmse.point_extended})
    spatial = metrics[metrics.scheme.ne('parcel') & metrics.procedure.isin(['incumbent','point_original','point_extended'])]
    spatial = spatial[['scheme','procedure','mae','rmse','r2','bias']].copy()
    spatial.columns = ['Esquema','Procedimiento','MAE','RMSE','R²','Sesgo']
    state = pd.read_csv(AUDIT / 'metrics-by-state.csv')
    state = state[state.scheme.eq('parcel') & state.procedure.isin(['incumbent','point_extended'])]
    state = state.groupby(['state','procedure']).agg(n=('n','first'),mae=('mae','mean'),bias=('bias','mean')).reset_index()
    state.columns = ['Estado','Procedimiento','Parcelas únicas','MAE medio','Sesgo medio']
    fold_records = []
    for (scheme, fold), g in oof[oof.scheme.ne('parcel')].groupby(['scheme','fold']):
        before, after = (g.incumbent-g.actual).abs().mean(), (g.point_extended-g.actual).abs().mean()
        fold_records.append([scheme,fold,len(g),before,after,after-before])
    foldtable = pd.DataFrame(fold_records, columns=['Esquema','Fold','n','MAE anterior','MAE nuevo','Δ MAE'])
    select = pd.read_csv(AUDIT / 'selections.csv')
    select = select[select.scheme.eq('parcel') & select.procedure.eq('point_extended')].candidate.value_counts().rename_axis('Selección interna').reset_index(name='Folds / 25')
    perm = pd.read_csv(AUDIT / 'permutation-oof.csv')
    rows = [[name,float(np.average(g.delta_mae,weights=g.n))] for name,g in perm.groupby('name')]
    perm_table = pd.DataFrame(rows,columns=['Grupo permutado','Aumento medio de MAE (t/ha)']).sort_values('Aumento medio de MAE (t/ha)',ascending=False)
    err = oof[oof.scheme.eq('parcel')].copy()
    err['error_anterior'] = (err.incumbent-err.actual).abs()
    err['error_nuevo'] = (err.point_extended-err.actual).abs()
    errors = err.groupby(['ID_parcela','state']).agg(observado=('actual','first'),mae_anterior=('error_anterior','mean'),mae_nuevo=('error_nuevo','mean')).reset_index()
    errors['delta_mae'] = errors.mae_nuevo-errors.mae_anterior
    errors.sort_values('mae_nuevo',ascending=False).to_csv(AUDIT/'error-review-by-plot.csv',index=False)
    worst = errors.nlargest(8,'mae_nuevo').copy()
    worst.columns = ['ID','Estado','Observado','MAE anterior','MAE nuevo','Δ MAE']
    metrics_section = f'''### 5.1 Comparación anidada por parcela

Cada cifra resume cinco repeticiones sobre las mismas 138 parcelas, no cinco conjuntos independientes. R² se promedia entre repeticiones; MAE y sesgo tienen unidades t/ha. [E7]; [E8].

{table(comparison)}

El selector ampliado reduce el MAE frente a la referencia en **{old.mae-new.mae:.6f} t/ha**, aproximadamente **{(old.mae-new.mae)*1000:.1f} kg/ha**. Frente al selector puntual original la diferencia es solo **0.001494 t/ha**: no se atribuye toda la mejora a los nuevos índices. Buena parte de la señal favorable aparece al eliminar la reserva para intervalos. La ampliación aporta la estabilidad exigida por la regla de promoción, pero esta ronda no identifica causalmente la aportación aislada de cada cambio.

**Resultado incómodo que se conserva:** Ridge obtiene MAE 0.3756 y RMSE 0.5187 en el diagnóstico aleatorio, inferiores a los del procedimiento promovido. No se lo declara perdedor. No era elegible como procedimiento de reemplazo en el protocolo y seleccionarlo ahora explotaría el mismo resultado externo usado para evaluarlo. Además, su MAE espacial es 0.5514 a 10 km y 0.6110 a 20 km, mayor que el del selector ampliado en ambos casos. Queda como hipótesis prioritaria para otra evaluación con evidencia independiente, no como permiso para seguir buscando hasta obtener la cifra mínima. [E1]; [E8]; [W7].

### 5.2 Consistencia entre particiones

{table(st)}

La semilla 20261017 empeora: **no hubo una mejora universal**. `point_original` mejora solo en tres de cinco semillas, por lo que no se promueve aunque su promedio sea favorable. `point_extended` mejora en cuatro y satisface las demás condiciones. Los intervalos descriptivos del cambio de MAE (nuevo − anterior) son **[−0.032044, −0.002555] t/ha** por parcelas y **[−0.029894, −0.006818] t/ha** por bloques de 20 km. Para `point_original`, el intervalo por bloques incluye cero: **[−0.025101, +0.007155]**. No son pruebas independientes de significación ni intervalos para las 59 predicciones. [E10].

### 5.3 Transferencia espacial y heterogeneidad

{table(spatial)}

El modelo promovido mejora frente a la referencia en las dos escalas. Sin embargo, `point_original` presenta mejores agregados espaciales que el ampliado. Por tanto, la decisión final responde a la regla conjunta predefinida y al objetivo de parcelas del mismo conjunto; **no demuestra superioridad del nuevo modelo para toda región desconocida**. A 20 km el sesgo nuevo es +0.2941 t/ha y el R² apenas 0.0901: sigue existiendo una debilidad importante de transferencia.

Los resultados por fold revelan cuánto depende el promedio de grupos grandes y difíciles:

{table(foldtable)}

El fold con más parcelas de evaluación a 20 km mejora mucho, mientras cuatro de los cinco folds empeoran su MAE. Los folds contienen grupos completos, pero tienen tamaños desiguales. La métrica agregada pondera parcelas, no folds por igual. No se reinterpretan estos resultados como una garantía de extrapolación. [E5]; [E6]; [W10].

### 5.4 Errores por estado y parcela

{table(state)}

Se reduce el MAE medio en los tres estados; eso no implica mejorar cada parcela ni elimina los errores grandes. Estas son las ocho parcelas con mayor error absoluto medio nuevo entre las cinco repeticiones:

{table(worst)}

Se conserva el detalle completo en [E15]. No se retiran estas observaciones ni se corrigen sus etiquetas para mejorar las métricas; requerirían evidencia independiente de un error de medición. [B5], PDF 70; [E5].

### 5.5 Estabilidad de selección e interpretación

{table(select)}

La mezcla se elige en 16 de 25 folds aleatorios. Los componentes concretos también pueden variar: no se debe confundir estabilidad de familia con estabilidad exacta de variables o pesos. En los otros folds compiten configuraciones individuales, incluido boosting. La selección final sobre 138 etiquetas se realiza de nuevo con el mismo procedimiento interno. [E16]; [E12].

La importancia se recalculó con modelos de cada fold externo de la semilla primaria 20261013 y diez permutaciones por grupo. Una fila nunca se explica con un modelo ajustado usando su etiqueta. Las variables del mismo grupo se permutan juntas y de forma consistente entre filtros de nube. Los aumentos de MAE se ponderan por número de parcelas:

{table(perm_table,6)}

La lluvia y temperatura dominan este diagnóstico. Los valores negativos pequeños de otros grupos no demuestran que carezcan de valor en toda configuración: hay redundancia, ruido y variación de selección. No se volvieron a eliminar grupos a partir de este diagnóstico externo. El resultado respalda evitar el relato de que agregar satélites siempre mejora; las recetas de vigor y humedad, evaluadas por separado, no superan a la referencia en MAE aleatorio. [E14]; [W13].'''
    current = pd.read_csv(BASE/'artifacts/predicciones_59.csv')
    prior = pd.read_csv(AUDIT/'incumbent/predicciones_59.csv')
    changes = prior.merge(current,on='ID_parcela',suffixes=('_anterior','_nuevo'),validate='one_to_one')
    before_col, after_col = changes.columns[1:3]
    changes['cambio_t_ha'] = changes[after_col]-changes[before_col]
    changes['cambio_absoluto_t_ha'] = changes.cambio_t_ha.abs()
    changes.sort_values('cambio_absoluto_t_ha',ascending=False).to_csv(AUDIT/'prediction-changes.csv',index=False,float_format='%.4f')
    largest = changes.nlargest(8,'cambio_absoluto_t_ha').drop(columns='cambio_absoluto_t_ha')
    largest.columns = ['ID','Predicción anterior','Predicción nueva','Cambio (t/ha)']
    values = current.iloc[:,1]
    delivery = f'''### 7.1 Configuración final

El selector interno sobre las 138 etiquetas eligió `blend_ridge_0.5`:

| Miembro | Peso | Variables y parámetros |
|---|---:|---|
| Ridge | 0.50 | Nube 60%; receta original de 181 variables, imputación y selección interna de 30, alpha 10. |
| Random Forest | 0.50 | Nube 60%; receta humedad/trayectoria de 42 variables antes de indicadores de ausencia, 180 árboles, hoja mínima 4, fracción de características 0.8. |

Ambos se reajustan con **138 parcelas** después de elegir la configuración. El CSV usa la mezcla de las predicciones, limitadas inferiormente a cero por la misma política usada al evaluar. No se aplican ajustes manuales a las 59 salidas. [I1]; [I4]; [E12].

La puntuación interna final es MAE **0.362012** y RMSE **0.513399**. Son valores utilizados para seleccionar, y **no sustituyen** las métricas externas de la sección 5. La diferencia entre ambas estimaciones es esperable por reutilización de la validación interna y tamaños de entrenamiento distintos. [E12]; [W7].

### 7.2 Entrega y cambios

Se verificaron exactamente 59 IDs únicos correspondientes a PREDICCION, sin valores ausentes o no finitos, con las dos columnas requeridas y cuatro decimales. Media **{values.mean():.4f} t/ha**, mínimo **{values.min():.4f}**, máximo **{values.max():.4f}**. Respecto del CSV anterior, el cambio medio es **{changes.cambio_t_ha.mean():+.4f} t/ha** y el cambio absoluto medio **{changes.cambio_absoluto_t_ha.mean():.4f} t/ha**. Estas diferencias describen salidas; no miden un error verdadero. [E17]; [E18].

{table(largest)}

Las tres copias de entrega son idénticas: `platform/artifacts/predicciones_59.csv`, `comparisons/predicciones_59.csv` y `comparisons/proposal.csv`. Los CSV de `proposal-01` y `proposal-02` permanecen intactos. Hash SHA-256 nuevo:

`3391c573da2588cbc6eb6c939e66513c8794df8a0b0a45c275bda3705357687b`

El anterior está respaldado con hash `53b1b2fe8f46c66814a12d036826bca80e5a5c4cbdd529a43358cef83ce665ff`. [E4]; [E12]; [E13]. La activación es local: **no se envió la entrega a FIRA**.

### 7.3 Coherencia de la aplicación

Se actualizaron conjuntamente modelo, CSV, dashboard, métricas y archivos OOF. La aplicación muestra **intervalo no disponible** para este predictor puntual; conserva límites nulos en lugar de reutilizar los conformales anteriores o convertirlos en cero. La metodología identifica ajuste con 138 etiquetas y cero de calibración.

Las gráficas de validación y el simulador económico usan una sola predicción externa por parcela: semilla primaria **20261013** para validación por parcela y cuadrícula de **20 km** para estrés espacial. Por ello, la pantalla puede mostrar MAE 0.3902 por parcela y 0.5977 espacial; el 0.3845 del reporte es el promedio de cinco repeticiones. No se multiplican las 36 observaciones de Hidalgo por cinco para aparentar una muestra mayor. Se conservan las fórmulas económicas y sus límites; ahora consumen las predicciones y errores de la versión nueva. [I4]; [E5]; [E19].

La importancia global usa OOF, mientras la sensibilidad individual sustituye grupos por las medianas del entrenamiento del modelo final. Esta última es una perturbación descriptiva, no un intervalo ni una estimación causal de manejo. Los rangos de características se recalcularon para las representaciones realmente usadas. [I4]; [B4].'''
    verification = '''Se completaron las siguientes verificaciones:

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

La ausencia de intervalos es deliberada y se prueba. La batería conserva compatibilidad con el formato anterior cuando un modelo sí declara calibración, pero para esta versión exige 138 IDs de ajuste, ningún ID de calibración y límites nulos.'''
    text = REPORT.read_text(encoding='utf8')
    for marker, section in [('RESULTADO',result),('METRICAS',metrics_section),('ENTREGA',delivery),('VERIFICACION',verification)]:
        text, n = re.subn(rf'<!-- {marker}_INICIO -->.*?<!-- {marker}_FIN -->',
                          lambda m: f'<!-- {marker}_INICIO -->\n{section}\n<!-- {marker}_FIN -->',text,flags=re.S)
        assert n == 1, marker
    refs = {
        'I4': BASE/'scripts/publish_refinement.py','I5': BASE/'scripts/verify_refinement.py',
        'E11':AUDIT/'verification.json','E12':AUDIT/'release-manifest.json','E13':AUDIT/'activation.json',
        'E14':AUDIT/'permutation-oof.csv','E15':AUDIT/'error-review-by-plot.csv',
        'E16':AUDIT/'selections.csv','E17':BASE/'artifacts/predicciones_59.csv','E18':AUDIT/'prediction-changes.csv',
        'E19':BASE/'docs/riesgo-economico.md','E20':AUDIT/'completion.json'}
    for ref,path in refs.items():
        if f'[{ref}]:' not in text:
            text += f'\n[{ref}]: <{path.as_posix()}>\n'
    REPORT.write_text(text,encoding='utf8')
    print(f'Report rendered: {REPORT}; MAE gain {gain_mae:.4f}%, RMSE gain {gain_rmse:.4f}%')


if __name__ == '__main__':
    main()
