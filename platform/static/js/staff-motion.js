"use strict";
(() => {
  const root = document.querySelector('body[data-page="staff"] .staff-main');
  if (!root) return;
  const gsap = window.gsap;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const records = new Map(), completed = new Set();
  let frame = 0;
  const canAnimate = () => Boolean(gsap && window.IntersectionObserver && !reduced.matches);
  const canPlay = () => !document.hidden && !root.inert;

  // Content stays visible until its observer actually sees it. No hidden CSS
  // pre-state: failed JS, blocked GSAP and reduced motion all retain real values.
  function finish(record) {
    if (record.finished) return;
    record.finished = true;
    record.timeline?.progress(1).kill();
    record.restore?.();
    record.element.dataset.staffMotion = 'complete';
    if (record.key) completed.add(record.key);
    if (completed.size > 1000) completed.clear();
    observer?.unobserve(record.element);
    records.delete(record.element);
  }

  function play(record) {
    if (!record.visible || !canPlay()) return;
    if (!canAnimate()) { finish(record); return; }
    if (record.timeline) { record.timeline.resume(); return; }
    record.element.dataset.staffMotion = 'playing';
    const timeline = gsap.timeline({paused:true, onComplete:() => finish(record)});
    record.timeline = timeline;
    record.build(timeline);
    timeline.play();
  }

  const observer = window.IntersectionObserver ? new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const record = records.get(entry.target);
      if (!record) return;
      record.visible = entry.isIntersecting && entry.intersectionRatio >= .12;
      if (record.visible) play(record); else record.timeline?.pause();
    });
  }, {root, rootMargin:'-64px 0px -24px 0px', threshold:[0,.12]}) : null;

  function register(element, key, build, restore, animate) {
    if (element.dataset.staffMotion || records.has(element)) return;
    const record = {element,key,build,restore,visible:false,timeline:null};
    if (!canAnimate() || completed.has(key) || !animate) {
      element.dataset.staffMotion = 'complete';
      return;
    }
    element.dataset.staffMotion = 'pending';
    records.set(element,record);
    observer.observe(element);
  }

  function counter(element, animate) {
    if (element.dataset.staffMotion) return;
    const original = [...element.childNodes].find(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
    if (!original) return;
    const text = original.textContent.trim();
    const match = /^([−-]?\$?)([\d,]+(?:\.\d+)?)(%?)$/.exec(text);
    if (!match) return;
    const value = Number(match[2].replaceAll(',',''));
    if (!Number.isFinite(value)) return;
    const digits = (match[2].split('.')[1] || '').length;
    const formatter = new Intl.NumberFormat('es-MX',{minimumFractionDigits:digits,maximumFractionDigits:digits});
    const card = element.closest('.kpi');
    const key = `counter:${element.closest('[id]')?.id}:${card?.querySelector('.kpi-label')?.textContent}:${text}`;
    let visible, accessible;
    const restore = () => {
      if (visible) visible.textContent = text;
    };
    register(element,key,timeline => {
      // Screen readers always receive the final number, never 30 live updates.
      visible = document.createElement('span');
      visible.setAttribute('aria-hidden','true');
      visible.className = 'staff-counter-visual';
      visible.append(document.createTextNode(text));
      accessible = document.createElement('span');
      accessible.className = 'sr-only';
      accessible.textContent = text;
      original.replaceWith(accessible,visible,document.createTextNode(' '));
      visible.style.minWidth = `${visible.getBoundingClientRect().width}px`;
      visible.firstChild.data = `${match[1]}${formatter.format(0)}${match[3]}`;
      const progress = {value:0};
      timeline.to(progress,{value,duration:.75,ease:'power2.out',onUpdate:() => {
        visible.firstChild.data = `${match[1]}${formatter.format(progress.value)}${match[3]}`;
      }});
    },restore,animate);
  }

  function chart(element, animate) {
    if (element.dataset.staffMotion) return;
    const host = element.parentElement;
    const key = `chart:${host.id}:${element.getAttribute('aria-label') || element.querySelector('desc')?.textContent || ''}`;
    const marks = [...element.querySelectorAll('rect, circle.chart-dot, circle.map-button')];
    if (!marks.length) return;
    const attributes = marks.map(mark => ({mark, width:mark.getAttribute('width'), x:mark.getAttribute('x'),
      y:mark.getAttribute('y'),height:mark.getAttribute('height'),r:mark.getAttribute('r'),opacity:mark.style.opacity}));
    const restore = () => attributes.forEach(({mark,...values}) => {
      for (const name of ['width','x','y','height','r']) if (values[name] !== null) mark.setAttribute(name,values[name]);
      if (values.opacity) mark.style.opacity=values.opacity; else mark.style.removeProperty('opacity');
    });
    register(element,key,timeline => {
      attributes.forEach(({mark,width,x,y,height,r},i) => {
        const delay = Math.min(i*.018,.22);
        if (mark.tagName.toLowerCase()==='circle') {
          timeline.fromTo(mark,{attr:{r:0},opacity:.15},{attr:{r:Number(r)},opacity:1,duration:.42,ease:'power2.out'},delay);
        } else if (host.id==='risk-histogram') {
          timeline.fromTo(mark,{attr:{height:0,y:Number(y)+Number(height)}},
            {attr:{height:Number(height),y:Number(y)},duration:.65,ease:'power2.out'},delay);
        } else {
          // Negative bars grow left from zero; their end label supplies the sign.
          const label = mark.nextElementSibling;
          const negative = label?.classList.contains('value-label') && Number(label.textContent.replaceAll(',',''))<0;
          timeline.fromTo(mark,{attr:{width:0,x:negative?Number(x)+Number(width):Number(x)}},
            {attr:{width:Number(width),x:Number(x)},duration:.65,ease:'power2.out'},delay);
        }
      });
    },restore,animate);
  }

  function reveal(element,animate) {
    const key = element.matches('tr') ? `row:${element.closest('table')?.className}:${element.textContent.trim()}` : `section:${element.id || element.textContent.trim().slice(0,100)}`;
    const opacity = element.style.opacity, transform = element.style.transform;
    register(element,key,timeline => {
      timeline.fromTo(element,{opacity:.45,y:6},{opacity:1,y:0,duration:.36,ease:'power2.out'});
    },() => {
      if (opacity) element.style.opacity=opacity; else element.style.removeProperty('opacity');
      if (transform) element.style.transform=transform; else element.style.removeProperty('transform');
    },animate);
  }

  function refresh({animate=true}={}) {
    // Release detached rows/SVGs when filtering, sorting or redrawing charts.
    for (const record of records.values()) if (!root.contains(record.element)) {
      record.timeline?.kill(); observer?.unobserve(record.element); records.delete(record.element);
    }
    root.querySelectorAll('.kpi-number').forEach(element => counter(element,animate));
    root.querySelectorAll('.chart > svg, .map-container > svg, #risk-histogram > svg').forEach(element => chart(element,animate));
    root.querySelectorAll('tbody > tr, [data-staff-reveal], .map-detail').forEach(element => reveal(element,animate));
    root.querySelectorAll('.map-detail').forEach(element => { element.setAttribute('role','status'); element.setAttribute('aria-live','polite'); });
  }

  // Observe added nodes, not animation attributes or every counter frame.
  new MutationObserver(mutations => {
    if (!mutations.some(m => [...m.addedNodes].some(n => n.nodeType===Node.ELEMENT_NODE))) return;
    cancelAnimationFrame(frame); frame=requestAnimationFrame(() => refresh());
  }).observe(root,{childList:true,subtree:true});
  function syncVisibility() {
    records.forEach(record => { if (canPlay()) play(record); else record.timeline?.pause(); });
  }
  new MutationObserver(syncVisibility).observe(root,{attributes:true,attributeFilter:['inert']});
  document.addEventListener('visibilitychange',syncVisibility);
  reduced.addEventListener('change',() => { if (reduced.matches) [...records.values()].forEach(finish); });
  root.addEventListener('focusin',event => {
    // Never leave a keyboard-focused map or row partially revealed.
    [...records.values()].forEach(record => { if (record.element.contains(event.target)) finish(record); });
  });
  function selectMapPoint(event) {
    const point = event.target.closest?.('.map-button');
    if (!point || (event.type==='keydown' && !['Enter',' '].includes(event.key))) return;
    point.closest('svg').querySelectorAll('.map-button').forEach(mark => mark.setAttribute('aria-pressed',String(mark===point)));
  }
  root.addEventListener('click',selectMapPoint);
  root.addEventListener('keydown',selectMapPoint);
  window.addEventListener('beforeprint',() => { [...records.values()].forEach(finish); });
  window.addEventListener('pagehide',() => { [...records.values()].forEach(finish); });
  window.StaffMotion = {refresh};
  refresh();
})();
