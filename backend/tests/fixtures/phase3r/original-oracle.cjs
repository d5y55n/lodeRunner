// Execute only the unchanged original scoring function, with inert DOM outputs.
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[2], 'utf8');
const start = source.indexOf('function scoring(candlesReceived,interval,entry,ls)');
if (start < 0) throw new Error('Original scoring function not found');
let cursor = source.indexOf('{', start), depth = 1, end = cursor + 1;
while (depth && end < source.length) {
  if (source[end] === '{') depth++;
  if (source[end] === '}') depth--;
  end++;
}
if (depth) throw new Error('Unbalanced scoring function');
const sandbox = {document: {getElementById: () => ({innerText: ''})}};
vm.createContext(sandbox);
vm.runInContext(source.slice(start, end), sandbox, {timeout: 1000});
const cases = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = cases.map(c => sandbox.scoring(c.candles, c.timeframe, c.entry, c.direction));
process.stdout.write(JSON.stringify(results));
