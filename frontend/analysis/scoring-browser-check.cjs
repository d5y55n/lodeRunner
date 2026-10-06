const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8011/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.querySelector('#scoring-percentile').textContent.includes('백분위'),null,{timeout:120000});
  const before=JSON.parse(await page.locator('#scoring-statistics').textContent());
  await page.screenshot({path:path.resolve(__dirname,'../../data/live-dashboard/scoring-percentile-card.png')});
  await page.locator('#price-mode').selectOption('manual');
  await page.locator('#manual-price').fill('70000');
  await page.locator('#manual-submit').click();
  await page.waitForFunction(()=>document.querySelector('#price-note').textContent.includes('사용자 입력'),null,{timeout:120000});
  const after=JSON.parse(await page.locator('#scoring-statistics').textContent());
  if(JSON.stringify(before.statistics)!==JSON.stringify(after.statistics))throw Error('Manual changed baseline');
  await page.locator('#manual-reset').click();
  await page.getByText('상세 분석 보기',{exact:true}).click();
  await page.locator('#scoring-histogram').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.resolve(__dirname,'../../data/live-dashboard/scoring-percentile-desktop.png')});
  await page.setViewportSize({width:390,height:900});
  await page.locator('#scoring-histogram').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.resolve(__dirname,'../../data/live-dashboard/scoring-percentile-mobile.png')});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  console.log(JSON.stringify({errors,overflow,current:before.observation_score,percentile:before.percentile,manualScore:after.observation_score,manualPercentile:after.percentile,baselineUnchanged:true}));
  if(errors.length||overflow)throw Error('Browser regression');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
