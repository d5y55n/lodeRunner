'use strict';
globalThis.AnalysisChart=class {
 constructor(element,onSelect){
  const L=LightweightCharts;
  this.chart=L.createChart(element,{autoSize:true,height:420,layout:{background:{color:'#fffdf7'},textColor:'#69716a',attributionLogo:true},grid:{vertLines:{color:'#edf0e7'},horzLines:{color:'#edf0e7'}},localization:{locale:'ko-KR',timeFormatter:time=>KO.kst(time*1000)},timeScale:{timeVisible:true,secondsVisible:false,tickMarkFormatter:time=>KO.kst(time*1000).slice(5,16)},crosshair:{mode:L.CrosshairMode.Normal}});
  this.candles=this.chart.addSeries(L.CandlestickSeries,{upColor:'#346b55',downColor:'#c56b46',borderVisible:false,wickUpColor:'#346b55',wickDownColor:'#c56b46'});
  this.slope=this.chart.addSeries(L.LineSeries,{color:'#8a7b59',lineWidth:2,priceLineVisible:false,lastValueVisible:false});
  this.markers=L.createSeriesMarkers(this.candles,[]);this.lines=[];this.key=null;
  this.chart.subscribeClick(e=>{if(e.time && e.point && document.getElementById('chart-replay').checked)onSelect(e.time);});
  this.chart.subscribeCrosshairMove(e=>{const r=e.seriesData.get(this.candles);if(r)document.getElementById('hover').textContent=`${KO.kst(e.time*1000)} · ${KO.t('open')} ${r.open} / ${KO.t('highPrice')} ${r.high} / ${KO.t('lowPrice')} ${r.low} / ${KO.t('close')} ${r.close}`;});
 }
 render(d,tf,scale,side,overlays){
  const key=d.symbol+':'+tf+':'+d.mode,previous=this.chart.timeScale().getVisibleLogicalRange();
  const precision=Math.min(12,Math.max(2,6-Math.floor(Math.log10(Math.abs(d.price)||1))));
  this.candles.applyOptions({priceFormat:{type:'price',precision,minMove:10**-precision}});
  this.slope.applyOptions({priceFormat:{type:'price',precision,minMove:10**-precision}});
  this.candles.setData(d.charts[tf].map(r=>({time:r.open_time/1000,open:r.open,high:r.high,low:r.low,close:r.close})));
  this.lines.forEach(l=>this.candles.removePriceLine(l));this.lines=[];
  const line=(price,title,color)=>{if(price!=null)this.lines.push(this.candles.createPriceLine({price,title,color,lineWidth:1,lineStyle:2,axisLabelVisible:true}));};
  line(d.price,KO.t('analysisClose'),'#24302e');
  if(d.price_mode==='manual')line(d.analysis_price,'사용자 입력 가격','#8a7b59');
  if(overlays){const r=d.scoring.timeframes[tf];line(r.nearest.support?.price,KO.t('SUPPORT'),'#346b55');line(r.nearest.resistance?.price,KO.t('RESISTANCE'),'#b25b46');}
  const g=DashboardModel.geometry(d,tf,scale,side),times=new Set(d.charts[tf].map(r=>r.open_time/1000));
  this.slope.setData(overlays&&g?[g.source,g.end]:[]);
  this.markers.setMarkers(overlays&&g?[{time:g.source.time,position:side==='high'?'aboveBar':'belowBar',color:'#8a7b59',shape:'circle',text:KO.t(side)+' N'+d.config.swing_ns[scale]},{time:g.end.time,position:'inBar',color:'#24302e',shape:'circle',text:KO.t('analysisPoint')}].filter(m=>times.has(m.time)):[]);
  document.getElementById('chart').dataset.sourceId=g?.sourceId||'';
  document.getElementById('hover').textContent=KO.t('hoverHint');
  document.getElementById('geometry-note').textContent=g?`${KO.t('sourceId')}: ${g.sourceId} · ${KO.t('knownAt')}: ${KO.kst(g.knownAt)}${times.has(g.source.time)?'':' · '+KO.t('sourceOutside')}`:KO.t('NO_CONFIRMED_SWING');
  if(this.key!==key){this.chart.timeScale().fitContent();this.key=key;}else if(previous)this.chart.timeScale().setVisibleLogicalRange(previous);
 }
 ticker(price,visible){if(this.liveLine)this.candles.removePriceLine(this.liveLine);this.liveLine=visible&&price!=null?this.candles.createPriceLine({price,title:KO.t('livePrice'),color:'#69716a',lineWidth:1,lineStyle:3,axisLabelVisible:true}):null;}
 zoom(factor){const r=this.chart.timeScale().getVisibleLogicalRange();if(r){const m=(r.from+r.to)/2,h=(r.to-r.from)*factor/2;this.chart.timeScale().setVisibleLogicalRange({from:m-h,to:m+h});}}
 reset(){this.chart.timeScale().fitContent();}
 clear(){this.ticker(null,false);this.lines.forEach(l=>this.candles.removePriceLine(l));this.lines=[];this.markers.setMarkers([]);this.slope.setData([]);this.candles.setData([]);this.key=null;document.getElementById('chart').dataset.sourceId='';document.getElementById('hover').textContent='분석 데이터 준비 중';}
};
