const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'static', 'app.js'), 'utf8');

test('Plan Bank compiles and shows a read-only reconciliation preview', () => {
  assert.doesNotThrow(() => new vm.Script(source));
  assert.match(source, /request\('\/api\/bank\/reconciliation'\)/);
  assert.match(source, /bankSuggestionCell\(t\)/);
  assert.match(source, /Coincidencias propuestas \(sin confirmar\)/);
  assert.match(source, /no transfiere ejemplares ni modifica HOME/);
  assert.match(source, /html\(goal\.form_name\|\|'Forma base'\)/);
});
