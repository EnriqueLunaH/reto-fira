// osbi-v1/src/js/constants/drawer.js

export const DRAWER_SELECTORS = Object.freeze({
  TRIGGER: '[data-drawer-trigger]',
  BACKDROP: '[data-drawer-backdrop]',
  CLOSE: '[data-drawer-close]',
  DRAWER: '[data-drawer]'
});

export const DRAWER_CLASSES = Object.freeze({
  BACKDROP_INACTIVE: ['opacity-0', 'visibility-hidden', 'pointer-events-none'],
  BACKDROP_ACTIVE: ['opacity-100', 'visibility-visible', 'pointer-events-auto'],
  DRAWER_INACTIVE: ['translate-x--100'],
  DRAWER_ACTIVE: ['translate-x-none']
});

export const DRAWER_TRANSITIONS = Object.freeze({
  BACKDROP: ['transition-backdrop', 'duration-200', 'ease-in'],
  DRAWER: ['transition-transform', 'duration-200', 'ease-in-out']
});

export const LOCK_CLASSES = Object.freeze({
  SCROLL_LOCK: 'overflow-hidden',
  SCROLL_UNLOCK: 'overflow-auto',
  POINTER_LOCK: 'pointer-events-none',
  POINTER_UNLOCK: 'pointer-events-auto'
});