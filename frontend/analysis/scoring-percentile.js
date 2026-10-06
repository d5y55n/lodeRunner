'use strict';
const ScoringPercentile=(()=>{
 function text(r){
  if(!r)return '과거 표본 부족';
  const direction={SUPPORT:'지지 우세',RESISTANCE:'저항 우세',BALANCED:'균형'}[r.direction];
  if(r.direction==='BALANCED')return direction;
  if(r.percentile==null)return direction+' · 과거 표본 부족';
  // Never round 99.999... up to an apparent endpoint or append a percent sign.
  const p=r.percentile<100&&r.percentile>=99.95?'<100.0':r.percentile.toFixed(1);
  const label={NORMAL:'보통',ELEVATED:'높음',STRONG:'강함',EXTREME:'극단적'}[r.label]||'';
  return direction+' · 과거 '+p+' 백분위'+(label?' · '+label:'');
 }
 function histogram(r){
  if(!r?.statistics?.signed?.count)return '<p>과거 표본 부족</p>';
  const {edges,counts}=r.histogram,max=Math.max(...counts,1),x=v=>40+(v+1)*260;
  const bars=counts.map((n,i)=>`<rect x="${x(edges[i])}" y="${140-n/max*110}" width="${(edges[i+1]-edges[i])*260}" height="${n/max*110}" fill="${edges[i]<0?'#3b6e91':'#244f43'}"><title>${edges[i].toFixed(2)} ~ ${edges[i+1].toFixed(2)}: ${n}</title></rect>`).join('');
  return `<svg viewBox="0 0 600 190" role="img" aria-label="종합 점수 과거 분포와 현재 점수 위치">${bars}<line x1="${x(r.observation_score)}" x2="${x(r.observation_score)}" y1="20" y2="145" stroke="#ba541d" stroke-width="2"/><text x="40" y="15">관측 횟수 (최대 ${max})</text><text x="40" y="165">-1</text><text x="300" y="165">0</text><text x="550" y="165">+1</text><text x="40" y="185">combinedNormalized · 주황선: 현재 ${r.observation_score.toFixed(4)}</text></svg>`;
 }
 return {text,histogram};
})();
if(typeof module!=='undefined')module.exports=ScoringPercentile;
