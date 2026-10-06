"""Sequential primary research then previously inspected replication, no tuning."""
import json
from app.market.aggregate_trades import write_json,sha256
from .design import ROOT,design,code_hash
from .prepare import initialize,prepare
from .analyze import analyze
from .reports import reports,completion


def main():
    initialize()
    prepare('development')
    analyze('development')
    reports('development')
    seal=dict(design_id=design()['design_id'],code_hash=code_hash(),
        model_hashes={str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'models').glob('*.parquet'))},
        development_summary_hash=sha256(ROOT/'development/summary.parquet'),
        selection='no rule or threshold selected; descriptive configuration only')
    seal['model_hashes']['context-model.json']=sha256(ROOT/'context-model.json')
    path=ROOT/'development-seal.json'
    if path.exists() and json.loads(path.read_text())!=seal:raise ValueError('Development seal changed')
    write_json(path,seal)
    print('DEVELOPMENT_SEALED',seal['design_id'],flush=True)
    prepare('replication')
    analyze('replication')
    reports('replication')
    completion()
    write_json(ROOT/'complete.json',dict(design_id=design()['design_id'],development_complete=True,
        replication_complete=True,replication_label='previously inspected replication period',
        final_test_used=False,rule_selected=False))
    print('PHASE35_COMPLETE',flush=True)


if __name__=='__main__':main()
