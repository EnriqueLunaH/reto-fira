"""Read production inputs, write support and baseline diagnostics only under audit."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'refinement-audit'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0,str(ROOT))
from pipeline.train import metrics, training_indices, SEED

meta=pd.read_csv(ROOT/'artifacts/parcels.csv')
x=pd.read_csv(ROOT/'artifacts/features-cloud-60.csv').set_index('ID_POLIGONO').loc[meta.ID_POLIGONO]
labelled=meta.CONJUNTO.eq('ENTRENAMIENTO').to_numpy()
climate=x.columns.str.startswith(('PREC','Tmin','Tmax','thermal'))
patterns=x.loc[:,climate].round(6).apply(tuple,axis=1)
distances=cdist(meta.loc[~labelled,['x_m','y_m']],meta.loc[labelled,['x_m','y_m']]).min(axis=1)
cor=x.loc[labelled].corr().abs()
unique_pairs=cor.where(np.triu(np.ones(cor.shape),1).astype(bool)).stack()
blocks=(np.floor(meta.x_m/20000).astype(int).astype(str)+'_'+np.floor(meta.y_m/20000).astype(int).astype(str))
train=meta.loc[labelled].reset_index(drop=True)
y=train.RENDIMIENTO_T_HA.to_numpy()
state=train.Estado.to_numpy()
records=[]
for fold,(tr,va) in enumerate(KFold(5,shuffle=True,random_state=SEED).split(train),1):
    fit,_=training_indices(tr,seed=SEED+fold)
    medians={st:np.median(y[fit][state[fit]==st]) for st in np.unique(state[fit])}
    fallback=np.median(y[fit])
    for pos in va:
        records.append({'ID_POLIGONO':train.iloc[pos].ID_POLIGONO,'fold':fold,'actual':y[pos],'state_median':float(medians.get(state[pos],fallback)),'global_median':float(fallback)})
rows=pd.DataFrame(records)
rows.to_csv(OUT/'state-baseline-oof.csv',index=False)
out={'n_features':x.shape[1],
     'n_climate_features':int(climate.sum()),
     'n_climate_unique_training_patterns':int(patterns[labelled].nunique()),
     'hidden_climate_pattern_unseen_n':sum(z not in set(patterns[labelled]) for z in patterns[~labelled]),
     'nearest_labelled_centroid_distance_m_quantiles':dict(zip(['min','median','p90','max'],np.quantile(distances,[0,.5,.9,1]).tolist())),
     'n_training_feature_pairs_abs_corr_gt_098':int((unique_pairs>.98).sum()),
     'spatial_20km_blocks_all':blocks.value_counts().to_dict(),
     'spatial_20km_blocks_training':blocks[labelled].value_counts().to_dict(),
     'state_median_oof':metrics(rows.actual,rows.state_median),
     'global_median_oof':metrics(rows.actual,rows.global_median)}
(OUT/'support-summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(out,ensure_ascii=False,indent=2))

