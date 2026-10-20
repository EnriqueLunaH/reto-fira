"""Financial, data-integrity and authorization checks for the staff simulator."""

import copy
import csv
import hashlib
import json
from pathlib import Path

import pytest
from werkzeug.datastructures import MultiDict

import app as app_module
import risk as risk_module
from app import create_app
from risk import RiskDataError, RiskInputError, risk_context, simulate_risk
from test_accounts import FakeSupabase, PASSWORD


ARTIFACTS = Path(__file__).resolve().parents[1] / 'artifacts'
PDF_TOTALS = {'small': 24_862, 'large': 24_489}


@pytest.fixture
def dashboard():
    return json.loads((ARTIFACTS / 'dashboard.json').read_text(encoding='utf-8'))


@pytest.fixture
def payload(dashboard):
    parcel = next(row for row in dashboard['parcels'] if row['state'] == 'Hidalgo')
    return {
        'parcel_id': parcel['id'],
        'profile': 'small',
        'residual_basis': 'parcel',
        'price_per_t': 7375,
        'direct_cost_change_pct': 0,
        'rent_per_ha': 0,
        'applicability_confirmed': 'yes',
    }


@pytest.fixture
def point_dashboard(dashboard, payload):
    """The PDF's 3.5 t/ha point is an independent financial audit case."""
    parcel = next(row for row in dashboard['parcels'] if row['id'] == payload['parcel_id'])
    parcel.update({'yield': 3.5, 'area_ha': 2.0, 'total_t': 7.0})
    return dashboard


@pytest.fixture
def zero_residual_artifacts(tmp_path):
    """A known outcome verifies loss metrics without duplicating the sampler."""
    (tmp_path / 'dashboard.json').write_bytes((ARTIFACTS / 'dashboard.json').read_bytes())
    for basis in ('parcel', 'spatial'):
        source = ARTIFACTS / f'validation-{basis}.csv'
        with source.open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            fieldnames = reader.fieldnames
            rows = list(reader)
        for row in rows:
            row['actual'] = row['predicted']
        with (tmp_path / source.name).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return tmp_path


@pytest.mark.parametrize('profile', ['small', 'large'])
def test_pdf_point_costs_and_break_even_are_reproduced(
        payload, point_dashboard, zero_residual_artifacts, profile):
    payload['profile'] = profile
    result = simulate_risk(payload, point_dashboard, zero_residual_artifacts)
    expected_cost = PDF_TOTALS[profile]
    expected_margin = 3.5 * 7375 - expected_cost

    for name in ('reference', 'scenario'):
        summary = result[name]
        assert summary['total_cost_per_ha'] == pytest.approx(expected_cost)
        assert summary['point_margin_per_ha'] == pytest.approx(expected_margin)
        assert summary['mean_margin_per_ha'] == pytest.approx(expected_margin)
        assert summary['mean_margin_total'] == pytest.approx(expected_margin * 2)
        assert summary['break_even_yield_t_ha'] == pytest.approx(expected_cost / 7375)
        assert summary['break_even_price_per_t'] == pytest.approx(expected_cost / 3.5)
        for percentile in ('p10', 'p50', 'p90'):
            assert summary[f'margin_{percentile}_per_ha'] == pytest.approx(expected_margin)
        assert summary['loss_frequency'] == 0
        assert summary['mean_loss_per_ha'] == 0
        assert summary['worst_decile_loss_per_ha'] == 0
        assert sum(bucket['count'] for bucket in summary['histogram']) == 20_000


def test_rent_is_added_once_and_loss_metrics_measure_shortfall(
        payload, point_dashboard, zero_residual_artifacts):
    payload.update(profile='large', rent_per_ha=4893)
    result = simulate_risk(payload, point_dashboard, zero_residual_artifacts)
    reference, scenario = result['reference'], result['scenario']
    # The source's insurance and finance costs are already in the published total.
    assert reference['total_cost_per_ha'] == 24_489
    assert reference['point_margin_per_ha'] == pytest.approx(1323.5)
    assert scenario['total_cost_per_ha'] == 29_382
    assert scenario['point_margin_per_ha'] == pytest.approx(-3569.5)
    assert scenario['mean_margin_per_ha'] == pytest.approx(-3569.5)
    assert scenario['loss_frequency'] == 1
    assert scenario['mean_loss_per_ha'] == pytest.approx(3569.5)
    assert scenario['worst_decile_loss_per_ha'] == pytest.approx(3569.5)


def test_mean_loss_counts_profitable_draws_as_zero_not_as_missing(
        payload, point_dashboard, zero_residual_artifacts):
    path = zero_residual_artifacts / 'validation-parcel.csv'
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        fieldnames, rows = reader.fieldnames, list(reader)
    hidalgo_rows = [row for row in rows if row['state'] == 'Hidalgo']
    for row in hidalgo_rows[::2]:
        row['actual'] = str(float(row['predicted']) - 1)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    payload['profile'] = 'large'
    summary = simulate_risk(payload, point_dashboard, zero_residual_artifacts)['scenario']
    loss_fraction = summary['loss_frequency']
    assert 0 < loss_fraction < 1
    # Two known outcomes: +1,323.50 and -6,051.50. The observed loss fraction,
    # rather than an independently reproduced RNG sequence, determines the mean.
    assert summary['mean_loss_per_ha'] == pytest.approx(6051.5 * loss_fraction)
    assert summary['mean_margin_per_ha'] == pytest.approx(
        1323.5 * (1 - loss_fraction) - 6051.5 * loss_fraction)
    assert summary['mean_loss_per_ha'] < 6051.5


def test_cost_change_applies_to_direct_budget_and_reference_stays_fixed(
        payload, point_dashboard, zero_residual_artifacts):
    payload.update(profile='small', direct_cost_change_pct=10, rent_per_ha=4893,
                   price_per_t=8000)
    result = simulate_risk(payload, point_dashboard, zero_residual_artifacts)
    scenario = result['scenario']
    expected_cost = 24_862 + 21_504 * .10 + 4893
    assert scenario['total_cost_per_ha'] == pytest.approx(expected_cost)
    assert scenario['point_margin_per_ha'] == pytest.approx(3.5 * 8000 - expected_cost)
    assert result['reference']['total_cost_per_ha'] == 24_862
    assert result['reference']['point_margin_per_ha'] == pytest.approx(950.5)


@pytest.mark.parametrize('basis', ['parcel', 'spatial'])
def test_real_residuals_produce_deterministic_ordered_financial_summaries(
        payload, dashboard, basis):
    payload['residual_basis'] = basis
    first = simulate_risk(payload, dashboard, ARTIFACTS)
    assert first == simulate_risk(payload, dashboard, ARTIFACTS)
    for name in ('reference', 'scenario'):
        summary = first[name]
        assert summary['margin_p10_per_ha'] <= summary['margin_p50_per_ha']
        assert summary['margin_p50_per_ha'] <= summary['margin_p90_per_ha']
        assert 0 <= summary['loss_frequency'] <= 1
        assert summary['mean_loss_per_ha'] >= 0
        assert summary['worst_decile_loss_per_ha'] >= summary['mean_loss_per_ha']
        assert sum(bucket['count'] for bucket in summary['histogram']) == 20_000
        assert all(bucket['count'] >= 0 for bucket in summary['histogram'])
    assert first['reference'] == first['scenario']


def test_paired_scenarios_translate_rent_and_improve_with_price(payload, dashboard):
    base = simulate_risk(payload, dashboard, ARTIFACTS)
    rented = simulate_risk({**payload, 'rent_per_ha': 4893}, dashboard, ARTIFACTS)
    better_price = simulate_risk({**payload, 'price_per_t': 8200}, dashboard, ARTIFACTS)
    for key in ('mean_margin_per_ha', 'margin_p10_per_ha', 'margin_p50_per_ha',
                'margin_p90_per_ha', 'point_margin_per_ha'):
        assert rented['scenario'][key] == pytest.approx(base['scenario'][key] - 4893)
        assert better_price['scenario'][key] >= base['scenario'][key]
    assert rented['scenario']['loss_frequency'] >= base['scenario']['loss_frequency']
    assert better_price['scenario']['loss_frequency'] <= base['scenario']['loss_frequency']
    assert rented['scenario']['mean_loss_per_ha'] >= base['scenario']['mean_loss_per_ha']
    assert better_price['scenario']['mean_loss_per_ha'] <= base['scenario']['mean_loss_per_ha']
    for result in (base, rented, better_price):
        assert result['reference']['mean_margin_per_ha'] == base['reference']['mean_margin_per_ha']
        assert [(bucket['lower'], bucket['upper']) for bucket in result['reference']['histogram']] == [
            (bucket['lower'], bucket['upper']) for bucket in result['scenario']['histogram']]


def test_simulation_does_not_mutate_inputs_or_prediction_artifacts(payload, dashboard):
    original_payload, original_dashboard = copy.deepcopy(payload), copy.deepcopy(dashboard)
    names = ('dashboard.json', 'predicciones_59.csv', 'validation-parcel.csv',
             'validation-spatial.csv')
    hashes = {name: hashlib.sha256((ARTIFACTS / name).read_bytes()).digest() for name in names}
    simulate_risk(payload, dashboard, ARTIFACTS)
    simulate_risk({**payload, 'residual_basis': 'spatial', 'rent_per_ha': 4893}, dashboard, ARTIFACTS)
    assert payload == original_payload
    assert dashboard == original_dashboard
    assert hashes == {name: hashlib.sha256((ARTIFACTS / name).read_bytes()).digest() for name in names}


def test_context_identifies_eligible_parcels_profiles_and_traceable_error_cohorts(dashboard):
    context = risk_context(dashboard, ARTIFACTS)
    expected_ids = {row['id'] for row in dashboard['parcels'] if row['state'] == 'Hidalgo'}
    assert {row['id'] for row in context['parcels']} == expected_ids
    assert {profile['id']: profile['total_cost_per_ha'] for profile in context['profiles']} == PDF_TOTALS
    assert context['defaults']['profile'] == 'small'
    assert context['defaults']['residual_basis'] == 'parcel'
    assert context['method']['draws'] == 20_000
    assert context['method']['seed'] == 20261015
    assert {basis['id'] for basis in context['method']['bases']} == {'parcel', 'spatial'}
    for basis in context['method']['bases']:
        source = ARTIFACTS / f"validation-{basis['id']}.csv"
        with source.open(newline='', encoding='utf-8') as stream:
            eligible = {row['ID_parcela'] for row in csv.DictReader(stream) if row['state'] == 'Hidalgo'}
        assert basis['count'] == len(eligible) == 36
        assert set(basis['source_ids']) == eligible
        assert basis['source_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()


@pytest.mark.parametrize('change', [
    {'parcel_id': 'AGC_DOES_NOT_EXIST'},
    {'profile': 'unknown'},
    {'residual_basis': 'unknown'},
    {'applicability_confirmed': 'no'},
    {'applicability_confirmed': 'true'},
    {'applicability_confirmed': True},
    {'price_per_t': 0},
    {'price_per_t': -1},
    {'price_per_t': 100001},
    {'rent_per_ha': -1},
    {'rent_per_ha': 100001},
    {'direct_cost_change_pct': -101},
    {'direct_cost_change_pct': 301},
])
def test_invalid_scenario_is_rejected(payload, dashboard, change):
    with pytest.raises(RiskInputError):
        simulate_risk({**payload, **change}, dashboard, ARTIFACTS)


@pytest.mark.parametrize('field', ['price_per_t', 'rent_per_ha', 'direct_cost_change_pct'])
@pytest.mark.parametrize('value', [True, False, None, 'nan', float('nan'),
                                  'inf', float('inf'), float('-inf'), 'invalid'])
def test_numeric_fields_reject_nonfinite_and_boolean_values(payload, dashboard, field, value):
    with pytest.raises(RiskInputError):
        simulate_risk({**payload, field: value}, dashboard, ARTIFACTS)


def test_budget_is_not_silently_applied_outside_hidalgo_or_without_confirmation(payload, dashboard):
    non_hidalgo = next(row for row in dashboard['parcels'] if row['state'] != 'Hidalgo')
    with pytest.raises(RiskInputError):
        simulate_risk({**payload, 'parcel_id': non_hidalgo['id']}, dashboard, ARTIFACTS)
    payload.pop('applicability_confirmed')
    with pytest.raises(RiskInputError):
        simulate_risk(payload, dashboard, ARTIFACTS)


@pytest.mark.parametrize('bad_content', [
    'ID_parcela,state,predicted\nAGC_009,Hidalgo,3.5\n',
    'ID_parcela,state,actual,predicted\nAGC_009,Hidalgo,nan,3.5\n',
    'ID_parcela,state,actual,predicted\nAGC_009,Hidalgo,3.5,3.0\n',
])
def test_missing_or_unusable_residual_data_fails_explicitly(
        payload, dashboard, tmp_path, bad_content):
    with pytest.raises(RiskDataError):
        simulate_risk(payload, dashboard, tmp_path)
    (tmp_path / 'validation-parcel.csv').write_text(bad_content, encoding='utf-8')
    with pytest.raises(RiskDataError):
        simulate_risk(payload, dashboard, tmp_path)


@pytest.mark.parametrize('field,value', [('actual', 'inf'), ('predicted', 'nan')])
def test_one_nonfinite_value_invalidates_an_otherwise_complete_error_cohort(
        payload, dashboard, zero_residual_artifacts, field, value):
    path = zero_residual_artifacts / 'validation-parcel.csv'
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        fieldnames, rows = reader.fieldnames, list(reader)
    next(row for row in rows if row['state'] == 'Hidalgo')[field] = value
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(RiskDataError):
        simulate_risk(payload, dashboard, zero_residual_artifacts)


@pytest.fixture
def client(tmp_path):
    return create_app({
        'TESTING': True,
        'SECRET_KEY': 'risk-tests-only',
        'ACCOUNT_BACKEND': FakeSupabase(),
        'AUTH_SESSION_DB': tmp_path / 'risk-sessions.sqlite3',
    }).test_client()


def login(client, role):
    client.get('/login/' + role)
    with client.session_transaction() as session:
        token = session['csrf_token']
    assert client.post('/login/' + role, data={
        'email': role + '@example.com', 'password': PASSWORD, 'csrf_token': token,
    }).status_code == 302
    with client.session_transaction() as session:
        return session['csrf_token']


@pytest.mark.parametrize('role', ['anonymous', 'productor'])
def test_simulation_and_source_documents_require_staff(client, payload, role):
    if role == 'anonymous':
        client.get('/login/staff')
        with client.session_transaction() as session:
            token = session['csrf_token']
        api_status, page_status = 401, 302
    else:
        token = login(client, role)
        api_status = page_status = 403
    # The rejected anonymous request clears its session, including the token.
    # Exercise the POST first so authentication is reached with a valid CSRF.
    assert client.post('/api/risk/simulate', data={**payload, 'csrf_token': token}).status_code == api_status
    assert client.get('/api/risk/context').status_code == api_status
    for path in ('/staff/riesgo', '/staff/riesgo/presupuesto.pdf', '/staff/riesgo/documentacion.md'):
        assert client.get(path).status_code == page_status


def test_staff_can_review_budget_and_submit_only_with_valid_csrf(client, payload):
    token = login(client, 'staff')
    for path in ('/staff/riesgo', '/staff/riesgo/presupuesto.pdf', '/staff/riesgo/documentacion.md'):
        assert client.get(path).status_code == 200
    assert client.get('/api/risk/context').status_code == 200
    assert client.post('/api/risk/simulate', data=payload).status_code == 400
    assert client.post('/api/risk/simulate', data={**payload, 'csrf_token': 'wrong'}).status_code == 400
    assert client.post('/api/risk/simulate', json={**payload, 'csrf_token': token}).status_code == 400
    response = client.post('/api/risk/simulate', data={**payload, 'csrf_token': token})
    assert response.status_code == 200
    assert {'parcel', 'assumptions', 'method', 'reference', 'scenario', 'comparison'} <= response.json.keys()
    invalid = client.post('/api/risk/simulate', data={**payload, 'price_per_t': 'nan', 'csrf_token': token})
    assert invalid.status_code == 400


def test_missing_residual_sources_return_structured_service_errors(
        client, payload, tmp_path, monkeypatch):
    token = login(client, 'staff')
    artifacts = tmp_path / 'artifacts'
    artifacts.mkdir()
    (artifacts / 'dashboard.json').write_bytes((ARTIFACTS / 'dashboard.json').read_bytes())
    monkeypatch.setattr(app_module, 'BASE', tmp_path)
    responses = [
        client.get('/api/risk/context'),
        client.post('/api/risk/simulate', data={**payload, 'csrf_token': token}),
    ]
    for response in responses:
        assert response.status_code == 503
        assert response.is_json
        assert isinstance(response.json['error'], str) and response.json['error']


@pytest.mark.parametrize('field', [
    'parcel_id', 'profile', 'residual_basis', 'price_per_t',
    'direct_cost_change_pct', 'rent_per_ha', 'applicability_confirmed',
])
def test_simulation_rejects_ambiguous_duplicate_form_fields(client, payload, field):
    token = login(client, 'staff')
    form = MultiDict({**payload, 'csrf_token': token})
    form.add(field, str(payload[field]))
    response = client.post('/api/risk/simulate', data=form)
    assert response.status_code == 400
    assert response.is_json
    assert 'un solo valor' in response.json['error']


def test_changed_budget_fails_closed_for_context_and_simulation(
        client, payload, monkeypatch):
    token = login(client, 'staff')
    # Change only the expected fingerprint in memory; preserve the source PDF.
    monkeypatch.setattr(risk_module, 'BUDGET_SHA256', '0' * 64)
    responses = [
        client.get('/api/risk/context'),
        client.post('/api/risk/simulate', data={**payload, 'csrf_token': token}),
    ]
    for response in responses:
        assert response.status_code == 503
        assert response.is_json
        assert 'presupuesto fuente cambió' in response.json['error']


@pytest.mark.parametrize('profile', ['small', 'large'])
@pytest.mark.parametrize('basis', ['parcel', 'spatial'])
def test_staff_api_calculates_both_bases_and_financing_profiles(
        client, payload, dashboard, profile, basis):
    token = login(client, 'staff')
    response = client.post('/api/risk/simulate', data={
        **payload, 'profile': profile, 'residual_basis': basis, 'csrf_token': token,
    })
    assert response.status_code == 200
    result = response.json
    assert result['assumptions']['profile']['id'] == profile
    assert result['scenario']['total_cost_per_ha'] == PDF_TOTALS[profile]
    assert result['method']['residual_basis'] == basis
    assert result['method']['residual_count'] == 36
    assert result['method']['paired_draws'] is True
    assert result['reference'] == result['scenario']
    assert sum(bucket['count'] for bucket in result['scenario']['histogram']) == 20_000
    parcel = next(row for row in dashboard['parcels'] if row['id'] == payload['parcel_id'])
    assert result['scenario']['mean_margin_total'] == pytest.approx(
        result['scenario']['mean_margin_per_ha'] * parcel['area_ha'])
