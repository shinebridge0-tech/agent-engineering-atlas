import json
import tempfile
from pathlib import Path

from experiments.recovery import run as recovery
from experiments.tool_safety import run as safety

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="experiment-", dir=local) as directory:
        result = {"recovery": recovery(Path(directory)), "tool_safety": safety()}
    (local / "experiment-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
