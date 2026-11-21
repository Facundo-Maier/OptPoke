'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname,'..');
const js=fs.readFileSync(path.join(root,'static/app.js'),'utf8');
const html=fs.readFileSync(path.join(root,'static/index.html'),'utf8');
const css=fs.readFileSync(path.join(root,'static/styles.css'),'utf8');

test('sidebar can open and collapse with an accessible persistent toggle',()=>{
  assert.doesNotThrow(()=>new vm.Script(js));
  assert.match(html,/id="sidebar-toggle"[^>]+aria-expanded="false"/);
  assert.match(html,/class="sidebar-toggle sidebar-edge-toggle"/);
  assert.match(css,/\.sidebar-edge-toggle\{[\s\S]*position:fixed/);
  const header=html.split('<header class="topbar">',2)[1].split('</header>',1)[0];
  assert.doesNotMatch(header,/sidebar-toggle/);
  assert.match(html,/id="app-shell"/);
  assert.match(html,/data-page="games"/);
  assert.match(js,/function setSidebar\(open\)/);
  assert.match(js,/sidebar\.inert=!open/);
  assert.match(css,/sidebar-collapsed \.sidebar/);
});
test('games manage separate save profiles and Bank selects them',()=>{
  assert.match(js,/async function renderGames\(\)/);
  assert.match(js,/function openGameSave\(game,save=null\)/);
  assert.match(js,/\/api\/game-saves/);
  assert.match(js,/id="bt-save"/);
  assert.match(js,/selectedSave\?\.game\|\|task\?\.game/);
  assert.doesNotMatch(js,/id="bt-game"/);
});

test('both Dex views expose a clearly disabled games filter placeholder',()=>{
  assert.match(js,/id="dex-available-games-only" type="checkbox" disabled/);
  assert.match(js,/Solo mostrar Pokémon obtenibles en mis juegos/);
  assert.match(js,/Próximamente · filtro sin implementar/);
  assert.doesNotMatch(js,/new URLSearchParams\([^)]*available_games_only/);
});
