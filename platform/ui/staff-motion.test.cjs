// UI lifecycle tests: no Flask, model, data files or extra packages.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../static/js/staff-motion.js'),'utf8');

function fixture({reduced=false,engine=true,staff=true}={}) {
  const events={},mediaEvents={},rootEvents={},observers=[],timelines=[];
  const style={removeProperty(key){delete this[key];}};
  const element={id:'section',dataset:{},style,textContent:'Visible content',matches:()=>false,
    contains:target=>target===element,setAttribute(){}};
  const root={inert:false,children:[element],addEventListener:(name,fn)=>rootEvents[name]=fn,
    contains:el=>root.children.includes(el),querySelectorAll:selector=>selector.startsWith('tbody')?root.children:[]};
  const media={matches:reduced,addEventListener:(name,fn)=>mediaEvents[name]=fn};
  const document={hidden:false,querySelector:()=>staff?root:null,addEventListener:(name,fn)=>events[name]=fn};
  class IntersectionObserver {
    constructor(callback,options){this.callback=callback;this.options=options;this.targets=new Set();observers.push(this);}
    observe(el){this.targets.add(el);} unobserve(el){this.targets.delete(el);}
  }
  class MutationObserver {observe(){} }
  const gsap={timeline(options){const tl={paused:true,killed:false,plays:0,resumes:0,
    fromTo(){return this;},play(){this.paused=false;this.plays++;return this;},
    resume(){this.paused=false;this.resumes++;return this;},pause(){this.paused=true;return this;},
    progress(){options.onComplete();return this;},kill(){this.killed=true;return this;}};
    timelines.push(tl);return tl;}};
  const window={gsap:engine?gsap:null,IntersectionObserver,addEventListener:(name,fn)=>events[name]=fn};
  vm.runInNewContext(source,{window,document,matchMedia:()=>media,IntersectionObserver,MutationObserver,
    Node:{ELEMENT_NODE:1,TEXT_NODE:3},Intl,requestAnimationFrame:fn=>fn(),cancelAnimationFrame(){}});
  const intersect=ratio=>observers[0].callback([{target:element,isIntersecting:ratio>0,intersectionRatio:ratio}]);
  return {element,root,window,document,media,mediaEvents,events,rootEvents,observers,timelines,intersect};
}

test('staff only: never initializes on the producer or public page',()=>{
  const f=fixture({staff:false});assert.equal(f.window.StaffMotion,undefined);assert.equal(f.observers.length,0);
});
test('offscreen content stays readable and starts only at the visibility threshold',()=>{
  const f=fixture();assert.equal(f.element.dataset.staffMotion,'pending');assert.equal(f.element.style.opacity,undefined);
  f.intersect(.01);assert.equal(f.timelines.length,0);
  f.intersect(.2);assert.equal(f.timelines.length,1);assert.equal(f.element.dataset.staffMotion,'playing');
  assert.equal(f.observers[0].options.root,f.root);
});
test('leaving the viewport pauses and returning resumes the same timeline',()=>{
  const f=fixture();f.intersect(.4);f.intersect(0);assert.equal(f.timelines[0].paused,true);
  f.intersect(.4);assert.equal(f.timelines.length,1);assert.equal(f.timelines[0].paused,false);
});
test('background tabs do not consume the entrance animation',()=>{
  const f=fixture();f.document.hidden=true;f.intersect(.8);assert.equal(f.timelines.length,0);
  f.document.hidden=false;f.events.visibilitychange();assert.equal(f.timelines.length,1);
});
test('an open modal drawer prevents animation under its overlay',()=>{
  const f=fixture();f.root.inert=true;f.intersect(.8);assert.equal(f.timelines.length,0);
  f.root.inert=false;f.events.visibilitychange();assert.equal(f.timelines.length,1);
});
test('reduced motion and missing GSAP both retain static content',()=>{
  for(const options of [{reduced:true},{engine:false}]){
    const f=fixture(options);assert.equal(f.element.dataset.staffMotion,'complete');assert.equal(f.timelines.length,0);
    assert.equal(f.element.style.opacity,undefined);
  }
});
test('enabling reduced motion finishes safely even with synchronous completion callbacks',()=>{
  const f=fixture();f.intersect(.8);f.media.matches=true;f.mediaEvents.change();
  assert.equal(f.element.dataset.staffMotion,'complete');assert.equal(f.timelines[0].killed,true);
  assert.equal(f.observers[0].targets.size,0);
});
test('filter replacement cancels detached animations and releases observed elements',()=>{
  const f=fixture();f.intersect(.8);f.root.children=[];f.window.StaffMotion.refresh();
  assert.equal(f.timelines[0].killed,true);assert.equal(f.observers[0].targets.size,0);
});
test('focused content is immediately complete and is not replayed on refresh',()=>{
  const f=fixture();f.rootEvents.focusin({target:f.element});assert.equal(f.element.dataset.staffMotion,'complete');
  f.window.StaffMotion.refresh();assert.equal(f.timelines.length,0);
});
test('redrawing with animate false keeps geometry static',()=>{
  const f=fixture();f.element.dataset={};f.root.children=[];f.window.StaffMotion.refresh();
  f.root.children=[f.element];f.window.StaffMotion.refresh({animate:false});
  assert.equal(f.element.dataset.staffMotion,'complete');assert.equal(f.timelines.length,0);
});
