from concurrent.futures import ThreadPoolExecutor
import pytest
from experiments.recovery import run as recovery
from experiments.tool_safety import Gate, run as safety


def test_recovery(tmp_path):
    result = recovery(tmp_path)
    assert result["durable_unique_tickets"] == 1
    assert result["negative_control_tickets"] == 2


def test_safety():
    assert safety()["unauthorized_side_effects"] == 0


def test_concurrent_budget():
    gate = Gate(b"test-only", budget=2)
    params = {"project": "demo", "subject": "test"}
    approval = gate.sign("create_ticket", params, "op", "human", 100)
    def attempt(_):
        try:
            gate.execute("create_ticket", params, "op", "human", approval, 1)
            return True
        except PermissionError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(16))) == 2
    assert len(gate.calls) == 2


def test_model_approval_is_not_authority():
    gate = Gate(b"test-only")
    with pytest.raises(PermissionError):
        gate.execute("create_ticket", {"project": "demo", "subject": "test"}, "op", "human", {"approve": True}, 1)
    assert gate.calls == []
