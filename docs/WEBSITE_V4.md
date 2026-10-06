# Website v4: manual Scoring and public events

Scoring directional percentile is now an additive feature. See
[SCORING_PERCENTILE.md](SCORING_PERCENTILE.md) for exact causal semantics,
coverage limitations, manual-price behavior, cache and verification results.

## Manual price

`GET /dashboard/{symbol}/price?price=<P>&at=<ISO timestamp>` is authoritative.
Omit price for the unchanged current **closed-analysis-price** behavior. The
live ticker remains visible separately. Responses contain `price_mode`,
`analysis_price`, `market_price`, `market_close`, and `converging_price_mode`.
`price` retains the original closed-market meaning for chart compatibility.

Manual P reprices Scoring only. Candidate maps are materialized once for each
symbol/decision/config, then reused for subsequent P values (two entries per
worker). Neither candles, Converging, nor persisted live snapshots are changed.
Optional `candidate_map` injection and a defensive copy were added to
`scoring.score`; all arithmetic is unchanged. The old source-file hash guard
was updated for this structural refactor, with new current-price parity and
immutable-map tests. Converging remains byte-for-byte unchanged.

Validation rejects malformed/nonfinite/nonpositive P. Small altcoin values
are allowed; non-representable derived numeric results fail rather than emit
Infinity. Manual prices are not rounded to an exchange trading tick: this is
analysis, not an order. Display uses significant digits. Returning to current
mode restores the actual snapshot. Epoch/request guards discard obsolete
responses after symbol, mode or price changes. Manual requests use cached
operational history; they do not download an arbitrary old replay date.

## Calendar iframe (current architecture)

The calendar panel contains "미국 주요 경제 일정", the requested Investing
iframe and its visible attribution immediately below the iframe scroll wrapper:
"Real Time Economic Calendar provided by Investing.com." The provider name links
to https://www.investing.com/ with target="_blank" and rel="noopener noreferrer".
The attribution is outside the scrolling container, has no clipping or fixed
height, and wraps naturally on mobile. URL:

```text
https://sslecal2.investing.com?columns=exc_flags,exc_currency,exc_importance,exc_actual,exc_forecast,exc_previous&importance=3&features=datepicker,timezone&countries=5&calType=week&timeZone=88&lang=18
```

This preserves US / importance 3 / weekly / Korean / actual, forecast and previous
columns. The frame is 300px high, fills the desktop panel, and has a 650px minimum
width inside an independently horizontally scrollable mobile wrapper.

Removed: InvestingCalendarProvider, all calendar parsing, server fetching/polling,
403 interpretation, stale calendar cache, 30/10/release notifications and calendar
browser notifications. Calendar data is never passed into Scoring, Converging or
LONG/SHORT signals. No substitute calendar data is generated.

On monitor initialization, legacy calendar state and economic notifications are
deleted from the shared operational SQLite database. YouTube identity, state and
notification deduplication records are preserved. The database remains required
for YouTube; it no longer stores a calendar.

The iframe is isolated from the rest of the page. A browser-reported frame error
can reveal "경제캘린더를 불러오지 못했습니다.". Cross-origin security prevents the
parent page from reliably determining HTTP failures or inspecting frame contents;
a frame can instead display the browser's own blocked/error document. There is
no probing, parsing, server fallback, timeout-based false success or bypass.

## YouTube polling and notifications

Only YouTube uses the existing monitor and optional browser notifications.
Default polling: 3600 seconds, YOUTUBE_POLL_SECONDS minimum 1800.
The internal scheduler and browser cached-status reads run every 15 seconds.
Official search quota usage and delayed detection remain unchanged.
LIVE / OFFLINE / UPCOMING, title, video ID and start times are preserved.
Errors retain explicitly stale last-known YouTube state.

Live-start notification IDs are unique per video across process restarts.
Browser delivery is opt-in and atomically claimed, at-most-once across tabs.
Only notifications newer than 120 seconds are claimed. A crash after claiming
may lose a popup, but in-app history retains it. No economic alerts are returned
or claimable. OS notification permission was not enabled during verification.

## YouTube setup and identity

Official Data API only: `channels.list(forHandle=@EZPZNOW)` resolves the immutable
channel once, then `search.list(channelId=...,eventType=live,type=video,part=snippet)`
checks current streams. Upcoming is a distinct search; `videos.list` obtains
scheduled/actual start time. Ended video details are not labeled LIVE. Errors
retain last-known video details marked stale, never claim OFFLINE after failure.

**Verified immutable channel ID:** `UCZJ9ZukOgTjKcjN9SJQPf7w`.
The real official API returned LIVE video `5rC2mYtDGzM` during verification,
including title and actual start time. This is a point-in-time result, not a
promise that the stream remains live. Channel ID is persisted operationally.

Enable YouTube Data API v3 in a Google Cloud project and restrict the API key
to that API. Preferred environment variable: `YOUTUBE_API_KEY`. No key belongs
in source control, a frontend asset or an API response. This Windows machine
also supports `%LOCALAPPDATA%/lodeRunner/youtube-key.dpapi`: Windows DPAPI
encrypted, decryptable only by the same Windows user. The provided key was
stored there, not in the project. The process environment takes precedence.
Restart after changing credentials. Missing credentials produce UNCONFIGURED,
not scraping. Because the key was posted in chat, rotate it in Google Cloud.

## Persistence and API

Operational data/live-dashboard/events.sqlite3 contains YouTube state, channel
identity and durable notification IDs/delivery flags only.
GET /events/status returns youtube, alerts and server_timestamp, with no calendar
or alert_minutes fields. POST /events/notifications/claim returns only
YOUTUBE_LIVE_STARTED items. Existing API paths remain compatible for YouTube.
Frozen research and all 2024 research data remain untouched.

## Verification: iframe revision

- Python: 402 tests passed, zero failures/errors. Retired calendar-parser tests
  were replaced by migration, YouTube retention and no-calendar-polling tests.
- Node: 18 tests passed, including exact iframe parameters, contained error
  handling, asset versions and YouTube polling-failure handling.
- Real backend verification: current-price parity, manual P=70000 changing only
  Scoring, unchanged Converging/candles, legacy BTC baseline parity.
- Real official YouTube status during this revision: OFFLINE, correct channel ID.
  LIVE/UPCOMING/error and restart deduplication remain covered by unit tests.
- Headless Chrome: desktop 1440px and mobile 390px had no page overflow and no
  JavaScript errors. Mobile frame is 650px within a 328px scrollable wrapper.
- The exact Investing iframe request returned HTTP 403 on this machine; Chrome
  displayed a connection-refused frame. Its dimensions and isolation were verified,
  but successful calendar contents could not be verified. No bypass was attempted.

Evidence in data/live-dashboard:
v4-tests.xml, v4-verification.json, v4-iframe-browser.json,
v4-iframe-1440.png and v4-iframe-390.png.
Reproduce browser checks using frontend/analysis/calendar-browser-check.cjs with
Playwright installed (or PLAYWRIGHT_MODULE pointing to its package), Chrome, and
the local server running on port 8011.

## Attribution restoration: 2026-10-06

Added the user-supplied attribution without changing the iframe URL or analytical
and YouTube code. All 18 Node tests passed. Browser screenshots at 1440px and
390px confirm a visible, unclipped attribution link and no document overflow.
The verification script no longer reads the iframe DOM; only parent-page DOM,
network status and screenshots are inspected. The widget returned HTTP 403 in
the verification browser, so neither calendar contents nor resolution of the
reported "Please restore the link..." warning could be confirmed. No bypass or
domain substitution was attempted. Provider reactivation is not confirmed.
Evidence: data/live-dashboard/v4-attribution-browser.json,
v4-attribution-1440.png and v4-attribution-390.png.
