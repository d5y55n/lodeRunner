const {test}=require('node:test');
const assert=require('node:assert/strict');
const m=require('./symbol-model.js');
const rows=[{symbol:'ETHUSDT',base_asset:'ETH'},{symbol:'BTCUSDT',base_asset:'BTC'},{symbol:'BTCUSDC',base_asset:'BTC'}];
test('symbol search is case insensitive and favorites sort first',()=>{
 assert.deepEqual(m.filter(rows,'btc',['BTCUSDT']).map(r=>r.symbol),['BTCUSDT','BTCUSDC']);
 assert.equal(m.filter(rows,' eth ')[0].symbol,'ETHUSDT');
 assert.equal(m.filter(rows,'unknown').length,0);
});
test('search bounds DOM result count',()=>{assert.equal(m.filter(Array.from({length:1000},(_,i)=>({symbol:'S'+i,base_asset:'S'})),'').length,40);});
test('recent list is bounded and deduplicated',()=>{assert.deepEqual(m.recent(['BTCUSDT','ETHUSDT'],'ETHUSDT'),['ETHUSDT','BTCUSDT']);assert.equal(m.recent(['1','2','3','4','5','6'],'7').length,6);});
test('small coin prices are not rounded to zero',()=>{assert.equal(m.money(.00000123),'$0.00000123');assert.equal(m.money(null),'-');});
