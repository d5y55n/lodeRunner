import json
from pathlib import Path
import numpy as np
from app.fullmap_scale.history import ROOT as BASE, SOURCE
from app.fullmap.contract import HOUR, FINAL_START
from app.fullmap.run import CONFIGS
from app.market.aggregate_trades import sha256, write_json
from app.research.models import identity

ROOT=BASE.parent/'phase3r2'
PROJECT=BASE.parent.parent
CODE=Path(__file__).parent
CONFIGS=CONFIGS[:5]
WINDOWS=(1,4,8)
DELTA=['support_normalized_delta','resistance_normalized_delta','normalized_delta_difference']
FLOW=DELTA+['support_delta','resistance_delta','raw_delta_difference','buy_share_difference',
    'support_volume_share','support_quantity','resistance_quantity','joint_quantity','shared_quantity']
CONDITIONS=['A1','A2','imbalance','clusters','candidates_per_cluster','distance_difference',
    'nearby_support','nearby_resistance','mean_age','mean_prior_crossings','mean_prior_visits',
    'mean_hours_since_last_contact','very_old_over_365d_fraction','volatility','recent_return',
    'map_direction','cluster_concentration','age_band']
PLAN=dict(version='3r2-v1',windows=list(WINDOWS),window='[T-window_hours,T); current T map intervals, not historical maps',
    maps='existing Phase3R1 events and memberships only; proximity .004 unchanged',
    flow_features=FLOW,conditioners=CONDITIONS,price_cuts='Phase3R1 development quartiles unchanged',
    flow_cuts='development only per detector and window, finite coverage-valid values; duplicate boundaries collapsed',
    schemes=['decile','ventile_if_supported','sign','shape'],
    sign='normalized value < -0.01 negative; abs(value)<=0.01 near_zero; >0.01 positive',
    shape='negative; near_zero; positive <=development positive-value 90th percentile moderate; above extreme',
    tails='development decile 0 and last; ventiles only if every development bin >=200 states and >=5 seven-day blocks',
    conditions='one frozen price stratum at a time, plus direction x cluster/candidates-per-cluster quartiles; not exact matching',
    age='nearby mean source age <=30, (30,180], (180,365], >365 days; retain existing very-old fraction',
    baselines='same-period all timestamps; same coverage/finite-flow cohort; same-cohort map-stratum alone',
    uncertainty='1000 shared resamples of fixed seven-day UTC blocks; seed 3202; minimum 5 represented blocks and 950 finite draws',
    ci_scope='all A windows, three normalized delta features, shape groups within A1/imbalance/clusters; all 24 grids',
    quarters='calendar UTC quarters, no tuning',replication='previously inspected replication period',
    no_threshold_selection=True,no_2024=True)

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def key(config):return identity(config)[:12]
def bounds(phase):
    if phase=='development':return 1641402000000,1672531200000
    if phase=='replication':return 1672531200000,FINAL_START
    raise ValueError('Unknown phase')
def guard(t,hours):
    if hours not in WINDOWS or t%HOUR or t>=FINAL_START or t-hours*HOUR<0:raise ValueError('Forbidden observation window')
def buckets(values,cuts):
    values=np.asarray(values,dtype=float)
    return np.where(np.isfinite(values),np.searchsorted(cuts,values,side='right'),-1)
def sign(values):
    a=np.asarray(values,dtype=float)
    return np.where(np.isfinite(a),np.where(a<-.01,0,np.where(a>.01,2,1)),-1)
def shape(values,positive_cut):
    a=np.asarray(values,dtype=float);s=sign(a)
    return np.where((s==2)&(a>positive_cut),3,s)
def check_freeze():
    seal=read(ROOT/'development-freeze.json')
    if seal['plan']!=PLAN:raise ValueError('Plan changed after freeze')
    for rel,digest in seal['files'].items():
        if sha256(ROOT/rel)!=digest:raise ValueError('Development changed')
    for name,digest in seal['code'].items():
        if sha256(CODE/name)!=digest:raise ValueError('Frozen code changed')
    return seal
def inventory():
    files=list(PROJECT.glob('PHASE3R1_*.md'))
    for directory in [BASE/'development',BASE/'replication',BASE/'reports',CODE.parent/'fullmap_scale',CODE.parent/'fullmap']:
        files.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in str(p))
    files.extend(p for p in BASE.glob('*') if p.is_file())
    return {str(p.relative_to(PROJECT)):sha256(p) for p in sorted(set(files))}
def initialize():
    ROOT.mkdir(exist_ok=True)
    if (ROOT/'plan.json').exists():
        if read(ROOT/'plan.json')!=PLAN:raise ValueError('Predeclared plan changed')
    else:
        write_json(ROOT/'plan.json',PLAN)
        write_json(ROOT/'preserved-before.json',inventory())
