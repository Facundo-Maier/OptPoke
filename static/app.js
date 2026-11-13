'use strict';
const $ = (selector, root=document) => root.querySelector(selector);
const app = $('#app');
const state = {page:'shiny',search:'',status:'all',sort:'dex',offset:0,limit:72,bankGame:'',bankAll:false,selectedGoalId:null,dexRequestSeq:0};
const html = (x) => String(x??'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const nf = new Intl.NumberFormat('es-UY');
const percent = n => (Number(n)*100).toLocaleString('es-UY',{maximumFractionDigits:2}) + '%';
let dexSpotlightObserver=null;
const pages = {shiny:'Shiny Dex',normal:'Living Dex',bank:'Plan Bank',hunts:'Cacerías',compare:'Comparador',settings:'Configuración'};
function toast(message){const el=$('#toast');el.textContent=message;el.classList.remove('hidden');setTimeout(()=>el.classList.add('hidden'),3500);}
async function request(url,options={}){
  const response=await fetch(url,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});
  if(!response.ok){let detail='Error '+response.status;try{const data=await response.json();detail=typeof data.detail==='string'?data.detail:detail;}catch{}throw Error(detail);}
  return response.json();
}
async function patch(url,data){return request(url,{method:'PATCH',body:JSON.stringify(data)});}
function modal(title,content){$('#modal-title').textContent=title;$('#modal-content').innerHTML=content;$('#modal-layer').classList.remove('hidden');}
function closeModal(){$('#modal-layer').classList.add('hidden');}
$('#modal-close').addEventListener('click',closeModal);
$('#modal-layer').addEventListener('click',e=>{if(e.target.id==='modal-layer')closeModal()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});
async function go(page){
  if(dexSpotlightObserver){dexSpotlightObserver.disconnect();dexSpotlightObserver=null;}
  state.page=page;state.search='';state.status='all';state.sort='dex';state.offset=0;state.selectedGoalId=null;state.dexRequestSeq++;
  document.querySelectorAll('.nav-item').forEach(el=>el.classList.toggle('selected',el.dataset.page===page));
  $('#breadcrumb-current').textContent=pages[page];
  app.innerHTML='<div class="loading">Cargando…</div>';
  window.scrollTo({top:0,behavior:'instant'});
  try {if(page==='shiny'||page==='normal')await renderDex();else if(page==='bank')await renderBank();else if(page==='hunts')await renderHunts();else if(page==='settings')await renderSettings();else await renderCompare();}
  catch(e){app.innerHTML=`<div class="empty"><strong>No se pudo cargar</strong>${html(e.message)}</div>`;}
}
document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener('click',()=>go(b.dataset.page)));
const head=(eyebrow,title,description,actions='')=>`<div class="eyebrow">${eyebrow}</div><div class="heading-row"><div><h1>${title}</h1><p class="description">${description}</p></div><div class="headline-actions">${actions}</div></div>`;
const stat=(label,done,total,foot)=>`<div class="stat-card"><div class="stat-label">${label}</div><div class="stat-number">${nf.format(done||0)}<span> / ${nf.format(total||0)}</span></div><div class="progress-track"><div class="progress-fill" style="width:${total?Math.min(100,Math.max(0,100*done/total)):0}%"></div></div><div class="stat-footer">${foot}</div></div>`;
function possibleSprite(item){
  // Source selection and fallbacks are managed by sprites.js.
  // The original form and shininess are preserved even when no image is found.
  return `<img loading="lazy" decoding="async" data-sprite-key="${html(item.form_key)}" alt="${html(item.species)}${item.form_name ? ' · '+html(item.form_name) : ''}${state.page==='shiny' ? ' shiny' : ''}">
    <span class="sprite-placeholder fallback" title="Imagen de esta forma no disponible">${html(item.species.slice(0,2).toUpperCase())}</span>`;
}

function dexHeader(summary, isShiny){
  const current=isShiny?summary.shiny:summary.normal;
  const rate=current.total ? (current.done/current.total)*100 : 0;
  return `<section class="dex-top" aria-label="Resumen de Pokédex">
    <div class="dex-titlebar"><span class="dex-title-mark" aria-hidden="true">◈</span><span>Pokédex Nacional</span><span class="dex-title-type">${isShiny?'✦ SHINY':'LIVING DEX'}</span></div>
    <div class="dex-summary"><span class="dex-summary-primary"><strong id="dex-summary-done">${nf.format(current.done)}</strong> / <strong>${nf.format(current.total)}</strong> en HOME</span>
    <div class="dex-summary-track" role="progressbar" aria-label="Progreso de la colección" aria-valuenow="${current.done}" aria-valuemax="${current.total}"><div id="dex-summary-fill" class="dex-summary-fill" style="width:${rate}%"></div></div>
    <span class="dex-summary-secondary">🔒 ${isShiny?`<strong id="dex-summary-locked">${nf.format(current.locked)}</strong>`:'—'} candados · <strong id="dex-summary-ot">${nf.format(current.ot_exceptions || 0)}</strong> OT ajeno</span>
    </div>
  </section>`;
}
async function updateDexSummary(){
  const overview=await request('/api/overview');
  const current=state.page==='shiny'?overview.shiny:overview.normal;
  const done=$('#dex-summary-done'), fill=$('#dex-summary-fill'), locked=$('#dex-summary-locked'), ot=$('#dex-summary-ot');
  if(done) done.textContent=nf.format(current.done);
  if(fill) fill.style.width=`${current.total?100*current.done/current.total:0}%`;
  const track=$('.dex-summary-track');if(track)track.setAttribute('aria-valuenow',current.done);
  if(locked)locked.textContent=nf.format(current.locked);
  if(ot)ot.textContent=nf.format(current.ot_exceptions || 0);
}
function renderDexSpotlight(goal){
  const pane=$('#dex-spotlight-content');if(!pane)return;
  if(!goal){pane.innerHTML='<div class="dex-spotlight-empty">No hay Pokémon para mostrar.</div>';return;}
  const label=window.OptPokeDex.labelFor(goal);
  const dex=goal.dex_number==null?'????':String(goal.dex_number).padStart(4,'0');
  pane.innerHTML=`<div class="dex-preview-caption">POKÉMON SELECCIONADO <span>#${dex}</span></div>
    <div class="dex-preview-stage"><div class="dex-preview-image">${possibleSprite(goal)}</div></div>
    <div class="dex-preview-name">${html(goal.species)}</div>
    <div class="dex-preview-form">${html(goal.form_name||'Forma base')}</div>
    <div class="dex-preview-details"><span>Estado</span><strong>${label==='Con candado'?'🔒 ':''}${label}</strong><span>OT</span><strong>${goal.ot_exception?'OT ajeno':'Sin marca'}</strong><span>En HOME</span><strong>${goal.in_home} / ${goal.target}</strong></div>
    <button class="dex-preview-edit" type="button" id="dex-preview-edit">Editar objetivo <span aria-hidden="true">↗</span></button>`;
  $('#dex-preview-edit').addEventListener('click',()=>openGoal(goal));
  const previewImage=pane.querySelector('img[data-sprite-key]');
  if(previewImage)window.OptPokeSprites.loadSprite(previewImage,goal,state.page==='shiny');
}
async function renderDex(){
  const result=await request('/api/overview');
  const isShiny=state.page==='shiny';
  app.innerHTML=`<div class="dex-sticky-header">`+dexHeader(result,isShiny)+
    `<div class="dex-controls"><div class="search-wrap"><svg class="dex-search-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></svg><input class="control" id="dex-search" aria-label="Buscar Pokémon" placeholder="Pokémon, forma o número..." value="${html(state.search)}"></div>
       <select id="dex-filter" aria-label="Filtrar por estado" class="control select"><option value="all">Todos</option><option value="missing">Pendientes</option><option value="done">En HOME</option><option value="locked">Con candado</option><option value="ot_exception">OT ajeno</option></select>
       <select id="dex-sort" aria-label="Ordenar Pokémon" class="control select"><option value="dex">Nº Pokédex</option><option value="name">Nombre A–Z</option></select></div></div>
     <div class="pokedex-shell"><aside id="dex-spotlight" class="dex-spotlight" aria-label="Vista del Pokémon seleccionado"><div id="dex-spotlight-content" class="dex-spotlight-inner"><div class="dex-spotlight-empty">Elegí un Pokémon del listado</div></div></aside>
     <section class="dex-index" aria-label="Índice de la Pokédex"><div class="dex-index-title"><span>Índice ${isShiny?'shiny':'normal'}</span><span class="dex-index-hint">Seleccioná una especie o cambiá su estado directamente</span></div>
     <div id="dex-container"></div></section></div>
     <div class="footer-attribution">Los sprites se descargan solamente la primera vez y se almacenan en tu PC. Para objetivos de varios ejemplares, el estado abre el editor de cantidades.</div>`;
  setupDexSpotlight();
  $('#dex-filter').value=state.status;$('#dex-sort').value=state.sort;
  let timer;
  $('#dex-search').addEventListener('input',e=>{clearTimeout(timer);timer=setTimeout(()=>{state.search=e.target.value;state.offset=0;loadDexList();},250)});
  $('#dex-filter').addEventListener('change',e=>{state.status=e.target.value;state.offset=0;loadDexList()});
  $('#dex-sort').addEventListener('change',e=>{state.sort=e.target.value;state.offset=0;loadDexList()});
  await loadDexList();
}
// Mantiene el panel del Pokémon seleccionado debajo de la cabecera persistente.
// ResizeObserver cubre los cambios de ancho, zoom y el salto de línea en filtros,
// sin adivinar una altura fija que podría solaparse con el sprite.
function setupDexSpotlight(){
  const header=$('.dex-sticky-header'), shell=$('.pokedex-shell');
  if(!header||!shell)return;
  const update=()=>shell.style.setProperty('--dex-header-height',Math.ceil(header.getBoundingClientRect().height)+'px');
  update();
  if(typeof ResizeObserver!=='undefined'){
    dexSpotlightObserver=new ResizeObserver(update);
    dexSpotlightObserver.observe(header);
  }
}
// Coloca la primera fila justo debajo de la cabecera fija al cambiar de página.
function scrollDexToList(){
  const list=$('.pokedex-shell'), header=$('.dex-sticky-header');
  if(!list||!header)return;
  const top=list.getBoundingClientRect().top+window.scrollY-header.getBoundingClientRect().height-8;
  window.scrollTo({top:Math.max(0,top),behavior:'instant'});
}
async function loadDexList(){
  const page=state.page;
  const seq=++state.dexRequestSeq;
  const args=new URLSearchParams({kind:page,search:state.search,status:state.status,sort:state.sort,offset:state.offset,limit:state.limit});
  const data=await request('/api/goals?'+args);
  if(page!==state.page || seq!==state.dexRequestSeq)return;
  const container=$('#dex-container');if(!container)return;
  if(!data.items.length){container.innerHTML=`<div class="dex-no-results">No se encontraron Pokémon para ese filtro.</div>`;renderDexSpotlight(null);return;}
  const selected=data.items.find(x=>x.id===state.selectedGoalId)||data.items[0];
  state.selectedGoalId=selected.id;
  const rows=window.OptPokeDex.renderRows(data.items,possibleSprite,state.selectedGoalId);
  const pageNumber=Math.floor(state.offset/state.limit)+1;
  const pageCount=Math.ceil(data.total/state.limit);
  // The range refers to entries in the *currently filtered and sorted list*,
  // not National Dex numbers (forms share Dex numbers).
  const pageOptions=Array.from({length:pageCount},(_,i)=>{
    const first=i*state.limit+1, last=Math.min((i+1)*state.limit,data.total);
    return `<option value="${i+1}" ${i+1===pageNumber?'selected':''}>${i+1} · ${nf.format(first)}–${nf.format(last)}</option>`;
  }).join('');
  container.innerHTML=`${rows}<div class="pagination"><button id="prev-page" class="btn btn-small" ${state.offset===0?'disabled':''}>← Anterior</button><label class="dex-page-picker">${nf.format(data.total)} resultados · Página <select id="dex-jump-page" aria-label="Ir a la página y rango de resultados" class="dex-page-select">${pageOptions}</select> / ${pageCount}</label><button id="next-page" class="btn btn-small" ${state.offset+state.limit>=data.total?'disabled':''}>Siguiente →</button></div>`;
  const byId=new Map(data.items.map(item=>[item.id,item]));
  const byFormKey=new Map(data.items.map(item=>[item.form_key,item]));
  container.querySelectorAll('img[data-sprite-key]').forEach(image=>{
    const item=byFormKey.get(image.dataset.spriteKey);
    if(item)window.OptPokeSprites.loadSprite(image,item,page==='shiny');
  });
  function selectGoal(goal){
    state.selectedGoalId=goal.id;
    container.querySelectorAll('[data-row-goal]').forEach(row=>row.classList.toggle('is-selected',Number(row.dataset.rowGoal)===goal.id));
    container.querySelectorAll('[data-select-goal]').forEach(btn=>btn.setAttribute('aria-pressed',String(Number(btn.dataset.selectGoal)===goal.id)));
    renderDexSpotlight(goal);
  }
  container.querySelectorAll('[data-select-goal]').forEach(btn=>btn.addEventListener('click',()=>{
    const goal=byId.get(Number(btn.dataset.selectGoal));if(goal){selectGoal(goal);if(window.matchMedia('(max-width: 850px)').matches)openGoal(goal);}
  }));
  container.querySelectorAll('[data-edit-goal]').forEach(btn=>btn.addEventListener('click',()=>{
    const goal=byId.get(Number(btn.dataset.editGoal));if(goal){selectGoal(goal);openGoal(goal)}
  }));
  container.querySelectorAll('[data-toggle-ot]').forEach(btn=>btn.addEventListener('click',async()=>{
    const goal=byId.get(Number(btn.dataset.toggleOt));if(!goal||btn.disabled)return;
    btn.disabled=true;
    try{
      await patch('/api/goals/'+goal.id,{ot_exception:!goal.ot_exception});
      toast(goal.ot_exception?'Marca de OT retirada':'Marcado: requiere OT ajeno');
      await Promise.all([loadDexList(),updateDexSummary()]);
    }catch(error){toast(error.message);btn.disabled=false}
  }));
  container.querySelectorAll('[data-toggle-home]').forEach(btn=>btn.addEventListener('click',async()=>{
    const goal=byId.get(Number(btn.dataset.toggleHome));if(!goal||btn.disabled)return;
    btn.disabled=true;
    try{
      const nextValue=goal.in_home>=goal.target?0:goal.target;
      await patch('/api/goals/'+goal.id,{in_home:nextValue});
      toast(nextValue?'Marcado En HOME':'Marcado como pendiente');
      await Promise.all([loadDexList(),updateDexSummary()]);
    }catch(error){toast(error.message);btn.disabled=false}
  }));
  renderDexSpotlight(selected);
  $('#prev-page').addEventListener('click',()=>{state.offset=Math.max(0,state.offset-state.limit);loadDexList();scrollDexToList();});
  $('#next-page').addEventListener('click',()=>{state.offset+=state.limit;loadDexList();scrollDexToList();});
  $('#dex-jump-page').addEventListener('change',e=>{state.offset=(Number(e.target.value)-1)*state.limit;loadDexList();scrollDexToList();});
}
function openGoal(goal){
  modal(`${goal.species}${goal.form_name?' · '+goal.form_name:''}`,`<p class="description" style="margin-bottom:22px">#${String(goal.dex_number).padStart(4,'0')} · ${goal.shiny?'Shiny':'Normal'}. Un objetivo se completa cuando los ejemplares llegan a HOME.</p>
  <form id="goal-form"><div class="form-grid"><div class="field"><label for="g-target">Ejemplares objetivo</label><input id="g-target" class="control" type="number" min="1" max="999" value="${goal.target}" required></div>
  <div class="field"><label for="g-home">Ejemplares en HOME</label><input id="g-home" class="control" type="number" min="0" max="999" value="${goal.in_home}" required></div>
  <div class="field full"><label for="g-lock">Disponibilidad de shiny / forma</label><select id="g-lock" class="control"><option value="unverified">Sin verificar</option><option value="obtainable">Obtenible</option><option value="locked">🔒 Bloqueado actualmente</option></select></div></div>
  <label class="dex-ot-field"><input type="checkbox" id="g-ot" ${goal.ot_exception?'checked':''}><span><strong>Solo obtenible sin mi OT</strong><small>Marca independiente del candado. Se aplica a esta forma, shiny o normal, por separado.</small></span></label>
  <p class="note">El candado es editable. La marca OT se gestiona manualmente; no se asignan excepciones automáticamente.</p><div class="form-actions"><button type="button" class="btn" id="cancel-goal">Cancelar</button><button type="submit" class="btn btn-primary">Guardar cambios</button></div></form>`);
  $('#g-lock').value=goal.obtainability;
  $('#cancel-goal').addEventListener('click',closeModal);
  $('#goal-form').addEventListener('submit',async e=>{
    e.preventDefault();try{await patch('/api/goals/'+goal.id,{target:Number($('#g-target').value),in_home:Number($('#g-home').value),obtainability:$('#g-lock').value,ot_exception:$('#g-ot').checked});closeModal();toast('Objetivo guardado');await renderDex();}
    catch(error){toast(error.message)}
  });
}
async function renderBank(){
  const [data,summary]=await Promise.all([request('/api/bank?pending=false'),request('/api/overview')]);
  app.innerHTML=head('FECHA LÍMITE · 26 FEB 2027','Plan Pokémon Bank','Todo lo que querés completar antes del cierre. Un objetivo termina al llegar a HOME.',`<span class="pill">◴ Transferencias</span>`)+
    `<div class="stat-grid">${stat('Ejemplares en HOME',summary.bank.done,summary.bank.total,'De los ejemplares planificados')}${stat('Tareas completadas',data.items.filter(x=>x.in_home>=x.required).length,data.items.length,'Por Pokémon y juego')}${stat('Tareas pendientes',summary.bank.open_tasks,data.items.length,'Se muestran sin completar')}</div>
    <div class="toolbar"><div class="toolbar-left"><select id="bank-game" class="control select" aria-label="Filtrar por juego"><option value="">Todos los juegos</option>${data.games.map(x=>`<option value="${html(x.game)}">${html(x.game)}</option>`).join('')}</select>
    <label class="switch"><input id="bank-show-all" type="checkbox" ${state.bankAll?'checked':''}> Mostrar completadas</label></div></div>
    <div id="bank-table"></div><div class="notice"><strong>Importante:</strong> los cambios de Bank y de la Pokédex no se actualizan mutuamente todavía; falta reconciliar cada tarea con una forma concreta de la colección.</div>`;
  $('#bank-game').value=state.bankGame;
  $('#bank-game').addEventListener('change',e=>{state.bankGame=e.target.value;loadBankTable()});
  $('#bank-show-all').addEventListener('change',e=>{state.bankAll=e.target.checked;loadBankTable()});
  await loadBankTable();
}
async function loadBankTable(){
  const query=new URLSearchParams({game:state.bankGame,pending:String(!state.bankAll)});
  const result=await request('/api/bank?'+query);
  const root=$('#bank-table');if(!root)return;
  if(!result.items.length){root.innerHTML='<div class="empty"><div class="empty-icon">◴</div><strong>No hay tareas con este filtro</strong>Importá el Excel 26Febrero27 desde la línea de comandos, o cambiá el filtro.</div>';return;}
  const groups=Object.groupBy?Object.groupBy(result.items,x=>x.game):result.items.reduce((a,x)=>((a[x.game]??=[]).push(x),a),{});
  root.innerHTML=Object.entries(groups).map(([game,items])=>{
    const status=result.games.find(x=>x.game===game);
    return `<div class="panel"><div class="panel-header"><div><h2>${html(game)} <span class="tiny">· ${items.length} tareas</span></h2><div class="tiny">Estado del juego</div></div>
    <div class="game-checks"><label class="toggle-line"><input class="bank-flag" type="checkbox" data-game="${html(game)}" data-field="started" ${status?.started?'checked':''}> Comenzado</label><label class="toggle-line"><input class="bank-flag" type="checkbox" data-game="${html(game)}" data-field="prepared" ${status?.prepared?'checked':''}> Preparado</label></div></div>
    <div class="table-wrap"><table class="data-table"><thead><tr><th>Pokémon</th><th>Notas / método</th><th>Objetivo</th><th>Capturados</th><th>En HOME</th><th></th></tr></thead><tbody>
    ${items.map(t=>`<tr data-bank-id="${t.id}"><td><div class="name-strong">${html(t.pokemon)}</div><div class="row-sub">${html(t.form_name||'Forma base')} · ${t.shiny?'Shiny':'Normal'}${t.ot_exception?' · OT de evento':''}</div></td>
    <td class="muted">${html(t.comments||'—')}</td><td>${t.required}</td><td><input class="tiny-input bank-caught" type="number" min="0" max="${t.required}" value="${t.caught}" aria-label="Capturados ${html(t.pokemon)}"></td>
    <td><input class="tiny-input bank-home" type="number" min="0" max="${t.required}" value="${t.in_home}" aria-label="HOME ${html(t.pokemon)}"></td>
    <td><button class="btn btn-small bank-save" type="button">Guardar</button></td></tr>`).join('')}</tbody></table></div></div>`;
  }).join('');
  root.querySelectorAll('.bank-save').forEach(btn=>btn.addEventListener('click',async()=>{
    const row=btn.closest('tr');const id=Number(row.dataset.bankId);
    try{await patch('/api/bank/'+id,{caught:Number($('.bank-caught',row).value),in_home:Number($('.bank-home',row).value)});toast('Tarea actualizada');await renderBank();}
    catch(error){toast(error.message)}
  }));
  root.querySelectorAll('.bank-flag').forEach(el=>el.addEventListener('change',async()=>{
    try{await patch('/api/bank-games/'+encodeURIComponent(el.dataset.game),{[el.dataset.field]:el.checked});toast('Estado del juego guardado');}
    catch(error){toast(error.message)}
  }));
}
async function renderHunts(){
  const hunts=await request('/api/hunts');
  app.innerHTML=head('SEGUIMIENTO DE INTENTOS','Cacerías','Contador y probabilidad acumulada. Las fases registran shiny que no eran el objetivo.',`<button id="new-hunt" class="btn btn-primary">+ Nueva cacería</button>`)+
    `<div class="section-title">Historial y sesiones <span class="tiny">${hunts.length} cacerías</span></div><div class="hunt-list" id="hunt-list"></div>
    <div class="notice"><strong>Cálculo actual:</strong> intentos independientes con probabilidad constante. SOS, cadenas y otros métodos variables se incorporarán con sus propias reglas verificadas.</div>`;
  $('#new-hunt').addEventListener('click',createHuntModal);
  if(!hunts.length){$('#hunt-list').innerHTML='<div class="empty"><div class="empty-icon">◉</div><strong>Todavía no hay cacerías</strong>Creá una o importá ShinyHunts.xlsm.</div>';return;}
  $('#hunt-list').innerHTML=hunts.map(h=>`<div class="hunt-card" data-hunt="${h.id}"><div class="hunt-card-top"><div><div class="kicker">${h.status==='active'?'● ACTIVA':h.status==='completed'?'✓ COMPLETADA':'○ PAUSADA'}</div><h2>${html(h.pokemon)}</h2><div class="tiny">${html(h.method||'Método sin especificar')}${h.game?' · '+html(h.game):''}</div></div><span class="tag ${h.status==='completed'?'green':''}">${nf.format(h.recorded_phases)} fases</span></div>
    <div class="counter-area"><button class="btn counter-action" data-delta="-1" aria-label="Restar intento">−</button><div class="counter-details"><div class="big-counter">${nf.format(h.attempts)}</div><div class="tiny">INTENTOS REGISTRADOS</div></div><button class="btn btn-primary counter-action" data-delta="1" aria-label="Sumar intento">+</button></div>
    <div class="hunt-meta"><span class="tag">Probabilidad acumulada: <strong>${percent(h.cumulative)}</strong></span><span class="tag">Por intento: 1 / ${h.probability?nf.format(Math.round(1/h.probability)):'?'}</span>${h.seconds_per_attempt?`<span class="tag">Tiempo estimado invertido: ${Math.round(h.attempts*h.seconds_per_attempt/60)} min</span>`:''}${h.shiny_found?'<span class="tag green">Shiny objetivo obtenido</span>':''}</div>
    <div class="hunt-actions"><button data-action="phase" class="btn btn-small">✧ Registrar fase</button><button data-action="edit" class="btn btn-small">Editar total / tiempos</button><button data-action="state" class="btn btn-small">${h.status==='active'?'Pausar':h.status==='completed'?'Marcar activa':'Reanudar'}</button><button data-action="complete" class="btn btn-small">Marcar completada</button></div></div>`).join('');
  $('#hunt-list').querySelectorAll('[data-hunt]').forEach(card=>{
    const hunt=hunts.find(x=>x.id===Number(card.dataset.hunt));
    card.querySelectorAll('[data-delta]').forEach(b=>b.addEventListener('click',async()=>{
      try{await patch('/api/hunts/'+hunt.id,{delta:Number(b.dataset.delta)});await renderHunts();}catch(e){toast(e.message)}
    }));
    card.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',async()=>{
      const action=b.dataset.action;
      if(action==='edit')return editHuntModal(hunt);
      if(action==='phase')return phaseModal(hunt);
      try{if(action==='state')await patch('/api/hunts/'+hunt.id,{status:hunt.status==='active'?'paused':'active'});
      else await patch('/api/hunts/'+hunt.id,{status:'completed',shiny_found:true});await renderHunts();}
      catch(e){toast(e.message)}
    }));
  });
}
function createHuntModal(){
  modal('Nueva cacería',`<form id="hunt-form"><div class="form-grid"><div class="field full"><label>Pokémon</label><input id="h-name" class="control" placeholder="Ej. Tapu Koko" maxlength="100" required></div>
    <div class="field"><label>Juego</label><input id="h-game" class="control" placeholder="Ej. Shield"></div><div class="field"><label>Método</label><input id="h-method" class="control" placeholder="Ej. Dynamax Adventures"></div>
    <div class="field"><label>Probabilidad: 1 entre…</label><input id="h-denom" class="control" type="number" min="1" step="any" value="4096" required></div>
    <div class="field"><label>Segundos por intento (opcional)</label><input id="h-seconds" class="control" type="number" min="0.01" step="any" placeholder="Ej. 35"></div></div>
    <div class="form-actions"><button type="button" id="cancel-hunt" class="btn">Cancelar</button><button type="submit" class="btn btn-primary">Crear</button></div></form>`);
  $('#cancel-hunt').addEventListener('click',closeModal);
  $('#hunt-form').addEventListener('submit',async e=>{
    e.preventDefault();try{const denominator=Number($('#h-denom').value);if(denominator<1)throw Error('Denominador inválido');
      await request('/api/hunts',{method:'POST',body:JSON.stringify({pokemon:$('#h-name').value,game:$('#h-game').value,method:$('#h-method').value,probability:1/denominator,seconds_per_attempt:$('#h-seconds').value?Number($('#h-seconds').value):null})});closeModal();toast('Cacería creada');await renderHunts();}catch(err){toast(err.message)}
  });
}
function editHuntModal(hunt){
  modal('Editar · '+hunt.pokemon,`<form id="hunt-edit"><div class="form-grid"><div class="field"><label>Total de intentos</label><input class="control" id="he-count" type="number" min="0" value="${hunt.attempts}" required></div><div class="field"><label>Probabilidad: 1 entre…</label><input id="he-odds" class="control" type="number" min="1" step="any" value="${1/hunt.probability}" required></div><div class="field full"><label>Segundos por intento</label><input id="he-seconds" class="control" type="number" step="any" min="0.01" value="${hunt.seconds_per_attempt||''}" placeholder="Sin especificar"></div></div><div class="form-actions"><button class="btn btn-primary" type="submit">Guardar</button></div></form>`);
  $('#hunt-edit').addEventListener('submit',async e=>{e.preventDefault();try{
    const data={attempts:Number($('#he-count').value),probability:1/Number($('#he-odds').value)};
    if($('#he-seconds').value)data.seconds_per_attempt=Number($('#he-seconds').value);
    await patch('/api/hunts/'+hunt.id,data);closeModal();await renderHunts();}catch(err){toast(err.message)}
  });
}
function phaseModal(hunt){
  modal('Registrar fase · '+hunt.pokemon,`<p class="description" style="margin-bottom:19px">Anotá el número de intento en el que apareció un shiny que no era tu objetivo.</p><form id="phase-form"><div class="form-grid"><div class="field"><label>Intento / aventura</label><input id="phase-number" class="control" type="number" min="0" max="${hunt.attempts}" value="${hunt.attempts}" required></div><div class="field"><label>Nota (opcional)</label><input id="phase-note" class="control" maxlength="200" placeholder="Ej. Golduck"></div></div><div class="form-actions"><button class="btn btn-primary" type="submit">Registrar</button></div></form>`);
  $('#phase-form').addEventListener('submit',async e=>{e.preventDefault();try{
    await request(`/api/hunts/${hunt.id}/phases`,{method:'POST',body:JSON.stringify({at_attempt:Number($('#phase-number').value),note:$('#phase-note').value})});closeModal();toast('Fase registrada');await renderHunts();}catch(err){toast(err.message)}
  });
}
async function renderCompare(){
  app.innerHTML=head('EN DESARROLLO','Comparador de métodos','Elegí una especie y descubrí la manera más rápida de conseguirla según tus juegos y condiciones.')+
    `<div class="panel"><div class="kicker">PRÓXIMO MÓDULO</div><h2>Tiempo estimado de obtención</h2><p class="description">El catálogo y los juegos disponibles ya están en la base. Faltan los datos verificados por juego y método, reglas de OT, Shiny Charm y duración manual de cada intento.</p>
    <div class="notice"><strong>No se muestran rankings inventados.</strong> Se habilitarán cuando los métodos estén identificados y verificados, con fecha y fuente.</div></div>`;
}
function setupAustinImport(){
  const modeInput=$('#austin-mode');
  const configs=[
    {source:'shiny',input:$('#austin-shiny-file'),button:$('#austin-shiny-preview'),results:$('#austin-shiny-results'),label:'Shiny Dex'},
    {source:'normal',input:$('#austin-normal-file'),button:$('#austin-normal-preview'),results:$('#austin-normal-results'),label:'Living Dex'},
  ];
  async function sendAustin(file,kind,mode,source,digest=''){
    const url='/api/austin/'+kind+'?'+new URLSearchParams({mode,source,...(digest?{digest}:{})});
    const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},body:file});
    const data=await res.json();
    if(!res.ok)throw Error(typeof data.detail==='string'?data.detail:'Error al importar el Excel');
    return data;
  }
  for(const conf of configs){
    let reviewed=null;
    function reset(){reviewed=null;conf.results.innerHTML='';}
    conf.input.addEventListener('change',reset);
    modeInput.addEventListener('change',reset);
    conf.button.addEventListener('click',async()=>{
      const file=conf.input.files[0],mode=modeInput.value;
      if(!file){toast(`Seleccioná el Excel de ${conf.label}`);return;}
      if(!/\.xlsx$/i.test(file.name)){toast('Debe ser un archivo .xlsx');return;}
      reset();conf.button.disabled=true;
      conf.results.textContent='Comparando esta hoja con tu colección…';
      try{
        const data=await sendAustin(file,'preview',mode,conf.source);
        reviewed={file,mode,digest:data.digest};
        const c=data.counts;
        const changes=data.changes.map(x=>`<li>${html(x.name)} · ${html(x.form)}: ${x.source==='NOT'?'Marcar OT ajeno':`${x.before_home} → ${x.after_home} en HOME`}</li>`).join('');
        conf.results.innerHTML=`<div class="austin-summary"><strong>${html(conf.label)} · ${nf.format(c.matched||0)} Pokémon reconocidos</strong>
          <p>${nf.format(c.obtained||0)} con 0 (obtenidos) · ${nf.format(c.pending||0)} con 1 (pendientes) · ${nf.format(c.not_ot||0)} con NOT (OT ajeno)</p>
          ${c.evo_unresolved?`<p class="austin-warning">${nf.format(c.evo_unresolved)} entradas EVO sin interpretar: no se cambiarán.</p>`:''}
          <p><strong>${nf.format(c.changed||0)} cambios</strong> · ${nf.format(c.unchanged||0)} sin cambios · ${nf.format(data.warnings_total||0)} advertencias</p></div>
          ${changes?`<details class="austin-details"><summary>Ver ejemplos de cambios (máximo 30)</summary><ul>${changes}</ul></details>`:''}
          ${data.warnings_total?`<details class="austin-details"><summary>Ver advertencias</summary><ul>${data.warnings.map(x=>`<li>${html(x)}</li>`).join('')}</ul></details>`:''}
          <button class="btn btn-primary" id="austin-${conf.source}-apply" type="button" ${c.changed?'':'disabled'}>Confirmar ${nf.format(c.changed||0)} cambios en ${html(conf.label)}</button>`;
        conf.results.querySelector(`#austin-${conf.source}-apply`)?.addEventListener('click',async()=>{
          if(!reviewed)return;
          const message=reviewed.mode==='replace'?
            `Se igualarán los 0/1 del Excel de ${conf.label}. Los pendientes podrían quitar progreso existente. ¿Continuar?`:
            `Se sumarán los obtenidos y las marcas OT de ${conf.label}, sin borrar progreso existente. ¿Continuar?`;
          if(!confirm(message))return;
          const button=conf.results.querySelector(`#austin-${conf.source}-apply`);
          button.disabled=true;
          try{
            const saved=await sendAustin(reviewed.file,'apply',reviewed.mode,conf.source,reviewed.digest);
            toast(`${saved.applied} objetivos actualizados`);
            conf.results.innerHTML=`<p class="austin-success">${html(conf.label)}: ${nf.format(saved.applied)} objetivos actualizados. Podés revisar la Pokédex.</p>`;
            reviewed=null;
          }catch(err){toast(err.message);button.disabled=false;}
        });
      }catch(err){conf.results.innerHTML=`<p class="austin-error">${html(err.message)}</p>`;}
      finally{conf.button.disabled=false;}
    });
  }
}
async function renderSettings(){
  const [games, spriteCache]=await Promise.all([request('/api/games'),request('/api/sprites/cache-status')]);
  app.innerHTML=head('PREFERENCIAS','Configuración','Elegí tus juegos y guardá una copia portable del progreso.')+
    `<div class="panel"><div class="panel-header"><h2>Juegos disponibles</h2><span class="tiny">Los cambios se guardan al instante</span></div><p class="description">El catálogo muestra todos los juegos; activá o desactivá aquellos que tenés disponibles. El Shiny Charm se configura por juego (en el futuro, por partida).</p>
     <div class="game-grid">${games.map(g=>`<div class="game-tile"><div class="game-title">${html(g.name)}</div><div class="game-checks"><label class="toggle-line" title="Juego disponible"><input class="game-check" data-game="${html(g.name)}" data-type="available" type="checkbox" ${g.available?'checked':''}> Disponible</label><label class="toggle-line" title="Shiny Charm"><input class="game-check" data-game="${html(g.name)}" data-type="shiny_charm" type="checkbox" ${g.shiny_charm?'checked':''}> Charm</label></div></div>`).join('')}</div></div>
     <div class="panel"><h2>Datos y copias de seguridad</h2><p class="description">El archivo JSON incluye objetivos, tareas Bank, cacerías, fases y configuración. Tu base SQLite vive fuera del código.</p>
     <div class="hunt-actions"><a class="btn" href="/api/backup" download="optpoke-backup.json">↓ Exportar respaldo JSON</a><button id="import-backup" class="btn">↑ Importar respaldo JSON</button><input id="backup-input" type="file" accept=".json,application/json" class="hidden"></div>
     <p class="note">Importar un respaldo sustituye el progreso local actual. Exportá uno primero.</p></div>
     <div class="panel austin-import"><h2>Importar progreso desde AustinJohn</h2>
     <p class="description">Ahora se admiten <strong>dos archivos Excel separados</strong>. Cada uno importa únicamente su colección. La vista previa no escribe nada en la base de datos.</p>
     <div class="austin-import-actions"><label class="austin-mode-label" for="austin-mode">Modo</label><select class="control" id="austin-mode"><option value="merge">Conservar mi progreso: sumar obtenidos</option><option value="replace">Igualar los 0/1 del Excel</option></select></div>
     <div class="austin-source"><h3>Shiny Dex</h3><p class="note">Excel de <strong>Home Shiny Dex Organizer</strong>, hoja <code>S-LivingFormLITE</code>.</p>
       <div class="austin-import-actions"><input id="austin-shiny-file" class="control" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" aria-label="Seleccionar Excel Shiny de AustinJohn">
       <button id="austin-shiny-preview" class="btn btn-primary" type="button">Revisar Shiny</button></div><div id="austin-shiny-results" role="status" aria-live="polite"></div></div>
     <div class="austin-source"><h3>Living Dex</h3><p class="note">Excel de <strong>Home Living Dex Organizer</strong>, hoja <code>LivingFormLITE</code>.</p>
       <div class="austin-import-actions"><input id="austin-normal-file" class="control" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" aria-label="Seleccionar Excel Living de AustinJohn">
       <button id="austin-normal-preview" class="btn btn-primary" type="button">Revisar Living</button></div><div id="austin-normal-results" role="status" aria-live="polite"></div></div>
     <p class="note"><strong>Estados:</strong> 0 = obtenido, 1 = pendiente, <strong>NOT = No OT</strong> (sin asumir captura). <strong>EVO</strong> se muestra como advertencia y no modifica ningún objetivo. Se ignoran los separadores «Gen». Los archivos originales permanecen intactos.</p>
     </div>
     <div class="panel"><h2>Sprites almacenados localmente</h2>
     <p class="description">Las imágenes se descargan únicamente al mostrarlas por primera vez. Después se sirven desde tu computadora, incluso tras reiniciar la aplicación; no se guardan en SQLite ni en los respaldos JSON.</p>
     <div class="kicker">${spriteCache.images.toLocaleString('es-UY')} imágenes · ${(spriteCache.bytes/1048576).toFixed(1)} MB · ${spriteCache.missing} ausencias recordadas</div>
     <p class="note">${spriteCache.offline?'Modo sin conexión activado: no se hacen solicitudes externas.':'Modo normal: solo se consultan fuentes externas cuando falta una imagen en la caché.'} Para iniciar sin ninguna descarga externa: <code>OPTPOKE_SPRITES_OFFLINE=1 python -m uvicorn app.main:app --reload</code>. Las imágenes que aún no estén guardadas mostrarán un marcador.</p></div>`;
  document.querySelectorAll('.game-check').forEach(el=>el.addEventListener('change',async()=>{try{await patch('/api/games/'+encodeURIComponent(el.dataset.game),{[el.dataset.type]:el.checked});toast('Preferencia guardada')}catch(e){toast(e.message)}}));
  setupAustinImport();
  $('#import-backup').addEventListener('click',()=>$('#backup-input').click());
  $('#backup-input').addEventListener('change',async e=>{
    const file=e.target.files[0];if(!file)return;
    if(!confirm('¿Querés reemplazar el progreso local con este respaldo? Esta acción no se puede deshacer.'))return;
    try{const data=JSON.parse(await file.text());await request('/api/backup',{method:'POST',body:JSON.stringify(data)});toast('Respaldo importado');await renderSettings();}
    catch(err){toast(err.message)}
  });
}
// Counter keyboard shortcut when a hunt is visible and the user is not typing.
document.addEventListener('keydown',async e=>{
  if(state.page!=='hunts'||!$('#modal-layer').classList.contains('hidden')||['INPUT','TEXTAREA','SELECT','BUTTON'].includes(document.activeElement?.tagName))return;
  if(e.code!=='Space'&&e.code!=='NumpadAdd')return;
  const active=$('.hunt-card .kicker');if(!active||!active.textContent.includes('ACTIVA'))return;
  const id=Number(active.closest('[data-hunt]').dataset.hunt);e.preventDefault();
  try{await patch('/api/hunts/'+id,{delta:1});await renderHunts()}catch(err){toast(err.message)}
});
go('shiny');

request('/api/runtime').then(config => {
  if (config.demo) {
    const notice = document.createElement('div');
    notice.textContent = 'DEMO · Datos ficticios · Los cambios se descartan al cerrar';
    notice.setAttribute('role', 'status');
    notice.style.cssText = 'padding:12px;background:#d6f282;color:#17251d;text-align:center;font-weight:bold';
    document.querySelector('.main-area').prepend(notice);
    document.title = 'DEMO · Opt. Poke';
  }
}).catch(() => {});
