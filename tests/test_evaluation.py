from scripts.evaluate import evaluate
from pathlib import Path


def test_frozen_regression():
    # Versioned R1 corpus, original frozen questions/labels remain unchanged.
    result = evaluate(expected_content_hash=Path("tests/r1-corpus.sha256").read_text().strip())
    assert len(result["rows"]) == 12
    assert result["metrics"]["B"]["hard_conflict_release"] == 0
    assert result["metrics"]["B"]["critical_unknown_release"] == 0
