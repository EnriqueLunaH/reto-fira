"use strict";
// Presentation adapter for the producer page; existing API values are not recalculated.
(() => {
  const A = window.Agro, $ = id => document.getElementById(id);
  const state = $('producer-state'), select = $('parcel-select'), search = $('parcel-search');
  const content = $('producer-content'), status = $('producer-status'), chart = $('vegetation-chart');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let parcels = [], geometry = null, requestId = 0, lastDetail = null, initialized = false;
  let searchTimer, chartFrame, chartWidth = 0, chartParcel = null;
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  const amount = (value, unit, digits = 0) => Number.isFinite(value) ? `${A.number(value, digits)} ${unit}` : 'Sin dato';
  const put = (id, text) => { $(id).textContent = text; };

  function message(text, kind = 'ready') {
    status.textContent = text;
    status.dataset.state = kind;
    $('producer-recovery').hidden = kind !== 'error';
  }
  function invalidate() {
    ++requestId;
    content.hidden = true;
    $('view-result').hidden = true;
    content.setAttribute('aria-busy', 'true');
    lastDetail = null;
    chartParcel = null;
  }
  function options() {
    clearTimeout(searchTimer);
    const query = normalize(search.value), old = select.value;
    const rows = parcels.filter(p => (!state.value || p.state === state.value) &&
      (!query || normalize(`${p.id} ${p.municipality}`).includes(query)));
    select.replaceChildren();
    for (const p of rows) {
      const option = document.createElement('option');
      option.value = p.id;
      option.textContent = `${p.id} · ${p.municipality}`;
      select.append(option);
    }
    select.disabled = !rows.length;
    if (rows.some(p => p.id === old)) select.value = old;
    $('clear-filters').hidden = !query && !state.value;
    put('parcel-count', `${rows.length} de ${parcels.length} parcelas`);
    if (rows.length) load();
    else {
      invalidate();
      content.setAttribute('aria-busy', 'false');
      message(parcels.length ? 'No encontramos parcelas. Prueba otro código o municipio, o limpia los filtros.' : 'Tu cuenta todavía no tiene parcelas asignadas. Contacta al staff para solicitar acceso.', 'empty');
    }
  }
  function drawMap() {
    if (!lastDetail || content.hidden) return;
    const feature = geometry?.features?.find(f => f.properties.ID_POLIGONO === lastDetail.parcel.id);
    if (feature) A.parcelMap($('parcel-map'), feature);
    else A.empty($('parcel-map'), 'El dibujo de esta parcela no está disponible. Consulta su código, municipio y superficie.');
  }
  function drawChart() {
    if (!lastDetail || content.hidden || $('producer-vegetation-panel').hidden || chart.clientWidth === 0) return;
    const width = Math.round(chart.clientWidth);
    if (chartParcel === lastDetail.parcel.id && width === chartWidth) return;
    chartWidth = width;
    chartParcel = lastDetail.parcel.id;
    A.lines(chart, lastDetail.history);
    // Preserve the shared renderer; add a non-color distinction only in this view.
    chart.querySelectorAll('polyline').forEach(line => {
      if (line.getAttribute('stroke') === A.colors[1]) line.setAttribute('stroke-dasharray', '7 5');
    });
  }
  function queueChart() {
    cancelAnimationFrame(chartFrame);
    chartFrame = requestAnimationFrame(drawChart);
  }
  function historyTable(history) {
    const body = $('vegetation-values');
    body.replaceChildren();
    ['Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre'].forEach((month, index) => {
      const row = document.createElement('tr'), heading = document.createElement('th');
      heading.scope = 'row';
      heading.textContent = month;
      row.append(heading);
      for (const sensor of ['Sentinel-2', 'Planet']) {
        const cell = document.createElement('td');
        const value = history.find(r => r.month === index + 4 && r.sensor === sensor)?.ndvi;
        cell.textContent = Number.isFinite(value) ? A.number(value, 3) : 'Sin medición';
        row.append(cell);
      }
      body.append(row);
    });
  }
  function render(data) {
    const p = data.parcel;
    put('parcel-title', p.id);
    put('parcel-location', `${p.municipality} · ${p.state}`);
    put('total-value', A.number(p.total_t, 1));
    put('total-explanation', Number.isFinite(p.total_t) ? 'Cantidad aproximada para la superficie registrada.' : 'No hay datos suficientes para mostrar el total.');
    put('yield-value', A.number(p.yield));
    put('yield-plain', Number.isFinite(p.yield) ? `Aproximadamente ${A.number(p.yield * 1000, 0)} kg por hectárea` : 'Rendimiento no disponible');
    put('area-value', A.number(p.area_ha));
    const interval = data.metadata?.interval;
    const hasRange = interval?.method !== 'not_estimated' && Number.isFinite(p.lower) && Number.isFinite(p.upper);
    $('yield-range').hidden = !hasRange;
    put('yield-range', hasRange ? `Rango estimado por hectárea: ${amount(p.lower, 'a', 2)} ${amount(p.upper, 'toneladas', 2)}.` : '');
    put('yield-range-note', hasRange ? 'La cantidad real puede quedar fuera del rango mostrado.' : 'La cantidad real puede ser mayor o menor. No hay un rango validado para esta estimación.');
    put('method-uncertainty', hasRange ? 'El rango expresa incertidumbre y depende de que la parcela sea comparable con las usadas para evaluar el cálculo. No garantiza una cantidad de grano.' : 'No se dispone de un rango de predicción validado para este cálculo. Una cifra única no significa que conozcamos la cosecha con certeza.');
    put('rain-value', amount(p.rain_mm, 'mm'));
    put('elevation-value', amount(p.elevation_m, 'm'));
    put('slope-value', amount(p.slope_deg, 'grados', 1));
    put('vegetation-coverage', Number.isFinite(p.clear_months) ? `Planet tiene observaciones válidas en ${p.clear_months} de los 7 meses. Un mes sin medición no equivale a ausencia de vegetación.` : 'Los meses sin medición no equivalen a ausencia de vegetación.');
    put('producer-notice', p.outside_training_range?.length ? 'Algunas características de esta parcela difieren de las observadas en las parcelas usadas para el cálculo. Conviene revisar esta estimación con especial cuidado.' : '');
    historyTable(data.history);
    content.hidden = false;
    $('view-result').hidden = false;
    content.setAttribute('aria-busy', 'false');
    drawMap();
    queueChart();
  }
  async function load() {
    invalidate();
    const current = requestId, parcelId = select.value;
    if (!parcelId) return;
    message(`Cargando la parcela ${parcelId}…`, 'loading');
    try {
      const data = await A.get(`/api/parcels/${encodeURIComponent(parcelId)}`);
      if (current !== requestId) return;
      lastDetail = data;
      render(data);
      message(`Mostrando ${data.parcel.id} · ${data.parcel.municipality}.`);
    } catch (error) {
      if (current !== requestId) return;
      content.hidden = true;
      $('view-result').hidden = true;
      content.setAttribute('aria-busy', 'false');
      message(error.message || 'No pudimos cargar esta parcela. Vuelve a intentarlo.', 'error');
    }
  }
  async function initialize() {
    invalidate();
    const current = requestId;
    state.disabled = search.disabled = select.disabled = true;
    message('Cargando parcelas…', 'loading');
    // Geometry is optional: a drawing failure must not hide the harvest estimate.
    A.get('/api/geometry').then(data => { geometry = data; drawMap(); }).catch(() => { geometry = null; drawMap(); });
    try {
      parcels = await A.get('/api/parcels');
      if (current !== requestId) return;
      initialized = true;
      state.replaceChildren();
      for (const name of ['', ...new Set(parcels.map(p => p.state))].sort()) {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name || 'Todos los estados';
        state.append(option);
      }
      state.disabled = search.disabled = false;
      options();
    } catch (error) {
      if (current !== requestId) return;
      content.setAttribute('aria-busy', 'false');
      put('parcel-count', 'Listado no disponible');
      message(error.message || 'No pudimos cargar el listado. Vuelve a intentarlo.', 'error');
    }
  }
  state.addEventListener('change', options);
  select.addEventListener('change', load);
  search.addEventListener('input', () => {
    invalidate();
    select.disabled = true;
    message('Buscando parcelas…', 'loading');
    clearTimeout(searchTimer);
    searchTimer = setTimeout(options, 180);
  });
  $('clear-filters').addEventListener('click', () => {
    state.value = search.value = '';
    options();
    search.focus();
  });
  $('producer-retry').addEventListener('click', () => initialized ? load() : initialize());
  new MutationObserver(queueChart).observe($('producer-vegetation-trigger'), {attributes:true, attributeFilter:['aria-expanded']});
  if ('ResizeObserver' in window) new ResizeObserver(queueChart).observe(chart);
  else window.addEventListener('resize', queueChart);

  // Brief, once-only entrance when the section reaches the viewport. Numbers stay exact.
  if ('IntersectionObserver' in window) {
    const active = new Set();
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting || content.hidden) return;
      observer.unobserve(entry.target);
      if (motion.matches || !entry.target.animate) return;
      const animation = entry.target.animate([{opacity:.65, transform:'translateY(6px)'}, {opacity:1, transform:'translateY(0)'}], {duration:300, easing:'ease-out'});
      active.add(animation);
      animation.onfinish = animation.oncancel = () => active.delete(animation);
    }), {threshold:.05, rootMargin:'0px 0px -24px 0px'});
    document.querySelectorAll('[data-producer-reveal]').forEach(element => observer.observe(element));
    motion.addEventListener('change', () => { if (motion.matches) active.forEach(animation => animation.finish()); });
    document.addEventListener('visibilitychange', () => { if (document.hidden) active.forEach(animation => animation.finish()); });
  }
  initialize();
})();
