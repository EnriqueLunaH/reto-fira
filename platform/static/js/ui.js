"use strict";
(() => {
  const root = document.documentElement;
  const picker = document.getElementById('theme-picker');
  const media = matchMedia('(prefers-color-scheme: dark)');
  const radios = [...document.querySelectorAll('input[name="nas-theme"]')];
  function applyTheme(preference) {
    if (!['light', 'dark', 'system'].includes(preference)) preference = 'dark';
    root.dataset.themePreference = preference;
    root.dataset.theme = preference === 'system' ? (media.matches ? 'dark' : 'light') : preference;
    radios.forEach(input => { input.checked = input.value === preference; });
  }
  applyTheme(root.dataset.themePreference || 'dark');
  radios.forEach(input => input.addEventListener('change', () => {
    if (!input.checked) return;
    applyTheme(input.value);
    try { localStorage.setItem('nas-theme', input.value); } catch (_) { /* Theme still works without persistence. */ }
    if (picker) { picker.open = false; picker.querySelector('summary').focus(); }
  }));
  media.addEventListener('change', () => { if (root.dataset.themePreference === 'system') applyTheme('system'); });
  window.addEventListener('storage', event => { if (event.key === 'nas-theme') applyTheme(event.newValue); });
  const toggle = document.getElementById('nas-menu-toggle');
  const panel = document.getElementById('nas-mobile-nav');
  function closeMenu(returnFocus = false) {
    if (!toggle || !panel) return;
    panel.hidden = true; toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-label', 'Abrir navegación');
    if (returnFocus) toggle.focus();
  }
  toggle?.addEventListener('click', () => {
    const opening = panel.hidden;
    panel.hidden = !opening; toggle.setAttribute('aria-expanded', String(opening)); toggle.setAttribute('aria-label', opening ? 'Cerrar navegación' : 'Abrir navegación');
    if (picker) picker.open = false;
  });
  picker?.addEventListener('toggle', () => { if (picker.open) closeMenu(); });
  panel?.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  document.addEventListener('click', event => {
    if (picker?.open && !picker.contains(event.target)) picker.open = false;
    if (panel && !panel.hidden && !event.target.closest('#nas-header')) closeMenu();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      if (picker?.open) { picker.open = false; picker.querySelector('summary').focus(); }
      if (panel && !panel.hidden) closeMenu(true);
    }
  });
  matchMedia('(min-width: 961px)').addEventListener('change', event => { if (event.matches) closeMenu(); });
  const password = document.getElementById('password');
  const reveal = document.getElementById('nas-password-toggle');
  reveal?.addEventListener('click', () => {
    const visible = password.type === 'password';
    password.type = visible ? 'text' : 'password';
    reveal.textContent = visible ? 'Ocultar' : 'Mostrar';
    reveal.setAttribute('aria-pressed', String(visible));
    reveal.setAttribute('aria-label', visible ? 'Ocultar contraseña' : 'Mostrar contraseña');
  });
  const active = document.querySelector('.staff-navigation [aria-current="page"]');
  if (active && matchMedia('(max-width: 960px)').matches) {
    const nav = active.closest('nav');
    nav.scrollLeft = Math.max(0, active.offsetLeft - nav.offsetLeft - 20);
  }
})();
