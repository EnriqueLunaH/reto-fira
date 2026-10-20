"use strict";
(async()=>{
  const A=window.Agro,$=id=>document.getElementById(id),state=$('staff-state'),search=$('staff-search');
  let data,sort='id',direction=1;
  const kpi=(label,value,unit,note)=>`<article class="kpi"><p class="kpi-label">${A.escape(label)}</p><p class="kpi-number">${value} <small>${unit}</small></p><p class="kpi-footnote">${A.escape(note)}</p></article>`;

  function render({animate=true}={}){
    const selectedState=state?.value||'',q=(search?.value||'').toLowerCase().trim();
    const rows=data.parcels.filter(p=>(!selectedState||p.state===selectedState)&&(!q||`${p.id} ${p.municipality}`.toLowerCase().includes(q)));

    if($('kpis')){
      const area=rows.reduce((s,p)=>s+p.area_ha,0),total=rows.reduce((s,p)=>s+p.total_t,0);
      $('kpis').innerHTML=kpi('Parcelas con predicción',String(rows.length),'','Conjunto PREDICCION')+kpi('Rendimiento estimado',area?A.number(total/area):'—','t/ha','Promedio ponderado por superficie')+kpi('Grano estimado',rows.length?A.number(total,1):'—','t','Suma de estimación × hectáreas')+kpi('Superficie registrada',A.number(area,1),'ha','Parcelas visibles');
      const byState=['Hidalgo','Puebla','Tlaxcala'].map((s,i)=>{const r=rows.filter(p=>p.state===s);const ha=r.reduce((a,p)=>a+p.area_ha,0);return {label:s,value:ha?r.reduce((a,p)=>a+p.total_t,0)/ha:null,color:A.colors[i]};}).filter(r=>r.value!==null);
      A.bars($('state-chart'),byState,'t/ha');
      A.regionalMap($('regional-map'),rows);
      $('overview-scope').textContent=`${rows.length} de ${data.parcels.length} parcelas · ${selectedState||'Todos los estados'}${q?' · Búsqueda activa':''}`;
      $('overview-empty').hidden=rows.length>0;
      $('staff-status').textContent='';
    }

    if($('predictions-table')){
      const hasInterval=p=>Number.isFinite(p.lower)&&Number.isFinite(p.upper);
      const showInterval=rows.some(hasInterval);
      $('prediction-interval-heading').hidden=!showInterval;
      const sorted=[...rows].sort((a,b)=>direction*(sort==='id'?a.id.localeCompare(b.id):a.yield-b.yield));
      $('predictions-table').innerHTML=sorted.length?sorted.map(p=>`<tr><th scope="row" class="row-id"><span class="predictions-parcel-id">${A.escape(p.id)}</span></th><td class="predictions-location"><span class="state-pill">${A.escape(p.state)}</span><span class="row-city">${A.escape(p.municipality)}</span></td><td class="predictions-numeric">${A.number(p.area_ha)}</td><td class="predictions-numeric predictions-yield">${A.number(p.yield,4)}</td>${showInterval?`<td class="predictions-numeric predictions-range">${hasInterval(p)?`${A.number(p.lower)} – ${A.number(p.upper)}`:"No disponible"}</td>`:''}<td class="predictions-numeric">${A.number(p.total_t)}</td></tr>`).join(''):`<tr><td colspan="${showInterval?6:5}" class="table-empty"><span class="predictions-empty-mark" aria-hidden="true">⌕</span><strong>No encontramos parcelas</strong><p>Prueba otro identificador o municipio, o restablece los filtros para volver al conjunto completo.</p><button type="button" class="button secondary" data-predictions-reset>Restablecer filtros</button></td></tr>`;
      $('table-count').textContent=`${rows.length} ${rows.length===1?'parcela':'parcelas'}`;
      $('predictions-results-note').textContent=`${rows.length} de ${data.parcels.length} parcelas${selectedState||q?' · Vista filtrada':''}`;
      $('predictions-filter-description').textContent=[selectedState||'Todos los estados',q?`Búsqueda: «${search.value.trim()}»`:'Sin búsqueda'].join(' · ');
      $('prediction-id-heading').setAttribute('aria-sort',sort==='id'?(direction===1?'ascending':'descending'):'none');
      $('prediction-yield-heading').setAttribute('aria-sort',sort==='yield'?(direction===1?'ascending':'descending'):'none');
      $('sort-id').setAttribute('aria-label',`Ordenar por parcela ${sort==='id'&&direction===1?'de mayor a menor':'de menor a mayor'}`);
      $('sort-yield').setAttribute('aria-label',`Ordenar por rendimiento ${sort==='yield'&&direction===1?'de mayor a menor':'de menor a mayor'}`);
      $('predictions-sort-description').textContent=`${sort==='id'?'Parcela':'Rendimiento'} · ${direction===1?'Ascendente':'Descendente'}`;
      const tableRegion=$('predictions-table').closest('[role="region"]'),viewKey=JSON.stringify([selectedState,q,sort,direction]);
      if(tableRegion.dataset.view!==viewKey){tableRegion.scrollTop=0;tableRegion.dataset.view=viewKey;}
      tableRegion.tabIndex=rows.length?0:-1;
      $('predictions-scroll-hint').hidden=!rows.length;
      if(rows.length)tableRegion.setAttribute('aria-describedby','predictions-scroll-hint');else tableRegion.removeAttribute('aria-describedby');
      const params=new URLSearchParams();
      if(selectedState)params.set('state',selectedState);
      if(q)params.set('search',q);
      $('download').href='/export/predictions.csv'+(params.size?'?'+params.toString():'');
    }

    if($('quality-kpis')){
      const validation=data.validation.filter(r=>!selectedState||r.state===selectedState),n=validation.length;
      const mae=n?validation.reduce((s,r)=>s+Math.abs(r.actual-r.predicted),0)/n:null,rmse=n?Math.sqrt(validation.reduce((s,r)=>s+(r.actual-r.predicted)**2,0)/n):null;
      const mean=n?validation.reduce((s,r)=>s+r.actual,0)/n:0,denominator=validation.reduce((s,r)=>s+(r.actual-mean)**2,0);
      const r2=denominator?1-validation.reduce((s,r)=>s+(r.actual-r.predicted)**2,0)/denominator:null,baseline=n?validation.reduce((s,r)=>s+Math.abs(r.actual-r.baseline),0)/n:null;
      $('quality-kpis').innerHTML=kpi('MAE por parcela',mae===null?'—':A.number(mae,3),'t/ha',`${n} parcelas fuera de muestra`)+kpi('RMSE por parcela',rmse===null?'—':A.number(rmse,3),'t/ha','Validación anidada en 5 particiones')+kpi('R² por parcela',r2===null?'—':A.number(r2,3),'','Comparado con la media observada')+kpi('MAE de referencia',baseline===null?'—':A.number(baseline,3),'t/ha','Mediana del entrenamiento por partición');
      A.scatter($('validation-chart'),validation);
      const spatial=selectedState?data.metrics.spatial_cv.by_state[selectedState]:data.metrics.spatial_cv.model;
      const spatialRows=data.spatial_validation.filter(r=>!selectedState||r.state===selectedState),spatialBaseline=spatialRows.length?spatialRows.reduce((s,r)=>s+Math.abs(r.actual-r.baseline),0)/spatialRows.length:null;
      A.bars($('spatial-chart'),[{label:'Por parcela',value:mae,color:A.colors[0]},{label:'Referencia parcela',value:baseline,color:A.colors[1]},{label:'Por bloques',value:spatial.mae,color:A.colors[3]},{label:'Referencia bloques',value:spatialBaseline,color:A.colors[2]}].filter(r=>r.value!==null),'MAE (t/ha)',{digits:3,longLabels:true});
    }

    if($('importance-chart')){
      A.bars($('importance-chart'),data.importance.map(r=>({label:r.name,value:r.mae_increase,color:A.colors[0]})),'Δ MAE (t/ha)',{longLabels:true,digits:3});
      if($('importance-scope'))$('importance-scope').textContent=data.metadata.importance_method==='grouped_permutation_outer_oof'?'Evaluación global · 138 parcelas fuera de muestra.':`Evaluación global · ${data.metadata.n_calibration} parcelas de calibración.`;
      if($('importance-method')&&data.metadata.importance_method==='grouped_permutation_outer_oof')$('importance-method').textContent='Se permutan grupos de variables en las cinco particiones externas de la primera repetición, con diez permutaciones por grupo. Describe el procedimiento seleccionado mediante distintos ajustes; no es una explicación causal ni una evaluación del modelo final sobre su propio entrenamiento.';
    }
    if($('model-note')){
      const m=data.metrics,nominal=data.metadata.interval.nominal_coverage;
      if(data.metadata.interval.method==='not_estimated'){
        $('model-note').textContent=`Modelo final: ${data.metadata.selection.name.replaceAll('_',' ')}. Ajuste con las ${data.metadata.n_fit} parcelas etiquetadas. La comparación repitió cinco veces la validación anidada y evaluó bloques de 10 y 20 km. Las gráficas muestran la primera repetición y el estrés de 20 km. No se publica un intervalo para este predictor; los rangos del modelo anterior no se reutilizan. Las 59 etiquetas ocultas no se conocen.`;
        if($('final-fitting-note'))$('final-fitting-note').textContent='El predictor puntual se ajusta con las 138 parcelas etiquetadas. No reserva parcelas para calibración de intervalos.';
      }else{
        $('model-note').textContent=`Modelo final: ${data.metadata.selection.name.replaceAll('_',' ')}. Filtro de nubes ≤ ${data.metadata.selection.cloud}%. Ajuste con ${data.metadata.n_fit} parcelas y calibración con ${data.metadata.n_calibration}. Cobertura observada de los rangos del ${nominal*100}% por parcela: ${A.number(m.parcel_cv.coverage_90*100,1)}% (${m.parcel_cv.interval_evaluation_n} casos); por bloques: ${A.number(m.spatial_cv.coverage_90*100,1)}% (${m.spatial_cv.interval_evaluation_n} casos con rango finito). Son resultados globales, no garantías individuales.`;
        if($('final-fitting-note'))$('final-fitting-note').textContent=`El modelo se ajusta con ${data.metadata.n_fit} parcelas y reserva ${data.metadata.n_calibration} para calibrar intervalos.`;
      }
    }
    window.StaffMotion?.refresh({animate});
  }

  let resizeTimer,lastWidth=$('main-content').clientWidth;
  window.addEventListener('resize',()=>{
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(()=>{
      const width=$('main-content').clientWidth;
      if(data&&width!==lastWidth){lastWidth=width;render({animate:false});}
    },160);
  });
  try{
    data=await A.get('/api/dashboard');
    $('staff-content').hidden=false;
    state?.addEventListener('change',render);
    search?.addEventListener('input',render);
    $('reset-filters')?.addEventListener('click',()=>{if(state)state.value='';if(search)search.value='';render();});
    $('sort-id')?.addEventListener('click',()=>{direction=sort==='id'?-direction:1;sort='id';render();});
    $('sort-yield')?.addEventListener('click',()=>{direction=sort==='yield'?-direction:1;sort='yield';render();});
    $('predictions-table')?.addEventListener('click',event=>{if(event.target.closest('[data-predictions-reset]'))$('reset-filters').click();});
    $('overview-empty')?.addEventListener('click',event=>{if(event.target.closest('[data-overview-reset]'))$('reset-filters').click();});
    if($('predictions-workbench')){
      $('predictions-workbench').setAttribute('aria-busy','false');
      $('staff-status').textContent='';
    }
    render();
  }catch(error){
    $('staff-status').textContent=error.message;
    if($('predictions-workbench')){
      $('predictions-workbench').setAttribute('aria-busy','false');
      $('table-count').textContent='Sin cargar';
      $('staff-status').classList.add('predictions-load-error');
    }
  }
})();
