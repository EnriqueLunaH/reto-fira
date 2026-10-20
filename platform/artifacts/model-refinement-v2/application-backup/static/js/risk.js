"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const form = $('risk-form');
  if (!form) return;
  const app = $('risk-app'), controls = $('risk-controls'), status = $('risk-status');
  const parcelInput = $('risk-parcel'), profileInput = $('risk-profile'), basisInput = $('risk-basis');
  const priceInput = $('risk-price'), costInput = $('risk-cost-change'), rentInput = $('risk-rent');
  const results = $('risk-results'), error = $('risk-error'), retry = $('risk-retry');
  const number = (value, digits = 2) => Number.isFinite(value)
    ? new Intl.NumberFormat('es-MX', {minimumFractionDigits: digits, maximumFractionDigits: digits}).format(Math.abs(value) < .5 * 10 ** (-digits) ? 0 : value)
    : 'Sin dato';
  const money = value => Number.isFinite(value) ? `${value < 0 ? '−' : ''}$${number(Math.abs(value))}` : 'Sin dato';
  const percent = value => `${number(value * 100, 1)}%`;
  const signed = (value, formatter) => `${value > 0 ? '+' : ''}${formatter(value)}`;
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  let context, lastResult, busy = false;

  async function request(url, options) {
    let response;
    try { response = await fetch(url, {credentials: 'same-origin', ...options}); }
    catch (_) { throw new Error('No se pudo conectar con el servidor. Comprueba la conexión y vuelve a intentar.'); }
    if (response.status === 401) throw new Error('Tu sesión terminó. Vuelve a iniciar sesión.');
    if (response.status === 403) throw new Error('No se pudo autorizar la solicitud. Recarga la página y vuelve a intentar.');
    let payload;
    try { payload = await response.json(); }
    catch (_) { throw new Error('El servidor no devolvió un resultado válido. Vuelve a intentar.'); }
    if (!response.ok) throw new Error(payload.error || payload.message || 'No se pudo completar el cálculo. Revisa los datos y vuelve a intentar.');
    return payload;
  }

  function setBusy(value, loadingMessage) {
    busy = value;
    app.setAttribute('aria-busy', String(value));
    controls.disabled = value;
    $('risk-submit').textContent = value ? 'Calculando…' : 'Calcular y comparar →';
    status.textContent = loadingMessage || '';
  }

  function options(select, rows, selected) {
    select.replaceChildren(...rows.map(row => {
      const option = element('option', '', row.label);
      option.value = row.id;
      option.selected = row.id === selected;
      return option;
    }));
  }

  function updateParcel() {
    const parcel = context?.parcels.find(row => row.id === parcelInput.value);
    $('risk-parcel-summary').hidden = !parcel;
    if (!parcel) return;
    $('risk-area').textContent = `${number(parcel.area_ha)} ha`;
    $('risk-yield').textContent = `${number(parcel.yield, 3)} t/ha`;
    $('risk-yield-range').textContent = `${number(parcel.lower, 3)}–${number(parcel.upper, 3)} t/ha`;
  }

  function updateBudget() {
    const profile = context?.profiles.find(row => row.id === profileInput.value);
    if (!profile) return;
    const rows = [
      ['Costos directos', profile.direct_cost_per_ha],
      ['Interés publicado', profile.interest_per_ha],
      ['Crédito de referencia', profile.credit_per_ha],
      ['Aportación propia de referencia', profile.own_contribution_per_ha],
      ['Costo total publicado', profile.total_cost_per_ha]
    ];
    $('risk-budget').replaceChildren(...rows.map(([label, value], index) => {
      const row = element('div', index === rows.length - 1 ? 'risk-budget-total' : '');
      row.append(element('dt', '', label), element('dd', '', `${money(value)}/ha`));
      return row;
    }));
  }

  function updateBasis() {
    const basis = context?.method.bases.find(row => row.id === basisInput.value);
    if (!basis) return;
    $('risk-basis-note').textContent = `${number(basis.count, 0)} errores fuera de muestra · MAE ${number(basis.mae_t_ha, 3)} t/ha. ${basis.id === 'spatial' ? 'Estrés por separación de bloques geográficos.' : 'Validación aleatoria por parcela.'}`;
  }

  function markStale() {
    if (lastResult && !results.hidden) $('risk-stale').hidden = false;
  }

  function resetScenario() {
    if (!context || busy) return;
    priceInput.value = context.defaults.price_per_t;
    costInput.value = context.defaults.direct_cost_change_pct;
    rentInput.value = context.defaults.rent_per_ha;
    markStale();
  }

  function sourceLink(id, value) {
    if (typeof value !== 'string') return;
    try {
      const url = new URL(value, window.location.origin);
      if (url.origin === window.location.origin && ['http:', 'https:'].includes(url.protocol)) $(id).href = url.href;
    } catch (_) { /* Keep the local source link when metadata is invalid. */ }
  }

  async function loadContext() {
    error.hidden = true;
    retry.hidden = true;
    setBusy(true, 'Cargando parcelas y presupuesto de referencia…');
    try {
      context = await request('/api/risk/context');
      const parcels = context.parcels.filter(parcel => parcel.state === 'Hidalgo');
      if (!parcels.length) throw new Error('No hay parcelas de Hidalgo disponibles para este análisis.');
      options(parcelInput, [{id: '', label: 'Selecciona una parcela'}, ...parcels.map(parcel => ({id: parcel.id, label: `${parcel.id} · ${parcel.municipality}`}))], '');
      options(profileInput, context.profiles, context.defaults.profile);
      options(basisInput, context.method.bases, context.defaults.residual_basis);
      priceInput.value = context.defaults.price_per_t;
      costInput.value = context.defaults.direct_cost_change_pct;
      rentInput.value = context.defaults.rent_per_ha;
      $('risk-draws-note').textContent = `${number(context.method.draws, 0)} escenarios · Cálculo en el servidor`;
      $('risk-method-note').textContent = `Configuración reproducible: ${number(context.method.draws, 0)} sorteos, semilla ${context.method.seed}. Solo se simula una parcela a la vez; no se agrega riesgo de cartera.`;
      $('risk-limitations').replaceChildren(...(context.limitations || []).map(note => element('li', '', note)));
      sourceLink('risk-budget-link', context.sources?.budget_url);
      sourceLink('risk-docs-link', context.sources?.documentation_url);
      updateParcel();
      updateBudget();
      updateBasis();
      setBusy(false);
    } catch (err) {
      setBusy(false);
      controls.disabled = true;
      error.textContent = err.message;
      error.hidden = false;
      status.textContent = 'No se cargó la configuración del simulador.';
      retry.hidden = false;
    }
  }

  function kpi(label, value, unit, note, negative = false) {
    const card = element('article', `kpi${negative ? ' risk-kpi-negative' : ''}`);
    const main = element('p', 'kpi-number', value);
    if (unit) main.append(document.createTextNode(' '), element('small', '', unit));
    card.append(element('p', 'kpi-label', label), main, element('p', 'kpi-footnote', note));
    return card;
  }

  function comparisonRows(reference, scenario, area) {
    return [
      ['Precio del grano (MXN/t)', 'price_per_t', money],
      ['Costos directos (MXN/ha)', 'direct_cost_per_ha', money],
      ['Interés publicado (MXN/ha)', 'interest_per_ha', money],
      ['Renta de la tierra (MXN/ha)', 'rent_per_ha', money],
      ['Costo total (MXN/ha)', 'total_cost_per_ha', money],
      ['Margen con rendimiento puntual (MXN/ha)', 'point_margin_per_ha', money],
      ['Margen medio simulado (MXN/ha)', 'mean_margin_per_ha', money, true],
      ['Margen medio total de la parcela (MXN)', 'mean_margin_total', money, true],
      ['Margen P10 (MXN/ha)', 'margin_p10_per_ha', money],
      ['Margen P50, mediana (MXN/ha)', 'margin_p50_per_ha', money],
      ['Margen P90 (MXN/ha)', 'margin_p90_per_ha', money],
      ['Escenarios con pérdida (%)', 'loss_frequency', percent, true],
      ['Déficit medio, todos los escenarios (MXN/ha)', 'mean_loss_per_ha', money],
      ['Déficit medio del peor 10% (MXN/ha)', 'worst_decile_loss_per_ha', money],
      ['Déficit medio del peor 10%, total parcela (MXN)', null, money, false, reference.worst_decile_loss_per_ha * area, scenario.worst_decile_loss_per_ha * area],
      ['Rendimiento de equilibrio (t/ha)', 'break_even_yield_t_ha', value => number(value, 3)],
      ['Precio de equilibrio (MXN/t)', 'break_even_price_per_t', money]
    ].map(([label, key, formatter, emphasis, referenceValue, scenarioValue]) => {
      const row = element('tr', emphasis ? 'risk-table-emphasis' : '');
      const heading = element('th', '', label);
      heading.scope = 'row';
      row.append(heading, element('td', '', formatter(key ? reference[key] : referenceValue)), element('td', '', formatter(key ? scenario[key] : scenarioValue)));
      return row;
    });
  }

  const NS = 'http://www.w3.org/2000/svg';
  function svgNode(name, attributes = {}, text) {
    const node = document.createElementNS(NS, name);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function histogram(reference, scenario) {
    const container = $('risk-histogram');
    const series = [{data: reference, label: 'Referencia', className: 'risk-bar-reference'}, {data: scenario, label: 'Escenario', className: 'risk-bar-scenario'}];
    const bins = series.flatMap(item => item.data.histogram || []).filter(bin => Number.isFinite(bin.lower) && Number.isFinite(bin.upper) && bin.upper > bin.lower);
    if (!bins.length) {
      container.replaceChildren(element('p', 'muted', 'No hay intervalos disponibles para mostrar la distribución.'));
      return;
    }
    const width = Math.max(280, Math.min(960, container.clientWidth || 900));
    const compact = width < 500;
    const height = compact ? 280 : 320, left = compact ? 44 : 62, right = compact ? 20 : 30, top = 32, bottom = 65;
    const low = Math.min(0, ...bins.map(bin => bin.lower)), high = Math.max(0, ...bins.map(bin => bin.upper));
    const maxPercent = Math.max(1, ...series.flatMap(item => (item.data.histogram || []).map(bin => 100 * bin.count / item.data.draws))) * 1.12;
    const x = value => left + (value - low) / (high - low || 1) * (width - left - right);
    const y = value => height - bottom - value / maxPercent * (height - top - bottom);
    const svg = svgNode('svg', {viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-labelledby': 'risk-hist-title risk-hist-desc'});
    svg.append(svgNode('title', {id: 'risk-hist-title'}, 'Distribución simulada del margen por hectárea: escenario y referencia'));
    svg.append(svgNode('desc', {id: 'risk-hist-desc'}, `Escenario: ${percent(scenario.loss_frequency)} con pérdida; referencia: ${percent(reference.loss_frequency)}. Las barras muestran el porcentaje de los sorteos por intervalo de margen en MXN por hectárea.`));
    for (let i = 0; i <= 4; i++) {
      const value = maxPercent * i / 4;
      svg.append(svgNode('line', {x1: left, x2: width - right, y1: y(value), y2: y(value), class: 'risk-grid-line'}));
      svg.append(svgNode('text', {x: left - 10, y: y(value) + 4, 'text-anchor': 'end'}, `${number(value, 0)}%`));
    }
    series.forEach((item, seriesIndex) => (item.data.histogram || []).forEach(bin => {
      if (!Number.isFinite(bin.lower) || !Number.isFinite(bin.upper) || bin.upper <= bin.lower || !Number.isFinite(bin.count)) return;
      const frequency = 100 * bin.count / item.data.draws;
      const binWidth = x(bin.upper) - x(bin.lower);
      const rect = svgNode('rect', {x: x(bin.lower) + 1 + seriesIndex * binWidth / 2, y: y(frequency), width: Math.max(.5, binWidth / 2 - 2), height: Math.max(0, y(0) - y(frequency)), class: item.className});
      rect.append(svgNode('title', {}, `${item.label}: de ${money(bin.lower)} a ${money(bin.upper)} MXN/ha · ${number(frequency, 1)}% de escenarios`));
      svg.append(rect);
    }));
    svg.append(svgNode('line', {x1: left, x2: width - right, y1: y(0), y2: y(0), class: 'risk-axis'}));
    if (low <= 0 && high >= 0) {
      svg.append(svgNode('line', {x1: x(0), x2: x(0), y1: top, y2: height - bottom, class: 'risk-zero-line'}));
      const alignEnd = x(0) > width * .65;
      svg.append(svgNode('text', {x: x(0) + (alignEnd ? -5 : 5), y: top - 10, 'text-anchor': alignEnd ? 'end' : 'start', class: 'risk-zero-label'}, 'Margen cero'));
    }
    const ticks = width < 360 ? 1 : compact ? 2 : 4;
    for (let i = 0; i <= ticks; i++) {
      const value = low + (high - low) * i / ticks;
      svg.append(svgNode('text', {x: x(value), y: height - bottom + 24, 'text-anchor': i === 0 ? 'start' : i === ticks ? 'end' : 'middle'}, money(value).replace(/\.00$/, '')));
    }
    svg.append(svgNode('text', {x: (left + width - right) / 2, y: height - 11, 'text-anchor': 'middle'}, 'Margen (MXN/ha)'));
    container.replaceChildren(svg);
  }

  function render(payload) {
    const {parcel, reference, scenario, comparison} = payload;
    const profile = context.profiles.find(row => row.id === profileInput.value);
    const basis = context.method.bases.find(row => row.id === basisInput.value);
    $('risk-results-heading').textContent = `Margen del escenario · ${parcel.id}`;
    $('risk-result-context').textContent = `${parcel.municipality}, Hidalgo · ${number(parcel.area_ha)} ha · ${profile?.label || profileInput.value} · ${basis?.label || basisInput.value}. ${number(scenario.draws, 0)} escenarios simulados.`;
    $('risk-sampling-note').textContent = `${payload.method.residual_count} errores observados en la base seleccionada; ${payload.method.negative_yield_draws_clipped} sorteos limitados a cero t/ha. Más sorteos no agregan evidencia histórica. Un 0% de escenarios con pérdida no significa riesgo cero.`;
    $('risk-kpis').replaceChildren(
      kpi('Margen medio simulado', money(scenario.mean_margin_per_ha), 'MXN/ha', `Total de la parcela: ${money(scenario.mean_margin_total)} MXN`, scenario.mean_margin_per_ha < 0),
      kpi('Escenarios con pérdida', percent(scenario.loss_frequency), '', `Referencia: ${percent(reference.loss_frequency)} · Cambio: ${signed(comparison.loss_frequency_change_pp, value => number(value, 1))} puntos porcentuales`),
      kpi('Déficit medio del peor 10%', money(scenario.worst_decile_loss_per_ha), 'MXN/ha', `Pérdida positiva; total: ${money(scenario.worst_decile_loss_per_ha * parcel.area_ha)} MXN`),
      kpi('Rendimiento de equilibrio', number(scenario.break_even_yield_t_ha, 3), 't/ha', `Precio de equilibrio: ${money(scenario.break_even_price_per_t)} MXN/t`)
    );
    $('risk-chart-summary').textContent = `En el escenario, el margen P10 es ${money(scenario.margin_p10_per_ha)} MXN/ha; la mediana es ${money(scenario.margin_p50_per_ha)} MXN/ha y el P90 es ${money(scenario.margin_p90_per_ha)} MXN/ha.`;
    $('risk-comparison').replaceChildren(...comparisonRows(reference, scenario, parcel.area_ha));
    $('risk-comparison-note').textContent = `Cambio del margen medio frente a referencia: ${signed(comparison.mean_margin_change_per_ha, money)} MXN/ha. El precio de equilibrio usa la estimación puntual de rendimiento; no garantiza un margen positivo en todos los sorteos.`;
    results.hidden = false;
    histogram(reference, scenario);
    $('risk-stale').hidden = true;
    results.hidden = false;
    $('risk-results-heading').focus({preventScroll: true});
    results.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'});
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || !context || !form.reportValidity()) return;
    const body = new URLSearchParams(new FormData(form));
    error.hidden = true;
    setBusy(true, 'Calculando el margen y la comparación con la referencia…');
    try {
      const payload = await request(form.action, {method: 'POST', body, headers: {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}});
      lastResult = payload;
      render(payload);
      setBusy(false, 'Cálculo completo. Los resultados corresponden a los supuestos indicados.');
    } catch (err) {
      setBusy(false);
      error.textContent = err.message;
      error.hidden = false;
      markStale();
      error.scrollIntoView({block: 'center'});
    }
  });
  parcelInput.addEventListener('change', updateParcel);
  profileInput.addEventListener('change', updateBudget);
  basisInput.addEventListener('change', updateBasis);
  form.addEventListener('input', markStale);
  form.addEventListener('change', markStale);
  $('risk-use-rent').addEventListener('click', () => {rentInput.value = '4893'; markStale();});
  $('risk-reset').addEventListener('click', resetScenario);
  retry.addEventListener('click', loadContext);
  window.addEventListener('resize', () => {
    if (lastResult && !results.hidden) histogram(lastResult.reference, lastResult.scenario);
  });
  loadContext();
})();
