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
  assert.equal(showdownForm('Unown','a'),'unown-a');
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
