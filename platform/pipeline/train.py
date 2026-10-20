"""Nested parcel CV, spatial stress test and frozen split-conformal predictions."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import warnings
import sys
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_regression, VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.model_selection import KFold, GroupKFold, train_test_split
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .features import build_features, ARTIFACTS, ROOT

SEED = 20261013
os.environ.setdefault('LOKY_MAX_CPU_COUNT', '2')
warnings.filterwarnings('ignore', message='Features .* are constant')


def metrics(y, prediction):
    return {'mae': float(mean_absolute_error(y, prediction)),
            'rmse': float(np.sqrt(mean_squared_error(y, prediction))),
            'r2': float(r2_score(y, prediction)), 'n': len(y),
            'bias': float(np.mean(prediction - y))}


def candidates():
    return [
        ('ridge_10', Ridge(alpha=10), 30),
        ('ridge_100', Ridge(alpha=100), 30),
        ('extra_trees', ExtraTreesRegressor(n_estimators=180, min_samples_leaf=3, max_features=.8, random_state=SEED, n_jobs=2), 60),
        ('random_forest', RandomForestRegressor(n_estimators=180, min_samples_leaf=4, max_features=.8, random_state=SEED, n_jobs=2), 60),
        ('gradient_boosting', HistGradientBoostingRegressor(max_iter=120, max_leaf_nodes=7, min_samples_leaf=12, l2_regularization=10, learning_rate=.05, random_state=SEED), 35),
        ('svr', SVR(C=5, epsilon=.15), 40),
    ]


def pipeline(estimator, k):
    return Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
                     ('variance', VarianceThreshold()), ('scale', StandardScaler()),
                     ('select', SelectKBest(f_regression, k=k)), ('model', clone(estimator))])


def predict_nonnegative(model, x):
    return np.maximum(model.predict(x), 0)


def select_model(matrices, y, train, groups=None, folds=3):
    splitter = GroupKFold(min(folds, len(np.unique(groups[train])))) if groups is not None else KFold(folds, shuffle=True, random_state=SEED)
    splits = list(splitter.split(train, groups=groups[train] if groups is not None else None))
    scores = []
    for cloud, matrix in matrices.items():
        for name, estimator, k in candidates():
            pred, actual = [], []
            for tr, va in splits:
                model = pipeline(estimator, k)
                model.fit(matrix.iloc[train[tr]], y[train[tr]])
                pred.extend(predict_nonnegative(model, matrix.iloc[train[va]]))
                actual.extend(y[train[va]])
            scores.append({'name': name, 'cloud': cloud, 'k': k, **metrics(actual, np.array(pred))})
    scores.sort(key=lambda score: (score['mae'], score['rmse'], score['name'], score['cloud']))
    best = scores[0]
    estimator = next(e for name, e, k in candidates() if name == best['name'])
    fitted = pipeline(estimator, best['k']).fit(matrices[best['cloud']].iloc[train], y[train])
    return fitted, best, scores


def conformal_quantile(errors, alpha=.1):
    """Finite-sample corrected order statistic; +infinity when calibration is insufficient."""
    errors = np.sort(np.asarray(errors))
    k = math.ceil((len(errors) + 1) * (1 - alpha))
    return float(errors[k - 1]) if k <= len(errors) else float('inf')


def training_indices(indices, groups=None, seed=SEED):
    if groups is None:
        return train_test_split(indices, test_size=.2, random_state=seed)
    # Hold out complete spatial blocks for calibration. No shared group can enter fitting.
    unique = np.unique(groups[indices])
    fit_groups, cal_groups = train_test_split(unique, test_size=.2, random_state=seed)
    return indices[np.isin(groups[indices], fit_groups)], indices[np.isin(groups[indices], cal_groups)]


def evaluate(matrices, y, metadata, spatial=False):
    blocks = (np.floor(metadata.x_m / 20000).astype(int).astype(str) + '_' +
              np.floor(metadata.y_m / 20000).astype(int).astype(str)).to_numpy()
    groups = blocks if spatial else None
    splitter = GroupKFold(5) if spatial else KFold(5, shuffle=True, random_state=SEED)
    records, folds = [], []
    for fold, (train, validation) in enumerate(splitter.split(metadata, groups=groups), 1):
        fit, calibration = training_indices(train, groups, seed=SEED + fold)
        model, best, scores = select_model(matrices, y, fit, groups)
        matrix = matrices[best['cloud']]
        q = conformal_quantile(abs(y[calibration] - predict_nonnegative(model, matrix.iloc[calibration])))
        pred = predict_nonnegative(model, matrix.iloc[validation])
        baseline = DummyRegressor(strategy='median').fit(matrix.iloc[fit], y[fit]).predict(matrix.iloc[validation])
        lo, hi = np.maximum(pred-q, 0), pred+q
        folds.append({'fold': fold, 'selection': best, 'fit_n': len(fit), 'calibration_n': len(calibration),
                      'metrics': metrics(y[validation], pred), 'interval_radius': q if np.isfinite(q) else None})
        for j, pos in enumerate(validation):
            records.append({'ID_parcela': metadata.iloc[pos].ID_POLIGONO, 'state': metadata.iloc[pos].Estado,
                            'fold': fold, 'actual': float(y[pos]), 'predicted': float(pred[j]),
                            'baseline': float(baseline[j]), 'lower': float(lo[j]) if np.isfinite(q) else None,
                            'upper': float(hi[j]) if np.isfinite(q) else None})
        print(('Spatial' if spatial else 'Parcel') + f' fold {fold}/5: {best["name"]}, clouds <= {best["cloud"]}, MAE {folds[-1]["metrics"]["mae"]:.3f}', flush=True)
    rows = pd.DataFrame(records)
    available = rows.lower.notna() & rows.upper.notna()
    summary = {'model': metrics(rows.actual, rows.predicted), 'baseline': metrics(rows.actual, rows.baseline),
               'coverage_90': float(((rows.loc[available,'actual'] >= rows.loc[available,'lower']) &
                                      (rows.loc[available,'actual'] <= rows.loc[available,'upper'])).mean()) if available.any() else None,
               'interval_evaluation_n': int(available.sum()), 'unbounded_interval_n': int((~available).sum()),
               'mean_interval_width': float((rows.loc[available,'upper']-rows.loc[available,'lower']).mean()) if available.any() else None,
               'folds': folds, 'by_state': {state: metrics(g.actual, g.predicted) for state, g in rows.groupby('state')},
               'spatial_blocks': int(len(np.unique(blocks))) if spatial else None}
    rows.to_csv(ARTIFACTS / ('validation-spatial.csv' if spatial else 'validation-parcel.csv'), index=False)
    return summary, rows


def groups_for_features(columns):
    rules = {
        'Lluvia': lambda c: c.startswith('PREC'),
        'Temperatura': lambda c: c.startswith(('Tmin', 'Tmax', 'thermal')),
        'Relieve': lambda c: c in ['elevation_m', 'slope_deg'],
        'Vegetación Sentinel-2': lambda c: c.startswith('sentinel2'),
        'Vegetación Planet': lambda c: c.startswith('planet'),
        'Señal Landsat': lambda c: c.startswith('landsat'),
        'Superficie': lambda c: c == 'area_ha',
    }
    return {name: [c for c in columns if rule(c)] for name, rule in rules.items()}


def run(force=False):
    metadata, matrices_all, histories = build_features(force)
    labelled = metadata.CONJUNTO.eq('ENTRENAMIENTO').to_numpy()
    train_meta = metadata.loc[labelled].reset_index(drop=True)
    matrices = {cloud: matrix.loc[train_meta.ID_POLIGONO].reset_index(drop=True) for cloud, matrix in matrices_all.items()}
    y = train_meta.RENDIMIENTO_T_HA.to_numpy()
    random_cv, rows = evaluate(matrices, y, train_meta)
    spatial_cv, spatial_rows = evaluate(matrices, y, train_meta, spatial=True)
    fit, calibration = training_indices(np.arange(len(y)))
    model, best, leaderboard = select_model(matrices, y, fit, folds=5)
    x = matrices[best['cloud']]
    holdout_pred = predict_nonnegative(model, x.iloc[calibration])
    residuals = abs(y[calibration] - holdout_pred)
    q = conformal_quantile(residuals)
    assert np.isfinite(q)
    baseline_pred = np.full(len(calibration), np.median(y[fit]))
    feature_groups = groups_for_features(x.columns)
    baseline_mae = mean_absolute_error(y[calibration], holdout_pred)
    rng = np.random.default_rng(SEED)
    importance = []
    for name, columns in feature_groups.items():
        drops = []
        for repeat in range(20):
            permuted = x.iloc[calibration].copy()
            permuted[columns] = permuted[columns].to_numpy()[rng.permutation(len(calibration))]
            drops.append(mean_absolute_error(y[calibration], predict_nonnegative(model, permuted))-baseline_mae)
        importance.append({'name': name, 'mae_increase': float(np.mean(drops)), 'std': float(np.std(drops))})
    importance.sort(key=lambda row: row['mae_increase'], reverse=True)
    hidden_meta = metadata.loc[~labelled].reset_index(drop=True)
    hidden = matrices_all[best['cloud']].loc[hidden_meta.ID_POLIGONO].reset_index(drop=True)
    prediction = predict_nonnegative(model, hidden)
    final = pd.DataFrame({'ID_parcela': hidden_meta.ID_POLIGONO, 'Rendimiento_predicho_t_ha': prediction})
    assert len(final) == 59 and final.ID_parcela.is_unique and np.isfinite(prediction).all()
    final.to_csv(ARTIFACTS / 'predicciones_59.csv', index=False, float_format='%.4f')
    medians = x.iloc[fit].median()
    sensitivities = {}
    for name, columns in feature_groups.items():
        reference = hidden.copy()
        reference[columns] = reference[columns].fillna(medians[columns])
        for c in columns:
            reference[c] = medians[c]
        sensitivities[name] = prediction - predict_nonnegative(model, reference)
    parcel_records = []
    for i, p in hidden_meta.iterrows():
        record = {'id': p.ID_POLIGONO, 'state': p.Estado, 'municipality': p.Municipio,
                  'area_ha': float(p.AREA_HA), 'yield': float(prediction[i]),
                  'lower': max(float(prediction[i]-q), 0), 'upper': float(prediction[i]+q),
                  'total_t': float(prediction[i]*p.AREA_HA), 'longitude': p.longitude, 'latitude': p.latitude,
                  'rain_mm': float(hidden.iloc[i].PREC_season_2025),
                  'elevation_m': float(hidden.iloc[i].elevation_m) if pd.notna(hidden.iloc[i].elevation_m) else None,
                  'slope_deg': float(hidden.iloc[i].slope_deg) if pd.notna(hidden.iloc[i].slope_deg) else None,
                  'clear_months': int(hidden.iloc[i].planet_months),
                  'sensitivity': sorted([{'name': name, 'delta': float(vals[i])} for name, vals in sensitivities.items()], key=lambda row: -abs(row['delta']))}
        record['outside_training_range'] = [c for c in x.columns if pd.notna(hidden.iloc[i][c]) and
                                             (hidden.iloc[i][c] < x.iloc[fit][c].min() or hidden.iloc[i][c] > x.iloc[fit][c].max())]
        parcel_records.append(record)
    selected_names = model.named_steps['impute'].get_feature_names_out(x.columns)
    selected_names = selected_names[model.named_steps['variance'].get_support()][model.named_steps['select'].get_support()].tolist()
    report = {'generated_at': datetime.now(timezone.utc).isoformat(), 'seed': SEED,
              'sklearn_version': sklearn.__version__, 'season': 'Abril–octubre de 2025',
              'n_training': 138, 'n_fit': len(fit), 'n_calibration': len(calibration), 'n_predictions': 59,
              'selection': best, 'leaderboard': leaderboard, 'selected_features': selected_names,
              'parcel_cv': random_cv, 'spatial_cv': spatial_cv,
              'calibration_point_metrics': metrics(y[calibration], holdout_pred),
              'calibration_baseline': metrics(y[calibration], baseline_pred),
              'interval': {'method': 'split conformal', 'nominal_coverage': .9, 'radius_t_ha': q,
                           'calibration_n': len(calibration), 'order_statistic': math.ceil((len(calibration)+1)*.9),
                           'assumption': 'Intercambiabilidad de parcelas de calibración y nuevas; no garantizada por dependencia espacial.'},
              'importance': importance, 'fit_ids': train_meta.iloc[fit].ID_POLIGONO.tolist(),
              'calibration_ids': train_meta.iloc[calibration].ID_POLIGONO.tolist(),
              'target_summary': {'min': float(y.min()), 'max': float(y.max()), 'mean': float(y.mean())}}
    (ARTIFACTS / 'metrics.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    dashboard = {'metadata': {k: report[k] for k in ['season','n_training','n_fit','n_calibration','n_predictions','generated_at','selection','interval']},
                 'parcels': parcel_records, 'metrics': {'parcel_cv': random_cv, 'spatial_cv': spatial_cv,
                                                       'calibration_point_metrics': report['calibration_point_metrics']},
                 'importance': importance, 'validation': json.loads(rows.to_json(orient='records')),
                 'spatial_validation': json.loads(spatial_rows.to_json(orient='records')),
                 'history': [r for r in histories[best['cloud']] if r['id'] in set(hidden_meta.ID_POLIGONO)]}
    (ARTIFACTS / 'dashboard.json').write_text(json.dumps(dashboard, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    joblib.dump({'pipeline': model, 'columns': x.columns.tolist(), 'cloud_threshold': best['cloud'], 'radius': q,
                 'fit_ids': report['fit_ids'], 'calibration_ids': report['calibration_ids']}, ARTIFACTS / 'model.joblib')
    fingerprints = []
    for path in sorted((ROOT / 'data').rglob('*')):
        if path.is_file():
            h = hashlib.sha256()
            with path.open('rb') as f:
                for block in iter(lambda: f.read(1024*1024), b''):
                    h.update(block)
            fingerprints.append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': h.hexdigest()})
    (ARTIFACTS / 'source-manifest.json').write_text(json.dumps(fingerprints, indent=2), encoding='utf-8')
    print(json.dumps({'selection': best, 'parcel_cv': random_cv['model'], 'spatial_cv': spatial_cv['model'],
                      'calibration': report['calibration_point_metrics'], 'q90': q}, indent=2), flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--force-features', action='store_true')
    run(parser.parse_args().force_features)
