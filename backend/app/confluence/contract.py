"""Predeclared definitions and guarded, auditable source access."""
import hashlib
import json
from itertools import combinations
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
ROOT = PROJECT / 'data/phase5'
CODE = Path(__file__).parent
TFS = ('15m', '1h', '4h', '1d')
STEPS = dict(zip(TFS, (900000, 3600000, 14400000, 86400000)))
WIDTHS = dict(zip(TFS, (.002, .004, .007, .022)))
END = 1704067200000
START = 1640995200000
REP = 1672531200000
SUBSETS = tuple(s for n in range(1, 5) for s in combinations(TFS, n))
ADDITIONS = ((('15m',), '1h'), (('1h',), '4h'), (('4h',), '1d'),
             (('15m', '1h'), '4h'), (('1h', '4h'), '1d'),
             (('15m', '1h', '4h'), '1d'), (('15m', '1h', '1d'), '4h'),
             (('15m', '4h', '1d'), '1h'), (('1h', '4h', '1d'), '15m'))
PLAN = dict(
    version='phase5-A-confluence-v1', timeframes=TFS, steps=STEPS, widths=WIDTHS,
    development='2022 eligible frozen 850-day maps only',
    replication='2023 previously inspected replication period; gated by complete development freeze',
    clock='15m closed timestamps; latest source<=T; age<one native step; no candle fill',
    direction='primary sign of nearby raw (support-resistance)/(support+resistance); exact zero balanced; empty neighborhood missing, not balanced',
    descriptors='separate A1 sign, A2 sign, raw imbalance sign, full-map and nearby counts, nearest geometry; no summed score',
    sign_sensitivity=['A1', 'A2'],
    nearby='unchanged original full/half native membership at source decision price; held with source state until next close',
    intervals='candidate p: closed [p*(1-w_tf),p*(1+w_tf)]; nearby uses original strict outer 1.5w boundary; no new proximity width',
    overlap='U_tf=union of native nearby intervals of one type; I_subset=intersection of U_tf; touching counts; preserve every connected component and every nonempty subset; maximum count is descriptive only',
    distance='max(lower-current_price,0,current_price-upper); also divided by current_price; no reclassification of held native scores at current price',
    participant_count='unique native candidate intervals intersecting each common component, counted per timeframe; candidate indices reference frozen catalog',
    categories='all 15 nonempty TF subsets, exact S/R/N/M pattern, separate marginal aligned counts and no-opposition counts, lower(15m,1h)/higher(4h,1d) exact patterns',
    incremental='within fixed base-aligned cohort: added agrees vs added neutral/conflicts; missing separately; same UTC block draws on both groups',
    baselines='all same-period eligible T; each constituent single-TF aligned; each proper lower-order aligned subset; explicit inclusive vs exclusive-only distinction',
    quantity='unchanged 15m A joint quantity from native 1-candle flow only as primary risk covariate; unavailable remains missing; quartiles development only',
    delta='unchanged support/resistance normalized Delta and joint/raw Delta; secondary quartile tables only',
    magnitude='per-timeframe development quartiles of abs(nearby imbalance); separate native bucket vector; all-four weak Q1, moderate Q2/Q3, strong Q4, mixed, missing; never summed',
    outcomes='reuse frozen Phase4 15m event_id/timestamp rows, LONG/SHORT x TP .003/.005 x SL .003/.005 x horizons 16/32/96; no regeneration',
    censoring='report all counts; rates/MFE/MAE conditional on complete horizon; censored retained explicitly',
    quarters='UTC 2022 and 2023 Q1-Q4 separately plus ALL',
    uncertainty='1000 shared multinomial resamples of epoch-aligned seven-day UTC blocks, seed 5105; paired subset/baseline or disjoint conditional contrasts; all 24 grids, all outcome rates and MFE/MAE',
    sparsity='supported>=200 complete timestamps and>=5 occupied seven-day blocks in BOTH contrast groups; CI needs>=950 finite draws; no rare-category merge; still report all cells',
    shapes='1/2/3/4: sparse if any unsupported; exact flat if all equal; monotonic up/down if ordered; otherwise nonlinear; quarterly sign changes reported not pooled away',
    no_2024=True, no_live_rules=True, no_winner=True, no_BC=True,
    hierarchy=[list(s) for s in SUBSETS], additions=[(list(b), a) for b, a in ADDITIONS])


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Phase 5 writes only')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False), encoding='utf-8')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def initialize():
    ROOT.mkdir(parents=True, exist_ok=True)
    p = ROOT / 'plan.json'
    if p.exists() and read(p) != json.loads(canonical(PLAN)):
        raise ValueError('Predeclared plan changed')
    write(p, PLAN)


def check_freeze():
    f = read(ROOT / 'development-freeze.json')
    if f['plan'] != json.loads(canonical(PLAN)):
        raise ValueError('Frozen definition changed')
    if hashlib.sha256(canonical({k:v for k,v in f.items() if k!='freeze_id'}).encode()).hexdigest()!=f['freeze_id']:
        raise ValueError('Freeze identity changed')
    if digest(PROJECT/'PHASE5_CONFLUENCE_CONTRACT.md')!=f['contract_report_sha256']:
        raise ValueError('Frozen contract report changed')
    for rel, h in f['files'].items():
        if digest(ROOT / rel) != h:
            raise ValueError('Frozen development artifact changed: ' + rel)
    for name, h in f['code'].items():
        if digest(CODE / name) != h:
            raise ValueError('Frozen code changed: ' + name)
    return f


def phase_guard(phase):
    if phase not in ('development', 'replication'):
        raise ValueError('Forbidden research period')
    if phase == 'replication':
        check_freeze()


def timestamp_guard(values, phase):
    low, high = (START, REP) if phase == 'development' else (REP, END)
    if not ((values >= low) & (values < high)).all():
        raise ValueError('Timestamp outside authorized phase')


class Sources:
    def __init__(self, phase):
        phase_guard(phase)
        self.phase = phase
        self.hashes = {}

    def frame(self, path):
        import pandas as pd
        path = Path(path).resolve()
        allowed = [PROJECT / 'data' / name / self.phase for name in ('phase3r1', 'phase3r2')]
        allowed += [PROJECT / 'data/phase4' / tf / self.phase for tf in TFS if tf != '1h']
        if not any(path.is_relative_to(p.resolve()) for p in allowed):
            raise ValueError('Unauthorized source path')
        if any('2024' in part for part in path.parts):
            raise ValueError('2024 forbidden')
        self.hashes[str(path.relative_to(PROJECT))] = digest(path)
        return pd.read_parquet(path)

    def save(self):
        write(ROOT / self.phase / 'source-hashes.json', self.hashes)
