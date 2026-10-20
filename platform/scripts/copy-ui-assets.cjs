"use strict";
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const destination = path.join(root, 'static', 'vendor', 'gsap');
fs.mkdirSync(destination, {recursive: true});
for (const filename of ['gsap.min.js', 'ScrollTrigger.min.js']) {
  fs.copyFileSync(path.join(root, 'node_modules', 'gsap', 'dist', filename), path.join(destination, filename));
}
fs.copyFileSync(path.join(root, 'node_modules', 'gsap', 'README.md'), path.join(destination, 'README.md'));
console.log('GSAP and ScrollTrigger copied to local static assets.');
