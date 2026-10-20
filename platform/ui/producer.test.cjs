// UI-only regression checks. In-memory API/DOM fixtures; no model or artifacts loaded.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/js/producer.js'), 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
const rows = [{id:'A', municipality:'Municipio Á', state:'Puebla'}, {id:'B', municipality:'Otro', state:'Hidalgo'}];
const detail = (id='A', overrides={}) => ({parcel:{...rows.find(p=>p.id===id), yield:3.3133, total_t:61.8926, area_ha:18.68, lower:null, upper:null, rain_mm:0, elevation_m:null, slope_deg:0, clear_months:0, outside_training_range:[], ...overrides}, history:[{sensor:'Planet', month:4, ndvi:0}], metadata:{interval:{method:'not_estimated'}}});
function fixture() {
  const elements={}, pending=[], timers=new Map(), observers=[];
  let timerId=0, plots=0;
  class Element {
    constructor(id='') { this.id=id; this.children=[]; this.value=''; this.textContent=''; this.hidden=false; this.dataset={}; this.attributes={}; this.events={}; this.clientWidth=500; }
    append(...nodes) { this.children.push(...nodes); if (nodes.length && ['parcel-select','producer-state'].includes(this.id) && this.children.length===nodes.length) this.value=nodes[0].value; }
    replaceChildren(...nodes) { this.children=[]; this.value=''; this.append(...nodes); }
    setAttribute(k,v) { this.attributes[k]=v; }
    getAttribute(k) { return this.attributes[k]; }
    addEventListener(k,fn) { this.events[k]=fn; }
    querySelectorAll() { return []; }
    focus() { this.focused=true; }
  }
  const el=id=>elements[id] ||= new Element(id);
  el('producer-content').hidden=true;
  el('producer-vegetation-panel').hidden=true;
  const document={getElementById:el, createElement:()=>new Element(), querySelectorAll:()=>[], addEventListener(){}};
  const number=(v,d=2)=>Number.isFinite(v)?new Intl.NumberFormat('es-MX',{minimumFractionDigits:d,maximumFractionDigits:d}).format(v):'Sin dato';
  const Agro={get:url=>new Promise((resolve,reject)=>pending.push({url,resolve,reject})),number,empty:(target,text)=>target.textContent=text,parcelMap:target=>target.textContent='map',lines:()=>plots++,colors:['a','b']};
  class Observer { constructor(fn){this.fn=fn;observers.push(this);} observe(){} }
  const window={Agro, matchMedia:()=>({matches:true,addEventListener(){}}),addEventListener(){}};
  const context={window,document,MutationObserver:Observer,requestAnimationFrame:fn=>{fn();return 0;},cancelAnimationFrame(){},setTimeout:fn=>{timers.set(++timerId,fn);return timerId;},clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(source,context);
  const take=url=>{const index=pending.findIndex(p=>p.url===url);assert.notEqual(index,-1,`Expected request ${url}`);return pending.splice(index,1)[0];};
  const flushSearch=()=>{const jobs=[...timers.values()];timers.clear();jobs.forEach(fn=>fn());};
  async function ready() { take('/api/parcels').resolve(rows);await tick();take('/api/parcels/A').resolve(detail());await tick(); }
  return {el,take,pending,ready,flushSearch,observers,get plots(){return plots;}};
}
test('exact API values, meaningful zeroes and no fabricated range', async()=>{
  const f=fixture();await f.ready();
  assert.equal(f.el('total-value').textContent,'61.9');
  assert.equal(f.el('yield-value').textContent,'3.31');
  assert.equal(f.el('rain-value').textContent,'0 mm');
  assert.equal(f.el('elevation-value').textContent,'Sin dato');
  assert.equal(f.el('yield-range').hidden,true);
  assert.match(f.el('yield-range-note').textContent,/No hay un rango validado/);
  assert.equal(f.el('vegetation-values').children[0].children[2].textContent,'0.000');
  assert.equal(f.el('vegetation-values').children[1].children[2].textContent,'Sin medición');
});
test('a geometry failure does not hide the yield estimate', async()=>{
  const f=fixture();f.take('/api/geometry').reject(new Error('offline'));await f.ready();
  assert.equal(f.el('producer-content').hidden,false);
  assert.match(f.el('parcel-map').textContent,/no está disponible/);
});
test('late response from a previous selection cannot overwrite the current parcel', async()=>{
  const f=fixture();await f.ready();
  f.el('parcel-select').events.change();const old=f.take('/api/parcels/A');
  assert.equal(f.el('producer-content').hidden,true);
  f.el('parcel-select').value='B';f.el('parcel-select').events.change();
  f.take('/api/parcels/B').resolve(detail('B'));await tick();
  old.resolve(detail('A'));await tick();
  assert.equal(f.el('parcel-title').textContent,'B');
});
test('search ignores accents; empty results hide stale data; clearing restores selection', async()=>{
  const f=fixture();await f.ready();
  f.el('parcel-search').value='municipio a';f.el('parcel-search').events.input();f.flushSearch();
  f.take('/api/parcels/A').resolve(detail());await tick();
  assert.equal(f.el('parcel-count').textContent,'1 de 2 parcelas');
  f.el('parcel-search').value='missing';f.el('parcel-search').events.input();f.flushSearch();
  assert.equal(f.el('producer-content').hidden,true);
  assert.equal(f.el('parcel-select').disabled,true);
  assert.equal(f.el('producer-status').dataset.state,'empty');
  f.el('clear-filters').events.click();f.take('/api/parcels/A').resolve(detail());await tick();
  assert.equal(f.el('parcel-count').textContent,'2 de 2 parcelas');
  assert.equal(f.el('producer-content').hidden,false);
  assert.equal(f.el('parcel-search').focused,true);
});
test('a request error provides retry and then restores content', async()=>{
  const f=fixture();await f.ready();f.el('parcel-select').value='B';f.el('parcel-select').events.change();
  f.take('/api/parcels/B').reject(new Error('No pudimos cargar los datos.'));await tick();
  assert.equal(f.el('producer-recovery').hidden,false);
  assert.equal(f.el('producer-content').hidden,true);
  f.el('producer-retry').events.click();f.take('/api/parcels/B').resolve(detail('B'));await tick();
  assert.equal(f.el('producer-recovery').hidden,true);
  assert.equal(f.el('parcel-title').textContent,'B');
});
test('initial failure is recoverable without duplicate event handlers', async()=>{
  const f=fixture();f.take('/api/parcels').reject(new Error('offline'));await tick();
  assert.equal(f.el('producer-recovery').hidden,false);
  f.el('producer-retry').events.click();await f.ready();
  assert.equal(f.el('producer-content').hidden,false);
});
test('chart stays deferred while collapsed and draws when the panel opens', async()=>{
  const f=fixture();await f.ready();assert.equal(f.plots,0);
  f.el('producer-vegetation-panel').hidden=false;f.observers[0].fn();
  assert.equal(f.plots,1);f.observers[0].fn();assert.equal(f.plots,1);
});
