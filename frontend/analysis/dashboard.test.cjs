const {test}=require('node:test');
const assert=require('node:assert/strict');
const m=require('./dashboard-model.js');
test('freshness expires without a response and on the next native decision',()=>{
 const p={connection:'CONNECTED',market_age_seconds:1,server_timestamp:900001,analysis_status:'READY',snapshot:{timestamp:900000,freshness:'FRESH'}};
 assert.equal(m.analysisFresh(p),true);assert.equal(m.analysisFresh(p,20),false);
 assert.equal(m.analysisFresh({...p,server_timestamp:1800000}),false);
 assert.equal(m.analysisFresh({...p,connection:'DISCONNECTED'}),false);
});
test('selected timeframe scale and source drive exact API geometry',()=>{
 const d={converging:{'15m':{short:{high:{source_id:'15m:high:2:0',source_time:0,source_price:110,known_at:2700000,observation_time:3600000},low:{source_id:'15m:low:2:900000',source_time:900000,source_price:90,known_at:3600000,observation_time:3600000}}}},charts:{'15m':[{open_time:2700000,close_time:3599999,close:100}]}};
 assert.equal(m.geometry(d,'15m','short','high').sourceId,'15m:high:2:0');
 assert.equal(m.geometry(d,'15m','short','low').source.value,90);
 assert.deepEqual(m.geometry(d,'15m','short','high').end,{time:2700,value:100});
 assert.equal(m.geometry(d,'15m','medium','high'),null);
});
test('clicked candle navigates to close, not its open or a future native bar',()=>{
 for(const tf of Object.keys(m.step))assert.equal(Date.parse(m.replayTime(0,tf)),m.step[tf]);
});
