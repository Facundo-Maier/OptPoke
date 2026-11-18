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

test('Bank TODO classification is explicit and never synchronizes HOME', () => {
  assert.match(source, /Solo Bank/);
  assert.match(source, /Relacionar con un objetivo de la Pokédex/);
  assert.match(source, /bank\/goal-options/);
  assert.match(source, /goal_id:linked\.checked/);
  assert.match(source, /no sincroniza automáticamente HOME/);
  assert.doesNotMatch(source, /request\('\/api\/bank\/reconciliation'\)/);
});
