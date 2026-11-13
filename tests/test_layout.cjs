/* node --test tests/test_layout.cjs */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const src = name => readFileSync(join(__dirname,'../static',name),'utf8');

test('Both Pokédex views share a sticky header while the list uses normal document scroll', () => {
  const app = src('app.js');
  const css = src('styles.css');
  assert.match(app, /class="dex-sticky-header"/);
  assert.match(css, /\.dex-sticky-header\s*\{[^}]*position:sticky;[^}]*top:0;/);
  assert.match(css, /\.pokedex-shell\{[^}]*overflow:visible;/);
  assert.doesNotMatch(css, /\.dex-list-body\s*\{[^}]*overflow-y\s*:\s*(auto|scroll)/);
});

test('Search icon uses an SVG and is centered independently of text font metrics', () => {
  const app = src('app.js');
  const css = src('styles.css');
  assert.match(app, /<svg class="dex-search-icon"/);
  assert.match(css, /\.dex-search-icon\s*\{[^}]*top:50%;[^}]*translateY\(-50%\)/);
  assert.match(css, /\.dex-controls \.search-wrap::before\{content:none;/);
});

test('Changing pages scrolls the rows below the persistent controls', () => {
  const app = src('app.js');
  assert.match(app, /function scrollDexToList\(\)/);
  assert.match(app, /scrollDexToList\(\);/);
  assert.match(app, /window\.scrollTo\(\{top:Math\.max\(0,top\),behavior:'instant'\}\)/);
});

test('Selected Pokémon preview sticks below dynamic header without trapping the index scroll', () => {
  const app = src('app.js');
  const css = src('styles.css');
  assert.match(app, /id="dex-spotlight-content" class="dex-spotlight-inner"/);
  assert.match(app, /function setupDexSpotlight\(\)/);
  assert.match(app, /new ResizeObserver\(update\)/);
  assert.match(app, /--dex-header-height/);
  assert.match(css, /\.dex-spotlight-inner\{position:sticky;top:calc\(var\(--dex-header-height, 160px\) \+ 10px\)/);
  assert.match(css, /\.pokedex-shell\{border:0;background:transparent;overflow:visible;/);
  assert.doesNotMatch(css, /\.dex-spotlight-inner\s*\{[^}]*overflow-y:\s*(auto|scroll)/);
  assert.match(css, /@media\(max-width:850px\)\{\s*\.dex-spotlight\{display:none\}/);
});

test('Pokédex and common panels use flat separators rather than nested cards', () => {
  const css = src('styles.css');
  assert.match(css, /\.dex-top\{border:0;background:transparent\}/);
  assert.match(css, /\.dex-list-body\{background:transparent\}/);
  assert.match(css, /\.panel\{background:transparent;border:0;border-top:/);
  assert.match(css, /\.stat-card\{background:transparent;border:0;/);
});
