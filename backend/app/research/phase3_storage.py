"""Bounded-memory parquet sinks and disk-backed normalized research queries."""
from pathlib import Path
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq


def literal(value):
    return "'"+str(value).replace("'","''")+"'"


def connect(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=2")
    con.execute("SET temp_directory="+literal(directory/"duckdb-tmp"))
    con.execute("SET preserve_insertion_order=false")
    return con


class Sink:
    def __init__(self,path,fields):
        self.schema=pa.schema(fields);self.rows=[];self.count=0
        self.writer=pq.ParquetWriter(path,self.schema,compression="zstd")

    def add(self,row):
        self.rows.append(row);self.count+=1
        if len(self.rows)>=20000:self.flush()

    def flush(self):
        if self.rows:self.writer.write_table(pa.Table.from_pylist(self.rows,schema=self.schema));self.rows=[]

    def close(self):
        self.flush();self.writer.close()


STR=pa.string();INT=pa.int64();FLOAT=pa.float64()
INTERACTIONS=[(k,STR) for k in ("interaction_id","event_id","candidate_id","configuration_id","zone_id","detector","kind","width_model","visit_group")]+[(k,INT) for k in ("start","observed_at","visit_number","known_at")]+[(k,FLOAT) for k in ("width_parameter","reference_close","zone_lower","zone_upper","concentration")]
LIFECYCLES=[("interaction_id",STR),("end",INT),("candles_spent",INT),("available_at",INT),("censored",pa.bool_())]
FEATURES=[(k,STR) for k in ("interaction_id","event_id","status")]+[(k,INT) for k in ("timestamp","as_of","window_start","baseline_start","baseline_end")]+[(k,FLOAT) for k in ("quantity","aggressive_buy_quantity","aggressive_sell_quantity","volume_delta","baseline_quantity","relative_zone_volume")]
