"use strict";
(() => {
  if (!window.gsap || !window.ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);
  const media = gsap.matchMedia();
  media.add('(prefers-reduced-motion: no-preference)', () => {
    const entrance = gsap.timeline({defaults: {ease: 'power3.out'}});
    entrance.from('.nas-title-line', {y: 38, opacity: 0, duration: .95, stagger: .11}, .1)
      .from('.nas-hero-enter', {y: 15, opacity: 0, duration: .75, stagger: .08}, .28)
      .from('.nas-glass-sheet', {opacity: 0, y: 35, duration: 1.4, stagger: .12}, .3)
      .from('.nas-art-label', {opacity: 0, y: 12, duration: .9}, .9);
    gsap.utils.toArray('.nas-reveal').forEach(element => {
      gsap.from(element, {y: 28, opacity: 0, duration: .9, ease: 'power2.out',
        scrollTrigger: {trigger: element, start: 'top 91%', once: true}});
    });
    if (!CSS.supports('animation-timeline: scroll()')) {
      gsap.to('.nas-scroll-progress', {scaleX: 1, ease: 'none', scrollTrigger: {trigger: document.body, start: 'top top', end: 'bottom bottom', scrub: true}});
    }
  });
  media.add('(min-width: 801px) and (prefers-reduced-motion: no-preference)', () => {
    gsap.to('.nas-glass-stack', {y: -70, rotationZ: -24, ease: 'none', scrollTrigger: {trigger: '.nas-hero', start: 'top top', end: 'bottom top', scrub: 1}});
    gsap.to('.nas-art-halo', {opacity: .2, ease: 'none', scrollTrigger: {trigger: '.nas-hero', start: 'top top', end: 'bottom top', scrub: true}});
    gsap.to('.nas-connection-wordmark', {xPercent: -3, ease: 'none', scrollTrigger: {trigger: '.nas-connection', start: 'top bottom', end: 'bottom top', scrub: 1.2}});
    const nodes = gsap.utils.toArray('.nas-story-node');
    const activate = index => nodes.forEach((node, i) => node.classList.toggle('is-active', i === index));
    gsap.utils.toArray('.nas-chapter').forEach((chapter, index) => {
      ScrollTrigger.create({trigger: chapter, start: 'top 65%', end: 'bottom 45%', onEnter: () => activate(index), onEnterBack: () => activate(index)});
      gsap.fromTo(chapter, {opacity: .35}, {opacity: 1, ease: 'none', scrollTrigger: {trigger: chapter, start: 'top 85%', end: 'top 45%', scrub: true}});
    });
    activate(0);
  });
  // No interception of wheel/touch input, forced snapping or artificial scrolling.
  document.fonts?.ready.then(() => ScrollTrigger.refresh());
})();
