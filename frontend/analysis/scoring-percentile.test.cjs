const {test}=require('node:test');
const assert=require('node:assert/strict');
const model=require('./scoring-percentile.js');
test('directional display, insufficient/legacy and no misleading rounding',()=>{
 assert.equal(model.text(null),'과거 표본 부족');
 assert.equal(model.text({direction:'BALANCED',percentile:null}),'균형');
 assert.match(model.text({direction:'SUPPORT',percentile:null}),/과거 표본 부족/);
 assert.match(model.text({direction:'RESISTANCE',percentile:99.999,label:'EXTREME'}),/저항 우세 · 과거 <100.0 백분위 · 극단적/);
 assert.ok(!model.text({direction:'SUPPORT',percentile:100}).includes('%'));
});
test('distribution chart keeps signed axis and current marker',()=>{
 const html=model.histogram({statistics:{signed:{count:2}},histogram:{edges:[-1,0,1],counts:[1,1]},observation_score:-.17});
 assert.match(html,/현재 -0.1700/);assert.match(html,/>-1</);assert.match(html,/>\+1</);
 assert.match(model.histogram(null),/과거 표본 부족/);
});
