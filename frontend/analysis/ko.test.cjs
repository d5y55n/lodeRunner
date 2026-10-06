'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ko = require('./ko.js');
test('asset URLs match content versions and translation loads before app', () => {
 const {createHash}=require('node:crypto');
 const html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
 for(const file of ['ko.js','v2.js','style.css','dashboard-model.js','chart.js','v3.css','symbol-model.js','events.js','calendar-frame.js','scoring-percentile.js','v4.css']){
  const hash=createHash('sha256').update(fs.readFileSync(path.join(__dirname,file))).digest('hex').slice(0,16);
  assert.ok(html.includes(`/assets/${file}?v=${hash}`),`${file}: update its content version after editing`);
  assert.ok(!html.includes(`/assets/${file}"`));
 }
 assert.ok(html.indexOf('/assets/ko.js?')<html.indexOf('/assets/v2.js?'));
});
test('display enums preserve technical identifiers', () => {
 for (const [input,output] of Object.entries({SUPPORT:'지지',RESISTANCE:'저항',BALANCED:'균형',EXTREME:'극단적',HIGH:'고점',LOW:'저점',UP:'상승',DOWN:'하락',short:'단기'})) assert.equal(ko.t(input),output);
 for (const value of ['BTCUSDT','15m','1h','4h','1d','N2','N4','N8','API']) assert.equal(ko.t(value),value);
});
test('formatting never changes numeric input', () => {
 assert.equal(ko.signed(.1255581673),'+0.126');
 assert.equal(ko.signed(-.1255581673),'-0.126');
 assert.equal(ko.percent(98.123456),'98.1%');
 for(const format of [ko.number,ko.signed,ko.percent]) assert.equal(format(null),'-');
});
test('KST rendering and input retain exact UTC instant', () => {
 assert.equal(ko.kst('2023-12-15T12:00:00Z'),'2023-12-15 21:00 KST');
 assert.equal(ko.inputUTC('2023-12-15T21:00'),'2023-12-15T12:00:00.000Z');
 assert.equal(ko.inputUTC('2023-12-15T21:00:30'),'2023-12-15T12:00:30.000Z');
 assert.equal(ko.kst('2022-12-31T18:00:00Z'),'2023-01-01 03:00 KST');
 assert.match(ko.kst('2023-12-15T12:00:00Z',true),/12:00 UTC/);
 assert.equal(ko.kst(null),'-');
});
test('translation produces a separate display tree without mutating API data', () => {
 const raw = {timestamp:1702641600000,config:{swing_ns:{short:2}},scoring:{overall:{state:'BALANCED',combined_normalized:.1255581673}},converging:{'15m':{short:{high:{source_type:'HIGH',source_side:'high',actual_direction:'DOWN',state:'NORMAL',percentile:38.6,velocity:null},low:{source_type:'LOW',actual_direction:'UP',state:'EXTREME',percentile:98.1}}}}};
 const before = JSON.stringify(raw);
 function freeze(v){if(v && typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}}
 freeze(raw);const translated=ko.tree(raw);
 assert.notEqual(translated,raw);
 assert.equal(Object.keys(ko.tree(raw.converging['15m'].short.high)).length,Object.keys(raw.converging['15m'].short.high).length);
 for(const tf of Object.values(raw.converging)) for(const scale of Object.values(tf)) for(const side of ['high','low']) ko.message(raw.scoring.overall.state,scale[side]);
 assert.equal(JSON.stringify(raw),before);
});
test('state descriptions are descriptive, handle missing data, and contain no trade predictions', () => {
 for(const state of ['NORMAL','ELEVATED','STRETCHED','EXTREME','NO_CONFIRMED_SWING','INSUFFICIENT_HISTORY']){
  const sentence=ko.message('SUPPORT',{state,actual_direction:'DOWN'});
  assert.match(sentence,/지지 우세/);assert.doesNotMatch(sentence,/매수 추천|매도 추천|반등 예상|하락 예상|회귀 확률/);
 }
 assert.match(ko.message('BALANCED',{state:'FLAT',actual_direction:'FLAT'}),/변화가 없습니다/);
});
test('all static translation keys resolve and form values stay technical', () => {
 const html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
 for(const match of html.matchAll(/data-i18n(?:-title|-aria)?="([^"]+)"/g)) assert.notEqual(ko.t(match[1]),match[1]);
 assert.match(html,/<html lang="ko">/);assert.match(html,/value="2023-12-15T21:00"/);
 for(const value of ['replay','live','short','medium','long']) assert.ok(html.includes(`value="${value}"`));
});
test('errors shown to users are Korean', () => {
 for(const input of ['2024 reserved','Missing native history','Gap','Invalid time','Failed to fetch','unexpected']) assert.match(ko.error(input),/[가-힣]/);
});
