'use strict';
const $=id=>document.getElementById(id),t=KO.t,fmt=KO.number;
KO.init();
let data=null,tf='15m',requestId=0,livePayload=null,lastReceived=0,rendered=null,polling=false;
let symbol='BTCUSDT',symbolEpoch=0,symbols=[];
let baseSnapshot=null,manualRequest=0;
function stored(key){try{const v=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(v)?v.filter(x=>typeof x==='string').slice(0,30):[];}catch{return [];}}
let favorites=stored('dashboard-favorites'),recents=stored('dashboard-recents');
function persist(){try{localStorage.setItem('dashboard-favorites',JSON.stringify(favorites));localStorage.setItem('dashboard-recents',JSON.stringify(recents));}catch{/* Storage may be disabled. */}}
const path=(area,suffix)=>'/'+area+'/'+encodeURIComponent(symbol)+suffix;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const slope=v=>v==null?'-':fmt(v*100,4)+t('perCandle');
const money=SymbolModel.money;
const chart=new AnalysisChart($('chart'),time=>{
 $('mode').value='replay';syncMode();$('at').value=KO.kst(DashboardModel.replayTime(time,tf)).slice(0,16).replace(' ','T');loadReplay();
});
async function get(url){const r=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(120000)});const j=await r.json();if(!r.ok)throw new Error(typeof j.detail==='string'?j.detail:JSON.stringify(j.detail));return j;}
function syncMode(){requestId++;$('at').disabled=$('mode').value==='live';$('chart-replay').checked=false;rendered=null;$('error').hidden=true;chart.ticker(null,false);if(data){$('status').textContent=t('previousSelection');$('status').classList.add('stale');}}
function accept(snapshot){if(snapshot.symbol!==symbol)return;baseSnapshot=snapshot;rendered=snapshot.timestamp+':'+snapshot.config_hash;if($('price-mode').value==='manual'){applyManual();return;}data=snapshot;render();}
function priceMode(){manualRequest++;$('manual-submit').disabled=false;const manual=$('price-mode').value==='manual';for(const id of ['manual-price','manual-submit','manual-reset'])$(id).hidden=!manual;$('manual-error').textContent='';if(!manual){$('price-note').textContent='실제 마감 종가 기준';if(baseSnapshot){data=baseSnapshot;render();}}else{$('price-note').textContent='가격을 입력하고 적용하세요. 적용 전까지 기존 분석값입니다.';}}
async function applyManual(){
 const raw=$('manual-price').value,p=Number(raw),token=++manualRequest,epoch=symbolEpoch;
 if(!raw||!Number.isFinite(p)||p<=0){$('manual-error').textContent='0보다 큰 유한한 가격을 입력하세요.';return;}
 if(!baseSnapshot){$('manual-error').textContent='종목 분석 준비가 먼저 필요합니다.';return;}
 $('manual-submit').disabled=true;$('manual-error').textContent='입력 가격 분석 중';
 try{const result=await get(path('dashboard','/price?')+new URLSearchParams({price:raw,at:new Date(baseSnapshot.timestamp).toISOString()}));if(token!==manualRequest||epoch!==symbolEpoch||$('price-mode').value!=='manual')return;data=result;render();$('price-note').textContent='지지·저항 분석 가격: 사용자 입력 '+money(result.analysis_price)+' · 수렴 분석: 실제 시장 종가 기준';$('manual-error').textContent='';}
 catch(e){if(token===manualRequest&&epoch===symbolEpoch)$('manual-error').textContent='입력 가격 분석 실패 · '+KO.error(e.message);}
 finally{if(token===manualRequest)$('manual-submit').disabled=false;}
}
$('price-controls').onsubmit=e=>{e.preventDefault();applyManual();};$('price-mode').onchange=priceMode;$('manual-reset').onclick=()=>{$('price-mode').value='current';priceMode();};
async function loadReplay(){
 const token=++requestId;$('load').disabled=true;$('loading').textContent=t('loading');$('error').hidden=true;
 try{const result=await get(path('dashboard','/replay?')+new URLSearchParams({at:KO.inputUTC($('at').value)}));if(token!==requestId||$('mode').value!=='replay')return;accept(result);}
 catch(e){if(token===requestId){$('error').textContent=KO.error(e.message);$('error').hidden=false;$('status').textContent=t('previous');$('status').classList.add('stale');}}
 finally{if(token===requestId){$('load').disabled=false;$('loading').textContent='';}}
}
async function poll(){
 if(polling)return;polling=true;const epoch=symbolEpoch;
 try{const p=await get(path('market','/status'));if(epoch!==symbolEpoch)return;livePayload=p;lastReceived=performance.now();$('error').hidden=true;
  if($('mode').value==='live'){
   if(p.snapshot && rendered!==p.snapshot.timestamp+':'+p.snapshot.config_hash)accept(p.snapshot);
   $('loading').textContent=p.analysis_status==='READY'?'':symbol+' · '+(p.error&&p.analysis_status==='HISTORY_INCOMPLETE'?'데이터 부족':p.progress?.queued?'다른 종목 작업 대기 중':'분석 데이터 준비 중')+(p.progress?.percent!=null?' '+p.progress.percent+'% · 준비 완료: '+(p.progress.prepared_timeframes.join(', ')||'없음')+' · 남은 구간: '+p.progress.missing_timeframes.join(', '):'');
   if(!data){const insufficient=p.error&&p.analysis_status==='HISTORY_INCOMPLETE';$('sr-state').textContent=$('converging-state').textContent=insufficient?'데이터 부족':'분석 준비 중';$('state-text').textContent=insufficient?'설정된 전체 이력이 필요합니다. 기간을 줄이거나 다른 종목의 데이터를 사용하지 않습니다.':symbol+'의 4개 시간봉을 모두 준비한 뒤 분석합니다.';}
  }refreshStatus();
 }catch(e){if(epoch===symbolEpoch){if(livePayload)livePayload.connection='DISCONNECTED';$('error').hidden=false;$('error').textContent='연결 또는 처리 오류 · 잠시 후 자동 재시도합니다.';refreshStatus();}}
 finally{polling=false;setTimeout(poll,3000);}
}
function refreshStatus(){
 const elapsed=lastReceived?(performance.now()-lastReceived)/1000:Infinity,state=DashboardModel.marketState(livePayload,elapsed);
 $('connection').textContent=state==='CONNECTED'?'정상':!livePayload||state==='CONNECTING'?'연결 중':'연결 끊김';$('connection').classList.toggle('stale',state!=='CONNECTED');
 $('live-price').textContent=money(livePayload?.ticker?.price);$('live-price').classList.toggle('stale',state!=='CONNECTED');
 $('market-update').textContent=t('marketUpdate')+': '+(livePayload?.ticker?KO.kst(livePayload.ticker.timestamp)+' · '+Math.floor(livePayload.market_age_seconds+elapsed)+t('secondsAgo'):'-');
 if($('mode').value==='live'){
  const fresh=DashboardModel.analysisFresh(livePayload,elapsed);$('status').textContent=fresh?'마감 봉 분석 · 정상':livePayload?.error&&livePayload?.analysis_status==='HISTORY_INCOMPLETE'?'데이터 부족':data?'데이터 지연':'분석 준비 중';$('status').classList.toggle('stale',!fresh);
  chart.ticker(livePayload?.ticker?.price,state==='CONNECTED');
 }else chart.ticker(null,false);
 $('debug-data').textContent=JSON.stringify({connection:livePayload?.connection,error:livePayload?.error,source_timestamp:data?.timestamp,calculated_timestamp:data?.calculated_timestamp,native_closed_at:data?.native_closed_at,config_hash:data?.config_hash,scoring_version:data?.config?.scoring_version,converging_version:data?.config?.converging_version,selected:data?DashboardModel.selected(data,tf,$('scale').value,$('source').value):null},null,2);
}
function render(){
 $('price').textContent=money(data.price);$('clock').textContent=KO.kst(data.timestamp);$('clock').title=KO.kst(data.timestamp,true);$('analysis-update').textContent=t('analysisUpdate')+': '+KO.kst(data.calculated_timestamp);
 $('status').textContent=t(data.data_status);$('status').classList.toggle('stale',data.freshness==='STALE');
 $('versions').textContent=data.config.scoring_version+' / '+data.config.converging_version+' · '+data.config_hash;
 const sp=data.scoring_percentile;$('scoring-percentile').textContent=ScoringPercentile.text(sp);$('scoring-histogram').innerHTML=ScoringPercentile.histogram(sp);$('scoring-statistics').textContent=JSON.stringify(sp||{status:'INSUFFICIENT_HISTORY'},null,2);$('scoring-coverage').textContent=sp?'동일 방향 표본 '+sp.sample_count+'개 · 실제 분포 기간 '+KO.kst(sp.coverage_start)+' ~ '+KO.kst(sp.coverage_end)+' · 전체 이력이 있는 시점만 사용':'';
 const s=data.scoring.overall;$('score').textContent=KO.signed(s.combined_normalized);$('sr-state').textContent=s.combined_normalized>0?'지지 우세':s.combined_normalized<0?'저항 우세':'균형';$('needle').style.left=((s.combined_normalized+1)*50)+'%';
 $('score').className=s.combined_normalized>0?'positive':s.combined_normalized<0?'negative':'';
 $('score-summary').textContent=['1d','15m','1h','4h'].map(x=>x+' '+KO.signed(data.scoring.timeframes[x].normalized,2)).join(' · ');
 const expanded=new Set([...$('tf-rows').querySelectorAll('details[open]')].map(e=>e.dataset.tf));
 $('tf-rows').innerHTML=Object.values(data.scoring.timeframes).map(r=>`<details data-tf="${r.tf}" ${expanded.has(r.tf)?'open':''}><summary class="row" title="${t('scoreEquation')}"><b>${r.tf}</b><span>${KO.signed(r.normalized)} × ${fmt(r.weight,2)} = ${KO.signed(r.weighted_contribution)}</span></summary><div class="detail">${r.available?'':t('noStructure')+' · '}${t('legacyScore')}: ${KO.signed(r.legacy_score,1)}<br>${t('nearbyCounts')}: ${r.raw_support_count} / ${r.raw_resistance_count}<br>${t('mapCounts')}: ${r.map_support_count} / ${r.map_resistance_count}<br>${t('weightedSides')}: ${fmt(r.weighted_support)} / ${fmt(r.weighted_resistance)}<br>${t('nearestDistances')}: ${KO.percent(r.nearest.support?.distance_pct,3)} / ${KO.percent(r.nearest.resistance?.distance_pct,3)}<br>${t('SUPPORT')}: ${money(r.nearest.support?.price)} / ${t('RESISTANCE')}: ${money(r.nearest.resistance?.price)}<br>${t('nativeClose')}: ${KO.kst(r.source_close,true)}<table><caption>${t('ageTitle')}</caption><thead><tr><th>${t('age')}</th><th>${t('countSides')}</th><th>${t('weightSides')}</th></tr></thead><tbody>${r.age_buckets.map(b=>`<tr><td>${t(b.age)}</td><td>${b.support_count} / ${b.resistance_count}</td><td>${fmt(b.weighted_support,1)} / ${fmt(b.weighted_resistance,1)}</td></tr>`).join('')}</tbody></table><small>${t('ageNote')}</small></div></details>`).join('');
 $('config').textContent=JSON.stringify(KO.tree({configuration:data.config,hash:data.config_hash,warnings:data.warnings,sources:data.sources}),null,2);
 for(const [name,n] of Object.entries(data.config.swing_ns))$('scale').querySelector(`option[value="${name}"]`).textContent='N'+n;
 renderSelection();loadHistory();
}
function sideCard(r){return `<div class="side"><small>${t(r.source_type||r.source_side)} ${t('origin')} · ${t(r.actual_direction||'UNAVAILABLE')}</small><strong>${KO.percent(r.percentile)}<small>${t('percentile')}</small></strong><span class="badge" title="${t('stretchHelp')}">${t(r.state)}</span><p>${t('samples')}: ${r.sample_count??0}<br>${t('ratio')}: ${r.stretch_ratio==null?'-':fmt(r.stretch_ratio,2)+t('timesUnit')}<br>${t('slope')}: ${slope(r.signed_slope)}<br>${t('median')}: ${slope(r.historical_median)}<br>${t('elapsed')}: ${r.elapsed_candles??'-'}<br><span title="${t('resetHelp')}">${t('velocity')}: ${fmt(r.velocity,2)}<br>${t('acceleration')}: ${fmt(r.acceleration,2)}</span></p><details><summary>${t('calculation')}</summary><div class="detail">${t('sourcePrice')}: ${money(r.source_price)}<br>${t('sourceTime')}: ${KO.kst(r.source_time,true)}<br>${t('knownAt')}: ${KO.kst(r.known_at,true)}<br>${t('asOf')}: ${KO.kst(r.observation_time,true)}<br>${t('sourceId')}: ${esc(r.source_id||'-')}<br>${t('recentPercentiles')}: ${r.recent_percentiles?.map(x=>KO.percent(x,2)).join(' / ')||'-'}</div></details></div>`;}
function renderSelection(){
 if(!data)return;
 $('tf-tabs').innerHTML=['15m','1h','4h','1d'].map(frame=>`<button type="button" data-tf="${frame}" class="${frame===tf?'active':''}" aria-pressed="${frame===tf}">${frame}</button>`).join('');
 $('tf-tabs').querySelectorAll('button').forEach(b=>b.onclick=()=>{tf=b.dataset.tf;renderSelection();});
 const scale=$('scale').value,side=$('source').value,r=DashboardModel.selected(data,tf,scale,side);
 $('converging-value').textContent=KO.percent(r.percentile);
 $('converging-state').textContent=t(r.actual_direction||'UNAVAILABLE')+' · '+t(r.state);
 $('converging-summary').textContent=tf+' · N'+data.config.swing_ns[scale]+' · '+t(side)+' 기준 · '+fmt(r.stretch_ratio,2)+'배 · 백분위';
 $('stretch').innerHTML=`<div class="scale-title">${tf} · ${t(scale)} (N${data.config.swing_ns[scale]}) · ${t(side)}</div>${sideCard(r)}`;
 $('state-text').innerHTML=`<div class="state-line"><small>${tf} / ${t(scale)} / ${t(side)} ${t('origin')}</small>${esc(KO.message(data.scoring.overall.state,r))}</div>`;
 if(data.price_mode==='manual')$('state-text').textContent='입력 가격의 지지·저항: '+t(data.scoring.overall.state)+' · 수렴은 실제 시장 종가를 관찰합니다.';
 $('cross-tf').innerHTML=Object.entries(data.converging).map(([frame,row])=>`<div class="cross-row"><b>${frame}</b><span>${t(side)} ${KO.percent(row[scale][side].percentile)}</span></div>`).join('');
 $('chart-title').textContent=symbol+' · '+tf;$('chart').setAttribute('aria-label',symbol+' 캔들 차트');chart.render(data,tf,scale,side,$('overlays').checked);refreshStatus();
}
async function loadHistory(){
 const epoch=symbolEpoch;
 try{const {rows}=await get(path('analysis','/history?limit=12'));if(epoch!==symbolEpoch)return;$('history-body').innerHTML=rows.map(r=>`<tr><td><button type="button" data-time="${r.timestamp}">${KO.kst(r.timestamp)}</button></td><td>${KO.signed(r.scoring.overall.combined_normalized)}<br>${esc(ScoringPercentile.text(r.scoring_percentile))}</td><td>${KO.percent(r.converging['15m'].medium.high.percentile)} / ${KO.percent(r.converging['15m'].medium.low.percentile)}</td><td>${KO.percent(r.converging['1h'].medium.high.percentile)} / ${KO.percent(r.converging['1h'].medium.low.percentile)}</td><td>${t(r.scoring.overall.state)}</td></tr>`).join('');$('history-empty').hidden=rows.length>0;
  $('history-body').querySelectorAll('button').forEach(b=>b.onclick=()=>{$('mode').value='replay';syncMode();$('at').value=KO.kst(Number(b.dataset.time)).slice(0,16).replace(' ','T');loadReplay();});
 }catch(e){if(epoch===symbolEpoch){$('history-empty').hidden=false;$('history-empty').textContent=t('historyUnavailable');}}
}
$('controls').addEventListener('submit',e=>{e.preventDefault();if($('mode').value==='replay')loadReplay();else{rendered=null;if(livePayload?.snapshot)accept(livePayload.snapshot);refreshStatus();}});
$('mode').onchange=()=>{syncMode();$('load').disabled=false;if($('mode').value==='replay')loadReplay();else{if(livePayload?.snapshot)accept(livePayload.snapshot);refreshStatus();}};
$('return-live').onclick=()=>{$('mode').value='live';$('mode').onchange();chart.reset();};
$('scale').onchange=renderSelection;$('source').onchange=renderSelection;$('overlays').onchange=renderSelection;
$('zoom-in').onclick=()=>chart.zoom(.75);$('zoom-out').onclick=()=>chart.zoom(1.3);$('reset').onclick=()=>chart.reset();
$('diagnostics').onclick=()=>{$('diagnostic-data').textContent=data?JSON.stringify(DashboardModel.selected(data,tf,$('scale').value,$('source').value),null,2):'데이터 부족';};
function shortcuts(){
 $('favorite').textContent=favorites.includes(symbol)?'★':'☆';$('favorite').setAttribute('aria-pressed',String(favorites.includes(symbol)));
 $('symbol-shortcuts').innerHTML=[...favorites.filter(s=>symbols.some(r=>r.symbol===s)).map(s=>`<button data-symbol="${esc(s)}">★ ${esc(s)}</button>`),'<span>최근 본 코인</span>',...recents.filter(s=>!favorites.includes(s)&&symbols.some(r=>r.symbol===s)).map(s=>`<button data-symbol="${esc(s)}">${esc(s)}</button>`)].join('');
 $('symbol-shortcuts').querySelectorAll('button').forEach(b=>b.onclick=()=>selectSymbol(b.dataset.symbol));
}
function searchSymbols(){
 const rows=SymbolModel.filter(symbols,$('symbol-search').value,favorites);
 $('symbol-results').hidden=false;$('symbol-results').innerHTML=rows.length?rows.map(r=>`<button type="button" data-symbol="${esc(r.symbol)}">${favorites.includes(r.symbol)?'★ ':''}${esc(r.symbol)}${r.history_readiness==='HISTORY_INCOMPLETE'?' · 데이터 부족':''}</button>`).join(''):'검색 결과 없음';
 $('symbol-results').querySelectorAll('button').forEach(b=>b.onclick=()=>selectSymbol(b.dataset.symbol));
}
function selectSymbol(next){
 if(!symbols.some(r=>r.symbol===next))return;
 symbol=next;symbolEpoch++;requestId++;data=null;livePayload=null;rendered=null;lastReceived=0;chart.clear();
 baseSnapshot=null;manualRequest++;$('price-mode').value='current';$('manual-price').value='';$('manual-submit').disabled=false;priceMode();
 $('chart').setAttribute('aria-label',next+' 캔들 차트');$('needle').style.left='50%';$('score').className='';
 for(const id of ['score','converging-value','price','clock','live-price'])$(id).textContent='-';
 for(const id of ['scoring-percentile','scoring-histogram','scoring-coverage','scoring-statistics','score-summary','converging-summary','tf-rows','stretch','cross-tf','history-body','config','versions','diagnostic-data','geometry-note','analysis-update'])$(id).textContent='';
 $('sr-state').textContent=$('converging-state').textContent='분석 준비 중';$('state-text').textContent=next+' 분석 데이터 준비 중';$('chart-title').textContent=next+' · '+tf;$('history-empty').hidden=false;
 $('selected-symbol').textContent=next;$('symbol-search').value='';$('symbol-results').hidden=true;$('load').disabled=false;$('mode').value='live';syncMode();$('loading').textContent=next+' 분석 데이터 준비 중';recents=SymbolModel.recent(recents,next);persist();shortcuts();refreshStatus();loadHistory();
}
$('symbol-search').oninput=searchSymbols;$('symbol-search').onfocus=searchSymbols;
$('symbol-search').onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();$('symbol-results').querySelector('button')?.focus();}if(e.key==='Enter'){e.preventDefault();$('symbol-results').querySelector('button')?.click();}if(e.key==='Escape')$('symbol-results').hidden=true;};
$('symbol-results').onkeydown=e=>{const buttons=[...$('symbol-results').querySelectorAll('button')],i=buttons.indexOf(document.activeElement);if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();buttons[(i+(e.key==='ArrowDown'?1:buttons.length-1))%buttons.length]?.focus();}if(e.key==='Escape'){$('symbol-results').hidden=true;$('symbol-search').focus();}};
document.addEventListener('click',e=>{if(!e.target.closest('.symbol-picker'))$('symbol-results').hidden=true;});
$('favorite').onclick=()=>{favorites=favorites.includes(symbol)?favorites.filter(s=>s!==symbol):[...favorites,symbol].slice(-30);persist();shortcuts();};
async function initSymbols(){try{symbols=(await get('/market/symbols')).symbols;recents=SymbolModel.recent(recents,symbol);persist();shortcuts();}catch{$('error').hidden=false;$('error').textContent='종목 목록을 불러오지 못했습니다. 자동 재시도합니다.';setTimeout(initSymbols,15000);}}
syncMode();initSymbols();poll();loadHistory();setInterval(refreshStatus,1000);
