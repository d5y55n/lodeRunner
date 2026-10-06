# Phase 2 완료 보고서

작업 대상: C:/Users/82108/Desktop/lodeRunner
완료일: 2026-09-27

## 결과

Phase 1을 유지하면서 중립적인 S/R 후보 연구 엔진을 구현했습니다.
후보 탐지, 구간 생성, 방문 추적, 미래 결과 측정, 대조군 비교를 분리했습니다.
임의 점수, 최적 파라미터 선택, ML, 매매 신호, 레버리지, 주문 기능은 추가하지 않았습니다.
Phase 3으로 진행하지 않았습니다.

## 추가 및 변경 파일

추가된 연구 모듈 (모두 backend/app/research/):
- __init__.py, models.py: 데이터 계약, 인과적 시각, 식별자
- data.py: 기존 Phase 1 Candle 모델 연결, 누락 캔들 거부
- detectors.py: 공통 인터페이스 및 A/B/C
- zones.py: 고정/원본 구간 폭, 적응형 확장 지점
- interactions.py: 방문 상태 및 이탈 규칙
- volume.py: 체결 계약/집계, D, 구간 거래량 특징
- outcomes.py: TP/SL 순서, MFE/MAE, 관측 미완료 처리
- config.py: 실험 설정 및 시간순 기간 분할
- runner.py: 독립 실험 실행, 대조군, 기술통계 비교
- smoke.py: BTCUSDT 다운로드/재실행 및 인과성 확인

추가된 테스트 (모두 backend/tests/):
- test_research_detectors.py
- test_research_interactions.py
- test_research_outcomes.py
- test_research_volume.py
- test_research_runner.py

문서:
- PROJECT_SPEC.md 수정: 기존 pivot 중심 Phase 2/3 설계를 연구용 A/B/C/D 계약으로 교체
- README.md 수정: 실행, 전체 테스트, 저장 데이터 재실행 방법
- docs/research/PHASE2.md 추가: 정확한 계산 의미와 데이터 요구사항
- docs/research/PHASE2_COMPLETION.md 추가: 이 완료 보고서

생성 데이터:
- data/research/phase2-smoke/BTCUSDT_1h_2024-01-01_2024-01-08.csv
- data/research/phase2-smoke/experiments.json
- data/research/phase2-smoke/summary.json

## 알고리즘과 공개 파라미터

| 항목 | 구현 |
| --- | --- |
| A | 양봉 다음 음봉: 두 고가 중 낮은 값이 저항. 음봉 다음 양봉: 두 저가 중 높은 값이 지지. 동률은 앞 캔들, 도지는 제외. 두 번째 캔들 마감 후 확정. |
| B | 좌우 N개 대비 엄격한 고점/저점. 동률 제외. 오른쪽 N개가 모두 마감된 시각에 확정. N을 독립 실험. |
| C | 고점/저점을 각각 추적하고, 이후 캔들 종가가 설정 비율만큼 반전하면 확정. 새 극값을 만든 당일 캔들에서는 확정하지 않음. 확인 후 해당 트래커를 확인 캔들로 재설정. |
| D | 실제 체결을 가격 bin 및 완료된 시간 창에 집계. 점유 bin 평균 거래량 대비 설정 배수 이상인 bin을 중립 후보로 생성. |
| 구간 폭 | ±0.05/0.10/0.20/0.30/0.50%, 별도 원본 15m=0.20%, 1h=0.40%, 4h=0.70%, 1d=2.20%. |
| 적응형 폭 | known_at 이전 데이터만 받는 확장 인터페이스. 기본 공식이나 우승 공식 없음. |
| 이탈 | 종가가 경계 바깥 / 경계에서 설정 추가 거리 바깥. 거리 비율 설정 가능. |
| 결과 | LONG/SHORT 각각 TP_FIRST, SL_FIRST, NEITHER, AMBIGUOUS. TP·SL 비율, 캔들 관측 기간을 그리드로 지정. |
| 거래량 | 체결 수량, 공격적 매수/매도, 델타, 직전 동일 길이 구간 대비 비율. 관측 창 길이 설정 가능. |
| 대조군 | 구간 시작부터 일정 캔들 간격마다 관측. 탐지기와 무관한 일정이며 동일 결과 측정 규칙 사용. |
| 실험 | 심볼, 시간대, 데이터 ID/해시, 코드 해시, 탐지기 설정, 폭, 이탈, TP/SL, 관측 기간, 시간순 분할을 저장. |

A 원본 출처:
C:/Users/82108/Documents/Codex/2026-04-28/new-chat-3/binance_bot/src/main/resources/static/scoring.js
원본 SHA256: d530f675733d9a27b84191f95d72c3058cfaaa448efca04daa40b1bdb2b64960
원본 가격 선택은 보존하고 +/-1, +/-0.5 등의 점수는 옮기지 않았습니다.

## 검증 결과

기존 Phase 1 테스트 12개 + 신규 연구 테스트 75개 = **87 passed**.
전체 실행: backend에서 .venv/Scripts/python.exe -m pytest
기존 FastAPI/Starlette 테스트 의존성의 폐기 예정 경고 1개가 있으며 실패는 없습니다.

결정적 합성 데이터로 다음을 검증했습니다:
A의 양방향 반전, 고저가 선택 6개 분기와 동률, B 고저점 및 확정 지연,
C 확정 지연과 동일 캔들 확정 방지, 모든 데이터 접두 구간의 미래 누출 방지,
고정/원본 폭, 적응형 확장 데이터 제한, 방문/꼬리/종가 진입,
연속 방문 묶기, 이탈 후 재진입, 지지/저항 관통 방향, 추가 거리 이탈,
LONG/SHORT의 네 가지 결과, 갭 시작 가격으로 확인 가능한 선행 경계,
MFE/MAE와 시각, 관측 미완료, 누락/역순 데이터 거부,
체결 bin 경계와 매수/매도 방향, 미래 체결 배제, 원본 데이터 연결,
독립 설정 그리드, 완전 재현성, 시간순 분할 및 최종 테스트 차단.

## 실제 BTCUSDT 스모크

실제 Binance USD-M Futures 1시간봉 168개:
2024-01-01 00:00 UTC ~ 2024-01-08 00:00 UTC (끝 시각 제외).

- 연구: 첫 100개, 2024-01-05 04:00 UTC까지.
- 검증 예약: 다음 34개, 2024-01-06 14:00 UTC까지.
- 최종 테스트 예약: 마지막 34개. 이번 실행에 사용하지 않음.
- A: 고정 폭 5개 및 원본 1h 폭, B: N=1/2, C: 반전 0.3%/0.5%.
- 각 설정에 경계 이탈/추가 0.1% 이탈을 적용하여 총 20개 실험.
- TP/SL 각각 0.3%/0.5%, 관측 4/8개 캔들, LONG/SHORT 모두 측정.
- 후보 수: A 55개, B N=1은 46개/N=2는 26개, C 0.3%는 96개/0.5%는 82개.
- 측정 행 106,064개. 설정과 관측 기간이 겹치므로 독립 표본 수가 아님.
- 모든 캔들 접두 구간에서 known_at 이전 후보 없음 확인.
- 구간별 방문 번호와 방문 기간 비중복 확인.
- 동일 데이터·설정 재실행 JSON 일치 확인.

데이터 SHA256: 508a070fbb35cca897621e02bd8f602f76f438d578a3ea5187ec629a9fe121c6
최종 결과 SHA256: 8f194ac0748076404c0d228cc6f46e7c9640919ec742621bdf2b4b016e7b6576

재실행:
backend에서 .venv/Scripts/python.exe -m app.research.smoke --dataset ../data/research/phase2-smoke/BTCUSDT_1h_2024-01-01_2024-01-08.csv

## 해석에 영향을 주는 선택

- 가상 진입은 첫 방문을 확인한 캔들의 종가이며, 다음 캔들부터 결과를 측정합니다. 구간 중간 가격 체결을 가정하지 않습니다.
- 같은 캔들에서 TP/SL을 모두 건드리면 순서를 알 수 없을 때 AMBIGUOUS입니다. 시가가 이미 경계 밖인 경우에는 확인 가능한 시가 선행 순서를 사용합니다.
- MFE/MAE는 TP/SL 이후도 포함한 전체 관측 창 기준이고, 발생 시각은 해당 캔들 마감 시각 단위입니다.
- 관측 기간 끝까지 데이터가 없으면 censored로 남기며, 미확정 결과를 NEITHER로 단정하지 않습니다.
- C는 독립 고저점 추적 방식이며, 번갈아 나오는 ZigZag를 강제하지 않습니다.
- 방문 종료 후 알게 된 최대 침투/체류 시간은 진입 시점 특징으로 사용하지 않습니다.
- 구간은 합치거나 순위를 매기지 않습니다. 서로 겹치는 구간과 결과를 독립 증거로 취급하지 않습니다.
- 대조군은 시장 상태까지 맞춘 집단이 아닌 고정 일정 비교군입니다. 기술통계 차이만 제공하며 예측 우위를 주장하지 않습니다.
- 연구/검증 경계마다 탐지기와 구간을 초기화합니다. 결과와 거래량 창이 다음 기간으로 넘어가지 않습니다.
- 적응형 폭과 대규모 조합 최적화는 구현하지 않았습니다.

## 남은 데이터 요구사항

D는 실제 과거 데이터 실험 없이 합성 체결 데이터로 검증했습니다.
실제 비교에는 해당 기간의 BTCUSDT USD-M Futures aggregate trades가 필요합니다:
ID(a), 가격(p), 수량(q), UTC 밀리초 시각(T), buyer-is-maker(m),
가능하면 원본 first/last trade ID(f/l), 파일 checksum, 수집 범위와 누락 검증 기록.

현재가 캔들의 총 거래량이나 taker 거래량으로 가격대별 거래량을 대체하지 않습니다.
원하는 관측·기준 기간 전체의 체결 수집 및 완전성 검증은 남아 있습니다.
공식 획득 경로는 [Binance aggregate trades API](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Compressed-Aggregate-Trades-List)와
[Binance public-data archive](https://github.com/binance/binance-public-data)입니다.

