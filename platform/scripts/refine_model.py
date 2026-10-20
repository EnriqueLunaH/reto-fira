"""Frozen, resumable paired experiment. Run --prepare, --evaluate, then --decide.

This script never replaces production. A promotion is a separate, verified step.
"""
import os
for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(variable, '1')
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from pipeline import train as legacy
from pipeline.refinement import (SEEDS, CLOUDS, load_data, specifications, select_models,
                                 split_indices, spatial_blocks, feature_recipe, sha256, write_json)

ART = BASE / 'artifacts'
OUT = ART / 'model-refinement-v2'
PROCEDURES = ['incumbent', 'point_original', 'point_extended', 'point_extended_single',
              'ridge', 'random_forest', 'gradient_boosting', 'environment', 'vigor', 'water_temporal',
              'median', 'state_median']


def input_paths():
    return [BASE / 'pipeline/train.py', BASE / 'pipeline/features.py', BASE / 'pipeline/refinement.py',
            Path(__file__), ART / 'parcels.csv', ART / 'environment.csv', ART / 'raster-coverage.csv',
            *[ART / f'features-cloud-{c}.csv' for c in CLOUDS],
            BASE.parent / 'data/fira/CSV-files/ID_area_rendimiento_70_30_Reto_AgroCebada.csv']


def verify_frozen():
    manifest = json.loads((OUT / 'input-hashes.json').read_text(encoding='utf8'))
    for rel, expected in manifest.items():
        if sha256(BASE / rel) != expected:
            raise ValueError(f'Frozen experiment input changed: {rel}; do not silently resume')


def prepare():
    if (OUT / 'protocol.json').exists():
        verify_frozen()
        print('Existing frozen protocol verified; nothing overwritten.', flush=True)
        return
    meta, X = load_data(ART)
    labels = pd.read_csv(BASE.parent / 'data/fira/CSV-files/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')
    joined = meta.merge(labels[['ID_POLIGONO', 'CONJUNTO', 'RENDIMIENTO_T_HA']], on='ID_POLIGONO', validate='one_to_one', suffixes=('', '_source'))
    assert joined.CONJUNTO.equals(joined.CONJUNTO_source)
    np.testing.assert_allclose(joined.RENDIMIENTO_T_HA, joined.RENDIMIENTO_T_HA_source, equal_nan=True)
    # Cached environment is trusted only after checking the source files that produced it.
    sources = json.loads((ART / 'source-manifest.json').read_text(encoding='utf8'))
    source_check = []
    for row in sources:
        path = BASE.parent / row['path']
        if path.suffix.lower() in ('.tif', '.csv', '.shp', '.shx', '.dbf', '.prj'):
            digest = sha256(path)
            if digest != row['sha256']:
                raise ValueError(f'Source changed; regenerate features before experiment: {path}')
            source_check.append(dict(path=row['path'], sha256=digest))
    OUT.mkdir(parents=True, exist_ok=True)
    backup = OUT / 'incumbent'
    backup.mkdir(exist_ok=True)
    production = ['model.joblib', 'metrics.json', 'dashboard.json', 'predicciones_59.csv',
                  'validation-parcel.csv', 'validation-spatial.csv']
    for name in production:
        shutil.copy2(ART / name, backup / name)
    shutil.copy2(BASE / 'pipeline/train.py', backup / 'train.py')
    for name in ('proposal.csv', 'proposal-01.csv', 'proposal-02.csv', 'predicciones_59.csv'):
        path = BASE.parent / 'comparisons' / name
        if path.exists():
            shutil.copy2(path, backup / f'comparisons-{name}')
    write_json(OUT / 'incumbent-hashes.json', {p.name: sha256(p) for p in backup.iterdir() if p.is_file()})
    write_json(OUT / 'source-check.json', source_check)
    write_json(OUT / 'input-hashes.json', {str(p.relative_to(BASE)) if p.is_relative_to(BASE) else os.path.relpath(p, BASE): sha256(p) for p in input_paths()})
    shapes = {}
    missing = []
    for cloud in CLOUDS:
        raw = X.filter(regex=f'^cloud{cloud}__').rename(columns=lambda c: c.split('__', 1)[1])
        for recipe in ('original', 'environment', 'vigor', 'water_temporal'):
            frame = feature_recipe(raw, recipe)
            shapes[f'{recipe}_{cloud}'] = frame.columns.tolist()
            for column in frame:
                missing.append(dict(cloud=cloud, recipe=recipe, column=column,
                                    missing_train=int(frame.loc[meta.CONJUNTO.eq('ENTRENAMIENTO'), column].isna().sum()),
                                    missing_hidden=int(frame.loc[meta.CONJUNTO.eq('PREDICCION'), column].isna().sum())))
    pd.DataFrame(missing).to_csv(OUT / 'feature-missingness.csv', index=False)
    protocol = {
        'created_at': datetime.now(timezone.utc).isoformat(), 'status': 'frozen_before_new_outer_results_exploratory_reused_labels',
        'target': 'RENDIMIENTO_T_HA', 'labelled_n': 138, 'hidden_n': 59,
        'seeds': list(SEEDS), 'outer_folds': 5, 'inner_folds': 3,
        'spatial': {'block_sizes_m': [10000, 20000], 'seed': SEEDS[0], 'folds': 5, 'grid_origin': [0, 0], 'crs': 'EPSG:6372'},
        'original': '18 legacy candidates; outer training holds out 20% for calibration exactly as before',
        'point_original': 'Same 18 candidates; all outer training observations available for selection/fitting',
        'point_extended': '18 legacy + 35 compact candidates; optionally inner-selected Ridge/RF blend weights .25/.5/.75. Endpoints are single candidates.',
        'specifications': specifications(), 'feature_columns': shapes,
        'primary_metric': 'MAE, t/ha; pooled OOF per repetition; average repetition MAE',
        'secondary_metrics': ['RMSE from mean repetition MSE', 'pooled R2 per repetition', 'bias', 'by-state errors', 'spatial stress'],
        'promotion': {
            'eligible': ['point_original', 'point_extended'],
            'minimum_mean_mae_gain_t_ha': .01, 'minimum_seeds_with_lower_mae': 4,
            'maximum_pooled_rmse_increase': 0,
            'spatial_rule': 'Do not worsen BOTH MAE and RMSE at BOTH 10km and 20km; report every spatial result',
            'bootstrap_rule': '95% descriptive paired parcel bootstrap upper endpoint below zero; average losses per ID before resampling; also report block bootstrap',
            'tie_rule': 'If both eligible pass, prefer point_original unless extended MAE is at least .01 t/ha lower',
            'interpretation': 'Operational exploratory acceptance policy, not FIRA thresholds or proof on the 59 hidden plots',
        },
        'family_and_recipe_results': 'Diagnostic ablations only; never promote their outer-CV winner separately',
        'uncertainty': 'If a full-data point predictor is promoted, do not transfer legacy conformal bounds. Optional intervals may be unavailable; preserve old artifacts.',
        'forbidden': ['hidden labels or pseudo-labels from comparison CSVs', 'global supervised selection',
                      'post-hoc outlier deletion or bias correction', 'fake multi-year yield labels', 'neural networks', 'unvalidated FAO/AquaCrop conversion'],
        'limits': ['138 labels previously used in development; no new blind test', 'five repetitions reuse the same plots',
                   'one labelled cycle cannot validate future-year forecasting', 'spatial blocks are few and unbalanced'],
    }
    write_json(OUT / 'protocol.json', protocol)
    print(f'Protocol frozen: {len(specifications())} single candidates; source hashes verified: {len(source_check)}', flush=True)


def jobs(meta):
    result = []
    for scheme, size, seeds in [('parcel', None, SEEDS), ('spatial10', 10000, [SEEDS[0]]), ('spatial20', 20000, [SEEDS[0]])]:
        groups = None if size is None else spatial_blocks(meta, size)
        for seed in seeds:
            for fold, (tr, va) in enumerate(split_indices(np.arange(len(meta)), seed, groups, 5), 1):
                result.append((scheme, size, seed, fold, tr.tolist(), va.tolist()))
    return result


def evaluate_job(job):
    started = time.monotonic()
    scheme, size, seed, fold, train, validation = job
    key = f'{scheme}-{seed}-{fold}'
    destination = OUT / 'folds' / f'{key}.json'
    if destination.exists():
        return key, 'cached'
    meta_all, full = load_data(ART)
    labelled = meta_all.CONJUNTO.eq('ENTRENAMIENTO')
    meta, X = meta_all.loc[labelled].reset_index(drop=True), full.loc[labelled].reset_index(drop=True)
    y = meta.RENDIMIENTO_T_HA.to_numpy()
    train, validation = np.asarray(train), np.asarray(validation)
    groups = None if size is None else spatial_blocks(meta, size)
    fit, calibration = legacy.training_indices(train, groups, seed=seed + fold)
    original_specs = [s for s in specifications() if s['recipe'] == 'original']
    old_models, old_selected, old_scores = select_models(X, y, fit, seed, groups, original_specs, allow_blend=False)
    models, selected, scores = select_models(X, y, train, seed, groups)
    models['incumbent'], selected['incumbent'] = old_models['point_original'], old_selected['point_original']
    pred = {name: np.maximum(model.predict(X.iloc[validation]), 0) for name, model in models.items()}
    pred['median'] = np.full(len(validation), np.median(y[train]))
    medians = pd.DataFrame({'state': meta.iloc[train].Estado.to_numpy(), 'y': y[train]}).groupby('state').y.median()
    pred['state_median'] = meta.iloc[validation].Estado.map(medians).fillna(np.median(y[train])).to_numpy()
    near = cdist(meta.iloc[validation][['x_m', 'y_m']], meta.iloc[train][['x_m', 'y_m']]).min(axis=1)
    rows = []
    blocks20 = spatial_blocks(meta, 20000)
    for j, pos in enumerate(validation):
        rows.append(dict(ID_parcela=meta.iloc[pos].ID_POLIGONO, state=meta.iloc[pos].Estado,
                         block20=blocks20[pos], actual=float(y[pos]), nearest_train_m=float(near[j]),
                         **{name: float(values[j]) for name, values in pred.items()}))
    if scheme == 'parcel' and seed == SEEDS[0]:
        for name in ('point_original', 'point_extended'):
            joblib.dump(models[name], OUT / 'folds' / f'{key}-{name}.joblib')
    details = dict(scheme=scheme, seed=seed, fold=fold, seconds=time.monotonic()-started,
                   training_ids=meta.iloc[train].ID_POLIGONO.tolist(), validation_ids=meta.iloc[validation].ID_POLIGONO.tolist(),
                   incumbent_fit_ids=meta.iloc[fit].ID_POLIGONO.tolist(), incumbent_calibration_ids=meta.iloc[calibration].ID_POLIGONO.tolist(),
                   inner_splits=[dict(train_ids=meta.iloc[tr].ID_POLIGONO.tolist(), validation_ids=meta.iloc[va].ID_POLIGONO.tolist())
                                 for tr, va in split_indices(train, seed, groups)],
                   selected=selected, inner_scores=scores, incumbent_inner_scores=old_scores, rows=rows)
    write_json(destination, details)
    return key, {name: round(legacy.metrics(y[validation], pred[name])['mae'], 4) for name in ('incumbent', 'point_original', 'point_extended')}


def evaluate(workers):
    verify_frozen()
    meta, _ = load_data(ART)
    meta = meta.loc[meta.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True)
    (OUT / 'folds').mkdir(exist_ok=True)
    work = jobs(meta)
    manifest = []
    for scheme, size, seed, fold, train, validation in work:
        for pos in validation:
            manifest.append(dict(scheme=scheme, seed=seed, fold=fold, ID_parcela=meta.iloc[pos].ID_POLIGONO))
    pd.DataFrame(manifest).to_csv(OUT / 'outer-folds.csv', index=False)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(evaluate_job, job) for job in work]
        for i, future in enumerate(as_completed(futures), 1):
            print(f'{i}/{len(work)} {future.result()}', flush=True)


def paired_bootstrap(rows, candidate, block=False):
    frame = rows.copy()
    frame['delta'] = abs(frame.actual - frame[candidate]) - abs(frame.actual - frame.incumbent)
    # Repetitions are not independent observations: collapse each plot first.
    frame = frame.groupby(['ID_parcela', 'block20'], as_index=False).delta.mean()
    rng = np.random.default_rng(20261018)
    if block:
        chunks = [g.delta.to_numpy() for _, g in frame.groupby('block20')]
        draws = [np.concatenate([chunks[i] for i in rng.integers(len(chunks), size=len(chunks))]).mean() for _ in range(5000)]
    else:
        values = frame.delta.to_numpy()
        draws = values[rng.integers(len(values), size=(5000, len(values)))].mean(axis=1)
    return np.quantile(draws, [.025, .975]).tolist()


def decide():
    verify_frozen()
    meta, _ = load_data(ART)
    train_meta = meta.loc[meta.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True)
    records, summaries, state_rows, selection_rows = [], [], [], []
    for job in jobs(train_meta):
        scheme, size, seed, fold, _, _ = job
        path = OUT / 'folds' / f'{scheme}-{seed}-{fold}.json'
        result = json.loads(path.read_text(encoding='utf8'))
        for row in result['rows']:
            records.append(dict(scheme=scheme, seed=seed, fold=fold, **row))
        for procedure, selected in result['selected'].items():
            selection_rows.append(dict(scheme=scheme, seed=seed, fold=fold, procedure=procedure,
                                       candidate=selected['id'], inner_mae=selected['mae']))
    frame = pd.DataFrame(records)
    for (scheme, seed), rows in frame.groupby(['scheme', 'seed']):
        assert len(rows) == 138 and rows.ID_parcela.is_unique
        for name in PROCEDURES:
            summaries.append(dict(scheme=scheme, seed=int(seed), procedure=name, **legacy.metrics(rows.actual, rows[name])))
            for state, subset in rows.groupby('state'):
                state_rows.append(dict(scheme=scheme, seed=int(seed), procedure=name, state=state, **legacy.metrics(subset.actual, subset[name])))
    summary = pd.DataFrame(summaries)
    frame.to_csv(OUT / 'paired-oof.csv', index=False)
    summary.to_csv(OUT / 'metrics-by-seed.csv', index=False)
    pd.DataFrame(state_rows).to_csv(OUT / 'metrics-by-state.csv', index=False)
    pd.DataFrame(selection_rows).to_csv(OUT / 'selections.csv', index=False)
    # Exact reference reconciliation prevents judging a different baseline by accident.
    initial = frame.loc[frame.scheme.eq('parcel') & frame.seed.eq(SEEDS[0])].set_index('ID_parcela')
    stored = pd.read_csv(OUT / 'incumbent/validation-parcel.csv').set_index('ID_parcela')
    np.testing.assert_allclose(initial.loc[stored.index, 'incumbent'], stored.predicted, atol=1e-10, rtol=0)
    aggregate = []
    for (scheme, procedure), subset in summary.groupby(['scheme', 'procedure']):
        aggregate.append(dict(scheme=scheme, procedure=procedure, repeats=len(subset), mae=float(subset.mae.mean()),
                              rmse=float(np.sqrt(np.mean(subset.rmse**2))), r2=float(subset.r2.mean()), bias=float(subset.bias.mean())))
    aggregate = pd.DataFrame(aggregate)
    aggregate.to_csv(OUT / 'metrics-aggregate.csv', index=False)
    by_scheme = aggregate.set_index(['scheme', 'procedure'])
    parcel = frame.loc[frame.scheme.eq('parcel')]
    decisions = {}
    for candidate in ('point_original', 'point_extended'):
        current = summary.loc[summary.scheme.eq('parcel') & summary.procedure.eq(candidate)].set_index('seed')
        reference = summary.loc[summary.scheme.eq('parcel') & summary.procedure.eq('incumbent')].set_index('seed')
        gain = float(reference.mae.mean() - current.mae.mean())
        ci = paired_bootstrap(parcel, candidate)
        spatial_bad = [all(by_scheme.loc[(s, candidate), metric] > by_scheme.loc[(s, 'incumbent'), metric]
                           for metric in ('mae', 'rmse')) for s in ('spatial10', 'spatial20')]
        gates = dict(mean_mae_gain_at_least_001=gain >= .01,
                     lower_mae_in_at_least_four_seeds=int((current.mae < reference.mae).sum()) >= 4,
                     no_pooled_rmse_increase=float(np.mean(current.rmse**2)) <= float(np.mean(reference.rmse**2)),
                     no_consistent_deterioration_at_both_spatial_scales=not all(spatial_bad),
                     descriptive_paired_parcel_ci_upper_below_zero=ci[1] < 0)
        decisions[candidate] = dict(eligible=all(gates.values()), gates=gates, mae_gain_t_ha=gain,
                                   improved_seeds=int((current.mae < reference.mae).sum()),
                                   delta_mae_ci95_parcel_descriptive=ci,
                                   delta_mae_ci95_block20_descriptive=paired_bootstrap(parcel, candidate, True))
    chosen = 'incumbent'
    if decisions['point_original']['eligible']:
        chosen = 'point_original'
    if decisions['point_extended']['eligible'] and (chosen == 'incumbent' or
            by_scheme.loc[('parcel', 'point_extended'), 'mae'] <= by_scheme.loc[('parcel', 'point_original'), 'mae'] - .01):
        chosen = 'point_extended'
    decision = dict(created_at=datetime.now(timezone.utc).isoformat(), selected_procedure=chosen,
                    candidates=decisions, production_modified=False, reference_reproduced_atol=1e-10,
                    limits='Exploratory reused labels. No claim that hidden accuracy improved; bootstrap is descriptive and does not correct CV/model-selection dependence.')
    write_json(OUT / 'decision.json', decision)
    print(aggregate.to_string(index=False), flush=True)
    print(json.dumps(decision, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--evaluate', action='store_true')
    parser.add_argument('--decide', action='store_true')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.evaluate:
        evaluate(args.workers)
    if args.decide:
        decide()
