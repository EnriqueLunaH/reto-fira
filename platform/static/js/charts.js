"use strict";
window.Agro = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const colors = ['var(--chart-one)','var(--chart-two)','var(--chart-three)','var(--chart-four)'];
  const chartWidth = container => Math.max(['validation-chart','spatial-chart','importance-chart'].includes(container.id)?220:320,Math.min(container.id==='importance-chart'?720:550,container.clientWidth));
  const number = (n, digits=2) => Number.isFinite(n) ? new Intl.NumberFormat('es-MX',{minimumFractionDigits:digits,maximumFractionDigits:digits}).format(Math.abs(n)<.5*10**(-digits)?0:n) : 'Sin dato';
  const yieldRange = parcel => Number.isFinite(parcel.lower) && Number.isFinite(parcel.upper) ? `${number(parcel.lower)} a ${number(parcel.upper)} t/ha` : 'Intervalo no disponible';
  const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const node = (name,attrs={},text) => {const n=document.createElementNS(NS,name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;};
  function svg(container, width, height, description){container.replaceChildren();const s=node('svg',{viewBox:`0 0 ${width} ${height}`,role:'img','aria-label':description});s.append(node('title',{},description));container.append(s);return s;}
  function empty(container,message='No hay observaciones para esta selección.'){container.replaceChildren();const p=document.createElement('p');p.className='empty-chart';p.textContent=message;container.append(p);}
  function legend(container, series, colorIndices){const l=document.createElement('div');l.className='chart-legend';series.forEach((r,i)=>{const span=document.createElement('span');const mark=document.createElement('i');mark.className='legend-dot';mark.style.backgroundColor=colors[(colorIndices?.[i]??i)%colors.length];span.append(mark,document.createTextNode(r));l.append(span);});container.append(l);}
  function bars(container,rows,unit='',opts={}){
    if(!rows.length){empty(container);return;}
    const stacked=(container.id==='spatial-chart'&&container.clientWidth<360)||(container.id==='importance-chart'&&container.clientWidth<480);
    const W=chartWidth(container),H=Math.max(180,rows.length*(stacked?62:43)+35),left=stacked?12:opts.longLabels?Math.min(185,W*.48):Math.min(115,W*.32),right=58,top=15,bottom=30;
    const lo=Math.min(0,...rows.map(r=>r.value)),hi=Math.max(.001,...rows.map(r=>r.value));const pad=(hi-lo)*.1;
    const min=lo<0?lo-pad:0,max=hi+pad,x=v=>left+(v-min)/(max-min)*(W-left-right);
    const s=svg(container,W,H,`Barras: ${rows.map(r=>`${r.label}, ${number(r.value)} ${unit}`).join('; ')}`);
    for(let i=0;i<4;i++){const v=min+(max-min)*i/3;s.append(node('line',{x1:x(v),x2:x(v),y1:top,y2:H-bottom,class:'grid-line'}));s.append(node('text',{x:x(v),y:H-8,'text-anchor':stacked?(i===0?'start':i===3?'end':'middle'):'middle'},number(v,container.id==='importance-chart'?2:1)));}
    if(lo<0)s.append(node('line',{x1:x(0),x2:x(0),y1:top,y2:H-bottom,stroke:'#9da994','stroke-width':1}));
    rows.forEach((r,i)=>{const y=top+i*(stacked?62:43)+(stacked?26:8);s.append(node('text',{x:stacked?left:left-12,y:stacked?y-8:y+16,'text-anchor':stacked?'start':'end'},r.label));const rect=node('rect',{x:Math.min(x(0),x(r.value)),y,width:Math.max(0.5,Math.abs(x(r.value)-x(0))),height:25,rx:3,fill:r.color||colors[i%colors.length]});rect.append(node('title',{},`${r.label}: ${number(r.value,3)} ${unit}`));s.append(rect);s.append(node('text',{x:W-8,y:y+17,'text-anchor':'end',class:'value-label'},number(r.value,opts.digits??2)));});
  }
  function lines(container,history){
    const sensors=['Sentinel-2','Planet'];const usable=history.filter(r=>r.ndvi!==null&&r.ndvi!==undefined&&Number.isFinite(r.ndvi));
    if(!usable.length){empty(container,'No hay mediciones de NDVI válidas durante el ciclo.');return;}
    const W=chartWidth(container),H=275,left=43,right=18,top=20,bottom=38,x=m=>left+(m-4)/6*(W-left-right),y=v=>top+(1-v)/1.2*(H-top-bottom);
    const s=svg(container,W,H,'NDVI mensual de abril a octubre de 2025, separado por sensor.');
    for(const v of [0,.25,.5,.75,1]){s.append(node('line',{x1:left,x2:W-right,y1:y(v),y2:y(v),class:'grid-line'}));s.append(node('text',{x:left-10,y:y(v)+4,'text-anchor':'end'},number(v,2)));}
    ['Abr','May','Jun','Jul','Ago','Sep','Oct'].forEach((m,i)=>s.append(node('text',{x:x(i+4),y:H-10,'text-anchor':'middle'},m)));
    sensors.forEach((sensor,i)=>{let segment=[];const draw=()=>{if(segment.length>1)s.append(node('polyline',{points:segment.map(r=>`${x(r.month)},${y(r.ndvi)}`).join(' '),fill:'none',stroke:colors[i],'stroke-width':2.5}));segment=[];};for(let m=4;m<=10;m++){const r=usable.find(r=>r.sensor===sensor&&r.month===m);if(!r){draw();continue;}segment.push(r);const mark=node('circle',{cx:x(m),cy:y(r.ndvi),r:4,fill:colors[i],class:'chart-dot'});mark.append(node('title',{},`${sensor}, mes ${m}: NDVI ${number(r.ndvi,3)}`));s.append(mark);}draw();});const present=sensors.filter(sensor=>usable.some(r=>r.sensor===sensor));legend(container,present,present.map(sensor=>sensors.indexOf(sensor)));
  }
  function scatter(container,rows){
    if(!rows.length){empty(container);return;}
    const W=chartWidth(container),H=300,left=45,bottom=40,right=25,top=20,max=Math.ceil(Math.max(6,...rows.flatMap(r=>[r.actual,r.predicted]))),x=v=>left+v/max*(W-left-right),y=v=>H-bottom-v/max*(H-top-bottom);
    const s=svg(container,W,H,`${rows.length} parcelas: rendimiento observado en el eje horizontal y estimado en el vertical, en t/ha.`);
    for(let i=0;i<=max;i+=Math.max(1,Math.floor(max/6))){s.append(node('line',{x1:left,x2:W-right,y1:y(i),y2:y(i),class:'grid-line'}));s.append(node('text',{x:left-10,y:y(i)+4,'text-anchor':'end'},String(i)));s.append(node('text',{x:x(i),y:H-bottom+20,'text-anchor':'middle'},String(i)));}
    s.append(node('line',{x1:x(0),x2:x(max),y1:y(0),y2:y(max),stroke:'#b9af94','stroke-dasharray':'5 5'}));
    rows.forEach(r=>{const i=['Hidalgo','Puebla','Tlaxcala'].indexOf(r.state);const c=node('circle',{cx:x(r.actual),cy:y(r.predicted),r:4.2,fill:colors[i],opacity:.75,class:'chart-dot'});c.append(node('title',{},`${r.ID_parcela}: observado ${number(r.actual)}, estimado ${number(r.predicted)} t/ha`));s.append(c);});s.append(node('text',{x:W/2,y:H-3,'text-anchor':'middle'},'Observado (t/ha)'));s.append(node('text',{x:left+4,y:12},'Estimado (t/ha)'));legend(container,['Hidalgo','Puebla','Tlaxcala']);
  }
  function parcelMap(container,feature){
    if(!feature){empty(container,'Geometría no disponible.');return;}
    const polygons=feature.geometry.type==='Polygon'?[feature.geometry.coordinates]:feature.geometry.coordinates;
    const points=polygons.flat(2),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),lat=(minY+maxY)/2,aspect=Math.cos(lat*Math.PI/180);
    const W=550,H=230,pad=30,scale=Math.min((W-2*pad)/((maxX-minX)*aspect||1),(H-2*pad)/(maxY-minY||1));
    const x=v=>W/2+(v-(minX+maxX)/2)*aspect*scale,y=v=>H/2-(v-(minY+maxY)/2)*scale;
    const s=svg(container,W,H,`Polígono de ${feature.properties.ID_POLIGONO}`);
    for(let i=0;i<10;i++)s.append(node('line',{x1:0,x2:W,y1:i*26,y2:i*26,stroke:'#dfe5d7','stroke-width':.5}));
    polygons.forEach(poly=>s.append(node('path',{d:poly.map(ring=>'M'+ring.map(p=>`${x(p[0])},${y(p[1])}`).join('L')+'Z').join(''),fill:'#76936d',stroke:'#355a40','stroke-width':2,'fill-rule':'evenodd'})));
    s.append(node('text',{x:W-22,y:22,'text-anchor':'end'},'N ↑'));s.append(node('text',{x:18,y:H-13},feature.properties.ID_POLIGONO));
  }
  function regionalMap(container,rows,onSelect){
    if(!rows.length){empty(container);return;}
    const W=550,H=275,pad=28,minX=Math.min(...rows.map(r=>r.longitude))-.03,maxX=Math.max(...rows.map(r=>r.longitude))+.03,minY=Math.min(...rows.map(r=>r.latitude))-.03,maxY=Math.max(...rows.map(r=>r.latitude))+.03;
    const x=v=>pad+(v-minX)/(maxX-minX)*(W-2*pad),y=v=>H-pad-(v-minY)/(maxY-minY)*(H-2*pad);const s=svg(container,W,H,`${rows.length} centros de parcela en longitud y latitud WGS 84.`);
    for(let i=1;i<5;i++){s.append(node('line',{x1:pad,x2:W-pad,y1:pad+i*(H-2*pad)/5,y2:pad+i*(H-2*pad)/5,class:'grid-line'}));s.append(node('text',{x:4,y:pad+i*(H-2*pad)/5+4},number(maxY-i*(maxY-minY)/5,1)));}
    rows.forEach(r=>{const c=node('circle',{cx:x(r.longitude),cy:y(r.latitude),r:5,fill:colors[['Hidalgo','Puebla','Tlaxcala'].indexOf(r.state)],stroke:'#fffef9','stroke-width':1,class:'map-button',tabindex:0,role:'button','aria-label':`${r.id}, ${number(r.yield)} t/ha`});c.append(node('title',{},`${r.id} · ${r.state} · ${number(r.yield)} t/ha`));const select=()=>{container.querySelector('.map-detail')?.remove();const d=document.createElement('div');d.className='map-detail';d.textContent=`${r.id} · ${r.municipality} · ${number(r.yield)} t/ha`;container.append(d);if(onSelect)onSelect(r);};c.addEventListener('click',select);c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});s.append(c);});s.append(node('text',{x:W-14,y:18,'text-anchor':'end'},'N ↑'));s.append(node('text',{x:W/2,y:H-4,'text-anchor':'middle'},'Longitud (°)'));legend(container,['Hidalgo','Puebla','Tlaxcala']);
  }
  async function get(url){const response=await fetch(url);if(!response.ok)throw new Error(response.status===401?'Tu sesión terminó. Vuelve a iniciar sesión.':'No pudimos cargar los datos. Intenta recargar la página.');return response.json();}
  return {colors,number,yieldRange,escape,bars,lines,scatter,parcelMap,regionalMap,get,empty};
})();
