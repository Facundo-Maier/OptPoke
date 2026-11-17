/* Run with: node --test tests/test_sprites.cjs */
const assert = require('node:assert/strict');
const {test} = require('node:test');
const {spriteSources,showdownForm,pokeApiVariety,loadSprite,localImageURL} = require('../static/sprites.js');

const pokemon = (dex_number, species, form_name = null) => ({dex_number,species,form_name});

test('base shiny falls back from classic pixel art to a 3D HOME shiny render', () => {
  const sources=spriteSources(pokemon(1000,'Gholdengo'),true);
  assert.match(sources[0].url,/pokemon\/shiny\/1000\.png$/);
  assert.match(sources[1].url,/pokemon\/other\/home\/shiny\/1000\.png$/);
  assert.equal(sources[1].kind,'render');
  assert(sources.every(s => !/pokemon\/other\/home\/1000\.png$/.test(s.url)));
});

test('regional shiny never falls back to the incorrect default form', () => {
  const sources=spriteSources(pokemon(37,'Vulpix','Alolan'),true);
  assert.match(sources[0].url,/dex-shiny\/vulpix-alola.png$/);
  assert(sources.every(s => !/shiny\/37\.png$/.test(s.url)));
  assert(sources.every(s => !/\/dex\/vulpix-alola.png$/.test(s.url)));
  assert.equal(pokeApiVariety(pokemon(37,'Vulpix','Alolan')),'vulpix-alola');
});

test('special forms map to Showdown filenames rather than the base species', () => {
  assert.equal(showdownForm('Unown','!'),'unown-exclamation');
  assert.equal(showdownForm('Unown','?'),'unown-question');
  assert.equal(showdownForm('Unown','a'),'unown');
  assert.equal(showdownForm('Vivillon','Poké Ball'),'vivillon-pokeball');
  assert.equal(showdownForm('Tauros','Paldean Blaze Breed'),'tauros-paldeablaze');
  assert.equal(showdownForm('Pikachu','Hoenn Cap'),'pikachu-hoenn');
  assert.equal(showdownForm('Zygarde','0.1'),'zygarde-10');
  assert.equal(showdownForm('Maushold','Family of 4'),'maushold-four');
});

test('Alcremie sweets remain distinct, even when a static cream sprite exists', () => {
  const one=spriteSources(pokemon(869,'Alcremie','Ruby Cream, Berry'),true);
  const other=spriteSources(pokemon(869,'Alcremie','Ruby Cream, Ribbon'),true);
  assert.match(one[0].url,/ani-shiny\/alcremie-rubycream-berry.gif$/);
  assert.match(other[0].url,/ani-shiny\/alcremie-rubycream-ribbon.gif$/);
  assert.notEqual(one[0].url,other[0].url);
  assert(one.every(s=>!s.url.includes('/dex-shiny/')));
});

test('default vanilla Alcremie uses the correct base animation', () => {
  const first=spriteSources(pokemon(869,'Alcremie','Vanilla Cream, Strawberry'),true);
  assert.match(first[0].url,/ani-shiny\/alcremie.gif$/);
});

test('normal sprites do not use shiny assets', () => {
  const paths=spriteSources(pokemon(37,'Vulpix','Alolan'),false).map(s=>s.url);
  assert(paths.every(path => !path.includes('shiny')));
});

test('loading recovers from failed sprite and chooses 3D HOME render', () => {
  const listeners={};
  const placeholder={style:{}};
  const image={isConnected:true,style:{},nextElementSibling:placeholder,
    classList:{toggle(name,on){this[name]=on;}},
    addEventListener(name,handler){listeners[name]=handler;}};
  loadSprite(image,pokemon(1000,'Gholdengo'),true);
  assert.match(decodeURIComponent(image.src),/shiny\/1000\.png$/);
  listeners.error();
  assert.match(decodeURIComponent(image.src),/home\/shiny\/1000\.png$/);
  listeners.load();
  assert.equal(image.classList['sprite-render'],true);
  assert.equal(placeholder.style.display,'none');
});


test('browser sprite references go through the local disk cache', () => {
  const url = 'https://play.pokemonshowdown.com/sprites/dex-shiny/vulpix-alola.png';
  const proxied = localImageURL(url);
  assert.equal(proxied, '/api/sprites/image?url='+encodeURIComponent(url));
  assert(!proxied.startsWith('https://'));
});

test('Fall season uses an exact Autumn shiny sprite for Deerling and Sawsbuck', () => {
  for (const [dex, species] of [[585, 'Deerling'], [586, 'Sawsbuck']]) {
    const sources = spriteSources(pokemon(dex, species, 'Fall'), true);
    assert.match(sources[0].url, new RegExp('dex-shiny/' + species.toLowerCase() + '-autumn\\.png$'));
    assert(sources.every(s => !s.url.endsWith('/' + species.toLowerCase() + '.png')));
  }
});

test('Dudunsparce three segments use the Showdown threesegment filename', () => {
  const sources = spriteSources(pokemon(982, 'Dudunsparce', '3 Segment'), true);
  assert.match(sources[0].url, /dex-shiny\/dudunsparce-threesegment\.png$/);
  assert(sources.every(s => !s.url.endsWith('/dudunsparce.png')));
});

test('World Cap Pikachu has the exact HOME render in Living, never shiny fallback', () => {
  const normal = spriteSources(pokemon(25, 'Pikachu', 'World Cap'), false);
  const shiny = spriteSources(pokemon(25, 'Pikachu', 'World Cap'), true);
  assert(normal.some(s => s.url.endsWith('/home/pikachu-world.png') && s.kind === 'render'));
  assert(shiny.every(s => !s.url.endsWith('/home/pikachu-world.png')));
  assert(normal.every(s => !s.url.endsWith('/pikachu.png')));
});

test('Default visual variants use exact base filenames in both collections', () => {
  const cases = [
    [201, 'Unown', 'a', 'unown'],
    [741, 'Oricorio', 'Baile Style', 'oricorio'],
    [774, 'Minior', 'Red Core', 'minior'],
  ];
  for (const [dex, species, form, file] of cases) {
    for (const shiny of [true,false]) {
      const sources = spriteSources(pokemon(dex, species, form), shiny);
      const dir = shiny ? 'dex-shiny' : 'dex';
      assert.match(sources[0].url, new RegExp('/' + dir + '/' + file + '\\.png$'));
      assert(sources.every(s => !s.url.endsWith('/' + file + '-a.png')));
      assert(sources.every(s => !s.url.endsWith('/' + file + '-baile.png')));
      assert(sources.every(s => !s.url.endsWith('/' + file + '-red.png')));
    }
  }
});

test('Alternate variants remain distinct from default Unown, Oricorio and Minior', () => {
  assert.equal(showdownForm('Unown', 'b'), 'unown-b');
  assert.equal(showdownForm('Oricorio', 'Sensu Style'), 'oricorio-sensu');
  assert.equal(showdownForm('Minior', 'Blue Core'), 'minior-blue');
});
