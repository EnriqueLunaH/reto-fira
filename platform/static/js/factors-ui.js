"use strict";
(() => {
  const chart = document.getElementById('importance-chart');
  if (!chart) return;
  const panel = document.getElementById('factors-analysis');
  const status = document.getElementById('staff-status');
  const loadingMessage = status.textContent;
  // Observe the existing renderer; this adapter only presents loading/error states.
  function presentChart() {
    if (!chart.querySelector('svg, .empty-chart')) return;
    panel.setAttribute('aria-busy', 'false');
    status.textContent = '';
  }
  new MutationObserver(presentChart).observe(chart, {childList: true});
  new MutationObserver(() => {
    if (status.textContent && status.textContent !== loadingMessage) {
      panel.setAttribute('aria-busy', 'false');
      status.classList.add('factors-load-error');
    }
  }).observe(status, {childList: true});
  presentChart();
})();
