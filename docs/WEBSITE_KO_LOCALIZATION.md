# Website v1 Korean UI Localization

## Scope

Display-only localization of the existing website. Backend code, configuration,
API fields/enums, scoring formulas and state thresholds are unchanged.
No research run, optimization or 2024 market-data acquisition was performed.

## Files

- `frontend/analysis/index.html`: Korean labels, accessible help and KST input.
- `frontend/analysis/ko.js`: centralized translations, display formatters and state descriptions.
- `frontend/analysis/app.js`: translated rendering without API object mutation.
- `frontend/analysis/style.css`: minimal wrapping and mobile input adjustments.
- `frontend/analysis/ko.test.cjs`: seven display-only regression tests.
- `docs/WEBSITE_KO_LOCALIZATION.md`: this report.

## Terminology

- S/R Scoring: 지지·저항 분석
- Converging: 수렴 분석
- Historical Percentile: 과거 백분위
- Stretch Ratio: 과도 배율
- Velocity / Acceleration: 과도 변화 속도 / 과도 변화 가속도
- HIGH / LOW: 고점 / 저점
- NORMAL / ELEVATED / STRETCHED / EXTREME: 보통 / 높음 / 과도 / 극단적

Technical identifiers, API values and source identifiers are preserved.
State descriptions do not add predictions or new classification thresholds.
Positive scores include a plus sign; percentiles include %, slopes use % / 봉.
Null derivatives display a dash. Help explains source-change resets.

## Verification

- Existing Python suite: 358 passed, zero failures/errors/skips. One existing
  Starlette/httpx deprecation warning remains.
- Frontend Node tests: 7 passed. Both JavaScript syntax checks passed.
- Before/after replay response: byte-for-byte identical for
  `2023-12-15T12:00:00Z`, including all scores and convergence metrics.
- Response SHA256: `0fbf16f3301d7c1eadd69992b07fcd12b2c45cb84d62aec5e3fd3e8f90d92756`.
- All eight captured backend/config file hashes are unchanged.
- KST input `2023-12-15T21:00` sends `2023-12-15T12:00:00.000Z`.
  Display: `2023-12-15 21:00 KST`, price `$42,800.0`, score `+0.009`.
- Desktop 1440px and mobile 390px inspected. No horizontal page overflow.
  Mobile input width is 345px. Details retain UTC alongside KST.
- Evidence: `data/website-v1/localization/verification.json`, `tests.xml`,
  `desktop.png` and `mobile.png`. Original pre-localization reports are retained.

## Re-run

### Cache compatibility follow-up

The user screenshot showed localized HTML with empty translation placeholders,
but legacy English dynamic cards and a UTC interpretation of the KST input.
This is consistent with an old cached app.js executing against the new HTML.
All three asset URLs now include a content-hash version to bypass old cache keys.
An additional regression test checks the versions against file contents and
ensures the dictionary loads before the application. Frontend tests: 8 passed.
Existing browser tabs must reload the page to load the corrected asset URLs.

From the project root:

```powershell
node --check frontend/analysis/ko.js
node --check frontend/analysis/app.js
node --test frontend/analysis/ko.test.cjs
```

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
