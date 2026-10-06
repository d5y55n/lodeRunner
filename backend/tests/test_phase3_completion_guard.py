import pytest

from app.research.phase3_reports import reports


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_partial_summary_cannot_be_reported_complete(tmp_path, phase):
    dest = tmp_path / phase
    dest.mkdir()
    (dest / "research_summary.csv").write_text("partial\n")
    with pytest.raises(ValueError, match="has not completed"):
        reports(tmp_path, phase)
