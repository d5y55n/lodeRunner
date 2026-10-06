// Static JavaScript compilation only. Does not open or emulate a browser.
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[2], 'utf8');
const scripts = [...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (scripts.length !== 1) throw new Error('Expected exactly one self-contained script');
new vm.Script(scripts[0][1]);
if (/<(?:script|link)[^>]+(?:src|href)=/i.test(source)) throw new Error('External dependency');
console.log('PASS: inline script syntax and offline dependency check (not visual browser QA).');
