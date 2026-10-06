"""Vectorized, bounded-memory exact-price range queries for saved interactions."""
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from .phase3_storage import FEATURES,connect,literal
from .phase3_profiles import Profiles


def range_quantities(frame,lower,upper):
    prices=frame.price.to_numpy()
    left=np.searchsorted(prices,lower,side="left");right=np.searchsorted(prices,upper,side="right")
    return frame.attrs["prefix"][right]-frame.attrs["prefix"][left]


def build_features(dest,root,start,quarantines):
    schema=pa.schema(FEATURES);path=dest/"decision_features.parquet"
    pending=dest/"decision_features.parquet.building"
    writer=pq.ParquetWriter(pending,schema,compression="zstd")
    profiles=Profiles(root/"profiles",quarantines);con=connect(dest)
    query="SELECT interaction_id,event_id,observed_at,known_at,zone_lower,zone_upper FROM read_parquet("+literal(dest/"interactions.parquet")+") ORDER BY observed_at"
    batches=con.execute(query).to_arrow_reader(100000);count=0
    for batch in batches:
        times=batch.column("observed_at").to_numpy();known=batch.column("known_at").to_numpy()
        if np.any(times<known) or np.any(times%3600000):raise ValueError("Invalid decision availability/alignment")
        lower=batch.column("zone_lower").to_numpy();upper=batch.column("zone_upper").to_numpy()
        boundaries=np.r_[0,np.flatnonzero(times[1:]!=times[:-1])+1,len(times)]
        for left,right in zip(boundaries,boundaries[1:]):
            timestamp=int(times[left]);n=int(right-left);current=baseline=None
            if timestamp-7200000<start:status="MISSING_TRADE_COVERAGE"
            elif profiles.quarantined(timestamp-7200000,timestamp):status="QUARANTINED_TRADE_COVERAGE"
            else:
                a=profiles.hour(timestamp-3600000);b=profiles.hour(timestamp-7200000)
                if a is None or b is None:status="MISSING_TRADE_COVERAGE"
                else:
                    status="AVAILABLE"
                    current=range_quantities(a,lower[left:right],upper[left:right])
                    baseline=range_quantities(b,lower[left:right],upper[left:right])[:,0]
            data={"interaction_id":batch.column("interaction_id").slice(int(left),n),
                  "event_id":batch.column("event_id").slice(int(left),n),"timestamp":np.full(n,timestamp,dtype=np.int64),
                  "as_of":np.full(n,timestamp,dtype=np.int64),"status":[status]*n}
            if current is not None:
                ratio=np.divide(current[:,0],baseline,out=np.full(n,np.nan),where=baseline!=0)
                data.update(quantity=current[:,0],aggressive_buy_quantity=current[:,1],aggressive_sell_quantity=current[:,2],
                    volume_delta=current[:,1]-current[:,2],baseline_quantity=baseline,
                    relative_zone_volume=pa.array(ratio,mask=np.isnan(ratio)),
                    window_start=np.full(n,timestamp-3600000,dtype=np.int64),
                    baseline_start=np.full(n,timestamp-7200000,dtype=np.int64),baseline_end=np.full(n,timestamp-3600000,dtype=np.int64))
            arrays=[pa.array(data[name],type=typ) if name in data else pa.nulls(n,type=typ) for name,typ in FEATURES]
            writer.write_table(pa.Table.from_arrays(arrays,schema=schema))
        count+=len(times)
        if count%1000000==0:print("BATCH_FEATURES",count,flush=True)
    writer.close();con.close();pending.replace(path)
    return count
