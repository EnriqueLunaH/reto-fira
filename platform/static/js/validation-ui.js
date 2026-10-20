"use strict";
(() => {
  const metrics = document.getElementById('quality-kpis');
  if (!metrics) return;
  const scope = document.getElementById('validation-scope');
  const count = document.getElementById('validation-count');
  const state = document.getElementById('staff-state');
  const status = document.getElementById('staff-status');
  const loadingMessage = status.textContent;
  function presentScope() {
    const sourceNote = metrics.querySelector('.kpi-footnote');
    if (!sourceNote) return;
    // Reuse the count already rendered by the original controller; no new metrics.
    count.textContent = sourceNote.textContent.replace(' fuera de muestra', ' evaluadas');
    document.getElementById('validation-selection').textContent = state.value || 'Todos los estados';
    scope.setAttribute('aria-busy', 'false');
    status.textContent = '';
    document.querySelectorAll('#validation-chart .chart-legend span').forEach(item => {
      item.hidden = Boolean(state.value && item.textContent.trim() !== state.value);
    });
  }
  new MutationObserver(presentScope).observe(metrics, {childList: true, subtree: true});
  new MutationObserver(() => {
    if (status.textContent && status.textContent !== loadingMessage) {
      scope.setAttribute('aria-busy', 'false'); count.textContent = 'Sin cargar';
      status.classList.add('validation-load-error');
    }
  }).observe(status, {childList: true, subtree: true});
  presentScope();
})();
