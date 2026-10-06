# Phase 2.5 완료 보고서

프로젝트: C:/Users/82108/Desktop/lodeRunner

## 완료 범위

공식 Binance BTCUSDT USD-M Futures aggregate-trade 수집, 무결성 보고,
실제 체결 기반 Volume-at-Price, Detector D 실행, A/B/C 거래량 부착,
검사용 CSV/JSON 및 자체 포함 오프라인 HTML을 구현했습니다.
Phase 2의 탐지 규칙은 유지했습니다. 파라미터 순위/최적화, 매매 신호,
Phase 3, 예약된 최종 테스트 평가를 수행하지 않았습니다.

## 수집 방법과 범위

공식 일별 아카이브:
https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2024-01-01.zip

같은 경로의 .CHECKSUM으로 SHA-256을 확인하고 ZIP CRC도 검증했습니다.
원본 ZIP, 공식 체크섬, 무결성 보고서는 별도로 보존됩니다.
REST 보조 수집도 구현했지만 실제 실행은 아카이브를 사용했습니다.
REST는 모의 응답 테스트로 검증했으며 실제 네트워크 실행은 하지 않았습니다.

- 기간: 2024-01-01 00:00 UTC 이상 ~ 2024-01-02 00:00 UTC 미만.
- 집계 체결 수: **761,222**.
- aggregate ID: 1965151407 ~ 1965912628.
- 원본 ZIP 크기: 10,064,410 bytes.
- SHA-256: ed5c4326e6ccdec61504bc7d9bed594c4fe0a88f845c7a6ec5b934c97c01cb1c.
- 관측 첫 체결: 1704067200038 ms, 마지막: 1704153599978 ms.
- 요청 경계와 관측 경계 거리: 시작 38ms / 종료 22ms.
- 최대 체결 간 시간 차이: 6,959ms.

기존 연구 구간의 첫 UTC 하루를 결과 확인 전에 고정했습니다.
예약 최종 테스트 시작 시각인 2024-01-06 14:00 UTC의 데이터는
탐지기, 거래량 특징 또는 결과 측정에 사용하지 않았습니다.

## 무결성 결과

상태: **PASS_WITH_WARNINGS**.

| 검사 | 결과 |
| --- | --- |
| 공식 SHA-256 / ZIP CRC | 통과 |
| 잘못된 가격·수량·시각 등 레코드 | 0 |
| 중복 aggregate ID | 0 |
| 중복 레코드 | 0 |
| 시간/ID 역순 | 0 |
| aggregate ID 불연속 | 0 |
| constituent first/last trade ID 불연속 | **28건 경고** |

이 28건은 기록에서 지우거나 채우지 않았습니다.
집계 ID의 연속성과 원본 파일 일치는 확인되지만, 개별 원체결까지
완전하다고 단정하지 않습니다. 원인 확인은 남아 있습니다.

별도 진단으로 실제 집계 수량과 기존 시간봉 거래량을 비교했을 때
시간별 최대 절대 차이는 **1.564 BTC**였습니다. 일부 인접 시간대의
차이는 서로 상쇄되지만 원인은 확정하지 않았습니다.
run-report.json에 양쪽 원값과 차이를 모두 저장했습니다.
캔들 거래량은 진단 비교에만 사용했으며 VAP나 특징을 대체하지 않았습니다.

## 실행 설정과 실제 결과

모든 가격대 bin은 0 기준 [lower,upper), 관측 창은 1시간입니다.
D의 기존 집중도 규칙: bin 수량 / 점유 bin 평균 수량 >= 1.5.
bin 폭은 50 USDT와 100 USDT를 그대로 병렬 기록했습니다.

| 탐지기 | 설정 | 후보 | 실제 거래량 부착 방문 |
| --- | --- | --- | --- |
| A | 원본 반전 캔들 가격 선택 | 지지 6 / 저항 6 | 17 |
| B | 좌우 비교 폭 1 | 지지 4 / 저항 4 | 13 |
| C | 이후 종가 반전 0.3% | 지지 14 / 저항 6 | 26 |
| D | 50 USDT bin, 집중도 1.5 | 중립 44 | 두 D 설정 합계 121 |
| D | 100 USDT bin, 집중도 1.5 | 중립 19 | 위 합계에 포함 |

- VAP 레코드: 두 bin 설정 합계 232개.
- A/B/C 생성 시점 특징: 40개 후보 모두 관측/기준 창 확보.
- D 초기 후보 4개는 이전 기준 창 부족으로 MISSING_TRADE_COVERAGE.
- 전체 방문 177개, 두 번 이상 방문한 구간 49개.
- 방문 특징 21개는 기준 수량 0으로 relative ratio를 null 처리.
- 향후 결과 행 354개는 의사결정 특징과 별도 파일에 저장.

연구 구간 폭은 기준 가격의 +/-0.2%, 이탈 규칙은 종가 경계 이탈입니다.
거래량 특징은 [T-1h,T), 기준은 [T-2h,T-1h)로 고정했습니다.
공격적 매수/매도, 델타, 총 수량과 기준 대비 비율을 저장합니다.
T와 같거나 이후인 체결은 포함하지 않습니다.
가상 LONG/SHORT 결과는 TP=SL=0.3%, 이후 4개 시간봉으로 관측했습니다.
어느 설정도 최적으로 선언하지 않았습니다.

## 검사 샘플과 시각화

샘플 규칙:
known_at, candidate ID 순으로 각 설정·종류의 첫 3개,
D 각 설정의 첫 6개를 선택합니다. 이어 각 탐지기의 이른 반복방문
구간 2개와 이른 교차 탐지기 중첩쌍 3개를 포함합니다.
미래 TP/SL 결과는 선택 함수의 입력이 아닙니다.
반복방문 기준은 사후 검사 목적임을 명시했습니다.

최종 샘플: A/B/C 각각 지지 3개·저항 3개 + D 중립 12개 = 30개 구간.
전체 후보도 함께 저장되므로 표본 이외의 반응을 확인할 수 있습니다.

sanity.html은 외부 서버·CDN·폰트 없이 동작하는 오프라인 문서입니다.
캔들, A/B/C/D 토글, source와 known_at 표식, 이후 방문,
시점 슬라이더 및 후보별 원자료를 표시합니다.
가격 축도 현재 슬라이더 시점까지의 캔들/알려진 선택 구간으로 계산합니다.
미래 결과와 완료된 방문의 사후 통계는 HTML에 내장하지 않았습니다.

브라우저 도구의 로컬 파일 URL 보안 정책으로 직접 화면을 열 수 없었습니다.
우회하지 않았으며 JavaScript 정적 구문 검사와 외부 의존성 부재 검사는 통과했습니다.
브라우저 렌더링/스크린샷 기반 검수는 미확인입니다.

## 관찰된 주의점

- 원체결 ID 경계 28건과 시간별 거래량 차이의 원인은 아직 확인되지 않았습니다.
- C는 이 구간에서 지지가 저항보다 많고(14 대 6), 독립 극값 재설정으로
  가까운 후보를 반복 생성할 수 있습니다. 규칙을 임의로 변경하지 않았습니다.
- D의 실제 50/100 USDT bin과 +/-0.2% 연구 구간은 다른 범위입니다.
  약 42,000 USDT에서 연구 구간 전체 폭은 약 168 USDT라 원 bin보다 넓을 수 있습니다.
- 전체 후보 사이에 탐지기가 다른 중첩쌍이 807개입니다.
  이를 서로 독립적인 확인 근거로 세지 않습니다.
- 첫 기준 창이 부족한 값과 기준 수량 0인 비율은 누락으로 드러냅니다.
- 날짜 끝의 불완전 관측 결과는 censored로 보존합니다.
- 같은 크기의 LONG/SHORT TP/SL에서 대칭적인 결과 수가 나오는 것은
  수익성이나 예측력의 증거가 아닙니다.

## 테스트와 재현성

기존 87개 + 신규 31개 = **전체 118 passed**.
기존 FastAPI/Starlette 폐기 예정 경고 1개가 있으며 실패는 없습니다.

검증 항목:
파싱/원체결 ID, 잘못된 값, 중복/순서/시각 단위, 아카이브 체크섬,
실패 보고서, REST 페이지 처리, bin 경계, 매수/매도 방향/델타,
인덱스 전후 동일 계산, 미래 체결 변조에도 과거 특징 불변,
기준 창 인과성, 실제 데이터 계약의 D, 내보내기 재현성 및
미래 결과 분리, 최종 구간 거부, 결정적 샘플링.

실제 데이터로 계산을 두 번 수행하고 CSV/JSON/HTML을 다시 기록하여
내용 및 파일 SHA-256이 모두 일치하는지 확인했습니다.
export-manifest.json에 각 파일 해시를 기록했습니다.

## 변경 파일

추가:
- backend/app/market/aggregate_trades.py
- backend/app/research/sanity_export.py
- backend/app/research/phase25.py
- backend/app/research/sanity_template.html
- backend/tests/test_aggregate_trades.py
- backend/tests/test_phase25_volume.py
- backend/tests/test_sanity_export.py
- backend/tests/check_sanity_script.cjs
- docs/research/PHASE25.md
- docs/research/PHASE25_COMPLETION.md

수정:
- backend/app/research/volume.py: 선택적 원체결 ID와 검증된 시간 인덱스.
- PROJECT_SPEC.md: Phase 2.5 범위와 중단 경계.
- README.md: 수집/재실행/검사 방법.

## 저장 위치와 실행

실제 프로젝트 산출물:
C:/Users/82108/Desktop/lodeRunner/data/research/phase25/

원본:
C:/Users/82108/Desktop/lodeRunner/data/raw/binance/aggTrades/

정규화 데이터와 무결성 manifest:
C:/Users/82108/Desktop/lodeRunner/data/processed/aggTrades/

backend 폴더에서:
```powershell
.venv/Scripts/python.exe -m app.market.aggregate_trades --start 2024-01-01 --end 2024-01-02
.venv/Scripts/python.exe -m app.research.phase25 --replay
.venv/Scripts/python.exe -m pytest
```

검사용 묶음의 decision_features는 당시 정보,
interactions_retrospective는 방문 완료 후 사실,
outcomes_future는 이후 결과입니다. event_id로 명시적으로 연결할 수 있습니다.

공식 출처: [Binance public-data format and checksum documentation](https://github.com/binance/binance-public-data).

