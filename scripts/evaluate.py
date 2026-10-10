"""Frozen self-built regression, identical keyword recall with/without constraints."""
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

from backend.content import load_all
from backend.decision import Question, classify, decide, export_report, relevance

ROOT = Path(__file__).resolve().parents[1]


def evaluate(corpus_root=None, expected_content_hash=None):
    # R1 registers an exact revised corpus checksum; never accept arbitrary drift.
    # Explicit old corpus roots still validate against the original frozen hash.
    if corpus_root is None and expected_content_hash is None:
        registry = ROOT / "tests/r1-corpus.sha256"
        if registry.exists():
            expected_content_hash = registry.read_text(encoding="utf-8").strip()
    corpus_root = Path(corpus_root) if corpus_root else ROOT / "content/cases"
    raw = (ROOT / "tests/scenarios.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != (ROOT / "tests/scenarios.sha256").read_text().strip():
        raise ValueError("Frozen scenario hash mismatch")
    frozen = json.loads(raw)
    parts = []
    for path in sorted(corpus_root.glob("*.md")):
        parts.extend([path.name.encode(), path.read_bytes()])
    actual_hash = hashlib.sha256(b"".join(parts)).hexdigest()
    if actual_hash != (expected_content_hash or frozen["content_sha256"]):
        raise ValueError("Frozen corpus changed; define a new explicit evaluation revision")
    cards = [c.model_dump() for c in load_all(corpus_root)]
    rows = []
    totals = {label: {"answer_recall_hits_at_3": 0, "answer_expected": 0, "hard_conflict_release": 0,
                     "critical_unknown_release": 0, "elapsed_ms": 0.0} for label in ["A", "B"]}
    for scenario in frozen["scenarios"]:
        request = Question.model_validate({k: scenario[k] for k in ["question", "cluster", "constraints"]})
        scoped = [c for c in cards if request.cluster == "all" or c["problem_cluster"] == request.cluster]
        begin = perf_counter()
        keyword = sorted([(relevance(request.question, c), c) for c in scoped if relevance(request.question, c)], key=lambda x: (-x[0], x[1]["id"]))[:3]
        totals["A"]["elapsed_ms"] += (perf_counter() - begin) * 1000
        begin = perf_counter()
        result = decide(request, cards)
        supported = [c for c in result["candidates"] if c["status"] == "compatible"][:3]
        totals["B"]["elapsed_ms"] += (perf_counter() - begin) * 1000
        a_ids = [c["id"] for _, c in keyword]
        b_ids = [c["card"]["id"] for c in supported]
        for label, returned in [("A", [c for _, c in keyword]), ("B", [c["card"] for c in supported])]:
            states = [classify(c, request.constraints)[0] for c in returned]
            totals[label]["hard_conflict_release"] += states.count("incompatible")
            totals[label]["critical_unknown_release"] += states.count("conditional")
            if scenario["kind"] == "answerable":
                ids = {c["id"] for c in returned}
                totals[label]["answer_expected"] += len(scenario["expected"])
                totals[label]["answer_recall_hits_at_3"] += len(ids & set(scenario["expected"]))
        by_id = {c["card"]["id"]: c["status"] for c in result["candidates"]}
        if scenario["kind"] == "hard_conflict":
            assert all(by_id.get(id) == "incompatible" for id in scenario["expected"]), scenario["id"]
        if scenario["kind"] == "insufficient":
            assert not supported, scenario["id"]
            assert "证据不足" in result["recommendation"]
        ids = [c["card"]["id"] for c in result["candidates"][:3]]
        exported, md = export_report(result, ids)
        assert json.loads(json.dumps(exported))["question"] == request.question
        assert "用户约束" in md
        for candidate in result["candidates"]:
            evidence = {s["source_id"] for s in candidate["card"]["sources"]}
            assert all(set(claim["evidence_ids"]).issubset(evidence) for claim in candidate["card"]["claims"])
        rows.append({"id": scenario["id"], "kind": scenario["kind"], "expected": scenario["expected"], "A_ids": a_ids,
                     "B_compatible_ids": b_ids, "candidate_states": by_id, "basis": scenario["basis"]})
    assert totals["B"]["hard_conflict_release"] == 0
    assert totals["B"]["critical_unknown_release"] == 0
    return {"scenario_hash": hashlib.sha256(raw).hexdigest(), "content_hash": actual_hash, "original_content_hash": frozen["content_sha256"], "explicit_content_revision": expected_content_hash is not None,
            "environment": platform.platform() + "; Python " + platform.python_version(), "metrics": totals,
            "reference_mapping": "structural evidence ID targets exist; not an independent semantic review", "exports": "12 JSON roundtrips and Markdown structure checks passed",
            "rows": rows, "limits": "12 self-built scenarios, 6 answerable / 3 target hard-conflicts / 3 insufficient. A returns top-3 keyword candidates without safety gates; B reports only compatible as supported. UI still shows excluded/conditional candidates explicitly. Time is one in-process run, no startup/browser/network/QPS claims. Paid model comparison NOT_RUN."}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root")
    parser.add_argument("--expected-content-hash")
    parser.add_argument("--output", default=".local/evaluation.json")
    args = parser.parse_args()
    result = evaluate(args.corpus_root, args.expected_content_hash)
    output = ROOT / args.output
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False, indent=2))
