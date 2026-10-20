"""Exploratory paired diagnostics; no writes to production artifacts.

Recipes frozen before execution; this is not an independent final validation.
"""
from pathlib import Path
import json
import sys
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.train import pipeline, predict_nonnegative, metrics, training_indices, SEED

OUT = ROOT / 'artifacts' / 'refinement-audit'
OUT.mkdir(parents=True, exist_ok=True)
meta = pd.read_csv(ROOT / 'artifacts/parcels.csv')
meta = meta.loc[meta.CONJUNTO.eq('ENTRENAMIENTO')].reset_index(drop=True)
y = meta.RENDIMIENTO_T_HA.to_numpy()
matrices = {c: pd.read_csv(ROOT / f'artifacts/features-cloud-{c}.csv').set_index('ID_POLIGONO').loc[meta.ID_POLIGONO].reset_index(drop=True) for c in [20,60]}
climate = [c for c in matrices[60].columns if c.startswith(('PREC', 'Tmin', 'Tmax', 'thermal'))]

def raw_pipeline(estimator):
    return Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
                     ('variance', VarianceThreshold()), ('scale', StandardScaler()), ('model', estimator)])

def build(recipe):
    if recipe == 'existing_rf60':
        return matrices[60], pipeline(RandomForestRegressor(n_estimators=180,min_samples_leaf=4,max_features=.8,random_state=SEED,n_jobs=2),60)
    if recipe == 'existing_ridge20':
        return matrices[20], pipeline(Ridge(alpha=10),30)
    if recipe == 'climate_ridge10':
        return matrices[60][climate], raw_pipeline(Ridge(alpha=10))
    if recipe == 'climate_rf':
        return matrices[60][climate], raw_pipeline(RandomForestRegressor(n_estimators=180,min_samples_leaf=4,max_features=.8,random_state=SEED,n_jobs=2))
    raise ValueError(recipe)

started = time.perf_counter()
rows=[]
for seed in [SEED, SEED+101]:
    for fold,(train,test) in enumerate(KFold(5,shuffle=True,random_state=seed).split(meta),1):
        fit,_ = training_indices(train,seed=SEED+fold)
        for recipe in ['existing_rf60','existing_ridge20','climate_ridge10','climate_rf']:
            for mode, fitting in [('reserve_calibration',fit),('all_outer_train',train)]:
                x,model=build(recipe)
                model.fit(x.iloc[fitting],y[fitting])
                pred=predict_nonnegative(model,x.iloc[test])
                for pos,p in zip(test,pred):
                    rows.append({'seed':seed,'fold':fold,'recipe':recipe,'fit_mode':mode,'fit_n':len(fitting),'ID_POLIGONO':meta.iloc[pos].ID_POLIGONO,'state':meta.iloc[pos].Estado,'actual':y[pos],'predicted':p})
        print(f'seed {seed}, fold {fold}: completed',flush=True)
frame=pd.DataFrame(rows)
frame.to_csv(OUT/'fixed-recipe-oof.csv',index=False)
summary=[]
for (seed,recipe,mode),g in frame.groupby(['seed','recipe','fit_mode']):
    summary.append({'seed':int(seed),'recipe':recipe,'fit_mode':mode,**metrics(g.actual,g.predicted)})
paired=[]
for (seed,mode),g in frame.groupby(['seed','fit_mode']):
    p=g.pivot(index='ID_POLIGONO',columns='recipe',values='predicted')
    truth=g.drop_duplicates('ID_POLIGONO').set_index('ID_POLIGONO').actual.loc[p.index]
    rng=np.random.default_rng(SEED)
    for recipe in p.columns:
        delta=(abs(p[recipe]-truth)-abs(p.existing_rf60-truth)).to_numpy()
        boots=delta[rng.integers(0,len(delta),size=(5000,len(delta)))].mean(axis=1)
        paired.append({'seed':int(seed),'fit_mode':mode,'recipe':recipe,'mae_delta_vs_rf':float(delta.mean()),'paired_bootstrap_95':np.quantile(boots,[.025,.975]).tolist()})
result={'purpose':'Exploratory fixed-recipe diagnostics; do not select final recipe on these outer outcomes','n':len(y),'climate_features':climate,'elapsed_seconds':time.perf_counter()-started,'summary':summary,'paired':paired}
(OUT/'fixed-recipe-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

