"""Paired, nested audit of one prespecified refinement; never changes production.

Run from platform: .venv/Scripts/python.exe scripts/evaluate_refinements.py
The original folds have already been inspected. Even the additional seed reuses
the same 138 labels: these are exploratory sensitivity results, not a blind test.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import sys
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, GroupKFold

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from pipeline import train as training

OUT = BASE / 'artifacts' / 'refinement-audit'
SEEDS = [20261013, 20261014]


def compact_columns(matrix):
    return [c for c in matrix if c.startswith(('PREC', 'Tmin', 'Tmax', 'thermal'))]


def select_compact(matrix, y, fit, groups, baseline_selection):
    """Only two extra candidates; no duplicate cloud variants for climate."""
    splitter = (GroupKFold(min(3, len(np.unique(groups[fit])))) if groups is not None
                else KFold(3, shuffle=True, random_state=training.SEED))
    splits = list(splitter.split(fit, groups=groups[fit] if groups is not None else None))
    scores = [dict(baseline_selection, feature_group='all')]
    for alpha in [10, 100]:
        predictions, actual = [], []
        for tr, va in splits:
            model = training.pipeline(Ridge(alpha=alpha), 'all')
            model.fit(matrix.iloc[fit[tr]], y[fit[tr]])
            predictions.extend(training.predict_nonnegative(model, matrix.iloc[fit[va]]))
            actual.extend(y[fit[va]])
        scores.append({'name': f'climate_ridge_{alpha}', 'cloud': 20, 'k': 'all',
                       'feature_group': 'climate', 'alpha': alpha,
                       **training.metrics(actual, np.array(predictions))})
    scores.sort(key=lambda s: (s['mae'], s['rmse'], s['name'], s['cloud']))
    best = scores[0]
    model = None
    if best['feature_group'] == 'climate':
        model = training.pipeline(Ridge(alpha=best['alpha']), 'all').fit(matrix.iloc[fit], y[fit])
    return model, best, scores


def paired_interval(rows, cluster=False):
    """Descriptive paired bootstrap: new MAE minus original MAE, same parcels.

    Block bootstrap is sensitivity only: there are only six spatial blocks.
    Neither bootstrap corrects reuse of labels, CV dependencies or selection.
    """
    rng = np.random.default_rng(20261014)
    delta = abs(rows.actual - rows.refined) - abs(rows.actual - rows.original)
    draws = []
    if cluster:
        blocks = rows.block.unique()
        chunks = [delta[rows.block.eq(b)].to_numpy() for b in blocks]
        for _ in range(3000):
            draws.append(np.concatenate([chunks[j] for j in rng.integers(len(blocks), size=len(blocks))]).mean())
    else:
        for _ in range(3000):
            draws.append(delta.to_numpy()[rng.integers(len(rows), size=len(rows))].mean())
    return np.quantile(draws, [.025, .975]).tolist()


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = {
        'status': 'exploratory_after_initial_audit_not_blind',
        'primary_metric': 'MAE; RMSE and spatial transfer are guardrails',
        'seeds': SEEDS,
        'original': '18 existing cloud/model candidates; original fit/calibration split',
        'refinement': 'same 18 candidates plus Ridge alpha=10/100 on climate only; all climate columns, selected only inside inner CV',
        'unchanged': ['target', 'features extraction', 'cloud variants', 'outer folds', 'fit/calibration split', 'nonnegative predictions'],
        'promotion_rule': 'No automatic promotion. Require lower MAE on both seeds, no higher RMSE on either, no material spatial deterioration, and paired parcel and block bootstrap MAE upper limits below zero on both random seeds. These are conservative exploratory screens, not proof of generalization.',
        'forbidden': ['tuning against hidden predictions', 'refitting conformal model on calibration labels', 'post-hoc bias correction'],
    }
    (OUT / 'protocol.json').write_text(json.dumps(protocol, ensure_ascii=False, indent=2), encoding='utf-8')
    metadata = pd.read_csv(BASE / 'artifacts/parcels.csv')
    metadata = metadata.loc[metadata.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True)
    y = metadata.RENDIMIENTO_T_HA.to_numpy()
    matrices = {}
    for cloud in [20, 40, 60]:
        matrix = pd.read_csv(BASE / f'artifacts/features-cloud-{cloud}.csv', index_col='ID_POLIGONO')
        matrices[cloud] = matrix.loc[metadata.ID_POLIGONO].reset_index(drop=True)
    compact = matrices[20][compact_columns(matrices[20])]
    blocks = (np.floor(metadata.x_m / 20000).astype(int).astype(str) + '_' +
              np.floor(metadata.y_m / 20000).astype(int).astype(str)).to_numpy()
    summaries = []
    records = []
    for spatial in [False, True]:
        # Spatial outer folds stay fixed; seed changes calibration group allocation,
        # inner random partitions (parcel only), and estimator randomness.
        for seed in SEEDS:
            training.SEED = seed
            groups = blocks if spatial else None
            splitter = GroupKFold(5) if spatial else KFold(5, shuffle=True, random_state=seed)
            fold_details = []
            for fold, (train, validation) in enumerate(splitter.split(metadata, groups=groups), 1):
                fit, calibration = training.training_indices(train, groups, seed=seed + fold)
                original, selected, _ = training.select_model(matrices, y, fit, groups)
                new_model, new_selected, scores = select_compact(compact, y, fit, groups, selected)
                original_prediction = training.predict_nonnegative(original, matrices[selected['cloud']].iloc[validation])
                if new_model is None:
                    refined_prediction = original_prediction
                else:
                    refined_prediction = training.predict_nonnegative(new_model, compact.iloc[validation])
                fold_details.append({'fold': fold, 'fit_n': len(fit), 'calibration_n': len(calibration),
                                     'original_selection': selected, 'refined_selection': new_selected,
                                     'inner_scores': scores})
                for j, pos in enumerate(validation):
                    records.append({'scheme': 'spatial' if spatial else 'parcel', 'seed': seed, 'fold': fold,
                                    'ID_parcela': metadata.iloc[pos].ID_POLIGONO, 'block': blocks[pos],
                                    'actual': y[pos], 'original': original_prediction[j], 'refined': refined_prediction[j]})
                print(f'{"spatial" if spatial else "parcel"} seed={seed} fold={fold}: {selected["name"]} -> {new_selected["name"]}', flush=True)
            rows = pd.DataFrame([r for r in records if r['seed'] == seed and r['scheme'] == ('spatial' if spatial else 'parcel')])
            summaries.append({'scheme': 'spatial' if spatial else 'parcel', 'seed': seed,
                              'original': training.metrics(rows.actual, rows.original),
                              'refined': training.metrics(rows.actual, rows.refined),
                              'delta_mae_ci95_parcel_descriptive': paired_interval(rows),
                              'delta_mae_ci95_block_descriptive': paired_interval(rows, cluster=True),
                              'folds': fold_details})
            (OUT / 'results.json').write_text(json.dumps(summaries, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
            pd.DataFrame(records).to_csv(OUT / 'paired-oof.csv', index=False)
    parcel_results = [r for r in summaries if r['scheme'] == 'parcel']
    spatial_results = [r for r in summaries if r['scheme'] == 'spatial']
    gates = {
        'lower_parcel_mae_on_both_seeds': all(r['refined']['mae'] < r['original']['mae'] for r in parcel_results),
        'no_higher_parcel_rmse_on_either_seed': all(r['refined']['rmse'] <= r['original']['rmse'] for r in parcel_results),
        'parcel_bootstrap_upper_limits_below_zero': all(r['delta_mae_ci95_parcel_descriptive'][1] < 0 for r in parcel_results),
        'block_bootstrap_upper_limits_below_zero': all(r['delta_mae_ci95_block_descriptive'][1] < 0 for r in parcel_results),
        'no_higher_spatial_mae_or_rmse': all(r['refined'][m] <= r['original'][m] for r in spatial_results for m in ['mae', 'rmse']),
    }
    decision = {'decision': 'retain_original' if not all(gates.values()) else 'review_before_promotion',
                'gates': gates, 'production_mutated_by_script': False,
                'interpretation': 'Exploratory sensitivity on reused labels; no superiority claim for the 59 hidden yields.'}
    (OUT / 'decision.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')
    fingerprints = {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in [BASE / 'pipeline/train.py', BASE / 'scripts/evaluate_refinements.py',
                              BASE / 'artifacts/parcels.csv', *[BASE / f'artifacts/features-cloud-{c}.csv' for c in [20, 40, 60]]]}
    (OUT / 'input-hashes.json').write_text(json.dumps(fingerprints, indent=2), encoding='utf-8')
    for result in summaries:
        print(json.dumps({k: v for k, v in result.items() if k != 'folds'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()
