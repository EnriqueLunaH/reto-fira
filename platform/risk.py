"""Experimental economic scenarios over existing, frozen yield predictions.

This module never trains a model or infers a distribution from conformal bounds.
The empirical error scenarios describe a sensitivity exercise, not calibrated
future financial probabilities. See docs/riesgo-economico.md for provenance.
"""

import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


DRAWS = 20_000
SEED = 20261015
REFERENCE_PRICE = 7375.0
REFERENCE_RENT = 4893.0
BUDGET_RELATIVE_PATH = Path('data/fira/context/Cebada_TMF_Hidalgo_PV_2026.pdf')
BUDGET_PATH = Path(__file__).resolve().parent.parent / BUDGET_RELATIVE_PATH
BUDGET_SHA256 = 'ac1166eb9af0416871ec661cef61f5ef5c39a6ebd0b35c60788c26cd8de4b5b8'
PROFILES = {
    'small': {
        'id': 'small', 'label': 'Hasta 160,000 UDIS',
        'direct_cost_per_ha': 21504.0, 'interest_per_ha': 3357.0,
        'credit_per_ha': 19353.0, 'own_contribution_per_ha': 2150.0,
        'total_cost_per_ha': 24862.0,
    },
    'large': {
        'id': 'large', 'label': 'Mayor a 160,000 UDIS',
        'direct_cost_per_ha': 21504.0, 'interest_per_ha': 2984.0,
        'credit_per_ha': 17203.0, 'own_contribution_per_ha': 4301.0,
        'total_cost_per_ha': 24489.0,
    },
}
BASES = {
    'parcel': ('validation-parcel.csv', 'Errores de validación por parcela'),
    'spatial': ('validation-spatial.csv', 'Errores por bloques espaciales (estrés)'),
}
LIMITATIONS = [
    'Ejercicio retrospectivo: estimaciones del ciclo 2025 valoradas con un presupuesto PV 2026; no es un pronóstico de la campaña 2026.',
    'Frecuencias experimentales condicionadas a los errores elegidos; no son probabilidades calibradas de pérdidas futuras ni de impago.',
    'El presupuesto del Altiplano de Hidalgo requiere confirmar modalidad y tecnología. Los Agrocostos no son estadísticamente representativos.',
    'Los errores fuera de muestra corresponden al procedimiento de selección, no a una distribución condicional validada del modelo final. Un solo ciclo no mide riesgo entre años.',
    'Precio, variación de costos y renta son condiciones fijas del escenario. No se inventan distribuciones, correlaciones, indemnizaciones ni castigos por calidad.',
    'El costo publicado ya incluye seguro e intereses; la renta se añade solo cuando se especifica. No se calcula caja, pago de deuda ni riesgo conjunto de cartera.',
    'El importe de financiamiento en UDIS corresponde a la operación; el perfil no se asigna automáticamente por la superficie de la parcela.',
    'Cero escenarios con pérdida no significa riesgo cero: el remuestreo no crea eventos fuera del soporte de los errores observados.',
]


class RiskInputError(ValueError):
    """A scenario input is missing, invalid, or outside the supported scope."""


class RiskDataError(ValueError):
    """The source artifacts are missing or cannot support the calculation."""


def _sha256(path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise RiskDataError('No está disponible una fuente necesaria del ejercicio.') from exc


def _budget_hash():
    digest = _sha256(BUDGET_PATH)
    if digest != BUDGET_SHA256:
        raise RiskDataError('El presupuesto fuente cambió; revisa sus cifras antes de volver a simular.')
    return digest


def _read_residuals(artifact_dir, basis):
    filename, label = BASES[basis]
    path = Path(artifact_dir) / filename
    errors, ids = [], []
    try:
        with path.open(encoding='utf-8', newline='') as source:
            reader = csv.DictReader(source)
            if not {'ID_parcela', 'state', 'actual', 'predicted'}.issubset(reader.fieldnames or []):
                raise RiskDataError('El archivo de validación no tiene las columnas necesarias.')
            for row in reader:
                if row['state'] != 'Hidalgo':
                    continue
                actual, predicted = float(row['actual']), float(row['predicted'])
                parcel_id = row['ID_parcela']
                if not parcel_id or parcel_id in ids or not all(math.isfinite(v) and v >= 0 for v in (actual, predicted)):
                    raise RiskDataError('La validación de Hidalgo contiene valores o identificadores inválidos.')
                ids.append(parcel_id)
                errors.append(actual - predicted)
    except (OSError, TypeError, ValueError, csv.Error) as exc:
        if isinstance(exc, RiskDataError):
            raise
        raise RiskDataError('No se pudo leer la evidencia de errores de validación.') from exc
    if len(errors) < 10:
        raise RiskDataError('Se necesitan al menos diez errores válidos de Hidalgo para este ejercicio experimental.')
    values = np.asarray(errors, dtype=float)
    return values, {
        'id': basis, 'label': label, 'count': len(values),
        'mae_t_ha': float(np.abs(values).mean()), 'bias_t_ha': float(values.mean()),
        'source_file': filename, 'source_sha256': _sha256(path),
        'source_ids': ids,
    }


def _parcels(dashboard):
    try:
        rows = []
        for row in dashboard['parcels']:
            if row['state'] != 'Hidalgo':
                continue
            area, predicted = float(row['area_ha']), float(row['yield'])
            if not math.isfinite(area) or area <= 0 or not math.isfinite(predicted) or predicted < 0:
                raise RiskDataError('Hay una superficie o estimación inválida en Hidalgo.')
            rows.append({key: row[key] for key in ('id', 'state', 'municipality', 'area_ha', 'yield', 'lower', 'upper')})
        if not rows or len({row['id'] for row in rows}) != len(rows):
            raise RiskDataError('No hay parcelas de Hidalgo válidas y únicas.')
        return rows
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, RiskDataError):
            raise
        raise RiskDataError('No se pudieron leer las estimaciones existentes de Hidalgo.') from exc


def risk_context(dashboard, artifact_dir):
    artifact_dir = Path(artifact_dir)
    bases = [_read_residuals(artifact_dir, basis)[1] for basis in BASES]
    return {
        'parcels': _parcels(dashboard),
        'profiles': [dict(profile) for profile in PROFILES.values()],
        'defaults': {'profile': 'small', 'residual_basis': 'parcel',
                     'price_per_t': REFERENCE_PRICE, 'direct_cost_change_pct': 0,
                     'rent_per_ha': 0, 'reference_rent_per_ha': REFERENCE_RENT},
        'method': {'draws': DRAWS, 'seed': SEED, 'bases': bases},
        'sources': {
            'budget_title': 'Agrocostos: Cebada, Altiplano de Hidalgo, TMF, PV 2026',
            'budget_url': '/staff/riesgo/presupuesto.pdf',
            'budget_sha256': _budget_hash(),
            'documentation_url': '/staff/riesgo/documentacion.md',
            'agrocostos_url': 'https://www.fira.gob.mx/Nd/Agrocostos.jsp',
            'budget_price_basis': 'Precio base PV 2025; insumos cotizados en abril de 2026.',
        },
        'limitations': list(LIMITATIONS),
    }


def _number(payload, key, default, minimum, maximum):
    raw = payload.get(key, default)
    try:
        if isinstance(raw, bool):
            raise ValueError
        value = float(raw)
        if not math.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError
        return value
    except (TypeError, ValueError, OverflowError) as exc:
        raise RiskInputError(f'{key}: se requiere un número entre {minimum:g} y {maximum:g}.') from exc


def _summary(yields, parcel, profile, price, cost_change, rent, edges):
    # Preserve the published total instead of silently "correcting" its $1
    # rounding discrepancy. Apply changes only to direct costs, not interest.
    extra_direct = profile['direct_cost_per_ha'] * cost_change / 100
    total_cost = profile['total_cost_per_ha'] + extra_direct + rent
    margins = yields * price - total_cost
    area = float(parcel['area_ha'])
    point_yield = float(parcel['yield'])
    shortfalls = np.maximum(-margins, 0)
    worst_count = max(1, math.ceil(DRAWS * .1))
    quantiles = np.quantile(margins, [.1, .5, .9])
    counts, _ = np.histogram(margins, bins=edges)
    return {
        'price_per_t': price,
        'direct_cost_per_ha': profile['direct_cost_per_ha'] + extra_direct,
        'interest_per_ha': profile['interest_per_ha'], 'rent_per_ha': rent,
        'total_cost_per_ha': total_cost,
        'mean_margin_per_ha': float(margins.mean()),
        'mean_margin_total': float(margins.mean() * area),
        'margin_p10_per_ha': float(quantiles[0]),
        'margin_p50_per_ha': float(quantiles[1]),
        'margin_p90_per_ha': float(quantiles[2]),
        'loss_frequency': float(np.mean(margins < 0)),
        'monte_carlo_standard_error_pp': float(np.sqrt(np.mean(margins < 0) * (1 - np.mean(margins < 0)) / DRAWS) * 100),
        'mean_loss_per_ha': float(shortfalls.mean()),
        'worst_decile_loss_per_ha': float(np.sort(shortfalls)[-worst_count:].mean()),
        'break_even_yield_t_ha': total_cost / price,
        'break_even_price_per_t': total_cost / point_yield if point_yield else None,
        'point_margin_per_ha': point_yield * price - total_cost,
        'histogram': [{'lower': float(edges[i]), 'upper': float(edges[i + 1]), 'count': int(count)}
                      for i, count in enumerate(counts)],
        'draws': DRAWS,
    }


def simulate_risk(payload, dashboard, artifact_dir):
    if payload.get('applicability_confirmed') != 'yes':
        raise RiskInputError('Confirma que el presupuesto, la modalidad y la tecnología son aplicables al ejercicio elegido.')
    profile_id = payload.get('profile', 'small')
    basis = payload.get('residual_basis', 'parcel')
    if not isinstance(profile_id, str) or profile_id not in PROFILES:
        raise RiskInputError('Selecciona un perfil de financiamiento válido.')
    if not isinstance(basis, str) or basis not in BASES:
        raise RiskInputError('Selecciona una base de errores válida.')
    parcel_id = payload.get('parcel_id')
    parcel = next((row for row in _parcels(dashboard) if row['id'] == parcel_id), None)
    if parcel is None:
        raise RiskInputError('Selecciona una parcela de Hidalgo disponible en el proyecto.')
    price = _number(payload, 'price_per_t', REFERENCE_PRICE, .01, 100_000)
    cost_change = _number(payload, 'direct_cost_change_pct', 0, -100, 300)
    rent = _number(payload, 'rent_per_ha', 0, 0, 100_000)
    errors, evidence = _read_residuals(artifact_dir, basis)
    sampled = np.random.default_rng(SEED).choice(errors, size=DRAWS, replace=True)
    unbounded_yields = float(parcel['yield']) + sampled
    yields = np.maximum(unbounded_yields, 0)
    profile = PROFILES[profile_id]
    base_margins = yields * REFERENCE_PRICE - profile['total_cost_per_ha']
    scenario_cost = profile['total_cost_per_ha'] + profile['direct_cost_per_ha'] * cost_change / 100 + rent
    scenario_margins = yields * price - scenario_cost
    low, high = min(base_margins.min(), scenario_margins.min()), max(base_margins.max(), scenario_margins.max())
    if low == high:
        low, high = low - .5, high + .5
    edges = np.linspace(low, high, 25)
    reference = _summary(yields, parcel, profile, REFERENCE_PRICE, 0, 0, edges)
    scenario = _summary(yields, parcel, profile, price, cost_change, rent, edges)
    artifact_dir = Path(artifact_dir)
    return {
        'parcel': parcel,
        'assumptions': {
            'profile': dict(profile), 'price_per_t': price,
            'direct_cost_change_pct': cost_change, 'rent_per_ha': rent,
            'applicability_confirmed': True,
            'budget_sha256': _budget_hash(),
            'prediction_input_sha256': hashlib.sha256(json.dumps(parcel, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest(),
            'budget_price_basis': 'PV 2025', 'budget_cost_basis': 'Abril de 2026',
            'currency': 'MXN',
        },
        'method': {
            'draws': DRAWS, 'seed': SEED, 'residual_basis': basis,
            'residual_count': len(errors), 'residual_evidence': evidence,
            'negative_yield_draws_clipped': int(np.sum(unbounded_yields < 0)),
            'yield_rule': 'max(0, estimación final + error firmado observado − predicho de validación en Hidalgo)',
            'paired_draws': True,
            'interpretation': 'Frecuencias de escenarios experimentales; no probabilidades calibradas de pérdidas futuras.',
        },
        'reference': reference, 'scenario': scenario,
        'comparison': {
            'mean_margin_change_per_ha': scenario['mean_margin_per_ha'] - reference['mean_margin_per_ha'],
            'loss_frequency_change_pp': (scenario['loss_frequency'] - reference['loss_frequency']) * 100,
        },
        'limitations': list(LIMITATIONS),
    }
