import zipfile
import pandas as pd
import pytest
from app.market.phase3_publication_audit import scan
from app.market.phase3_coverage import official_daily


def archive(tmp_path,ids):
    path=tmp_path/"trades.zip"
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("trades.csv","".join(f"{i},100,1,{i},{i},{1000+i},false\n" for i in ids))
    return path


def test_reversed_publication_preserves_every_issue_and_raw_quantity(tmp_path):
    path=archive(tmp_path,[1,5,2,6]);issues=tmp_path/"issues.parquet"
    minutes,gaps,duplicates,ordering=scan([path],issues)
    assert minutes.quantity.sum()==4 and minutes["count"].sum()==4
    assert ordering["raw_reversals"]==1 and ordering["raw_positive_jumps"]==2
    assert pd.read_parquet(issues).id_step.tolist()==[4,-3,4]
    assert gaps==[] and duplicates==0


def test_duplicate_publication_not_silently_deduplicated(tmp_path):
    path=archive(tmp_path,[1,1,2,4]);issues=tmp_path/"issues.parquet"
    minutes,gaps,duplicates,ordering=scan([path],issues)
    assert minutes.quantity.sum()==4 and duplicates==1
    assert gaps[0]["before"]["id"]==2 and gaps[0]["after"]["id"]==4


def test_daily_acquisition_rejects_2024_before_network(tmp_path):
    with pytest.raises(ValueError,match="reserved"):
        official_daily("2024-01-01","aggTrades",tmp_path)
