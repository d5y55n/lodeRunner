# Optimization and Parity

A1 is unchanged. 850 calendar days, 20,400 closed hourly candles, close at T,
one-hour steps, full dependency expiration, known_at <= T and prior outcome
semantics remain exactly as Phase 3R. Original golden tests remain in the suite.

A/B candidates are cataloged once; membership filters confirmation and complete
source span. C starts at each rolling left boundary. Its deterministic high/low
tracker state is replayed until BOTH tracker indices equal a cached state after
the same candle; equal state plus equal subsequent inputs proves an identical
suffix. Only then is the suffix reused. Without synchronization, the complete
window is replayed. This is not a switch to global-history initialization.
Tests include flat never-synchronizing tracks and randomized rolling windows.

Geometry uses vector arithmetic and exact original full/half boundaries.
Nearest ties retain known_at/source/price tie-breaking. Cluster pairs use
sorted interval endpoints, including touching boundaries. D uses the identical
reference rolling arithmetic with compact hourly views instead of DataFrames.

Catalog indices are deterministic within each run/stage catalog. Daily membership
checkpoints plus added/removed uint32 arrays are zlib-compressed in Parquet.
Unused precomputed rows are pruned after generation without renumbering indices;
A and B/C catalogs are disjoint, with one record per used candidate in each phase.
Chronological phases remain self-contained and share the original candidate SHA
identities, rather than treating a repeated historical level as new evidence.
Restore original event order by known_at then RESISTANCE before SUPPORT for
same-candle B/C events. Identity remains the original candidate SHA, not the
integer index. Raw memberships remain reconstructable; scores cannot substitute
for them. State feature rows omit redundant member-ID arrays only.

Reference gate: 168 snapshots and 576 outcome rows;
all fields compared, five physical future-truncation checks, D quantities and
coverage identical/numerically equivalent (rtol=atol=1e-12). Gate source hashes
prevent execution after an untested engine change.

Actual benchmark: 1,000 timestamps / 5,000 directional maps, including streaming
exports and A age/crossing features. Initialization 4.99s;
loop 57.15s; peak RAM 2.443 GiB;
output 12.47 MiB. Linear projection for
17,407 timestamps: 16.66 minutes and
217.06 MiB. This projection excludes separate D,
outcome and statistical analysis work. Actual stage runtimes are in completion.
No hundreds-of-GB duplicated JSONL inspection export is generated for the full run.

Frozen analysis ID: `6b8bfc02671f6f9621b522bf65412e697f5f114bec47e371d5cefb9feb431c95`. Feature/model/code digests are checked
before replication. Rendering/audit code is outside the research-definition seal.
