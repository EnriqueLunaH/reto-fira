from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_window
from shapely.geometry import box, mapping
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/fira'
ARTIFACTS = ROOT / 'platform/artifacts'
GEOD = Geod(ellps='WGS84')
INDICES = {
    'Sentinel-2': ['ndvi', 'evi', 'lai', 'ndwi', 'msi', 'dswi2', 'dswi5'],
    'Planet': ['ndvi', 'evi', 'lai', 'msavi'],
    'Landsat': ['vi6t'],
}


def area(geometry, geographic):
    if geometry.is_empty:
        return 0.0
    return abs(GEOD.geometry_area_perimeter(geometry)[0]) if geographic else geometry.area


def zonal_mean(src, geometry):
    """Exact polygon/cell intersections, weighted by area; never zero-fill NoData."""
    window = geometry_window(src, [mapping(geometry)])
    values = src.read(1, window=window, masked=True)
    transform = src.window_transform(window)
    geographic = src.crs.is_geographic
    weights, data = [], []
    total_area = area(geometry, geographic)
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            if np.ma.is_masked(values[row, col]) or not np.isfinite(values[row, col]):
                continue
            x0, y0 = transform * (col, row)
            x1, y1 = transform * (col + 1, row + 1)
            intersection = geometry.intersection(box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
            weight = area(intersection, geographic)
            if weight > 0:
                weights.append(weight)
                data.append(float(values[row, col]))
    if not weights:
        return np.nan, 0.0, 0
    return float(np.average(data, weights=weights)), min(sum(weights) / total_area, 1.0), len(weights)


def load_parcels():
    labels = pd.read_csv(DATA / 'CSV-files/ID_area_rendimiento_70_30_Reto_AgroCebada.csv').dropna(axis=1, how='all')
    plots = gpd.read_file(DATA / 'plots/Parcelas_Reto_AGC_CONJUNTO.shp').rename(columns={'ID_POLIGON': 'ID_POLIGONO'})
    assert labels.ID_POLIGONO.is_unique and plots.ID_POLIGONO.is_unique
    assert set(labels.ID_POLIGONO) == set(plots.ID_POLIGONO)
    assert plots.geometry.is_valid.all() and not plots.geometry.is_empty.any()
    assert labels.CONJUNTO.value_counts().to_dict() == {'ENTRENAMIENTO': 138, 'PREDICCION': 59}
    assert labels.loc[labels.CONJUNTO.eq('PREDICCION'), 'RENDIMIENTO_T_HA'].isna().all()
    assert labels.loc[labels.CONJUNTO.eq('ENTRENAMIENTO'), 'RENDIMIENTO_T_HA'].notna().all()
    plots = plots.set_index('ID_POLIGONO').loc[labels.ID_POLIGONO].reset_index()
    assert np.array_equal(plots.CONJUNTO, labels.CONJUNTO)
    parcels = plots[['ID_POLIGONO', 'Estado', 'Municipio', 'geometry']].merge(labels, validate='one_to_one')
    parcels = gpd.GeoDataFrame(parcels, crs=plots.crs).to_crs(4326)
    centers = parcels.to_crs(6372).centroid
    geographic = gpd.GeoSeries(centers, crs=6372).to_crs(4326)
    parcels['longitude'], parcels['latitude'] = geographic.x.values, geographic.y.values
    parcels['x_m'], parcels['y_m'] = centers.x.values, centers.y.values
    return parcels


def extract_environment(parcels, force=False):
    cache = ARTIFACTS / 'environment.csv'
    coverage_path = ARTIFACTS / 'raster-coverage.csv'
    if cache.exists() and coverage_path.exists() and not force:
        return pd.read_csv(cache, float_precision='round_trip').set_index('ID_POLIGONO')
    paths = sorted(DATA.rglob('*.tif'))
    assert len(paths) == 146, f'Expected 146 rasters, found {len(paths)}'
    values_by_name, coverage_by_name = {}, {}
    projections, audit = {}, []
    for i, path in enumerate(paths):
        name = path.stem
        if name.startswith('Elevacion'):
            name = 'elevation_m'
        elif name.startswith('Pendiente'):
            name = 'slope_deg'
        with rasterio.open(path) as src:
            key = src.crs.to_string()
            if key not in projections:
                projections[key] = parcels.to_crs(src.crs).geometry.tolist()
            summaries = [zonal_mean(src, geom) for geom in projections[key]]
            values_by_name[name] = [v[0] if v[1] >= .8 else np.nan for v in summaries]
            coverage_by_name[name] = [v[1] for v in summaries]
            audit.append({'file': str(path.relative_to(ROOT)), 'feature': name, 'crs': key,
                          'resolution': list(src.res), 'nodata': src.nodata,
                          'min_coverage': min(v[1] for v in summaries),
                          'missing_parcels': sum(not np.isfinite(v[0]) for v in summaries),
                          'below_80pct_coverage': sum(v[1] < .8 for v in summaries),
                          'min_pixels': min(v[2] for v in summaries), 'max_pixels': max(v[2] for v in summaries)})
        if i % 24 == 0:
            print(f'Raster {i+1}/146: {name}', flush=True)
    result = pd.DataFrame(values_by_name, index=parcels.ID_POLIGONO)
    result.to_csv(cache)
    pd.DataFrame(coverage_by_name, index=parcels.ID_POLIGONO).to_csv(coverage_path)
    (ARTIFACTS / 'raster-audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    return result


def climate_features(environment):
    out = environment[['elevation_m', 'slope_deg']].copy()
    for variable in ['PREC', 'Tmin', 'Tmax']:
        for month in range(4, 11):
            out[f'{variable}_2025_{month:02}'] = environment[f'{variable}_2025_{month:02}']
        for year in range(2022, 2026):
            columns = [f'{variable}_{year}_{m:02}' for m in range(4, 11)]
            vals = environment[columns]
            out[f'{variable}_season_{year}'] = vals.sum(axis=1, min_count=7) if variable == 'PREC' else vals.mean(axis=1)
        historic = out[[f'{variable}_season_{y}' for y in range(2022, 2025)]].mean(axis=1)
        out[f'{variable}_history_mean'] = historic
        out[f'{variable}_anomaly_2025'] = out[f'{variable}_season_2025'] - historic
        out = out.drop(columns=[f'{variable}_season_{y}' for y in range(2022, 2025)])
    for month in range(4, 11):
        out[f'thermal_range_{month:02}'] = out[f'Tmax_2025_{month:02}'] - out[f'Tmin_2025_{month:02}']
    out['PREC_early'] = environment[[f'PREC_2025_{m:02}' for m in [4, 5, 6]]].sum(axis=1, min_count=3)
    out['PREC_mid'] = environment[[f'PREC_2025_{m:02}' for m in [7, 8]]].sum(axis=1, min_count=2)
    out['PREC_late'] = environment[[f'PREC_2025_{m:02}' for m in [9, 10]]].sum(axis=1, min_count=2)
    return out


def clean_satellite(frame, threshold):
    df = frame.drop_duplicates().copy()
    df['date'] = pd.to_datetime(df.fecha_captura, format='%d/%m/%Y', errors='raise')
    df = df.loc[df.date.between('2025-04-01', '2025-10-31')].copy()
    df = df.loc[df.porcentaje_nubosidad.between(0, threshold)].copy()
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    # Reflectance normalized differences are in [-1,1]. Ratios/EVI have no universal [-1,1] bound.
    for index in ['ndvi', 'ndwi']:
        col = f'{index}_promedio'
        if col in df:
            df.loc[~df[col].between(-1, 1), col] = np.nan
    df['month'] = df.date.dt.month
    return df


def satellite_features(basic, pro, parcel_ids, threshold):
    parcel_index = pd.Index(parcel_ids, name='ID_POLIGONO')
    values_by_name = {}
    audit, histories = [], []
    for sensor, indices in INDICES.items():
        source = pro if sensor == 'Planet' else basic.loc[basic.sensor.eq(sensor)]
        df = clean_satellite(source, threshold)
        prefix = sensor.lower().replace('-', '')
        cols = [f'{i}_promedio' for i in indices]
        monthly = df.groupby(['ID_POLIGONO', 'month'])[cols].median()
        for index, col in zip(indices, cols):
            pivot = monthly[col].unstack('month').reindex(index=parcel_index, columns=range(4, 11))
            for month in range(4, 11):
                values_by_name[f'{prefix}_{index}_{month:02}'] = pivot[month]
            values_by_name[f'{prefix}_{index}_mean'] = pivot.mean(axis=1)
            values_by_name[f'{prefix}_{index}_peak'] = pivot.max(axis=1)
            values_by_name[f'{prefix}_{index}_spread'] = pivot.std(axis=1)
            values_by_name[f'{prefix}_{index}_late_change'] = pivot[[9, 10]].mean(axis=1) - pivot[[6, 7, 8]].mean(axis=1)
        # Each month has equal weight; frequent acquisitions cannot dominate the entire season.
        key = 'vi6t_promedio' if sensor == 'Landsat' else 'ndvi_promedio'
        usable = df.loc[df[key].notna()]
        values_by_name[f'{prefix}_observations'] = usable.groupby('ID_POLIGONO').size().reindex(parcel_index, fill_value=0)
        values_by_name[f'{prefix}_months'] = usable.groupby('ID_POLIGONO').month.nunique().reindex(parcel_index, fill_value=0)
        audit.append({'sensor': sensor, 'threshold': threshold, 'source_rows': len(source),
                      'season_rows': int(pd.to_datetime(source.fecha_captura, format='%d/%m/%Y').between('2025-04-01','2025-10-31').sum()),
                      'retained_rows': len(df), 'usable_main_index': len(usable),
                      'clear_zero_usable': int((usable.porcentaje_nubosidad == 0).sum()),
                      'no_main_index_parcels': int((values_by_name[f'{prefix}_months'] == 0).sum())})
        for (pid, month), row in monthly.iterrows():
            histories.append({'id': pid, 'month': int(month), 'sensor': sensor,
                              **{col.replace('_promedio',''): None if pd.isna(row[col]) else float(row[col]) for col in cols}})
    return pd.DataFrame(values_by_name, index=parcel_index), audit, histories


def build_features(force=False):
    ARTIFACTS.mkdir(exist_ok=True)
    parcels = load_parcels()
    environment = extract_environment(parcels, force)
    climate = climate_features(environment)
    basic = pd.read_csv(DATA / 'CSV-files/Conjunto_datos_BASICO_AgroCebada2026.csv')
    pro = pd.read_csv(DATA / 'CSV-files/Conjunto_datos_PRO_AgroCebada.csv')
    assert set(basic.ID_POLIGONO) <= set(parcels.ID_POLIGONO)
    assert set(pro.ID_POLIGONO) <= set(parcels.ID_POLIGONO)
    matrices, audits, histories = {}, {}, {}
    for threshold in [20, 40, 60]:
        satellite, audit, history = satellite_features(basic, pro, parcels.ID_POLIGONO, threshold)
        frame = climate.join(satellite)
        frame['area_ha'] = parcels.set_index('ID_POLIGONO').AREA_HA
        # Six decimals exceed source precision and stabilize cached/in-memory tree thresholds.
        frame = frame.round(6)
        # Location/state and ID are kept as metadata, never predictors.
        frame.to_csv(ARTIFACTS / f'features-cloud-{threshold}.csv')
        matrices[threshold], audits[threshold], histories[threshold] = frame, audit, history
    metadata = parcels.drop(columns='geometry')
    metadata.to_csv(ARTIFACTS / 'parcels.csv', index=False)
    (ARTIFACTS / 'cloud-audit.json').write_text(json.dumps(audits, indent=2), encoding='utf-8')
    parcels[['ID_POLIGONO','Estado','Municipio','CONJUNTO','geometry']].to_file(ARTIFACTS / 'parcels.geojson', driver='GeoJSON')
    return metadata, matrices, histories
