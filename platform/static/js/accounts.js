"use strict";
(() => {
  const form = document.getElementById('producer-account-form');
  if (!form) return;
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const rows = [...form.querySelectorAll('[data-parcel-option]')];
  const boxes = rows.map(row => row.querySelector('input'));
  function count() {
    const total = boxes.filter(box => box.checked).length;
    document.getElementById('assignment-count').textContent = total === 1 ? '1 parcela seleccionada' : `${total} parcelas seleccionadas`;
  }
  function mode() {
    const selected = form.querySelector('[name="access_mode"]:checked')?.value;
    form.querySelectorAll('[data-access-panel]').forEach(panel => {
      panel.hidden = panel.dataset.accessPanel !== selected;
      panel.querySelectorAll('input,button').forEach(input => { input.disabled = panel.hidden; });
    });
  }
  form.querySelectorAll('[name="access_mode"]').forEach(radio => radio.addEventListener('change', mode));
  document.getElementById('parcel-filter').addEventListener('input', event => {
    const search = normalize(event.target.value.trim());
    rows.forEach(row => { row.hidden = !normalize(row.textContent).includes(search); });
    document.getElementById('no-parcel-matches').hidden = rows.some(row => !row.hidden);
  });
  form.querySelectorAll('[data-parcel-action]').forEach(button => button.addEventListener('click', () => {
    rows.forEach((row, index) => {
      if (button.dataset.parcelAction === 'clear' || !row.hidden) {
        boxes[index].checked = button.dataset.parcelAction === 'select';
      }
    });
    count();
  }));
  boxes.forEach(box => box.addEventListener('change', count));
  mode();
  count();
})();
