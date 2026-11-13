/* node --test tests/test_dex_list.cjs */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {renderRows, labelFor, homeControl, otControl} = require('../static/dex-list.js');
const entry = (overrides={}) => ({
  id:1, dex_number:37, species:'Vulpix', form_name:'Alolan',
  form_key:'vulpix-alola', obtainability:'unverified',
  in_home:0, target:1, ...overrides,
});
const sprite = row => `<img data-sprite-key="${row.form_key}" alt="sprite">`;

test('National Pokédex is one numbered row per form, no cards and no nested buttons', () => {
  const html=renderRows([entry(),entry({id:2,dex_number:38,species:'Ninetales'})],sprite,1);
  assert.match(html,/<ul class="dex-list-body">/);
  assert.equal((html.match(/class="dex-list-item"/g)||[]).length,2);
  assert.match(html,/class="dex-row is-selected/);
  assert.match(html,/class="dex-select" data-select-goal="1" aria-pressed="true"/);
  assert.match(html,/class="dex-number">0037<\/span>/);
  assert.match(html,/data-sprite-key="vulpix-alola"/);
  assert.match(html,/data-toggle-home="1"/);
  assert.match(html,/data-edit-goal="1"/);
  assert.doesNotMatch(html,/poke-card|dex-grid/);
});

test('Single-copy goals can be marked En HOME or returned to Pendiente inline', () => {
  const pending=homeControl(entry());
  const done=homeControl(entry({in_home:1}));
  assert.match(pending,/data-toggle-home="1"/);
  assert.match(pending,/Marcar en HOME/);
  assert.match(pending,/Pendiente/);
  assert.match(done,/data-toggle-home="1"/);
  assert.match(done,/Marcar como pendiente/);
  assert.match(done,/En HOME/);
});

test('Multi-copy goals open the quantity editor instead of jumping 0/3 to 3/3', () => {
  const markup=homeControl(entry({target:3,in_home:1}));
  assert.match(markup,/Parcial/);
  assert.match(markup,/data-edit-goal="1"/);
  assert.doesNotMatch(markup,/data-toggle-home/);
});

test('Locked goals show a lock without inline HOME toggling', () => {
  const markup=homeControl(entry({obtainability:'locked'}));
  assert.match(markup,/Con candado/);
  assert.match(markup,/🔒/);
  assert.doesNotMatch(markup,/<button/);
});

test('Selected row and HOME status are separate keyboard-accessible controls', () => {
  const markup=renderRows([entry()],sprite,1);
  assert.equal((markup.match(/<button\b/g)||[]).length,4); // select, toggle HOME, OT, edit
  assert.equal((markup.match(/<\/button>/g)||[]).length,4);
  assert.match(markup,/aria-pressed="true"/);
});

test('Species and form names are HTML escaped even in button labels', () => {
  const markup=renderRows([entry({species:'<script>',form_name:'Original "x" & <y>'})],()=>'<i>placeholder</i>');
  assert.doesNotMatch(markup,/<script>/);
  assert.match(markup,/&lt;script&gt;/);
  assert.match(markup,/&quot;x&quot; &amp; &lt;y&gt;/);
});

test('Empty Pokédex does not invent phantom rows', () => {
  const markup=renderRows([],sprite);
  assert.match(markup,/dex-list-body/);
  assert.doesNotMatch(markup,/class="dex-list-item"/);
});

test('OT exception is a distinct interactive control regardless of HOME or locked', () => {
  assert.match(otControl(entry()), /OT —/);
  assert.match(otControl(entry({ot_exception:1})), /OT ajeno/);
  assert.match(otControl(entry({ot_exception:1,obtainability:'locked'})), /data-toggle-ot="1"/);
  const markup=renderRows([entry({ot_exception:1})],sprite);
  assert.match(markup,/class="dex-ot-cell"/);
  assert.match(markup,/aria-pressed="true"/);
});
