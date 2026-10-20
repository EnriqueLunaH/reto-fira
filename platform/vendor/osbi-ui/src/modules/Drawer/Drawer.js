// osbi-v1/src/js/modules/Drawer/Drawer.js

import { BREAKPOINTS } from '../../constants/breakpoints.js';
import { DRAWER_CLASSES, DRAWER_SELECTORS, DRAWER_TRANSITIONS, LOCK_CLASSES } from '../../constants/drawer.js';

const activeDrawers = [];
let isGlobalListenerInitialized = false;

class DrawerController {
  #triggerEl;
  #drawerEl;
  #backdropEl;
  #isOpen = false;
  #transitionTimeout;
  #mql;

  constructor(triggerEl, config) {
    this.#triggerEl = triggerEl;

    const targetId = this.#triggerEl.getAttribute('aria-controls');
    this.#drawerEl = document.getElementById(targetId);

    if (this.#drawerEl) {
      this.#backdropEl = this.#drawerEl.closest(DRAWER_SELECTORS.BACKDROP);
    }

    if (config.unlockCondition && window.matchMedia) {
      this.#mql = window.matchMedia(`(min-width: ${config.unlockCondition})`);
    }
  }

  init() {
    if (!this.#drawerEl) return;
    this.#initListeners();
    this.#initMediaQuery();
  }

  #initListeners() {
    this.#triggerEl.addEventListener('click', this.open);
    
    this.#drawerEl.addEventListener('click', (e) => {
      const closeBtn = e.target.closest(DRAWER_SELECTORS.CLOSE);
      if (closeBtn) {
        // [Corrección 1]: Verificación estricta de pertenencia de instancia para prevenir el cierre en cascada por Event Bubbling
        const closestDrawer = closeBtn.closest(DRAWER_SELECTORS.DRAWER);
        if (closestDrawer === this.#drawerEl) {
          e.preventDefault();
          e.stopPropagation();
          this.close();
        }
      }
    });
  }

  #initMediaQuery() {
    if (!this.#mql) return;
    
    const handleMediaChange = (e) => {
      if (e.matches && this.#isOpen) {
        this.reset();
      }
    };
    
    if (this.#mql.addEventListener) {
      this.#mql.addEventListener('change', handleMediaChange);
    } else {
      this.#mql.addListener(handleMediaChange);
    }
  }

  open = (e) => {
    if (e) e.preventDefault();
    if (this.#isOpen) return;

    if (this.#mql && this.#mql.matches) return;

    const currentActiveCount = activeDrawers.length;
    const isFirstDrawer = currentActiveCount === 0;

    if (!isFirstDrawer) {
      const parentDrawer = activeDrawers[currentActiveCount - 1];
      parentDrawer.getDrawerElement().classList.add(LOCK_CLASSES.SCROLL_LOCK);
    } else {
      document.body.classList.add(LOCK_CLASSES.SCROLL_LOCK);
    }

    activeDrawers.push(this);
    this.#isOpen = true;
    this.#triggerEl.setAttribute('aria-expanded', 'true');

    // [Corrección 2]: Aplicación de clases de transición previa al cambio de estado visual
    if (isFirstDrawer && this.#backdropEl) {
      this.#backdropEl.classList.add(...DRAWER_TRANSITIONS.BACKDROP);
    }
    this.#drawerEl.classList.add(...DRAWER_TRANSITIONS.DRAWER);

    // Reflow forzado leyendo 'offsetWidth' para asegurar que el motor de renderizado aplique las transiciones antes del cambio final de clase
    void this.#drawerEl.offsetWidth;

    if (isFirstDrawer && this.#backdropEl) {
      this.#backdropEl.classList.add(...DRAWER_CLASSES.BACKDROP_ACTIVE);
      this.#backdropEl.classList.remove(...DRAWER_CLASSES.BACKDROP_INACTIVE);
    }
    
    this.#drawerEl.classList.add(...DRAWER_CLASSES.DRAWER_ACTIVE);
    this.#drawerEl.classList.remove(...DRAWER_CLASSES.DRAWER_INACTIVE, LOCK_CLASSES.SCROLL_LOCK);

    clearTimeout(this.#transitionTimeout);
    this.#transitionTimeout = setTimeout(() => {
      if (isFirstDrawer && this.#backdropEl) {
        this.#backdropEl.classList.remove(...DRAWER_TRANSITIONS.BACKDROP);
      }
      this.#drawerEl.classList.remove(...DRAWER_TRANSITIONS.DRAWER);
      
      const firstFocusable = this.#drawerEl.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (firstFocusable) firstFocusable.focus();
    }, 200);
  }

  close = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!this.#isOpen) return;

    const index = activeDrawers.indexOf(this);
    if (index === -1) return;

    const drawersToClose = activeDrawers.splice(index);
    
    for (let i = drawersToClose.length - 1; i >= 0; i--) {
      drawersToClose[i].executeClose(i === 0);
    }
  }

  executeClose(returnFocus) {
    this.#isOpen = false;
    this.#triggerEl.setAttribute('aria-expanded', 'false');

    const activeCount = activeDrawers.length;
    const isLastDrawer = activeCount === 0;

    if (!isLastDrawer) {
      const newParentDrawer = activeDrawers[activeCount - 1];
      newParentDrawer.getDrawerElement().classList.remove(LOCK_CLASSES.SCROLL_LOCK);
    } else {
      document.body.classList.remove(LOCK_CLASSES.SCROLL_LOCK);
    }

    if (isLastDrawer && this.#backdropEl) {
      this.#backdropEl.classList.add(...DRAWER_TRANSITIONS.BACKDROP);
    }
    this.#drawerEl.classList.add(...DRAWER_TRANSITIONS.DRAWER);

    // Reflow forzado
    void this.#drawerEl.offsetWidth;

    if (isLastDrawer && this.#backdropEl) {
      this.#backdropEl.classList.add(...DRAWER_CLASSES.BACKDROP_INACTIVE);
      this.#backdropEl.classList.remove(...DRAWER_CLASSES.BACKDROP_ACTIVE);
    }
    
    this.#drawerEl.classList.add(...DRAWER_CLASSES.DRAWER_INACTIVE);
    this.#drawerEl.classList.remove(...DRAWER_CLASSES.DRAWER_ACTIVE);

    if (returnFocus) {
      this.#triggerEl.focus();
    }

    clearTimeout(this.#transitionTimeout);
    this.#transitionTimeout = setTimeout(() => {
      this.#drawerEl.classList.remove(...DRAWER_TRANSITIONS.DRAWER);
      if (isLastDrawer && this.#backdropEl) {
        this.#backdropEl.classList.remove(...DRAWER_TRANSITIONS.BACKDROP);
      }
    }, 200);
  }

  reset = () => {
    if (!this.#isOpen) return;
    this.#isOpen = false;
    this.#triggerEl.setAttribute('aria-expanded', 'false');
    
    const index = activeDrawers.indexOf(this);
    if (index !== -1) {
      activeDrawers.splice(index, 1);
    }

    clearTimeout(this.#transitionTimeout);

    this.#drawerEl.classList.remove(...DRAWER_TRANSITIONS.DRAWER, ...DRAWER_CLASSES.DRAWER_ACTIVE, LOCK_CLASSES.SCROLL_LOCK);
    this.#drawerEl.classList.add(...DRAWER_CLASSES.DRAWER_INACTIVE);

    if (activeDrawers.length === 0) {
      document.body.classList.remove(LOCK_CLASSES.SCROLL_LOCK);
      if (this.#backdropEl) {
        this.#backdropEl.classList.remove(...DRAWER_TRANSITIONS.BACKDROP, ...DRAWER_CLASSES.BACKDROP_ACTIVE);
        this.#backdropEl.classList.add(...DRAWER_CLASSES.BACKDROP_INACTIVE);
      }
    }
  }

  getDrawerElement() {
    return this.#drawerEl;
  }
}

export default class Drawer {
  #selector;
  #config;
  #instances;

  constructor(selector = DRAWER_SELECTORS.TRIGGER, config = {}) {
    this.#selector = selector;
    this.#config = { unlockCondition: null, ...config };
    this.#instances = [];
  }

  init() {
    const triggers = document.querySelectorAll(this.#selector);
    if (!triggers.length) return this.#instances;

    triggers.forEach(trigger => {
      const instance = new DrawerController(trigger, this.#config);
      instance.init();
      this.#instances.push(instance);
    });

    this.#initGlobalListeners();
    return this.#instances;
  }

  #initGlobalListeners() {
    if (isGlobalListenerInitialized) return;
    isGlobalListenerInitialized = true;

    document.addEventListener('click', (e) => {
      const backdrop = e.target.closest(DRAWER_SELECTORS.BACKDROP);
      if (backdrop && e.target === backdrop && activeDrawers.length > 0) {
        activeDrawers[activeDrawers.length - 1].close();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && activeDrawers.length > 0) {
        activeDrawers[activeDrawers.length - 1].close();
      }
    });
  }
}