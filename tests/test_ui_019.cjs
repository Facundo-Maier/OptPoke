const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const js=fs.readFileSync('static/app.js','utf8');
const css=fs.readFileSync('static/styles.css','utf8');

test('direct page selector is accessible and updates offset',()=>{
  assert.match(js,/id="dex-jump-page"/);
  assert.match(js,/aria-label="Ir a la página y rango de resultados"/);
  assert.match(js,/state\.offset=\(Number\(e\.target\.value\)-1\)\*state\.limit/);
});
test('selected preview sprite floats gently with reduced motion support',()=>{
  assert.match(css,/\.dex-preview-image img\{animation:optpoke-selected-float/);
  assert.match(css,/transform:translateY\(-6px\)/);
  assert.match(css,/prefers-reduced-motion:reduce/);
});
test('Austin import is always previewed and NOT never maps to HOME in UI',()=>{
  assert.match(js,/\/api\/austin\/.*preview|sendAustin\(file,'preview'/);
  assert.match(js,/NOT = No OT/);
  assert.match(js,/Confirmar.*c\.changed/);
});

test('page selector displays first and last filtered record numbers',()=>{
  assert.match(js,/const first=i\*state\.limit\+1, last=Math\.min/);
  assert.match(js,/nf\.format\(first\).*nf\.format\(last\)/);
});
test('import allows separate Shiny and Living files with distinct confirmation controls',()=>{
  assert.match(js,/id="austin-shiny-file"/);
  assert.match(js,/id="austin-normal-file"/);
  assert.match(js,/source:'shiny'/);
  assert.match(js,/source:'normal'/);
  assert.match(js,/c\.evo_unresolved/);
});
