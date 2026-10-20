// osbi-v1/src/js/core/FloatingManager.js

/**
 * FloatingManager
 * Implementa el patrón Publish/Subscribe para actuar como un Mediador global.
 * Coordina el estado de los elementos flotantes (Dropdown, Select, Combobox)
 * para asegurar que solo los elementos correspondientes permanezcan abiertos.
 */
export const FloatingManager = {
  EVENT_NAME: 'osbi:floating:open',

  /**
   * Notifica a todos los suscriptores que un elemento flotante se ha abierto.
   * @param {string} id - El ID del contenedor flotante abierto.
   * @param {HTMLElement} triggerEl - El elemento del DOM que disparó la apertura.
   */
  notifyOpen(id, triggerEl) {
    document.dispatchEvent(new CustomEvent(this.EVENT_NAME, {
      detail: { id, triggerEl }
    }));
  },

  /**
   * Suscribe un componente para escuchar aperturas de otros elementos flotantes.
   * @param {Function} callback - La función a ejecutar.
   */
  subscribe(callback) {
    document.addEventListener(this.EVENT_NAME, callback);
  },

  /**
   * Elimina la suscripción de un componente.
   * @param {Function} callback - La función a remover.
   */
  unsubscribe(callback) {
    document.removeEventListener(this.EVENT_NAME, callback);
  }
};