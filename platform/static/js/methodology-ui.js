"use strict";
(() => {
  const note = document.getElementById('model-note');
  if (!note) return;
  const report = document.getElementById('methodology-model-report');
  const status = document.getElementById('staff-status');
  const loadingMessage = status.textContent;
  // Present the original controller's text without parsing or recalculating it.
  function presentReport() {
    if (!note.textContent) return;
    report.setAttribute('aria-busy', 'false');
    status.textContent = '';
  }
  new MutationObserver(presentReport).observe(note, {childList: true});
  new MutationObserver(() => {
    if (status.textContent && status.textContent !== loadingMessage) {
      report.setAttribute('aria-busy', 'false');
      status.classList.add('methodology-load-error');
    }
  }).observe(status, {childList: true});
  presentReport();
})();
