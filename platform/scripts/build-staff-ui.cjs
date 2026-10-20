"use strict";
const path = require('node:path');
require('esbuild').buildSync({
  entryPoints: [path.resolve(__dirname, '../ui/staff.js')],
  outfile: path.resolve(__dirname, '../static/js/staff-ui.js'),
  bundle: true,
  minify: true,
  target: ['es2020'],
  legalComments: 'linked',
  banner: {js: '/* NAS staff interface · OSBI SelectMenu + Drawer. See vendor/osbi-ui/README.md. */'}
});
console.log('OSBI staff interface bundled locally.');
require('esbuild').buildSync({
  entryPoints: [path.resolve(__dirname, '../ui/risk-selects.js')],
  outfile: path.resolve(__dirname, '../static/js/risk-ui.js'),
  bundle: true,
  minify: true,
  target: ['es2020'],
  legalComments: 'linked',
  banner: {js: '/* NAS risk interface · OSBI SelectMenu. See vendor/osbi-ui/README.md. */'}
});
console.log('OSBI risk selects bundled locally.');
