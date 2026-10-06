'use strict';
// Display-only translations. API enums, configuration and numeric values stay intact.
globalThis.KO = (() => {
 const LABELS = {
  lastGoodData:'마지막 정상 분석 유지',
  livePrice:'실시간 가격', analysisClose:'분석 기준 종가', analysisPoint:'분석 지점', marketConnection:'시장 연결',marketUpdate:'가격 갱신',analysisUpdate:'분석 계산 시각',secondsAgo:'초 전',
  CONNECTED:'정상',CONNECTING:'연결 중',DISCONNECTED:'연결 끊김',STALE:'데이터 지연',HISTORY_INCOMPLETE:'전체 과거 이력 준비 중 또는 부족',UPDATING:'마감 봉 분석 중',
  returnLive:'현재로 돌아가기',sourceSelect:'기준점 선택',sourceOutside:'기준점은 표시 캔들 범위 밖입니다',chartReplay:'캔들 클릭으로 과거 탐색',previousSelection:'이전 선택 결과 · 새 분석 대기',
  historyTitle:'최근 분석 기록',historyNote:'15분봉 마감 시각별 기록 · 중기 N4의 고점 / 저점 백분위 · 시각을 누르면 과거 탐색',historyEmpty:'아직 저장된 분석 기록이 없습니다.',historyUnavailable:'분석 기록을 불러올 수 없습니다.',
  historyTime:'분석 시각',historyState:'구조 상태',debug:'개발자 진단 · 원본 값',versions:'계산 버전',diagnosticsLegacyOnly:'사후 진단은 기존 연구 재생 구간에서만 지원합니다.',
  SUPPORT:'지지', RESISTANCE:'저항', BALANCED:'균형', NORMAL:'보통', ELEVATED:'높음', STRETCHED:'과도', EXTREME:'극단적',
  UP:'상승', DOWN:'하락', UPWARD:'상승', DOWNWARD:'하락', UPWARD_STRETCH:'상승 과열', DOWNWARD_STRETCH:'하락 과열',
  HIGH:'고점', LOW:'저점', high:'고점', low:'저점', short:'단기', medium:'중기', long:'장기', FLAT:'변화 없음',
  NO_CONFIRMED_SWING:'확정된 스윙 없음', INSUFFICIENT_HISTORY:'과거 표본 부족', UNAVAILABLE:'사용 불가',
  REPLAY:'과거 데이터 재생', CLOSED_CANDLE_LIVE:'실시간 마감 봉', AVAILABLE:'사용 가능', MISSING:'데이터 없음',
  PENDING:'관측 대기', OBSERVED:'관측 완료', DIRECTION_CHANGED:'방향 변경', WAITING:'대기 중',
  LOADING:'불러오는 중', READY:'정상', ERROR:'오류', RESERVED:'보호된 데이터', REFRESH_REQUIRED:'새로고침 필요',
  EXPANDING:'확대 중', RELAXING:'완화 중', ACCELERATING:'가속 중', DECELERATING:'감속 중', RESET:'기준점 변경으로 초기화',
  SUPPORT_DOMINATED:'지지 우세', RESISTANCE_DOMINATED:'저항 우세',
  '0-30d':'최근 30일', '30-90d':'30~90일', '90-180d':'90~180일', '180-365d':'180일~1년', '365d+':'1년 이상',
  title:'BTC 지지·저항 · 수렴 분석', brand:'지지·저항과 움직임', instrument:'실시간 시장 관찰 · v2',
  eyebrow:'두 개의 분석 축 · 매매 신호 없음', hero:'현재 가격의 위치.', heroEm:'그곳까지 움직인 속도.',
  intro:'지지·저항의 위치와 움직임의 속도를 독립적으로 관찰합니다.', market:'BTCUSDT / 달러 기반 무기한 선물',
  waiting:'데이터 대기', closedOnly:'마감된 봉만 사용', mode:'데이터 모드', replay:'과거 탐색', live:'실시간',
  decisionTime:'분석 시각 / 한국시간(KST)', load:'분석 새로고침 ↗', loading:'원본 이력 · 인과적 분포를 불러오는 중…',
  previous:'이전 결과 표시 · 새 요청 실패', unavailable:'데이터 사용 불가', closedPrice:'15m 마감 가격', lastUpdate:'마지막 업데이트', dataStatus:'데이터 상태',
  where:'01 / 가격의 위치', scoringTitle:'지지·저항 분석', combinedScore:'종합 정규화 점수',
  scoringNote:'시간봉별 정규화 후 가중합니다. 원점수를 합산하지 않습니다.',
  howFast:'02 / 움직임의 속도', convergingTitle:'수렴 분석', timeframe:'시간봉',
  convergingNote:'고점·저점 기준점과 실제 방향별로 과거 분포를 구분합니다. 백분위는 반전 확률이 아닙니다.',
  observation:'03 / 시장 관찰', currentState:'현재 시장 상태', swingScale:'스윙 규모',
  separate:'두 분석 축을 합치지 않고 나란히 표시합니다.', configuration:'공식 · 설정 · 데이터 출처',
  stateNote:'움직임의 속도가 정상화되는 것과 가격 반등은 다릅니다. 자동 주문·레버리지·예측 신호 없음.',
  chartContext:'04 / 가격 흐름', overlays:'최근접 지지·저항 및 스윙', zoomIn:'확대', zoomOut:'축소', resetChart:'차트 초기화',
  chartAria:'BTC 캔들 차트. 휠로 확대하고 드래그하여 이동할 수 있습니다.', hoverHint:'휠: 확대 · 드래그: 이동 · 마우스: 시가·고가·저가·종가',
  chartNote:'주황: 지지 후보 · 파랑: 저항 후보 · 점선: 확정된 스윙 기준점. 후보 유형은 현재가 위·아래 위치를 보장하지 않습니다.',
  diagnosticsTitle:'사후 진단 / 미래 관측 분리', diagnosticsNote:'현재 판단에 사용하지 않는 별도 기록입니다. 진입 당시 분포와 같은 스윙 기준점을 고정해 이후 기울기 변화를 표시합니다. 아직 관측하지 못한 시점은 관측 대기로 표시합니다.',
  diagnosticsButton:'선택 시간봉·스윙 규모 기록 조회', diagnosticsLoading:'사후 관측 기록을 불러오는 중…',
  footer:'지지·저항 점수 = 위치 / 수렴 분석 = 움직임의 속도', footerNote:'계산 과정을 공개합니다. 수익 우위를 주장하지 않습니다.',
  scoringHelp:'현재 가격 주변에 과거 지지·저항 후보가 얼마나 분포되어 있는지 계산합니다. 최근에 생성된 후보일수록 더 높은 가중치를 받고, 각 시간봉의 점수는 후보 수 차이를 보정하기 위해 정규화됩니다.',
  convergingHelp:'최근 확정된 스윙 고점·저점에서 현재 가격까지의 시간 대비 움직임을 계산하고, 같은 조건의 과거 기울기 분포와 비교합니다. 백분위가 높을수록 과거보다 빠르고 가파른 움직임입니다.',
  noPrediction:'이는 가격이 특정 방향으로 움직일 것이라는 예측이 아니라 현재 움직임의 과도 정도를 나타냅니다.',
  stretchHelp:'시간 대비 가격 움직임의 기울기가 과거보다 비정상적으로 큰 상태',
  noStructure:'주변 지지·저항 후보 없음', legacyScore:'기존 점수', nearbyCounts:'주변 지지 / 저항 후보 수', mapCounts:'전체 지지 / 저항 후보 수',
  weightedSides:'가중 지지 / 저항', nearestDistances:'최근접 지지 / 저항 거리', nativeClose:'해당 시간봉 마감 시각',
  age:'생성 후 경과 기간', ageTitle:'기간별 가중 기여도', countSides:'지지 / 저항 후보 수', weightSides:'지지 / 저항 가중 기여도',
  ageNote:'후보 수는 전체 후보 기준이며, 기여도는 현재가 주변 후보만 반영합니다.',
  calculation:'상세 보기', scoreEquation:'시간봉 점수 × 시간봉 가중치 = 가중 기여도',
  origin:'기준점', percentile:'과거 백분위', ratio:'과도 배율', slope:'방향 포함 기울기', magnitude:'기울기 크기', perCandle:'% / 봉',
  velocity:'과도 변화 속도', acceleration:'과도 변화 가속도', sourcePrice:'기준 가격', sourceTime:'기준 시각', knownAt:'확정 시각',
  elapsed:'경과 봉 수', candleUnit:'봉', median:'과거 기울기 중앙값', samples:'과거 표본 수', asOf:'관측 시각', sourceId:'기준점 식별자',
  recentPercentiles:'최근 과거 백분위', quantiles:'과거 기울기 분위수', beforeCalculation:'계산 전', timesUnit:'배',
  currentPrice:'현재 가격', open:'시가', highPrice:'고가', lowPrice:'저가', close:'종가',
  resetHelp:'기준점 또는 방향 변경 시 초기화합니다. 같은 기준점의 연속된 유효 관측값이 없으면 계산 전으로 표시합니다.',
  NORMAL_HELP:'과거 일반 범위', ELEVATED_HELP:'평소보다 가파름', STRETCHED_HELP:'과거 대비 상당히 가파름', EXTREME_HELP:'과거에서도 드문 수준의 기울기'
 };
 const KEYS = {configuration:'계산 설정',hash:'설정 해시',warnings:'유의 사항',sources:'데이터 출처',
  scoring_version:'지지·저항 계산 버전',converging_version:'수렴 계산 버전',history_days:'과거 데이터 범위(일)',half_life_days:'반감기(일)',recency_floor:'최신성 가중치 하한',outer_multiplier:'바깥 구간 배율',widths:'시간봉별 근접 범위',tf_weights:'시간봉 가중치',balanced_band:'균형 표시 범위',swing_ns:'스윙 규모',converging_history_days:'수렴 과거 데이터 범위(일)',percentile_bands:'백분위 표시 경계',diagnostic_horizons:'사후 관측 간격(봉)',min_distribution_samples:'최소 과거 표본 수',chart_candles:'차트 표시 봉 수',replay_default:'기본 재생 시각',
  retrospective_only:'사후 진단 전용',baseline:'비교 분포 기준',events:'관측 기록',entry:'시작 관측값',future:'이후 관측값',horizon:'경과 봉 수',status:'상태',percentile:'과거 백분위',signed_slope:'방향 포함 기울기(원본)',slope_magnitude:'기울기 크기(원본)',observed_at:'관측 시각',sample_count:'과거 표본 수',direction:'방향',historical_median:'과거 기울기 중앙값(원본)',quantiles:'과거 분위수(원본)',stretch_ratio:'과도 배율',state:'상태',source_side:'기준점 종류',source_type:'기준점 종류',source_id:'기준점 식별자',swing_n:'스윙 확인 봉 수',actual_direction:'실제 방향',source_price:'기준 가격',source_time:'기준 시각',known_at:'확정 시각',elapsed_candles:'경과 봉 수',observation_time:'관측 기준 시각',timestamp:'시각',velocity:'과도 변화 속도',acceleration:'과도 변화 가속도',recent_percentiles:'최근 과거 백분위',derivative_basis:'속도·가속도 계산 기준',timeframe:'시간봉',short:'단기',medium:'중기',long:'장기',p25:'25백분위',p50:'50백분위',p75:'75백분위',p90:'90백분위',p95:'95백분위',p99:'99백분위'};
 const TEXT = {
  'Descriptive analysis, not probability or a trading rule.':'현재 상태를 설명하는 분석이며 확률이나 매매 규칙이 아닙니다.',
  'Empirical slope normalization is not proof of mean reversion.':'과거 기울기와의 비교는 평균 회귀의 증거가 아닙니다.',
  'Repeated observations from one source are serially dependent.':'동일한 기준점에서 반복 관측한 값들은 서로 독립적이지 않습니다.',
  'Scoring uses common 15m P; Converging uses each native closed price.':'지지·저항 점수는 공통 15m 마감 가격을, 수렴 분석은 각 시간봉의 마감 가격을 사용합니다.',
  'Inclusive proximity endpoints intentionally differ from strict legacy research endpoints.':'근접 범위의 경계값을 포함하므로 기존 연구의 엄격한 경계 처리와 다릅니다.',
  'Swing bootstrap: 2*max(N)+3 earlier candles. Until the first confirmed source, observations are absent, never backfilled.':'스윙 초기화에는 2×최대 N+3개의 이전 봉을 사용합니다. 첫 기준점 확정 전 관측값은 없으며 사후 보충하지 않습니다.',
  'frozen entry CDF; same source; sign changes explicit':'시작 시점의 누적분포와 동일 기준점을 고정하며 방향 변경을 별도로 표시합니다.',
  'same extreme; each past point uses its own past-only CDF; null before confirmation or sign change':'동일 기준점을 유지하며 각 시점의 과거 전용 분포를 사용합니다. 확정 전이나 방향 변경 시 계산 전으로 표시합니다.'
 };
 const t = key => LABELS[key] ?? key;
 const number = (v,n=3) => v == null ? '-' : Number(v).toFixed(n);
 const signed = (v,n=3) => v == null ? '-' : (v>0?'+':'')+Number(v).toFixed(n);
 const percent = (v,n=1) => v == null ? '-' : number(v,n)+'%';
 const kst = (value,detail=false) => {
  if(value==null)return '-'; const d=new Date(value);if(!Number.isFinite(d.getTime()))return '-';
  const local=new Date(d.getTime()+9*3600000).toISOString().slice(0,16).replace('T',' ');
  return local+' KST'+(detail?' ('+d.toISOString().slice(0,16).replace('T',' ')+' UTC)':'');
 };
 const inputUTC = value => new Date(value+'+09:00').toISOString();
 const message = (state,row) => {
  const where={SUPPORT:'지지 우세 구간',RESISTANCE:'저항 우세 구간',BALANCED:'균형 구간'}[state]||'상태 미확인 구간';
  if(row.state==='NO_CONFIRMED_SWING')return `현재 가격은 ${where}이며, 아직 확정된 스윙 기준점이 없습니다.`;
  if(row.state==='INSUFFICIENT_HISTORY')return `현재 가격은 ${where}이며, 기울기를 비교할 과거 표본이 부족합니다.`;
  if(row.actual_direction==='FLAT')return `현재 가격은 ${where}이며, 기준 가격 대비 변화가 없습니다.`;
  const degree={NORMAL:'과거 일반 범위에 있습니다',ELEVATED:'평소보다 가파릅니다',STRETCHED:'과거 대비 상당히 가파릅니다',EXTREME:'과거에서도 드물 만큼 극단적으로 가파릅니다'}[row.state]||'확인되지 않았습니다';
  return `현재 가격은 ${where}이며, ${t(row.actual_direction)} 기울기는 ${degree}.`;
 };
 const error = value => {
  const raw=String(value);
  if(raw.includes('HISTORY_INCOMPLETE'))return '전체 850일 과거 이력이 부족합니다. 운영 데이터는 수집된 범위에서만 탐색할 수 있습니다. 기간을 줄이거나 빈 봉을 보충하지 않았습니다.';
  if(raw.includes('2024'))return '2024년은 보호된 데이터입니다. 요청한 과거 범위가 2024년과 겹칩니다. 2023년 재생을 이용하거나 과거 범위를 명시적으로 설정해 주세요.';
  if(/Missing native history|Incomplete|Empty|coverage gap/.test(raw))return '요청한 범위의 과거 데이터가 부족합니다. 데이터를 임의로 보충하거나 기간을 줄이지 않았습니다.';
  if(/Gap|duplicate|unordered|Invalid OHLC|nonfinite/.test(raw))return '데이터 무결성 검사에서 오류가 확인되어 계산을 중단했습니다.';
  if(/Invalid time|isoformat|Timestamp|Live mode/.test(raw))return '분석 시각을 확인해 주세요. 재생 시각은 한국시간(KST)으로 입력합니다.';
  if(/Failed to fetch|fetch failed|NetworkError|Market data unavailable/.test(raw))return '데이터를 불러올 수 없습니다. 서버 연결과 데이터 상태를 확인한 뒤 다시 시도해 주세요.';
  return '요청 처리 중 오류가 발생했습니다. 입력값과 서버 상태를 확인해 주세요.';
 };
 const timeKeys=new Set(['source_time','known_at','timestamp','observation_time','observed_at','replay_default']);
 const tree = (value,key='') => {
  if(value==null)return '계산 전';if(timeKeys.has(key))return kst(value,true);
  if(Array.isArray(value))return value.map(v=>tree(v));
  if(typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k==='source_side'?'기준점 구분':KEYS[k]||k,tree(v,k)]));
  if(typeof value==='boolean')return value?'예':'아니요';
  if(typeof value==='string')return TEXT[value]||LABELS[value]||value;
  return value;
 };
 function init(){document.title=t('title');document.querySelectorAll('[data-i18n]').forEach(e=>e.textContent=t(e.dataset.i18n));document.querySelectorAll('[data-i18n-title]').forEach(e=>e.title=t(e.dataset.i18nTitle));document.querySelectorAll('[data-i18n-aria]').forEach(e=>e.setAttribute('aria-label',t(e.dataset.i18nAria)));}
 return {t,number,signed,percent,kst,inputUTC,message,error,tree,init};
})();
if(typeof module!=='undefined')module.exports=globalThis.KO;
