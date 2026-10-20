"""Auditable point-prediction comparison; no hidden labels or global target selection.

All learned preprocessing lives inside the fitted estimator. Recipe transforms are
row-local and use only the supplied April--October 2025 feature tables.
"""
import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, RegressorMixin, clone
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_regression
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.model_selection import KFold, GroupKFold

from . import train as legacy

SEEDS = (20261013, 20261014, 20261015, 20261016, 20261017)
CLOUDS = (20, 40, 60)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def feature_recipe(raw, recipe):
    """Fixed, target-free definitions. No interpolated phenology or zero-filled gaps."""
    if recipe == 'original':
        return raw.copy()
    if recipe == 'environment':
        return raw[[c for c in raw if c.startswith(('PREC', 'Tmin', 'Tmax', 'thermal'))
                    or c in ('elevation_m', 'slope_deg', 'area_ha')]].copy()
    out = raw[['elevation_m', 'slope_deg', 'area_ha', 'PREC_early', 'PREC_mid', 'PREC_late']].copy()
    for label, months in [('apr_jun', (4, 5, 6)), ('jul_aug', (7, 8)), ('sep_oct', (9, 10))]:
        minimum = raw[[f'Tmin_2025_{m:02}' for m in months]].mean(axis=1, skipna=False)
        maximum = raw[[f'Tmax_2025_{m:02}' for m in months]].mean(axis=1, skipna=False)
        out[f'temp_mean_{label}'] = (minimum + maximum) / 2
        out[f'temp_range_{label}'] = maximum - minimum
    # Monthly medians already give each month equal influence, regardless of visits.
    for sensor in ('sentinel2', 'planet'):
        for index in ('ndvi', 'evi'):
            for summary in ('mean', 'peak', 'late_change'):
                key = f'{sensor}_{index}_{summary}'
                out[key] = raw[key]
        out[f'{sensor}_months'] = raw[f'{sensor}_months']
    if recipe == 'vigor':
        return out
    if recipe != 'water_temporal':
        raise ValueError(f'Unknown feature recipe: {recipe}')
    for sensor, index in [('sentinel2', 'ndwi'), ('sentinel2', 'msi'), ('sentinel2', 'dswi2'), ('planet', 'msavi')]:
        for summary in ('mean', 'late_change'):
            key = f'{sensor}_{index}_{summary}'
            out[key] = raw[key]
    for sensor in ('sentinel2', 'planet'):
        # Calendar summaries, not observed sowing/flowering dates. Require >=4 of 6 months.
        cols = [f'{sensor}_ndvi_{m:02}' for m in range(5, 11)]
        values = raw[cols]
        enough = values.notna().sum(axis=1) >= 4
        out[f'{sensor}_ndvi_may_oct_mean'] = values.mean(axis=1).where(enough)
        out[f'{sensor}_ndvi_may_oct_spread'] = values.std(axis=1).where(enough)
        out[f'{sensor}_ndvi_may_oct_months'] = values.notna().sum(axis=1)
        early = raw[[f'{sensor}_ndvi_{m:02}' for m in (5, 6)]].mean(axis=1, skipna=False)
        mid = raw[[f'{sensor}_ndvi_{m:02}' for m in (7, 8)]].mean(axis=1, skipna=False)
        out[f'{sensor}_ndvi_change_may_jun_to_jul_aug'] = mid - early
    return out


class RecipeTransformer(TransformerMixin, BaseEstimator):
    def __init__(self, cloud=60, recipe='original'):
        self.cloud = cloud
        self.recipe = recipe

    def fit(self, X, y=None):
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        self.output_columns_ = self.transform(X).columns.to_numpy()
        return self

    def transform(self, X):
        prefix = f'cloud{self.cloud}__'
        raw = X[[c for c in X if c.startswith(prefix)]].rename(columns=lambda c: c[len(prefix):])
        if raw.empty:
            raise ValueError(f'Missing input columns for cloud threshold {self.cloud}')
        return feature_recipe(raw, self.recipe)

    def get_feature_names_out(self, input_features=None):
        return self.output_columns_


class WeightedPredictor(RegressorMixin, BaseEstimator):
    """Fitted members and weights frozen by inner CV, never by hidden predictions."""
    def __init__(self, members, weights):
        self.members = members
        self.weights = weights

    def predict(self, X):
        return sum(weight * np.maximum(member.predict(X), 0)
                   for member, weight in zip(self.members, self.weights))


def specifications():
    specs = []
    for cloud in CLOUDS:
        for name, estimator, k in legacy.candidates():
            specs.append(dict(id=f'original_c{cloud}_{name}', recipe='original', cloud=cloud,
                              name=name, family=('ridge' if name.startswith('ridge') else name), k=k))
    for recipe in ('environment', 'vigor', 'water_temporal'):
        for cloud in ((20,) if recipe == 'environment' else CLOUDS):
            for name in ('ridge_1', 'ridge_10', 'ridge_100', 'random_forest', 'gradient_boosting'):
                specs.append(dict(id=f'{recipe}_c{cloud}_{name}', recipe=recipe, cloud=cloud,
                                  name=name, family=('ridge' if name.startswith('ridge') else name), k='all'))
    return specs


def make_model(spec, seed):
    if spec['recipe'] == 'original':
        estimator = next(clone(e) for name, e, k in legacy.candidates() if name == spec['name'])
    elif spec['name'].startswith('ridge'):
        estimator = Ridge(alpha=float(spec['name'].split('_')[-1]))
    elif spec['name'] == 'random_forest':
        estimator = RandomForestRegressor(n_estimators=180, min_samples_leaf=4, max_features=.8)
    else:
        estimator = HistGradientBoostingRegressor(max_iter=120, max_leaf_nodes=7, min_samples_leaf=12,
                                                  l2_regularization=10, learning_rate=.05)
    if 'random_state' in estimator.get_params():
        estimator.set_params(random_state=seed)
    if 'n_jobs' in estimator.get_params():
        estimator.set_params(n_jobs=1)
    return Pipeline([
        ('recipe', RecipeTransformer(spec['cloud'], spec['recipe'])),
        ('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
        ('variance', VarianceThreshold()), ('scale', StandardScaler()),
        ('select', SelectKBest(f_regression, k=spec['k'])), ('model', estimator),
    ])


def split_indices(indices, seed, groups=None, folds=3):
    splitter = (KFold(folds, shuffle=True, random_state=seed) if groups is None else
                GroupKFold(min(folds, len(np.unique(groups[indices])))))
    return [(indices[tr], indices[va]) for tr, va in
            splitter.split(indices, groups=None if groups is None else groups[indices])]


def select_models(X, y, indices, seed, groups=None, specs=None, allow_blend=True):
    """Returns only inner-CV evidence and fitted models; outer labels are not inputs."""
    specs = specifications() if specs is None else specs
    splits = split_indices(np.arange(len(indices)), seed, None if groups is None else groups[indices])
    rows, predictions = [], {}
    for spec in specs:
        pred = np.full(len(indices), np.nan)
        for tr, va in splits:
            model = make_model(spec, seed).fit(X.iloc[indices[tr]], y[indices[tr]])
            pred[va] = np.maximum(model.predict(X.iloc[indices[va]]), 0)
        assert np.isfinite(pred).all()
        predictions[spec['id']] = pred
        rows.append({**spec, **legacy.metrics(y[indices], pred)})
    order = lambda row: (row['mae'], row['rmse'], row['id'])
    rows.sort(key=order)
    selected = {'point_original': min((s for s in rows if s['recipe'] == 'original'), key=order)}
    for family in ('ridge', 'random_forest', 'gradient_boosting'):
        subset = [s for s in rows if s['family'] == family]
        if subset:
            selected[family] = min(subset, key=order)
    for recipe in ('environment', 'vigor', 'water_temporal'):
        subset = [s for s in rows if s['recipe'] == recipe]
        if subset:
            selected[recipe] = min(subset, key=order)
    selected['point_extended_single'] = rows[0]
    if allow_blend and 'ridge' in selected and 'random_forest' in selected:
        a, b = selected['ridge'], selected['random_forest']
        for weight in (.25, .5, .75):
            pred = weight * predictions[a['id']] + (1 - weight) * predictions[b['id']]
            rows.append(dict(id=f'blend_ridge_{weight:g}', recipe='blend', name='ridge_rf_blend',
                             family='blend', members=[a['id'], b['id']], weights=[weight, 1-weight],
                             **legacy.metrics(y[indices], pred)))
    rows.sort(key=order)
    selected['point_extended'] = rows[0]
    by_id = {s['id']: s for s in rows}
    fitted = {}

    def fit_selected(spec):
        if spec['id'] not in fitted:
            if spec['recipe'] == 'blend':
                fitted[spec['id']] = WeightedPredictor([fit_selected(by_id[s]) for s in spec['members']], spec['weights'])
            else:
                fitted[spec['id']] = make_model(spec, seed).fit(X.iloc[indices], y[indices])
        return fitted[spec['id']]

    models = {name: fit_selected(spec) for name, spec in selected.items()}
    return models, selected, rows


def load_data(artifact_dir):
    meta = pd.read_csv(artifact_dir / 'parcels.csv')
    if not meta.ID_POLIGONO.is_unique or len(meta) != 197:
        raise ValueError('Expected exactly 197 unique plots')
    labelled = meta.CONJUNTO.eq('ENTRENAMIENTO')
    if labelled.sum() != 138 or meta.loc[~labelled, 'RENDIMIENTO_T_HA'].notna().any():
        raise ValueError('Invalid labelled/hidden split')
    frames = []
    for cloud in CLOUDS:
        raw = pd.read_csv(artifact_dir / f'features-cloud-{cloud}.csv', index_col='ID_POLIGONO')
        if not raw.index.is_unique or set(raw.index) != set(meta.ID_POLIGONO):
            raise ValueError('Feature IDs do not match parcels')
        if any(c in raw for c in ('RENDIMIENTO_T_HA', 'CONJUNTO', 'Estado', 'x_m', 'y_m')):
            raise ValueError('Metadata or target leaked into features')
        frames.append(raw.loc[meta.ID_POLIGONO].add_prefix(f'cloud{cloud}__').reset_index(drop=True))
    return meta, pd.concat(frames, axis=1)


def spatial_blocks(meta, size):
    return (np.floor(meta.x_m / size).astype(int).astype(str) + '_' +
            np.floor(meta.y_m / size).astype(int).astype(str)).to_numpy()
