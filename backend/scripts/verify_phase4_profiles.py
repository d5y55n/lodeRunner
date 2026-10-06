"""Independent read-only monthly parity audit; does not change frozen research code."""
import numpy as np
import pandas as pd
from app.multimap.contract import ROOT,read,sha256,write_json
from app.multimap.profiles import SOURCE
from app.multimap.freeze import check
from app.research.phase3_engine import load_coverage


def main():
    for tf in ['15m','4h','1d']:check(tf)
    coverage=load_coverage(SOURCE);results=[]
    for year in [2022,2023]:
        for month in range(1,13):
            label=f'{year}-{month:02d}';folder=ROOT/'trade-profiles-15m'/label
            manifest=read(folder/'manifest.json')
            if manifest['coverage_id']!=coverage['coverage_id']:raise ValueError('Coverage policy changed')
            path=SOURCE/'profiles'/(label+'.parquet')
            if sha256(path)!=coverage['source_profile_hashes'][label]:raise ValueError('Hourly source changed')
            parts=[]
            for name,digest in manifest['partitions'].items():
                if sha256(folder/name)!=digest:raise ValueError('Quarter-hour partition changed')
                parts.append(pd.read_parquet(folder/name))
            f=pd.concat(parts,ignore_index=True);f['hour']=f.start//3600000*3600000
            first=(manifest['observation_start']+3599999)//3600000*3600000
            end=manifest['observation_end']//3600000*3600000
            f=f[(f.hour>=first)&(f.hour<end)]
            new=f.groupby(['hour','price'])[['quantity','buy','sell']].sum().sort_index()
            old=pd.read_parquet(path)
            old=old[(old.hour>=first)&(old.hour<end)].set_index(['hour','price'])[['quantity','buy','sell']].sort_index()
            pd.testing.assert_index_equal(old.index,new.index)
            np.testing.assert_allclose(old.to_numpy(),new.to_numpy(),rtol=1e-10,atol=1e-8)
            results.append(dict(month=label,status='PASS',full_hour_start=first,end_exclusive=end,
                exact_hour_price_rows=len(new),quantity=float(new.quantity.sum()),
                maximum_absolute_error=float(np.max(np.abs(old.to_numpy()-new.to_numpy()))),
                quarter_manifest_sha256=sha256(folder/'manifest.json'),hourly_profile_sha256=sha256(path)))
            print('FULL_MONTH_PROFILE_PARITY',label,len(new),flush=True)
    write_json(ROOT/'profile-parity-full-months.json',dict(status='PASS',months=24,results=results,
        rule='Exact observed price and hour indexes, quantity/buy/sell; only whole covered hours, no empty-bin filling',
        rtol=1e-10,atol=1e-8,no_2024=True,no_research_configuration_changes=True))


if __name__=='__main__':main()
