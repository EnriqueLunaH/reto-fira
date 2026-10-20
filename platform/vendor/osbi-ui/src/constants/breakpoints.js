// osbi-v1/src/js/constants/breakpoints.js

/**
 * Global Breakpoints Constant
 * * Mirrors the SCSS $breakpoints map (src/scss/abstracts/_breakpoints.scss).
 * Used for hardware-accelerated JS media queries (window.matchMedia).
 * Object.freeze ensures the configuration is immutable.
 */
export const BREAKPOINTS = Object.freeze({
  sm: '30rem',     // ~480px
  md: '48rem',     // ~768px
  lg: '64rem',     // ~1024px
  xl: '80rem',     // ~1280px
  '2xl': '96rem'   // ~1536px
});