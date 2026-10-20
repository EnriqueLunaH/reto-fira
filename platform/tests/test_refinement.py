"""Guard against label leakage, accidental spatial mixing and altered recipes."""
import numpy as np
import pandas as pd
import json
import joblib
import hashlib
from sklearn.base import clone
from pipeline.features import ARTIFACTS
from pipeline.refinement import (feature_recipe, load_data, specifications, make_model,
                                 select_models, split_indices, spatial_blocks)


def training_data():
    meta, X = load_data(ARTIFACTS)
    labelled = meta.CONJUNTO.eq('ENTRENAMIENTO')
    return meta.loc[labelled].reset_index(drop=True), X.loc[labelled].reset_index(drop=True)


def test_outer_labels_cannot_change_inner_selection_or_predictions():
    meta, X = training_data()
    y = meta.RENDIMIENTO_T_HA.to_numpy()
    fit = np.arange(45)
    specs = [s for s in specifications() if s['recipe'] == 'original' and s['cloud'] == 60 and s['family'] == 'ridge']
    first, selection, scores = select_models(X, y, fit, 20261013, specs=specs, allow_blend=False)
    poisoned = y.copy()
    poisoned[45:] = 10000
    second, selection2, scores2 = select_models(X, poisoned, fit, 20261013, specs=specs, allow_blend=False)
    assert selection == selection2 and scores == scores2
    np.testing.assert_array_equal(first['point_original'].predict(X.iloc[45:]), second['point_original'].predict(X.iloc[45:]))
    trained = first['point_original']
    recipe = trained.named_steps['recipe'].transform(X.iloc[fit])
    np.testing.assert_allclose(trained.named_steps['impute'].statistics_, recipe.median().fillna(0).to_numpy())


def test_spatial_inner_and_outer_splits_keep_complete_blocks():
    meta, X = training_data()
    for size in (10000, 20000):
        groups = spatial_blocks(meta, size)
        seen = []
        for train, validation in split_indices(np.arange(len(meta)), 20261013, groups, 5):
            assert not set(groups[train]) & set(groups[validation])
            seen.extend(validation)
            for inner, holdout in split_indices(train, 20261013, groups):
                assert not set(groups[inner]) & set(groups[holdout])
                assert not set(validation) & (set(inner) | set(holdout))
        assert sorted(seen) == list(range(138))


def test_recipe_missingness_is_not_zero_and_is_row_local():
    raw = pd.read_csv(ARTIFACTS / 'features-cloud-60.csv', index_col='ID_POLIGONO').iloc[:3].copy()
    months = [f'planet_ndvi_{m:02}' for m in range(5, 11)]
    raw.loc[raw.index[0], months] = np.nan
    raw.loc[raw.index[1], months] = [.2, .3, .4, .5, np.nan, np.nan]
    values = feature_recipe(raw, 'water_temporal')
    assert np.isnan(values.iloc[0].planet_ndvi_may_oct_mean)
    assert values.iloc[0].planet_ndvi_may_oct_months == 0
    assert abs(values.iloc[1].planet_ndvi_may_oct_mean - .35) < 1e-12
    pd.testing.assert_frame_equal(values.iloc[[1]], feature_recipe(raw.iloc[[1]], 'water_temporal'))
    raw.loc[raw.index[1], 'Tmin_2025_05'] = np.nan
    assert np.isnan(feature_recipe(raw, 'water_temporal').iloc[1].temp_mean_apr_jun)


def test_candidates_are_bounded_cloneable_and_target_free():
    meta, X = training_data()
    specs = specifications()
    assert len(specs) == 53 and len({s['id'] for s in specs}) == 53
    for recipe in ('original', 'environment', 'vigor', 'water_temporal'):
        spec = next(s for s in specs if s['recipe'] == recipe and s['family'] == 'ridge')
        model = clone(make_model(spec, 20261013)).fit(X.iloc[:35], meta.RENDIMIENTO_T_HA.iloc[:35])
        assert np.isfinite(model.predict(X.iloc[35:40])).all()
        assert not any('RENDIMIENTO' in c or 'ID_POLIGONO' in c for c in model.named_steps['recipe'].get_feature_names_out())


def test_published_model_matches_frozen_decision_and_has_no_inherited_interval():
    audit = ARTIFACTS / 'model-refinement-v2'
    if not (audit / 'activation.json').exists():
        import pytest
        pytest.skip('No refined release activated')
    decision = json.loads((audit / 'decision.json').read_text())
    manifest = json.loads((audit / 'release-manifest.json').read_text())
    activation = json.loads((audit / 'activation.json').read_text())
    model = joblib.load(ARTIFACTS / 'model.joblib')
    report = json.loads((ARTIFACTS / 'metrics.json').read_text(encoding='utf8'))
    assert model['procedure'] == decision['selected_procedure'] == manifest['procedure']
    assert all(decision['candidates'][model['procedure']]['gates'].values())
    assert report['selection'] == manifest['selection']
    assert model['radius'] is None and report['interval']['method'] == 'not_estimated'
    assert len(model['fit_ids']) == 138 and model['calibration_ids'] == []
    if hasattr(model['pipeline'], 'members'):
        weights = model['pipeline'].weights
        assert abs(sum(weights)-1) < 1e-12 and all(w > 0 for w in weights)
        assert weights == report['selection']['weights']
    production = (ARTIFACTS / 'predicciones_59.csv').read_bytes()
    assert hashlib.sha256(production).hexdigest() == activation['prediction_sha256']
    assert production == (ARTIFACTS.parents[1] / 'comparisons/proposal.csv').read_bytes()
    for filename in ('proposal-01.csv', 'proposal-02.csv'):
        assert (ARTIFACTS.parents[1] / 'comparisons' / filename).read_bytes() == (audit / 'incumbent' / f'comparisons-{filename}').read_bytes()
