// osbi-v1/src/js/modules/SelectMenu/SelectMenu.js

import { computePosition, autoUpdate, offset, flip, size } from '@floating-ui/dom';
import { FloatingManager } from '../../core/FloatingManager.js';

class SelectMenuController {
  #triggerEl;
  #listboxContainerEl;
  #listboxEl;
  #textTargetEl;
  #caretEl;
  #config;
  #isOpen;
  #cleanupAutoUpdate;

  #boundHandleClickOutside;
  #boundHandleKeyDown;
  #boundHandleOptionClick;
  #boundHandleOtherMenuOpen;

  constructor(triggerEl, config = {}) {
    this.#triggerEl = triggerEl;
    this.#isOpen = false;
    
    const targetId = this.#triggerEl.getAttribute('aria-controls');
    this.#listboxContainerEl = document.getElementById(targetId);
    
    if (!this.#listboxContainerEl) return;
    
    this.#listboxEl = this.#listboxContainerEl.querySelector('[data-select-menu-list]');
    this.#textTargetEl = this.#triggerEl.querySelector('[data-select-menu-text]');
    this.#caretEl = this.#triggerEl.querySelector('[data-select-menu-caret]');

    this.#config = {
      offset: 4,
      hasCheckIcon: false,
      iconClasses: [],
      toggleClass: { active: [], inactive: [] },
      onSelect: null,
      ...config
    };

    this.#boundHandleClickOutside = this.#handleClickOutside.bind(this);
    this.#boundHandleKeyDown = this.#handleKeyDown.bind(this);
    this.#boundHandleOptionClick = this.#handleOptionClick.bind(this);
    this.#boundHandleOtherMenuOpen = this.#handleOtherMenuOpen.bind(this);
  }

  init() {
    if (!this.#listboxContainerEl) return;

    Object.assign(this.#listboxContainerEl.style, {
      position: 'absolute',
      top: '0',
      left: '0'
    });

    this.#syncInitialState();
    this.#bindEvents();
  }

  #bindEvents() {
    this.#triggerEl.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggle();
    });
    
    this.#listboxEl.addEventListener('click', this.#boundHandleOptionClick);

    // Patrón Pub/Sub: Suscribirse al FloatingManager
    FloatingManager.subscribe(this.#boundHandleOtherMenuOpen);
  }

  toggle() {
    this.#isOpen ? this.close() : this.open();
  }

  open() {
    if (this.#isOpen) return;
    this.#isOpen = true;
    
    // Notificar globalmente a través del mediador
    FloatingManager.notifyOpen(this.#listboxContainerEl.id, this.#triggerEl);

    this.#triggerEl.setAttribute('aria-expanded', 'true');
    if (this.#caretEl) this.#caretEl.classList.add('rotate-180');

    window.requestAnimationFrame(() => {
      this.#listboxContainerEl.classList.replace('opacity-0', 'opacity-100');
      this.#listboxContainerEl.classList.replace('visibility-hidden', 'visibility-visible');
      this.#listboxContainerEl.classList.replace('pointer-events-none', 'pointer-events-auto');
      this.#listboxContainerEl.classList.replace('translate-y--2', 'translate-y-none');
    });

    this.#startPositioning();

    document.addEventListener('click', this.#boundHandleClickOutside);
    window.addEventListener('keydown', this.#boundHandleKeyDown);
  }

  close() {
    if (!this.#isOpen) return;
    this.#isOpen = false;
    this.#triggerEl.setAttribute('aria-expanded', 'false');

    if (this.#caretEl) this.#caretEl.classList.remove('rotate-180');

    window.requestAnimationFrame(() => {
      this.#listboxContainerEl.classList.replace('opacity-100', 'opacity-0');
      this.#listboxContainerEl.classList.replace('visibility-visible', 'visibility-hidden');
      this.#listboxContainerEl.classList.replace('pointer-events-auto', 'pointer-events-none');
      this.#listboxContainerEl.classList.replace('translate-y-none', 'translate-y--2');
    });

    if (this.#cleanupAutoUpdate) {
      this.#cleanupAutoUpdate();
      this.#cleanupAutoUpdate = null;
    }

    document.removeEventListener('click', this.#boundHandleClickOutside);
    window.removeEventListener('keydown', this.#boundHandleKeyDown);
  }

  // Agnostic Resolver: Evalúa el ID y comprueba la anidación para decidir si debe cerrar
  #handleOtherMenuOpen(event) {
    const { id, triggerEl } = event.detail;
    if (this.#isOpen && id !== this.#listboxContainerEl.id && !this.#listboxContainerEl.contains(triggerEl)) {
      this.close();
    }
  }

  #updatePosition() {
    return computePosition(this.#triggerEl, this.#listboxContainerEl, {
      placement: 'bottom-start',
      middleware: [
        offset(this.#config.offset),
        flip(),
        size({
          apply({ rects, elements }) {
            Object.assign(elements.floating.style, {
              width: `${rects.reference.width}px`
            });
          }
        })
      ],
    }).then(({ x, y }) => {
      const dpr = window.devicePixelRatio || 1;
      const roundByDPR = value => Math.round(value * dpr) / dpr;

      Object.assign(this.#listboxContainerEl.style, {
        left: `${roundByDPR(x)}px`,
        top: `${roundByDPR(y)}px`,
      });
    });
  }

  #startPositioning() {
    this.#cleanupAutoUpdate = autoUpdate(
      this.#triggerEl,
      this.#listboxContainerEl,
      () => this.#updatePosition()
    );
  }

  #syncInitialState() {
    const allOptions = this.#listboxEl.querySelectorAll('[role="option"]');
    allOptions.forEach(opt => {
      const isSelected = opt.getAttribute('aria-selected') === 'true';
      this.#updateOptionVisuals(opt, isSelected);
    });
  }

  #handleOptionClick(e) {
    const option = e.target.closest('[role="option"]');
    if (!option) return;

    const value = option.getAttribute('data-value');
    const label = option.textContent.trim();

    const allOptions = this.#listboxEl.querySelectorAll('[role="option"]');
    allOptions.forEach(opt => {
      opt.setAttribute('aria-selected', 'false');
      this.#updateOptionVisuals(opt, false);
    });

    option.setAttribute('aria-selected', 'true');
    this.#updateOptionVisuals(option, true);

    if (this.#textTargetEl) {
      this.#textTargetEl.textContent = label;
    }

    this.close();
    this.#triggerEl.focus();

    if (typeof this.#config.onSelect === 'function') {
      this.#config.onSelect(value, label, option);
    }
  }

  #updateOptionVisuals(option, isSelected) {
    const { active, inactive } = this.#config.toggleClass;
    const { hasCheckIcon, iconClasses } = this.#config;

    if (isSelected) {
      if (inactive?.length) option.classList.remove(...inactive);
      if (active?.length) option.classList.add(...active);
      
      if (hasCheckIcon && !option.querySelector('i[data-select-icon]')) {
        const icon = document.createElement('i');
        icon.setAttribute('data-select-icon', '');
        icon.setAttribute('aria-hidden', 'true');
        if (iconClasses?.length) icon.classList.add(...iconClasses);
        option.appendChild(icon);
      }
    } else {
      if (active?.length) option.classList.remove(...active);
      if (inactive?.length) option.classList.add(...inactive);
      
      if (hasCheckIcon) {
        const icon = option.querySelector('i[data-select-icon]');
        if (icon) icon.remove();
      }
    }
  }

  #handleClickOutside(event) {
    if (!this.#triggerEl.contains(event.target) && !this.#listboxContainerEl.contains(event.target)) {
      this.close();
    }
  }

  #handleKeyDown(event) {
    if (!this.#isOpen) return;

    if (event.key === 'Escape') {
      this.close();
      this.#triggerEl.focus();
      return;
    }

    const options = Array.from(this.#listboxEl.querySelectorAll('[role="option"]'));
    if (options.length === 0) return;

    const currentIndex = options.findIndex(opt => opt.getAttribute('aria-selected') === 'true');

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      const nextIndex = currentIndex < options.length - 1 ? currentIndex + 1 : 0;
      this.#focusAndSelectOption(options, nextIndex);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prevIndex = currentIndex > 0 ? currentIndex - 1 : options.length - 1;
      this.#focusAndSelectOption(options, prevIndex);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.close();
      this.#triggerEl.focus();
    }
  }

  #focusAndSelectOption(options, index) {
    options[index].click();
    options[index].scrollIntoView({ block: 'nearest' });
  }
}

export default class SelectMenu {
  #selector;
  #config;
  #instances;

  constructor(selector = '[data-select-menu-trigger]', config = {}) {
    this.#selector = selector;
    this.#config = config;
    this.#instances = [];
  }

  init() {
    const triggers = document.querySelectorAll(this.#selector);
    
    if (!triggers.length) return this.#instances;

    triggers.forEach(trigger => {
      const instance = new SelectMenuController(trigger, this.#config);
      instance.init();
      this.#instances.push(instance);
    });

    return this.#instances;
  }
}