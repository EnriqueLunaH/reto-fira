"""Independent arithmetic/partition checks of the completed experiment."""
import json
from pathlib import Path
import sys
import hashlib
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'artifacts/model-refinement-v2'


def verify():
    meta = pd.read_csv(BASE / 'artifacts/parcels.csv').set_index('ID_POLIGONO')
    train_ids = set(meta.index[meta.CONJUNTO.eq('ENTRENAMIENTO')])
    hidden_ids = set(meta.index[meta.CONJUNTO.eq('PREDICCION')])
    rows = pd.read_csv(OUT / 'paired-oof.csv')
    metrics = pd.read_csv(OUT / 'metrics-by-seed.csv')
    maximum_difference = 0.
    for (scheme, seed), frame in rows.groupby(['scheme', 'seed']):
        assert len(frame) == 138 and frame.ID_parcela.is_unique
        assert set(frame.ID_parcela) == train_ids
        np.testing.assert_array_equal(frame.actual, meta.loc[frame.ID_parcela].RENDIMIENTO_T_HA)
        for _, item in metrics.loc[metrics.scheme.eq(scheme) & metrics.seed.eq(seed)].iterrows():
            error = frame[item.procedure].to_numpy() - frame.actual.to_numpy()
            observed = frame.actual.to_numpy()
            independent = dict(mae=np.abs(error).sum()/len(error), rmse=np.sqrt(np.dot(error, error)/len(error)),
                               bias=error.sum()/len(error), r2=1-np.dot(error,error)/np.dot(observed-observed.mean(), observed-observed.mean()))
            for name, value in independent.items():
                maximum_difference = max(maximum_difference, abs(value-item[name]))
                assert abs(value-item[name]) < 1e-10
    folds = list((OUT / 'folds').glob('*.json'))
    assert len(folds) == 35
    for path in folds:
        fold = json.loads(path.read_text(encoding='utf8'))
        train, val = set(fold['training_ids']), set(fold['validation_ids'])
        fit, cal = set(fold['incumbent_fit_ids']), set(fold['incumbent_calibration_ids'])
        assert not train & val and train | val == train_ids
        assert not fit & cal and fit | cal == train
        assert not hidden_ids & (train | val)
        if fold['scheme'].startswith('spatial'):
            size = 10000 if fold['scheme'] == 'spatial10' else 20000
            def groups(ids):
                xy = np.floor(meta.loc[sorted(ids), ['x_m','y_m']].to_numpy()/size).astype(int)
                return set(map(tuple, xy))
            assert not groups(train) & groups(val)
            assert not groups(fit) & groups(cal)
        for split in fold['inner_splits']:
            a, b = set(split['train_ids']), set(split['validation_ids'])
            assert not a & b and a | b == train and not (a | b) & val
            if fold['scheme'].startswith('spatial'):
                assert not groups(a) & groups(b)
        best = min(fold['inner_scores'], key=lambda s: (s['mae'], s['rmse'], s['id']))
        assert best['id'] == fold['selected']['point_extended']['id']
    for rel, digest in json.loads((OUT/'input-hashes.json').read_text()).items():
        assert hashlib.sha256((BASE/rel).read_bytes()).hexdigest() == digest
    for name, digest in json.loads((OUT/'incumbent-hashes.json').read_text()).items():
        assert hashlib.sha256((OUT/'incumbent'/name).read_bytes()).hexdigest() == digest
    output = dict(status='passed', folds_verified=35, oof_rows=len(rows), unique_labelled_plots=len(train_ids),
                  hidden_label_use=False, metric_rows_verified=len(metrics), maximum_metric_difference=maximum_difference,
                  grouped_splits_verified=True, frozen_inputs_unchanged=True, incumbent_backup_unchanged=True,
                  limitations='Arithmetic and partition verification; does not establish independence or hidden accuracy.')
    (OUT/'verification.json').write_text(json.dumps(output, indent=2), encoding='utf8')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    verify()
