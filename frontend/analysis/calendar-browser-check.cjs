'use strict';
// Run with Playwright installed or its package path in PLAYWRIGHT_MODULE.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
(async()=>{
 const output=path.resolve(__dirname,'../../data/live-dashboard');
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  const errors=[],responses=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.url().startsWith('https://sslecal2.investing.com'))responses.push({url:r.url(),status:r.status()});});
  await page.goto('http://127.0.0.1:8011/',{waitUntil:'domcontentloaded'});
  await page.locator('#investing-calendar').scrollIntoViewIfNeeded();
  await page.waitForTimeout(8000);
  const report={responses,errors,viewports:[]};
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:900});
   await page.locator('.investing-attribution').scrollIntoViewIfNeeded();
   const attribution=await page.locator('.investing-attribution').evaluate(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {text:e.textContent,visible:r.height>0&&s.visibility==='visible'&&s.display!=='none',withinViewport:r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight,href:e.querySelector('a').href,outsideScrollWrapper:!e.closest('.calendar-viewport')};});
   if(!attribution.visible||!attribution.withinViewport||!attribution.outsideScrollWrapper)throw Error('Attribution hidden or clipped');
   report.viewports.push(await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,wrapperWidth:document.querySelector('.calendar-viewport').clientWidth,frameWidth:document.querySelector('iframe').clientWidth})));
   report.viewports.at(-1).attribution=attribution;
   await page.screenshot({path:path.join(output,`v4-attribution-${width}.png`)});
  }
  // The embedded provider DOM must not be read; inspect screenshots visually.
  report.frameInspection='Screenshot only; no iframe DOM access';
  report.youtube=await page.locator('#youtube-status').innerText();
  await fs.writeFile(path.join(output,'v4-attribution-browser.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
  if(errors.length||report.viewports.some(v=>v.documentWidth>v.width))throw Error('Browser regression');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
