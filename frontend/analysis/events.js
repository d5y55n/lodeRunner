'use strict';
(()=>{
 const el=id=>document.getElementById(id),safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const when=s=>s?new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(s*1000))+' KST':'-';
 let latest=null,enabled=false,failed=false;try{enabled=localStorage.getItem('events-notifications')==='on';}catch{}
 function note(n){return 'EZPZ 라이브 시작 · '+n.payload.title;}
 function render(){if(!latest)return;const y={...latest.youtube},now=Date.now()/1000;y.stale=y.stale||now-(y.valid_at||0)>2*y.poll_seconds;
  el('youtube-status').textContent=({LIVE:'EZPZ 라이브 중',OFFLINE:'오프라인',UPCOMING:'라이브 예정',ERROR:'라이브 확인 실패',UNCONFIGURED:'YouTube 연동 설정 필요',LOADING:'확인 중'})[y.state]||'확인 실패';
  if(y.stale&&y.state!=='UNCONFIGURED')el('youtube-status').textContent+=' · 데이터 지연';
  el('youtube-live').innerHTML=y.video_id&&/^[\w-]{11}$/.test(y.video_id)?`${y.state==='ERROR'?'마지막 확인 정보 · ':''}<a target="_blank" rel="noopener" href="https://www.youtube.com/watch?v=${safe(y.video_id)}">${safe(y.title)}</a>${y.scheduled_start?'<p>예정: '+safe(when(Date.parse(y.scheduled_start)/1000))+'</p>':''}`:'';
  if(y.video_id&&/^https:\/\/i\.ytimg\.com\//.test(y.thumbnail||''))el('youtube-live').innerHTML+=`<img src="${safe(y.thumbnail)}" alt="EZPZ 방송 미리보기" loading="lazy">`;
  el('youtube-time').textContent='확인: '+when(y.checked_at)+(y.actual_start?' · 시작: '+when(Date.parse(y.actual_start)/1000):'');el('local-alerts').innerHTML=latest.alerts.filter(n=>n.kind==='YOUTUBE_LIVE_STARTED').map(n=>'<p>'+safe(when(n.created))+' · '+safe(note(n))+'</p>').join('')||'아직 알림이 없습니다.';
  if(failed){el('youtube-status').textContent='라이브 확인 실패 · 이전 정보일 수 있습니다.';}
 }
 el('enable-notifications').onclick=async()=>{
  if(enabled){enabled=false;try{localStorage.setItem('events-notifications','off');}catch{}}
  else if('Notification' in window){let asked=false;try{asked=localStorage.getItem('events-permission-asked')==='yes';}catch{}if(Notification.permission==='default'&&!asked){try{localStorage.setItem('events-permission-asked','yes');}catch{}await Notification.requestPermission();}enabled=Notification.permission==='granted';try{localStorage.setItem('events-notifications',enabled?'on':'off');}catch{}}
  el('enable-notifications').textContent=enabled?'브라우저 알림 끄기':'브라우저 알림 켜기';el('notification-status').textContent=enabled?'브라우저 알림 사용 중':'앱 내 알림만 사용합니다. 권한은 브라우저 설정에서 변경할 수 있습니다.';
 };
 async function poll(){try{const r=await fetch('/events/status',{cache:'no-store',signal:AbortSignal.timeout(25000)});if(!r.ok)throw Error();latest=await r.json();failed=false;render();if(enabled&&'Notification' in window&&Notification.permission==='granted'){const r=await fetch('/events/notifications/claim',{method:'POST'});if(r.ok)for(const n of (await r.json()).notifications)new Notification(note(n),{tag:n.id});}}
 catch{failed=true;el('youtube-status').textContent='라이브 확인 실패';}
 finally{setTimeout(poll,15000);}}
 el('enable-notifications').textContent=enabled?'브라우저 알림 끄기':'브라우저 알림 켜기';poll();setInterval(render,30000);
})();
