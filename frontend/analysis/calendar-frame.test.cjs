const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
test('YouTube polling failure does not access retired calendar elements',async()=>{
 const elements=new Map(['enable-notifications','youtube-status'].map(id=>[id,{textContent:''}]));
 let retry=false;
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'events.js'),'utf8'),{
  document:{getElementById:id=>{assert.ok(elements.has(id),id);return elements.get(id);}},
  fetch:async()=>{throw Error('offline');},AbortSignal,Intl,Date,
  setTimeout:()=>{retry=true;},setInterval:()=>{},
 });
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(elements.get('youtube-status').textContent,'라이브 확인 실패');
 assert.equal(retry,true);
});
test('calendar embeds the requested Investing configuration without parsing controls',()=>{
 const html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
 const src=html.match(/id="investing-calendar"[^>]*src="([^"]+)"/)[1].replaceAll('&amp;','&');
 const url=new URL(src);
 assert.equal(url.origin,'https://sslecal2.investing.com');
 for(const [key,value] of Object.entries({importance:'3',features:'datepicker,timezone',countries:'5',calType:'week',timeZone:'88',lang:'18',columns:'exc_flags,exc_currency,exc_importance,exc_actual,exc_forecast,exc_previous'}))assert.equal(url.searchParams.get(key),value);
 for(const id of ['calendar-status','next-events','today-events','calendar-time'])assert.ok(!html.includes(`id="${id}"`));
 assert.ok(html.includes('class="calendar-viewport"'));
 assert.match(html,/<\/iframe><\/div><div class="investing-attribution">Real Time Economic Calendar provided by <a href="https:\/\/www.investing.com\/" target="_blank" rel="noopener noreferrer">Investing.com<\/a>\.<\/div>/);
});
test('iframe error is contained and never triggers a backend request',()=>{
 let onError;const message={hidden:true};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'calendar-frame.js'),'utf8'),{document:{getElementById:id=>id==='investing-calendar'?{addEventListener:(event,fn)=>{assert.equal(event,'error');onError=fn;}}:message}});
 assert.equal(message.hidden,true);onError();assert.equal(message.hidden,false);
});
