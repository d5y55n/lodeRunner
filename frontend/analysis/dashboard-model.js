'use strict';
globalThis.DashboardModel = {
 step:{'15m':900000,'1h':3600000,'4h':14400000,'1d':86400000},
 selected(d,tf,scale,side){return d?.converging?.[tf]?.[scale]?.[side]||null;},
 geometry(d,tf,scale,side){
  const r=this.selected(d,tf,scale,side);
  if(!r?.source_id || r.source_time==null || r.observation_time==null)return null;
  const end=d.charts[tf].find(c=>c.close_time+1===r.observation_time);
  return end?{sourceId:r.source_id,knownAt:r.known_at,source:{time:r.source_time/1000,value:r.source_price},end:{time:end.open_time/1000,value:end.close}}:null;
 },
 marketState(p,elapsed=0){return p?.connection==='CONNECTED' && p.market_age_seconds!=null && p.market_age_seconds+elapsed<15?'CONNECTED':'DISCONNECTED';},
 analysisFresh(p,elapsed=0){return !!p?.snapshot && this.marketState(p,elapsed)==='CONNECTED' && p.snapshot.freshness==='FRESH' && p.analysis_status==='READY' && p.snapshot.timestamp===Math.floor((p.server_timestamp+elapsed*1000)/this.step['15m'])*this.step['15m'];},
 replayTime(time,tf){return new Date(time*1000+this.step[tf]).toISOString();}
};
if(typeof module!=='undefined')module.exports=globalThis.DashboardModel;
