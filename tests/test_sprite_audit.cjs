'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {cacheFile,evaluate,inventory,toCSV,argsParse,saveReports} = require('../scripts/auditar_sprites.cjs');
const {spriteSources} = require('../static/sprites.js');

function temp(action) {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'optpoke-audit-test-'));
  try {return action(dir);} finally {fs.rmSync(dir,{recursive:true,force:true});}
}
const base={key:'pikachu',dex_number:25,species:'Pikachu',form_name:null};
const regional={key:'vulpix-1',dex_number:37,species:'Vulpix',form_name:'Alolan'};

test('No network is used by cache inventory and absent cache is unknown',()=>temp(dir=>{
  const result=evaluate(base,true,dir);
  assert.equal(result.estado,'sin_comprobar');
  assert.equal(result.fallos_404,0);
  assert.ok(result.sin_comprobar>0);
}));
test('Cached regional shiny is distinguished from normal form',()=>temp(dir=>{
  const url=spriteSources(regional,true)[0].url;
  const {file}=cacheFile('image:'+url,'.png',dir);
  fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,'cached test bytes');
  assert.equal(evaluate(regional,true,dir).estado,'cacheado_revisar_forma');
  assert.equal(evaluate(regional,false,dir).estado,'sin_comprobar');
}));
test('Configured 404 sources are not retried in the audit',()=>temp(dir=>{
  const sources=spriteSources(base,true);
  for (const src of sources) {
    const {missing}=cacheFile('image:'+src.url,'.png',dir);
    fs.mkdirSync(path.dirname(missing),{recursive:true});
    fs.writeFileSync(missing,'');
  }
  const result=evaluate(base,true,dir);
  assert.equal(result.estado,'sin_imagen_en_fuentes_configuradas');
  assert.equal(result.fallos_404,sources.length);
}));
test('Temporary retry pause is not confused with a missing sprite',()=>temp(dir=>{
  const src=spriteSources(base,true)[0];
  const {file}=cacheFile('image:'+src.url,'.png',dir);
  fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file+'.retry','');
  assert.equal(evaluate(base,true,dir).estado,'sin_comprobar');
}));
test('PokeAPI variety metadata may provide an exact cached render',()=>temp(dir=>{
  const {file}=cacheFile('variety:vulpix-alola','.json',dir);
  const url='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home/shiny/37.png';
  fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,JSON.stringify({shiny:url,normal:null}));
  const sprite=cacheFile('image:'+url,'.png',dir);
  fs.mkdirSync(path.dirname(sprite.file),{recursive:true});
  fs.writeFileSync(sprite.file,'cached');
  assert.equal(evaluate(regional,true,dir).estado,'cacheado_revisar_forma');
}));
test('Inventory uses independent shiny and normal key sets',()=>temp(dir=>{
  const catalog={forms:[base,regional],shiny_keys:['pikachu'],normal_keys:['pikachu','vulpix-1']};
  assert.equal(inventory(catalog,dir).length,3);
  assert.equal(inventory(catalog,dir,true).length,1);
}));
test('CSV escaping and report output are stable',()=>temp(dir=>{
  const row={...evaluate(regional,true,dir),especie:'Mr. "Mime"; demo'};
  assert.match(toCSV([row]),/"Mr\. ""Mime""; demo"/);
  saveReports([row],path.join(dir,'reportes'));
  assert.ok(fs.existsSync(path.join(dir,'reportes','pendientes_especiales.csv')));
}));
test('Online checks require explicit opt-in and are capped at 30',()=>{
  assert.equal(argsParse([]).check,0);
  assert.equal(argsParse(['--probar-online','20']).check,20);
  for(const value of ['0','31','hola']) {
    assert.throws(()=>argsParse(['--probar-online',value]));
  }
});
