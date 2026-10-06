import hashlib
import json
from pathlib import Path
from app.confluence.contract import PROJECT, TFS, STEPS, WIDTHS, START, REP, END, digest, read, canonical

ROOT=PROJECT/'data/phase5_1'
CODE=Path(__file__).parent
PATHS=(('15m',),('1h',),('4h',),('1d',),('15m','1h'),('1h','4h'),('4h','1d'),
       ('15m','1h','4h'),('1h','4h','1d'),TFS)
HIERARCHY=(('15m',),('15m','1h'),('15m','1h','4h'),TFS)
PLAN=dict(version='phase5.1-current-price-A-v1',timeframes=TFS,widths=WIDTHS,
    hypotheses=['H1 SSSS LONG','H2 RRRR SHORT','H3 exact lower-to-higher hierarchy','H4 strength within SSSS/RRRR'],
    current_price='P=existing closed 15m close at T, identical P used for every timeframe',
    maps='reuse latest fully closed native A candidate membership, 850-day window anchored at source native close; no new/expired membership between native closes',
    evaluation='only rescore frozen candidate prices at P with original strict full/half proximity rules; not a new detector or native-map rebuild',
    classification='nearby unweighted s/r counts: s>r S, s<r R, s==r and s+r>0 N, empty/unavailable M',
    scores='A1=full_s-full_r + .5*(half_s-half_r); A2=full_s-full_r; per-timeframe only, no cross-TF sum',
    distances='nearest in full frozen side map at P; ties by abs(price-P),known_at,source_timestamp,price; signed price/P-1 and absolute fraction preserved',
    old_phase5='carried source-price descriptors are comparison/audit only; never primary current-price classification',
    spatial='no overlap/unions/intersections read or computed; prior spatial conclusions irrelevant to H1-H4',
    patterns='all 256 S/R/N/M patterns exact N, including zero cells; no performance-driven merges; primary SSSS/RRRR only',
    hierarchy=HIERARCHY,secondary_paths=PATHS,
    baselines='SSSS LONG / RRRR SHORT minus all, respective 15m,15m+1h,15m+1h+4h; same 15m event cohort; adjacent hierarchy and conditional added-state contrasts',
    strength='retain continuous four-dimensional signed and absolute imbalance; no weighted score',
    native_strength_cuts='per-timeframe quartiles of valid abs(current-P imbalance) across eligible 2022 decision clock; no replication refit',
    strength_groups='within SSSS/RRRR: each native Q1-Q4; all weak(Q1), all medium(Q2/Q3), >=1/2/3/4 native Q4, exact Q4 count 0..4, mixed(not all weak/medium/strong); explicit missing',
    summaries='minimum/median/maximum of four absolute imbalances, complete 4D only; conditional-development quartile curves AND univariate continuous OLS slopes for all six outcomes, not a fitted strategy',
    continuous='slope=cov(x,y)/var(x), report per 0.1 absolute imbalance; pooled shared seven-day UTC block bootstrap, quarterly slopes, no independent p-values or multivariate weights',
    geometry='all four nearest favored-type candidates within their existing strict full-weight native band vs any outside, within SSSS/RRRR; descriptive distance max quartiles additionally',
    quantity='unchanged existing 15m A one-candle joint zone quantity; 2022 global quartiles: Q1 low, Q2/Q3 medium, Q4 high; unavailable remains missing; not direction/strength',
    delta='unchanged 15m support/resistance normalized and raw/joint fields retained; appendix descriptive means only, never classification/strength',
    outcomes='existing Phase4 15m exact event/timestamp rows reused; LONG/SHORT, TP/SL .003/.005, horizons16/32/96; no regeneration',
    censoring='all N and censored counted, outcome rates and MFE/MAE on complete horizon only',
    chronology='2022 ALL,Q1-Q4; review and hash full definition/code/buckets/artifacts before any 2023 read; 2023 previously inspected replication period',
    uncertainty='reuse Phase5 seven-day epoch-aligned UTC block bootstrap, 1000 draws seed5105; paired/nested masks use same draws; six metrics; pooled CI and quarter effects',
    support='>=200 complete events and>=5 occupied blocks on both contrast sides; CI>=950 finite draws and>=5 blocks; zero/missing/sparse remain explicit',
    inference='exploratory dependent grids; no strongest-cell selection; no independent-row p-values; primary vs secondary explicitly labeled',
    audit='all native-source score parity, 15m reuse identity, current-P reference parity on deterministic patterns and calendar boundaries, physically truncated source-state lookup; real absent M documented with synthetic M fixture',
    no_2024=True,no_live_rule=True,no_leverage=True,no_spatial=True,no_detector_change=True)


def write(path,value):
    p=Path(path)
    if not p.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Phase 5.1 writes only')
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False),encoding='utf-8')


def initialize():
    ROOT.mkdir(parents=True,exist_ok=True)
    if (ROOT/'plan.json').exists() and read(ROOT/'plan.json')!=json.loads(canonical(PLAN)):
        raise ValueError('Predeclared plan changed')
    write(ROOT/'plan.json',PLAN)


def check_freeze():
    f=read(ROOT/'development-freeze.json')
    if f['plan']!=json.loads(canonical(PLAN)):raise ValueError('Frozen plan changed')
    if hashlib.sha256(canonical({k:v for k,v in f.items() if k!='freeze_id'}).encode()).hexdigest()!=f['freeze_id']:
        raise ValueError('Freeze identity changed')
    for name,h in f['code'].items():
        if digest(CODE/name)!=h:raise ValueError('Frozen code changed '+name)
    for name,h in f['files'].items():
        if digest(ROOT/name)!=h:raise ValueError('Frozen development changed '+name)
    from app.confluence.contract import check_freeze as old_check
    old_check()
    return f


def guard(phase):
    if phase not in ['development','replication']:raise ValueError('Unauthorized phase')
    if phase=='replication':check_freeze()


class Sources:
    def __init__(self,phase):
        guard(phase);self.phase=phase;self.hashes={}
    def frame(self,path,columns=None):
        import pandas as pd
        p=Path(path).resolve()
        allowed=[PROJECT/'data/phase5'/self.phase/'native',PROJECT/'data/phase3r1'/self.phase]
        allowed += [PROJECT/'data/phase4'/tf/self.phase for tf in ['15m','4h','1d']]
        if any('2024' in s for s in p.parts) or not any(p.is_relative_to(a.resolve()) for a in allowed):
            raise ValueError('Unauthorized source; no spatial or 2024 input')
        self.hashes[str(p.relative_to(PROJECT))]=digest(p)
        return pd.read_parquet(p,columns=columns)
    def save(self):
        path=ROOT/self.phase/'source-hashes.json'
        old=read(path) if path.exists() else {}
        for k,h in self.hashes.items():
            if k in old and old[k]!=h:raise ValueError('Input changed mid-run')
        old.update(self.hashes);write(path,old)
