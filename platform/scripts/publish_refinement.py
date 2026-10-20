"""Build, verify and optionally activate only the procedure accepted by the audit.

Point models using all 138 labels deliberately have no inherited conformal bounds.
"""
import os
for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(variable, '1')
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import joblib
import numpy as np
import pandas as pd
import sklearn
from pipeline.refinement import SEEDS, load_data, select_models, specifications, sha256, write_json
from pipeline import train as legacy
from pipeline.features import satellite_features, DATA
from refine_model import verify_frozen

ART = BASE / 'artifacts'
OUT = ART / 'model-refinement-v2'
STAGE = OUT / 'release'


def grouped_columns(columns):
    base_names = list(dict.fromkeys(c.split('__', 1)[1] for c in columns))
    groups = legacy.groups_for_features(base_names)
    return {name: [c for c in columns if c.split('__', 1)[1] in cols] for name, cols in groups.items()}


def oof_summary(rows):
    return dict(model=legacy.metrics(rows.actual, rows.predicted), baseline=legacy.metrics(rows.actual, rows.baseline),
                by_state={state: legacy.metrics(g.actual, g.predicted) for state, g in rows.groupby('state')},
                coverage_90=None, interval_evaluation_n=0, unbounded_interval_n=0, mean_interval_width=None,
                interval_status='not_estimated_for_full_data_point_model')


def build():
    verify_frozen()
    decision = json.loads((OUT / 'decision.json').read_text(encoding='utf8'))
    if decision['selected_procedure'] == 'incumbent':
        print('No challenger passed the frozen rule; production is retained.')
        return False
    verification = json.loads((OUT / 'verification.json').read_text())
    assert verification['status'] == 'passed'
    procedure = decision['selected_procedure']
    meta, full = load_data(ART)
    labelled = meta.CONJUNTO.eq('ENTRENAMIENTO')
    train_meta, hidden_meta = meta.loc[labelled].reset_index(drop=True), meta.loc[~labelled].reset_index(drop=True)
    X, hidden = full.loc[labelled].reset_index(drop=True), full.loc[~labelled].reset_index(drop=True)
    y = train_meta.RENDIMIENTO_T_HA.to_numpy()
    specs = specifications()
    if procedure == 'point_original':
        specs = [s for s in specs if s['recipe'] == 'original']
    models, selected, leaderboard = select_models(X, y, np.arange(len(y)), SEEDS[0], specs=specs,
                                                  allow_blend=procedure == 'point_extended')
    model, choice = models[procedure], selected[procedure]
    prediction = np.maximum(model.predict(hidden), 0)
    assert prediction.shape == (59,) and np.isfinite(prediction).all()
    STAGE.mkdir(exist_ok=True)
    full_out = full.copy()
    full_out.insert(0, 'ID_POLIGONO', meta.ID_POLIGONO)
    full_out.to_csv(STAGE / 'features-cloud-all.csv', index=False)
    final = pd.DataFrame({'ID_parcela': hidden_meta.ID_POLIGONO, 'Rendimiento_predicho_t_ha': prediction})
    final.to_csv(STAGE / 'predicciones_59.csv', index=False, float_format='%.4f')
    oof = pd.read_csv(OUT / 'paired-oof.csv')
    validations, summaries = {}, {}
    for scheme, filename in [('parcel', 'validation-parcel.csv'), ('spatial20', 'validation-spatial.csv')]:
        subset = oof.loc[oof.scheme.eq(scheme) & oof.seed.eq(SEEDS[0])].copy()
        subset['predicted'], subset['baseline'] = subset[procedure], subset['median']
        subset['lower'], subset['upper'] = np.nan, np.nan
        rows = subset[['ID_parcela', 'state', 'fold', 'actual', 'predicted', 'baseline', 'lower', 'upper']]
        rows.to_csv(STAGE / filename, index=False)
        validations[scheme], summaries[scheme] = rows, oof_summary(rows)
    # Permutations share the same order across clouds and within a correlated group.
    groups = grouped_columns(X.columns)
    perm_records = []
    for fold in range(1, 6):
        detail = json.loads((OUT / 'folds' / f'parcel-{SEEDS[0]}-{fold}.json').read_text())
        positions = train_meta.index[train_meta.ID_POLIGONO.isin(detail['validation_ids'])].to_numpy()
        fold_model = joblib.load(OUT / 'folds' / f'parcel-{SEEDS[0]}-{fold}-{procedure}.joblib')
        valid_x = X.iloc[positions]
        base = np.abs(y[positions] - np.maximum(fold_model.predict(valid_x), 0)).mean()
        rng = np.random.default_rng(SEEDS[0] + fold)
        for name, columns in groups.items():
            for repeat in range(10):
                altered = valid_x.copy()
                altered[columns] = altered[columns].to_numpy()[rng.permutation(len(altered))]
                loss = np.abs(y[positions] - np.maximum(fold_model.predict(altered), 0)).mean()
                perm_records.append(dict(fold=fold, repeat=repeat, name=name, n=len(positions), delta_mae=float(loss-base)))
    perm = pd.DataFrame(perm_records)
    perm.to_csv(OUT / 'permutation-oof.csv', index=False)
    importance = [dict(name=name, mae_increase=float(np.average(g.delta_mae, weights=g.n)),
                       std=float(g.delta_mae.std())) for name, g in perm.groupby('name')]
    importance.sort(key=lambda r: -r['mae_increase'])
    medians = X.median()
    sensitivities = {}
    for name, columns in groups.items():
        reference = hidden.copy()
        for column in columns:
            reference[column] = medians[column]
        sensitivities[name] = prediction - np.maximum(model.predict(reference), 0)
    # A history is a descriptive sensor time series; use an explicitly recorded cut.
    history_cloud = choice.get('cloud', 60)
    basic = pd.read_csv(DATA / 'CSV-files/Conjunto_datos_BASICO_AgroCebada2026.csv')
    pro = pd.read_csv(DATA / 'CSV-files/Conjunto_datos_PRO_AgroCebada.csv')
    _, _, history = satellite_features(basic, pro, hidden_meta.ID_POLIGONO, history_cloud)
    hidden_ids = set(hidden_meta.ID_POLIGONO)
    history = [row for row in history if row['id'] in hidden_ids]
    raw_context = full.filter(regex='^cloud60__').rename(columns=lambda c: c.split('__', 1)[1]).loc[~labelled].reset_index(drop=True)
    members = model.members if hasattr(model, 'members') else [model]
    ranges = []
    for member in members:
        recipe = member.named_steps['recipe']
        fitting, future = recipe.transform(X), recipe.transform(hidden)
        names = member.named_steps['impute'].get_feature_names_out(fitting.columns)
        names = names[member.named_steps['variance'].get_support()][member.named_steps['select'].get_support()]
        for column in names:
            if column in fitting:
                outside = future[column].notna() & ((future[column] < fitting[column].min()) | (future[column] > fitting[column].max()))
                ranges.append((f'c{recipe.cloud}:{column}', outside.to_numpy()))
    parcels = []
    for i, parcel in hidden_meta.iterrows():
        context = raw_context.iloc[i]
        parcels.append(dict(id=parcel.ID_POLIGONO, state=parcel.Estado, municipality=parcel.Municipio,
                            area_ha=float(parcel.AREA_HA), yield_=float(prediction[i]), lower=None, upper=None,
                            total_t=float(prediction[i]*parcel.AREA_HA), longitude=float(parcel.longitude), latitude=float(parcel.latitude),
                            rain_mm=float(context.PREC_season_2025), elevation_m=None if pd.isna(context.elevation_m) else float(context.elevation_m),
                            slope_deg=None if pd.isna(context.slope_deg) else float(context.slope_deg), clear_months=int(context.planet_months),
                            sensitivity=sorted([dict(name=name, delta=float(values[i])) for name, values in sensitivities.items()], key=lambda r: -abs(r['delta'])),
                            outside_training_range=sorted(set(name for name, values in ranges if values[i]))))
        parcels[-1]['yield'] = parcels[-1].pop('yield_')
    interval = dict(method='not_estimated', nominal_coverage=None, radius_t_ha=None, calibration_n=0,
                    reason='Predictor puntual ajustado con las 138 etiquetas. No se trasladan los intervalos del modelo anterior.')
    metadata = dict(season='Abril–octubre de 2025', n_training=138, n_fit=138, n_calibration=0, n_predictions=59,
                    generated_at=datetime.now(timezone.utc).isoformat(), selection=choice, interval=interval,
                    procedure=procedure, history_cloud_threshold=history_cloud, importance_method='grouped_permutation_outer_oof',
                    importance_n=138, primary_validation_seed=SEEDS[0], repeated_validation_seeds=list(SEEDS))
    report = {**metadata, 'seed': SEEDS[0], 'sklearn_version': sklearn.__version__, 'leaderboard': leaderboard,
              'parcel_cv': summaries['parcel'], 'spatial_cv': summaries['spatial20'],
              'importance': importance, 'fit_ids': train_meta.ID_POLIGONO.tolist(), 'calibration_ids': [],
              'evaluation_note': 'Primary-seed OOF shown for dashboard; five paired repeats and both spatial scales in model-refinement-v2.',
              'calibration_point_metrics': None, 'calibration_baseline': None,
              'target_summary': dict(min=float(y.min()), max=float(y.max()), mean=float(y.mean()))}
    write_json(STAGE / 'metrics.json', report)
    dashboard = dict(metadata=metadata, parcels=parcels, metrics=dict(parcel_cv=summaries['parcel'], spatial_cv=summaries['spatial20'], calibration_point_metrics=None),
                     importance=importance, validation=json.loads(validations['parcel'].to_json(orient='records')),
                     spatial_validation=json.loads(validations['spatial20'].to_json(orient='records')), history=history)
    write_json(STAGE / 'dashboard.json', dashboard)
    joblib.dump(dict(pipeline=model, columns=X.columns.tolist(), cloud_threshold='all', radius=None,
                     fit_ids=train_meta.ID_POLIGONO.tolist(), calibration_ids=[], procedure=procedure), STAGE / 'model.joblib')
    persisted = joblib.load(STAGE / 'model.joblib')
    cached = pd.read_csv(STAGE / 'features-cloud-all.csv', index_col='ID_POLIGONO')
    actual = np.maximum(persisted['pipeline'].predict(cached.loc[final.ID_parcela, persisted['columns']]), 0)
    submitted = pd.read_csv(STAGE / 'predicciones_59.csv')
    np.testing.assert_allclose(actual, submitted.Rendimiento_predicho_t_ha, atol=.00005, rtol=0)
    assert submitted.ID_parcela.is_unique and set(submitted.ID_parcela) == hidden_ids
    write_json(OUT / 'release-manifest.json', dict(procedure=procedure, selection=choice, interval=interval,
               files={path.name: sha256(path) for path in STAGE.iterdir() if path.is_file()},
               comparisons_before_sha256=sha256(BASE.parent/'comparisons/proposal.csv'), verified_model_csv_tolerance=.00005))
    print(json.dumps(dict(procedure=procedure, selection=choice, staged_rows=59, interval=interval), ensure_ascii=False, indent=2))
    return True


def activate():
    verify_frozen()
    manifest = json.loads((OUT / 'release-manifest.json').read_text(encoding='utf8'))
    decision = json.loads((OUT / 'decision.json').read_text(encoding='utf8'))
    assert decision['selected_procedure'] == manifest['procedure'] != 'incumbent'
    for name, digest in manifest['files'].items():
        assert sha256(STAGE / name) == digest
    for name in manifest['files']:
        temporary = ART / (name + '.new')
        shutil.copyfile(STAGE / name, temporary)
        os.replace(temporary, ART / name)
    for name in ('proposal.csv', 'predicciones_59.csv'):
        destination = BASE.parent / 'comparisons' / name
        temporary = destination.with_suffix('.csv.new')
        shutil.copyfile(STAGE / 'predicciones_59.csv', temporary)
        os.replace(temporary, destination)
    write_json(OUT / 'activation.json', dict(activated_at=datetime.now(timezone.utc).isoformat(), procedure=manifest['procedure'],
               prediction_sha256=sha256(ART / 'predicciones_59.csv'), backup='model-refinement-v2/incumbent',
               interval='No interval published for the refitted point predictor'))
    print('Verified release activated; comparison CSVs synchronized.')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    available = build() if args.build else True
    if args.activate and available:
        activate()
