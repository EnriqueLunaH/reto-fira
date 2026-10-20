import csv
import io
import json
from pathlib import Path
import re
import joblib
import numpy as np
import pandas as pd
import pytest
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box
from app import create_app
from pipeline.features import clean_satellite, zonal_mean, ARTIFACTS, ROOT
from pipeline.train import conformal_quantile


@pytest.fixture
def client():
    return create_app({'TESTING': True, 'SECRET_KEY': 'only-for-tests'}).test_client()


def login(client, role):
    client.get('/login/' + role)
    with client.session_transaction() as session:
        token = session['csrf_token']
    email, password = ('ejemploproductor@ejemplo.com', '123Productor#') if role == 'productor' else ('ejemplotecnico@ejemplo.com', '123Tecnico#')
    return client.post('/login/' + role, data={'email': email, 'password': password, 'csrf_token': token})


def test_authentication_roles_and_csrf(client):
    assert client.get('/api/parcels').status_code == 401
    assert client.get('/export/predictions.csv').status_code == 302
    assert client.post('/login/productor', data={'email':'ejemploproductor@ejemplo.com','password':'123Productor#'}).status_code == 400
    assert login(client, 'productor').status_code == 302
    assert client.get('/api/parcels').status_code == 200
    assert client.get('/api/dashboard').status_code == 403
    assert client.get('/staff').status_code == 403
    assert client.get('/export/predictions.csv').status_code == 403
    assert client.post('/logout').status_code == 400
    with client.session_transaction() as session:
        token=session['csrf_token']
    assert client.post('/logout', data={'csrf_token':token}).status_code == 302
    assert client.get('/api/parcels').status_code == 401


def test_submission_has_exact_hidden_ids_four_decimals_and_model_values(client):
    labels = pd.read_csv(ROOT/'data/fira/CSV-files/ID_area_rendimiento_70_30_Reto_AgroCebada.csv')
    hidden = set(labels.loc[labels.CONJUNTO.eq('PREDICCION'), 'ID_POLIGONO'])
    file_rows = list(csv.DictReader((ARTIFACTS/'predicciones_59.csv').open()))
    assert len(file_rows) == 59
    assert {r['ID_parcela'] for r in file_rows} == hidden
    assert all(re.fullmatch(r'\d+\.\d{4}', r['Rendimiento_predicho_t_ha']) for r in file_rows)
    assert login(client, 'staff').status_code == 302
    response=client.get('/export/predictions.csv')
    assert list(csv.DictReader(io.StringIO(response.text))) == file_rows
    model=joblib.load(ARTIFACTS/'model.joblib')
    features=pd.read_csv(ARTIFACTS/f'features-cloud-{model["cloud_threshold"]}.csv').set_index('ID_POLIGONO')
    x=features.loc[[r['ID_parcela'] for r in file_rows],model['columns']]
    pred=np.maximum(model['pipeline'].predict(x),0)
    np.testing.assert_allclose(pred, [float(r['Rendimiento_predicho_t_ha']) for r in file_rows], atol=.00005)
    assert not hidden.intersection(model['fit_ids']+model['calibration_ids'])
    assert not set(model['fit_ids']).intersection(model['calibration_ids'])
    report=json.loads((ARTIFACTS/'metrics.json').read_text(encoding='utf8'))
    if report['interval']['method']=='not_estimated':
        assert len(model['fit_ids'])==138 and model['calibration_ids']==[]
        assert model['radius'] is None
        dashboard=client.get('/api/dashboard').json
        assert all(p['lower'] is None and p['upper'] is None for p in dashboard['parcels'])
        assert report['n_fit']==138 and report['n_calibration']==0
    else:
        assert len(model['fit_ids'])==110 and len(model['calibration_ids'])==28


def test_export_filters_and_geometry_scope(client):
    login(client,'staff')
    parcels=client.get('/api/parcels?state=Puebla&search=AGC_011').json
    assert [p['id'] for p in parcels] == ['AGC_011']
    rows=list(csv.DictReader(io.StringIO(client.get('/export/predictions.csv?state=Puebla&search=AGC_011').text)))
    assert [r['ID_parcela'] for r in rows] == ['AGC_011']
    assert client.get('/api/parcels?state=Desconocido').status_code==400
    assert len(client.get('/api/geometry').json['features'])==59
    assert client.get('/api/parcels/AGC_001').status_code==404
    assert client.get('/api/dashboard').status_code==200


def test_cloud_zero_is_valid_and_hundred_is_not_zero_imputed():
    frame=pd.DataFrame({'ID_POLIGONO':['AGC_001']*5,'fecha_captura':['15/06/2025']*4+['01/11/2025'],
                        'porcentaje_nubosidad':[0,100,30,np.nan,0], 'ndvi_promedio':[.6,np.nan,.4,.5,.9]})
    retained=clean_satellite(frame,40)
    assert retained.porcentaje_nubosidad.tolist()==[0,30]
    assert retained.ndvi_promedio.tolist()==[.6,.4]


def test_area_weighted_zonal_mean_and_nodata():
    with MemoryFile() as memory:
        with memory.open(driver='GTiff',height=1,width=2,count=1,dtype='float32',crs='EPSG:6372',
                         transform=from_origin(0,1,1,1),nodata=-9999) as raster:
            raster.write(np.array([[[10,30]]],dtype='float32'))
            mean,coverage,pixels=zonal_mean(raster,box(.5,0,2,1))
            assert mean==pytest.approx((10*.5+30*1)/1.5)
            assert coverage==pytest.approx(1) and pixels==2
            raster.write(np.array([[[-9999,30]]],dtype='float32'))
            mean,coverage,pixels=zonal_mean(raster,box(0,0,2,1))
            assert mean==30 and coverage==pytest.approx(.5)


def test_conformal_finite_sample_rank_and_oof_coverage():
    assert conformal_quantile(np.arange(28))==26
    assert conformal_quantile(np.arange(4))==float('inf')
    report=json.loads((ARTIFACTS/'metrics.json').read_text(encoding='utf8'))
    calibration=set(report['calibration_ids'])
    assert len(calibration)==report['n_calibration']
    assert not calibration.intersection(report['fit_ids'])
    for path in ['validation-parcel.csv','validation-spatial.csv']:
        rows=pd.read_csv(ARTIFACTS/path)
        assert len(rows)==138 and rows.ID_parcela.is_unique
        result=report['parcel_cv' if 'parcel' in path else 'spatial_cv']
        assert abs(rows.actual-rows.predicted).mean()==pytest.approx(result['model']['mae'])
        assert np.sqrt(((rows.actual-rows.predicted)**2).mean())==pytest.approx(result['model']['rmse'])
    if report['interval']['method']=='not_estimated':
        assert report['interval']['radius_t_ha'] is None
        assert report['parcel_cv']['coverage_90'] is None
        assert report['spatial_cv']['coverage_90'] is None
    else:
        assert report['interval']['radius_t_ha']>0
