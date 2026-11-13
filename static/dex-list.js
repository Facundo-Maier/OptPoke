/*
 * Pokédex Nacional: índice compacto y controles por objetivo.
 * La selección y las acciones de HOME son botones separados: no se anidan
 * controles y es posible navegar únicamente con teclado.
 */
'use strict';
(function (root) {
  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g,
    c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function labelFor(item) {
    const done = item.in_home >= item.target;
    if (item.obtainability === 'locked') return 'Con candado';
    if (done) return 'En HOME';
    if (item.in_home > 0) return 'Parcial';
    return 'Pendiente';
  }

  function homeControl(item) {
    const id = Number(item.id);
    const label = labelFor(item);
    const done = item.in_home >= item.target;
    const locked = item.obtainability === 'locked';
    const css = locked ? 'locked' : done ? 'done' : item.in_home > 0 ? 'partial' : 'missing';
    const symbol = locked ? '🔒' : done ? '✓' : item.in_home > 0 ? '◒' : '○';
    const content = `<span class="dex-state-symbol" aria-hidden="true">${symbol}</span><span>${label}</span>`;
    if (locked) {
      return `<span class="dex-status dex-status-${css}" title="Shiny no disponible; editá el objetivo para cambiarlo">${content}</span>`;
    }
    if (Number(item.target) !== 1) {
      // Un solo clic nunca puede afirmar que llegaron varios ejemplares a HOME.
      return `<button type="button" class="dex-status dex-status-${css}" data-edit-goal="${id}"
        aria-label="Editar cantidades en HOME de ${escapeHTML(item.species)} (${Number(item.in_home)} de ${Number(item.target)})" title="Editar cantidad en HOME">${content}</button>`;
    }
    return `<button type="button" class="dex-status dex-status-${css}" data-toggle-home="${id}"
      aria-label="${done?'Marcar como pendiente':'Marcar en HOME'}: ${escapeHTML(item.species)}${item.form_name?' · '+escapeHTML(item.form_name):''}"
      title="${done?'Volver a Pendiente':'Marcar como En HOME'} con un clic">${content}</button>`;
  }

  function otControl(item) {
    const flagged = Boolean(item.ot_exception);
    const name = escapeHTML(item.species);
    return `<button type="button" class="dex-ot ${flagged?'dex-ot-exception':'dex-ot-normal'}"
      data-toggle-ot="${Number(item.id)}" aria-pressed="${flagged}"
      aria-label="${flagged?'Quitar':'Marcar'} excepción de OT: ${name}"
      title="${flagged?'Se obtiene sin tu OT. Clic para quitar la marca':'Marcar que no se puede obtener con tu OT'}">${flagged?'OT ajeno':'OT —'}</button>`;
  }

  function renderRows(items, spriteMarkup, selectedId=null) {
    const rows = items.map(item => {
      const done = item.in_home >= item.target;
      const locked = item.obtainability === 'locked';
      const selected = Number(item.id) === Number(selectedId);
      const name = escapeHTML(item.species);
      const form = escapeHTML(item.form_name || 'Forma base');
      const number = Number.isFinite(Number(item.dex_number)) && item.dex_number != null
        ? String(item.dex_number).padStart(4, '0') : '????';
      return `<li class="dex-list-item"><div class="dex-row ${selected?'is-selected':''} ${done?'done':''} ${locked?'locked':''}" data-row-goal="${Number(item.id)}">
        <button type="button" class="dex-select" data-select-goal="${Number(item.id)}" aria-pressed="${selected?'true':'false'}"
          aria-label="Seleccionar ${name}, ${form}, número ${number}">
          <span class="dex-number">${number}</span>
          <span class="dex-sprite">${spriteMarkup(item)}</span>
          <span class="dex-info"><span class="dex-pokemon" title="${name}">${name}</span><span class="dex-form" title="${form}">${form}</span></span>
        </button>
        <span class="dex-state-cell">${homeControl(item)}</span>
        <span class="dex-ot-cell">${otControl(item)}</span>
        <span class="dex-count"><strong>${Number(item.in_home)}</strong><span> / ${Number(item.target)}</span></span>
        <button type="button" class="dex-edit" data-edit-goal="${Number(item.id)}" aria-label="Editar ${name}, ${form}" title="Editar objetivo">⋯</button>
      </div></li>`;
    }).join('');

    return `<div class="dex-index-table" aria-label="Lista de Pokémon">
      <div class="dex-list-head" aria-hidden="true"><span class="dex-head-pokemon">Nº · Pokémon</span><span>Estado</span><span>OT</span><span class="dex-head-count">En HOME</span><span></span></div>
      <ul class="dex-list-body">${rows}</ul>
    </div>`;
  }
  root.OptPokeDex = {renderRows, labelFor, homeControl, otControl};
  if (typeof module !== 'undefined' && module.exports) module.exports = {renderRows, labelFor, homeControl, otControl};
})(typeof window !== 'undefined' ? window : globalThis);
