# Phase 3 Inspection Notes

These are structural checks, not evidence of predictive edge or instructions to
retune detectors. Development and validation outcome reports are separate.

## Saved-Artifact Causality Check

Development matched_control_links.parquet has 50,328 links, 16,776 distinct
targets and 14,288 distinct controls. A direct check against events.parquet
confirmed control_timestamp + horizon <= target_timestamp for every link, and
confirmed event IDs are unique. Reused control events are explicitly not new
independent observations.

## Development Candidate Counts

The saved development candidate dataset contains 115,553 rows: A 9,201,
B 13,252, C 30,624, and D 62,476. B/C/D counts combine their two declared detector
settings; these totals do not represent equal experimental exposure.

## Behaviors Requiring Caution

- A deliberately preserves the original scoring.js reference-candle choice.
  It is not rewritten as the maximum high or minimum low of the reversal pair.
  This unusual choice is part of the approved detector, not a performance fix.
- C maintains independent high and low trackers, resetting each after its own
  confirmation. It is not an alternating zigzag. More frequent candidates than
  A do not imply stronger information.
- Zones have no new age-based expiry in this research. Long-lived, overlapping
  zones can produce many repeated visits to the same market timestamp.
- Development contains 64,229,528 interaction rows but at most 17,519 distinct
  hourly decision events. Outcome configurations multiply measurement counts
  again. Neither row counts nor event deduplication establish independence;
  adjacent horizons still overlap.
- D regions are neutral concentration regions, not directional entry signals.
  Its 50/100 USD bins and 1.5 occupied-bin mean multiplier remain declared
  settings, not optimal choices. Zone width is a separate parameter.
- Summary groups pool support/resistance candidate kinds within a detector
  configuration. LONG and SHORT are separate hypothetical outcome measurements,
  not support-only buys or resistance-only sells. Candidate kind remains in the
  interaction dataset for inspection; these pooled rates are not a trading rule.
- A zero baseline zone quantity leaves relative volume undefined, not infinite
  and not zero. Its relative-volume bucket is MISSING even when the current
  trade coverage status is AVAILABLE. Coverage counts and bucket counts therefore
  answer different questions.
- Missing volume after quarantine is not zero activity. Price-only A/B/C
  observations remain included. Official candle volume is used as forensic
  comparison evidence, never substituted into aggregate-trade features.
- Source daily/monthly agreement and the coverage tolerance do not prove that
  every execution is represented. Boundary-conservation classifications are
  documented coverage interpretations, not reconstructed trade records.

No rules were changed to address these observations. Use the machine-readable
configuration manifests and separate phase reports for exact counts and rates.

## Development-Only Outcome Inspection

Inspected only after the seven-setting validation configuration was frozen.
In the predeclared display slice (original 1h width, LONG, TP=SL=0.003, eight
candles), ambiguous outcomes account for approximately 33.8%-37.7% across the
seven settings. Hourly OHLC cannot determine which boundary was reached first
inside those candles. These observations must not be assigned favorable wins.

Each display setting covers 16,930-17,440 unique hourly events out of 17,519
available development decision closes. The extensive overlap and differences
between row-weighted and event-balanced rates are important limitations, not
evidence of seven independent predictive discoveries. No parameter changes or
edge claims follow from this inspection.
