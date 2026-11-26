const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf8');

test('Bank TODO editor is syntactically valid and supports create, edit and delete', () => {
  assert.doesNotThrow(() => new vm.Script(source));
  assert.match(source, /function openBankTask\(task=null\)/);
  assert.match(source, /method:'POST'/);
  assert.match(source, /method:'DELETE'/);
  assert.match(source, /bank-edit/);
  assert.match(source, /bank-new-task/);
});

test('Bank TODO links are explicit and HOME credit requires transferred eligible OT', () => {
  assert.match(source, /Solo Bank/);
  assert.match(source, /Vincular a Shiny\/Living Dex/);
  assert.match(source, /Vinculada a/);
  assert.match(source, /bank\/goal-options/);
  assert.match(source, /goal_id:linked\.checked/);
  assert.match(source, /ot_origin:/);
  assert.match(source, /bt-ot-origin/);
  assert.match(source, /no cambia la Dex/);
  assert.doesNotMatch(source, /request\('\/api\/bank\/reconciliation'\)/);
});
test('Dex editor separates OT obtainability from NOT and HOME', () => {
  assert.match(source, /id="g-own-ot"/);
  assert.match(source, /id="g-ot"/);
  assert.match(source, /No obtenible con mi OT/);
  assert.match(source, /No significa que esté obtenido/);
});
