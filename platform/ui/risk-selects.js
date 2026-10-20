import SelectMenu from '../vendor/osbi-ui/src/modules/SelectMenu/SelectMenu.js';

// Presentation adapter: keep the existing selects, validation and FormData intact.
document.querySelectorAll('[data-risk-select]').forEach(field => {
  const id = field.dataset.riskSelect;
  const select = document.getElementById(id), trigger = document.getElementById(`${id}-open`);
  const popup = document.getElementById(`${id}-popup`), list = popup.querySelector('[role="listbox"]');
  const error = document.getElementById(`${id}-error`), controls = select.closest('fieldset');
  const [menu] = new SelectMenu(`#${id}-open`, {
    offset: 8,
    onSelect(value) {
      select.value = value;
      select.dispatchEvent(new Event('change', {bubbles: true}));
    }
  }).init();
  const options = () => [...list.querySelectorAll('[role="option"]')];
  function syncSelection() {
    const selected = select.selectedOptions[0];
    trigger.querySelector('[data-select-menu-text]').textContent = selected?.textContent || 'Selecciona una opción';
    trigger.title = selected?.textContent || '';
    options().forEach(option => option.setAttribute('aria-selected', String(option.dataset.value === select.value)));
    trigger.setAttribute('aria-invalid', 'false');
    error.hidden = true;
  }
  function rebuild() {
    menu.close();
    list.replaceChildren(...[...select.options].map(option => {
      const item = field.querySelector('template').content.firstElementChild.cloneNode(true);
      const button = item.querySelector('button');
      button.dataset.value = option.value;
      button.disabled = option.disabled;
      item.querySelector('[data-risk-option-label]').textContent = option.textContent;
      return item;
    }));
    syncSelection();
  }
  function syncDisabled() {
    trigger.disabled = select.disabled || controls.disabled;
    if (trigger.disabled) menu.close();
  }
  new MutationObserver(rebuild).observe(select, {childList: true, subtree: true});
  new MutationObserver(syncDisabled).observe(controls, {attributes: true, attributeFilter: ['disabled']});
  select.addEventListener('change', syncSelection);
  select.addEventListener('invalid', event => {
    event.preventDefault();
    trigger.setAttribute('aria-invalid', 'true');
    error.hidden = false;
    requestAnimationFrame(() => trigger.focus());
  });
  select.classList.add('sr-only');
  select.tabIndex = -1;
  select.setAttribute('aria-hidden', 'true');
  trigger.setAttribute('role', 'combobox');
  trigger.setAttribute('aria-required', String(select.required));
  field.querySelector('label').htmlFor = trigger.id;
  trigger.hidden = false;
  rebuild(); syncDisabled();

  const focusOption = last => requestAnimationFrame(() => {
    if (trigger.getAttribute('aria-expanded') !== 'true') return;
    const available = options().filter(option => !option.disabled);
    (last ? available.at(-1) : available.find(option => option.getAttribute('aria-selected') === 'true') || available[0])?.focus();
  });
  trigger.addEventListener('click', () => focusOption(false));
  trigger.addEventListener('keydown', event => {
    if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
    event.preventDefault(); event.stopPropagation();
    menu.open(); focusOption(event.key === 'ArrowUp');
  });
  let typed = '', timer;
  popup.addEventListener('keydown', event => {
    const available = options().filter(option => !option.disabled), index = available.indexOf(document.activeElement);
    let next;
    if (event.key === 'ArrowDown') next = (index + 1) % available.length;
    if (event.key === 'ArrowUp') next = (index - 1 + available.length) % available.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = available.length - 1;
    if (next !== undefined) {
      event.preventDefault(); event.stopPropagation(); available[next]?.focus();
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault(); event.stopPropagation(); available[index]?.click();
    } else if (event.key === 'Tab') {
      menu.close(); trigger.focus();
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault(); event.stopPropagation(); clearTimeout(timer);
      typed += event.key.toLocaleLowerCase('es');
      available.find(option => option.textContent.trim().toLocaleLowerCase('es').startsWith(typed))?.focus();
      timer = setTimeout(() => { typed = ''; }, 600);
    }
  });
  popup.addEventListener('focusout', event => {
    if (!popup.contains(event.relatedTarget) && event.relatedTarget !== trigger) menu.close();
  });
});
