"use strict";
(() => {
  let preference = 'dark';
  try { const saved = localStorage.getItem('nas-theme'); if (['light', 'dark', 'system'].includes(saved)) preference = saved; } catch (_) { /* Private browsing may disable storage. */ }
  const resolved = preference === 'system' ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : preference;
  document.documentElement.dataset.theme = resolved;
  document.documentElement.dataset.themePreference = preference;
})();
