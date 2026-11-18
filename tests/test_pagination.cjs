const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('static/app.js','utf8');
const loader=source.slice(source.indexOf('async function loadDexList(){'),source.indexOf('function openGoal('));
function harness(total, offset=0){
  const elements=new Map();
  const $=id=>{if(!elements.has(id))elements.set(id,{innerHTML:'',addEventListener(event,fn){this[event]=fn;}});return elements.get(id);};
  const state={page:'shiny',offset,limit:72,dexRequestSeq:0};
  const context={state,$,nf:new Intl.NumberFormat('es-UY'),URLSearchParams,
    document:{querySelectorAll:()=>[]},request:async()=>({items:[],total}),
    renderDexSpotlight(){},scrollDexToList(){}};
  vm.createContext(context);vm.runInContext(loader,context);
  return {context,elements,$};
}
test('pagination renders in header on empty results with both directions disabled',async()=>{
  const h=harness(0);
  await h.context.loadDexList();
  assert.match(h.$('#dex-pagination').innerHTML,/0–0/);
  assert.equal((h.$('#dex-pagination').innerHTML.match(/disabled/g)||[]).length,2);
  assert.doesNotMatch(h.$('#dex-container').innerHTML,/prev-page|next-page/);
});
test('top next, previous and page picker update the offset',async()=>{
  const h=harness(200);
  await h.context.loadDexList();
  h.$('#next-page').click();assert.equal(h.context.state.offset,72);
  await h.context.loadDexList();
  h.$('#prev-page').click();assert.equal(h.context.state.offset,0);
  await h.context.loadDexList();
  h.$('#dex-jump-page').change({target:{value:'3'}});assert.equal(h.context.state.offset,144);
});
test('removing the last filtered result returns to the preceding valid page',async()=>{
  const h=harness(72,72);
  await h.context.loadDexList();
  assert.equal(h.context.state.offset,0);
});
