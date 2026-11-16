#!/usr/bin/env node
/**
 * Auditoría offline-first. Por defecto solo inspecciona la caché en disco.
 * --probar-online N consulta como máximo N fuentes mediante FastAPI local.
 * Reutiliza el mismo resolvedor de imágenes que la interfaz.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const {spriteSources, pokeApiVariety} = require('../static/sprites.js');
const CATALOG = path.join(__dirname, '..', 'data', 'catalog.json');

function cacheRoot(env = process.env) {
  return path.resolve(env.OPTPOKE_DATA_DIR || path.join(os.homedir(), '.optpoke'), 'sprites');
}
function cacheFile(key, ext, root) {
  const digest = crypto.createHash('sha256').update(key, 'utf8').digest('hex');
  const dir = path.join(root, digest.slice(0, 2));
  return {file: path.join(dir, digest + ext), missing: path.join(dir, digest + '.missing')};
}
function imageRecord(url, root) {
  const ext = url.toLowerCase().endsWith('.gif') ? '.gif' : '.png';
  const {file, missing} = cacheFile('image:' + url, ext, root);
  const found = fs.existsSync(file);
  const absent = fs.existsSync(missing);
  const pause = file + '.retry';
  const paused = fs.existsSync(pause) && Date.now() - fs.statSync(pause).mtimeMs < 15 * 60 * 1000;
  return {url, state:found?'cacheado':absent?'404':paused?'reintento_pausado':'sin_comprobar', file:found?file:null};
}
function varietyRecord(item, shiny, root) {
  const variety = pokeApiVariety(item);
  if (!variety) return {key:null, state:'no_aplica', url:null};
  const {file, missing} = cacheFile('variety:' + variety, '.json', root);
  if (fs.existsSync(file)) {
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf8'));
      return {key:variety, state:'cacheado', url:data[shiny?'shiny':'normal'] || null};
    } catch (_) {
      return {key:variety, state:'cache_invalida', url:null};
    }
  }
  const pause = file + '.retry';
  const paused = fs.existsSync(pause) && Date.now() - fs.statSync(pause).mtimeMs < 15 * 60 * 1000;
  return {key:variety, state:fs.existsSync(missing)?'404':paused?'reintento_pausado':'sin_comprobar', url:null};
}
function evaluate(item, shiny, root) {
  const seen = new Set();
  const sources = spriteSources(item, shiny).map(s=>s.url);
  const variety = varietyRecord(item, shiny, root);
  if (variety.url) sources.push(variety.url);
  const records = sources.filter(url=>!seen.has(url)&&seen.add(url)).map(url=>imageRecord(url,root));
  const success = records.find(rec=>rec.state==='cacheado');
  const uncertain = records.some(rec=>['sin_comprobar','reintento_pausado'].includes(rec.state)) ||
    ['sin_comprobar','reintento_pausado'].includes(variety.state);
  const state = success ? 'cacheado_revisar_forma'
    : (!records.length && variety.state==='no_aplica') ? 'sin_fuente_configurada'
    : variety.state==='cache_invalida' ? 'revisar_cache'
    : uncertain ? 'sin_comprobar' : 'sin_imagen_en_fuentes_configuradas';
  return {
    coleccion:shiny?'Shiny':'Living', dex:item.dex_number, clave:item.key,
    especie:item.species, forma:item.form_name||'Forma base',
    estado:state, fuente_cacheada:success?.url||'',
    fuentes_probadas:records.length, fallos_404:records.filter(r=>r.state==='404').length,
    sin_comprobar:records.filter(r=>r.state==='sin_comprobar').length,
    variedad_api:variety.key||'', estado_variedad:variety.state, sources:records
  };
}
function inventory(catalog, root, onlySpecial=false) {
  const byKey = new Map(catalog.forms.map(f=>[f.key,f]));
  const result = [];
  for (const [shiny, keys] of [[true,catalog.shiny_keys],[false,catalog.normal_keys]]) {
    for (const key of keys) {
      const item = byKey.get(key);
      if (!item) throw new Error('Falta forma del catálogo: ' + key);
      if (onlySpecial && !item.form_name) continue;
      result.push(evaluate(item,shiny,root));
    }
  }
  return result;
}
function csvQuote(value) {
  const raw = String(value??'');
  return /[\n\r",;]/.test(raw)?'"'+raw.replaceAll('"','""')+'"':raw;
}
function toCSV(items) {
  const fields = ['coleccion','dex','clave','especie','forma','estado','fuente_cacheada',
    'fuentes_probadas','fallos_404','sin_comprobar','variedad_api','estado_variedad'];
  return '\ufeff'+[fields.join(';'),...items.map(r=>fields.map(f=>csvQuote(r[f])).join(';'))].join('\n')+'\n';
}
function countStates(items) {
  return items.reduce((acc,row)=>{acc[row.estado]=(acc[row.estado]||0)+1;return acc;},{});
}
function printUsage() {
  process.stdout.write('Uso: node scripts/auditar_sprites.cjs [opciones]\n\n' +
    '  --solo-especiales  Solo formas especiales\n' +
    '  --probar-online N  Hasta N consultas (1-30) por API local; requiere servidor\n' +
    '  --salida DIR      Carpeta de informes (por defecto reportes_sprites/)\n' +
    '  --ayuda            Ayuda\n\n' +
    'Sin --probar-online no hay solicitudes de red.\n');
}
function argsParse(argv) {
  let check=0,onlySpecial=false,output=path.join(__dirname,'..','reportes_sprites');
  for (let i=0;i<argv.length;i++) {
    if (argv[i]==='--ayuda'||argv[i]==='-h') return {help:true};
    if (argv[i]==='--solo-especiales') {onlySpecial=true;continue;}
    if (argv[i]==='--salida') {
      if (!argv[i+1]) throw new Error('Falta DIR de salida');
      output=path.resolve(argv[++i]);continue;
    }
    if (argv[i]==='--probar-online') {
      const value=argv[++i];
      if (!/^\d+$/.test(value||'')||Number(value)<1||Number(value)>30)
        throw new Error('--probar-online requiere un entero entre 1 y 30');
      check=Number(value);continue;
    }
    throw new Error('Argumento desconocido: '+argv[i]);
  }
  return {check,onlySpecial,output};
}
function delay(ms) {return new Promise(resolve=>setTimeout(resolve,ms));}
async function trialLocal(url, base) {
  const target=base+'/api/sprites/image?url='+encodeURIComponent(url);
  const response=await fetch(target,{signal:AbortSignal.timeout(10000)});
  if (![200,404,503].includes(response.status)) throw new Error('API local: HTTP '+response.status);
  await response.arrayBuffer();return response.status;
}
async function trialVariety(key,base) {
  const response=await fetch(base+'/api/sprites/variety/'+encodeURIComponent(key),
    {signal:AbortSignal.timeout(10000)});
  if (![200,404,503].includes(response.status)) throw new Error('API variedad: HTTP '+response.status);
  await response.arrayBuffer();return response.status;
}
async function tryOnline(rows, limit, base) {
  let calls=0,errors=0;
  const ordered=[...rows].sort((a,b)=>Number(b.forma!=='Forma base')-Number(a.forma!=='Forma base'));
  const attempted=new Set();
  for (const row of ordered) {
    if (calls>=limit) break;
    if (row.estado==='cacheado_revisar_forma') continue;
    for (const rec of row.sources) {
      if (calls>=limit) break;
      if (rec.state!=='sin_comprobar'||attempted.has(rec.url)) continue;
      attempted.add(rec.url);
      try {
        const status=await trialLocal(rec.url,base);
        process.stdout.write('  '+row.clave+' ('+row.coleccion+'): '+status+' '+rec.url+'\n');
      } catch(err) {errors++;process.stderr.write('  '+row.clave+': '+err.message+'\n');}
      calls++;
      await delay(450);
    }
    if (calls<limit && row.estado_variedad==='sin_comprobar' && row.variedad_api) {
      const key='variety:'+row.variedad_api;
      if (!attempted.has(key)) {
        attempted.add(key);
        try {
          const status=await trialVariety(row.variedad_api,base);
          process.stdout.write('  variedad '+row.variedad_api+': '+status+'\n');
        } catch(err) {errors++;process.stderr.write('  variedad: '+err.message+'\n');}
        calls++;await delay(450);
      }
    }
  }
  return {calls,errors};
}
function saveReports(rows,dir,meta={}) {
  fs.mkdirSync(dir,{recursive:true});
  fs.writeFileSync(path.join(dir,'inventario.csv'),toCSV(rows),'utf8');
  const unresolved=rows.filter(r=>r.estado!=='cacheado_revisar_forma');
  fs.writeFileSync(path.join(dir,'pendientes.csv'),toCSV(unresolved),'utf8');
  fs.writeFileSync(path.join(dir,'pendientes_especiales.csv'),
    toCSV(unresolved.filter(r=>r.forma!=='Forma base')),'utf8');
  const summary={fecha:new Date().toISOString(),catalogo:rows.length,
    estados:countStates(rows),...meta,
    nota:'Cacheado no prueba que la forma/color sea correcto. Sin comprobar no implica que la imagen no exista.'};
  fs.writeFileSync(path.join(dir,'resumen.json'),JSON.stringify(summary,null,2)+'\n','utf8');
  return {summary,unresolved:unresolved.length};
}
async function main() {
  let opts;
  try {opts=argsParse(process.argv.slice(2));}
  catch(err) {console.error(err.message);printUsage();process.exitCode=2;return;}
  if (opts.help) {printUsage();return;}
  const catalog=JSON.parse(fs.readFileSync(CATALOG,'utf8'));
  const root=cacheRoot();
  let rows=inventory(catalog,root,opts.onlySpecial);
  let online=null;
  if (opts.check) {
    console.log('Prueba optativa: máximo '+opts.check+' consultas a la API local.');
    online=await tryOnline(rows,opts.check,(process.env.OPTPOKE_URL||'http://127.0.0.1:8000').replace(/\/$/,''));
    rows=inventory(catalog,root,opts.onlySpecial);
  }
  const {summary,unresolved}=saveReports(rows,opts.output,{datos_locales:root,verificacion_online:online});
  console.log('Objetivos revisados: '+summary.catalogo+'; pendientes según caché: '+unresolved);
  console.log('Estados: '+JSON.stringify(summary.estados));
  console.log('Informes: '+opts.output);
  console.log('IMPORTANTE: la caché no verifica visualmente la forma ni el color shiny.');
}
if (require.main===module) main().catch(err=>{console.error(err);process.exitCode=1;});
module.exports={cacheRoot,cacheFile,imageRecord,varietyRecord,evaluate,inventory,
  toCSV,countStates,argsParse,saveReports};
