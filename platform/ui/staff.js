import SelectMenu from '../vendor/osbi-ui/src/modules/SelectMenu/SelectMenu.js';
import Drawer from '../vendor/osbi-ui/src/modules/Drawer/Drawer.js';
import { BREAKPOINTS } from '../vendor/osbi-ui/src/constants/breakpoints.js';

// UI adapters only: the existing dashboard owns filtering and all calculations.
const trigger = document.getElementById('staff-state-open');
if (trigger) {
  const valueInput = document.getElementById('staff-state');
  const popup = document.getElementById('staff-state-popup');
  const options = [...popup.querySelectorAll('[role="option"]')];
  const [menu] = new SelectMenu('#staff-state-open', {
    offset: 8,
    onSelect(value) {
      valueInput.value = value;
      valueInput.dispatchEvent(new Event('change', {bubbles: true}));
    }
  }).init();

  document.getElementById('reset-filters')?.addEventListener('click', () => {
    // Use the component's selection path so label, option and value stay in sync.
    options[0].click();
    document.getElementById('reset-filters').focus();
  });

  // Adapt OSBI's immediate arrow selection to standard listbox focus/commit.
  let typed = '', typeTimer;
  const openAndFocus = last => {
    menu.open();
    requestAnimationFrame(() => {
      if (trigger.getAttribute('aria-expanded') === 'true') {
        (last ? options.at(-1) : options.find(option => option.getAttribute('aria-selected') === 'true') || options[0]).focus();
      }
    });
  };
  trigger.addEventListener('keydown', event => {
    if (['ArrowDown', 'ArrowUp'].includes(event.key)) {
      event.preventDefault(); event.stopPropagation();
      openAndFocus(event.key === 'ArrowUp');
    }
  });
  popup.addEventListener('keydown', event => {
    const index = options.indexOf(document.activeElement);
    let next;
    if (event.key === 'ArrowDown') next = (index + 1) % options.length;
    if (event.key === 'ArrowUp') next = (index - 1 + options.length) % options.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = options.length - 1;
    if (next !== undefined) {
      event.preventDefault(); event.stopPropagation(); options[next].focus();
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault(); event.stopPropagation(); options[index]?.click();
    } else if (event.key === 'Tab') {
      // Keep native tab order after returning to the trigger, then close.
      menu.close(); trigger.focus();
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault(); event.stopPropagation();
      clearTimeout(typeTimer); typed += event.key.toLocaleLowerCase('es');
      options.find(option => option.textContent.trim().toLocaleLowerCase('es').startsWith(typed))?.focus();
      typeTimer = setTimeout(() => { typed = ''; }, 600);
    }
  });
  trigger.addEventListener('click', () => {
    if (trigger.getAttribute('aria-expanded') === 'true') openAndFocus(false);
  });
  popup.addEventListener('focusout', event => {
    if (!popup.contains(event.relatedTarget) && event.relatedTarget !== trigger) menu.close();
  });
}

const drawerTrigger = document.getElementById('staff-menu-open');
const panel = document.getElementById('staff-navigation-panel');
const main = document.getElementById('main-content');
const picker = document.getElementById('theme-picker');
const desktop = matchMedia(`(min-width: ${BREAKPOINTS.lg})`);
new Drawer('#staff-menu-open', {unlockCondition: BREAKPOINTS.lg}).init();
function syncDrawer() {
  const open = !desktop.matches && drawerTrigger.getAttribute('aria-expanded') === 'true';
  main.inert = open;
  if (open) {
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'true');
    panel.setAttribute('aria-label', 'Navegación del espacio técnico');
  } else {
    panel.removeAttribute('role'); panel.removeAttribute('aria-modal'); panel.removeAttribute('aria-label');
    if (!desktop.matches && document.activeElement.closest('#staff-navigation-panel')) drawerTrigger.focus();
    if (picker) picker.open = false;
  }
}
new MutationObserver(syncDrawer).observe(drawerTrigger, {attributes: true, attributeFilter: ['aria-expanded']});
desktop.addEventListener('change', syncDrawer);
syncDrawer();
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && picker?.open) {
    event.preventDefault(); event.stopImmediatePropagation();
    picker.open = false; picker.querySelector('summary').focus();
    return;
  }
  if (event.key !== 'Tab' || desktop.matches || drawerTrigger.getAttribute('aria-expanded') !== 'true') return;
  const focusable = [...panel.querySelectorAll('a[href],button,summary,input:not([type="hidden"])')]
    .filter(element => !element.disabled && element.getClientRects().length);
  const first = focusable[0], last = focusable.at(-1);
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}, true);
