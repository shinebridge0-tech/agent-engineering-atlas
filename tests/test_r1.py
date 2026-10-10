import asyncio
import copy
import json
import shutil
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend import app as api, indexing
from backend.content import CONTENT, Card, load_all
from backend.decision import Constraints, Question, classify, decide, export_report


@pytest.fixture
def cards():
    return [c.model_dump() for c in load_all()]


@pytest.fixture
def client():
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c


@pytest.mark.parametrize("field", ["approval", "data_external", "idempotency"])
@pytest.mark.parametrize(
    "value,expected",
    [
        ("omitted", "unknown"),
        (None, "unknown"),
        (True, "yes"),
        (False, "no"),
        ("unknown", "unknown"),
        ("yes", "yes"),
        ("no", "no"),
    ],
)
def test_fact_matrix(client, field, value, expected):
    constraints = {} if value == "omitted" else {field: value}
    r = client.post("/api/decision", json={"question": "工具 审批", "constraints": constraints})
    assert r.status_code == 200
    assert r.json()["constraints"][field] == expected


@pytest.mark.parametrize("value", ["", 0, 1, [], {}, "true", "false"])
def test_invalid_facts(client, value):
    assert (
        client.post("/api/decision", json={"question": "工具", "constraints": {"approval": value}}).status_code == 422
    )


def test_omitted_critical_and_irrelevant_unknowns(cards, client):
    for payload in [
        {"question": "工具 审批"},
        {"question": "工具 审批", "constraints": {}},
        {"question": "工具 审批", "constraints": None},
    ]:
        r = client.post("/api/decision", json=payload)
        assert r.status_code == 200
        states = {c["card"]["id"]: c["status"] for c in r.json()["candidates"]}
        assert states["bound-approval"] == "conditional"
        assert states["tool-allowlist"] == "compatible"
    approved = decide(Question(question="工单", constraints={"approval": True, "idempotency": True}), cards)
    assert next(c for c in approved["candidates"] if c["card"]["id"] == "stable-idempotency")["status"] == "compatible"


@pytest.mark.parametrize("permission", ["no", "yes", "unknown"])
def test_local_permission_recall(cards, permission):
    result = decide(
        Question(question="关键词 检索", cluster="retrieval", constraints={"data_external": permission}), cards
    )
    assert {c["card"]["id"] for c in result["candidates"] if c["status"] == "compatible"} == {
        "keyword-retrieval",
        "hybrid-retrieval",
        "permission-filter",
    }


def test_permission_monotonicity_and_external_negative(cards):
    for card in cards:
        before = classify(card, Constraints(approval="yes", idempotency="yes", data_external="no"))[0]
        after = classify(card, Constraints(approval="yes", idempotency="yes", data_external="yes"))[0]
        assert not (before == "compatible" and after == "incompatible")
    card = copy.deepcopy(cards[0])
    card["frameworks"] = ["neutral"]
    card["hard_requirements"] = [{"key": "data_external", "value": "yes", "critical": True}]
    assert [classify(card, Constraints(data_external=p))[0] for p in ["no", "unknown", "yes"]] == [
        "incompatible",
        "conditional",
        "compatible",
    ]
    card["hard_requirements"][0]["value"] = "unknown"
    assert classify(card, Constraints(data_external="no"))[0] == "conditional"


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    root = tmp_path / "cases"
    shutil.copytree(CONTENT, root)
    db = tmp_path / "index.db"
    monkeypatch.setattr(api, "rebuild", lambda: indexing.rebuild(root, db))
    monkeypatch.setattr(api, "read_cards", lambda: indexing.read_cards(db))
    return root, db


def export_payload(request, result, format="json"):
    return {
        "request": request,
        "selected": ["stable-idempotency"],
        "format": format,
        "content_revision": result.get("content_revision", "missing"),
        "result_id": result.get("result_id", "missing"),
    }


@pytest.mark.parametrize("mutation", ["body", "metadata", "evidence", "status"])
def test_stale_revision(isolated, mutation):
    root, db = isolated
    with TestClient(app, base_url="http://127.0.0.1") as c:
        q = {"question": "工单", "constraints": {"approval": "yes", "idempotency": "yes"}}
        a = c.post("/api/decision", json=q).json()
        payload = export_payload(q, a)
        assert c.post("/api/export", json=payload).status_code == 200
        p = root / "stable-idempotency.md"
        text = p.read_text(encoding="utf8")
        replacements = {
            "body": ("\n## 使用边界", "\nR1 isolated body\n## 使用边界"),
            "metadata": ("revision: 1", "revision: 2"),
            "evidence": ("lines: 903-929", "lines: 903-930"),
            "status": ("status: current", "status: needs_recheck"),
        }
        old, new = replacements[mutation]
        assert old in text
        p.write_text(text.replace(old, new), encoding="utf8")
        indexing.rebuild(root, db)
        for fmt in ["json", "markdown"]:
            payload["format"] = fmt
            assert c.post("/api/export", json=payload).status_code == 409
        b = c.post("/api/decision", json=q).json()
        assert b["content_revision"] != a["content_revision"]
        assert c.post("/api/export", json=export_payload(q, b)).json()["content_revision"] == b["content_revision"]


def test_export_binding_and_same_view(isolated, monkeypatch):
    root, db = isolated
    with TestClient(app, base_url="http://127.0.0.1") as c:
        q = {"question": "工单", "constraints": {"approval": "yes", "idempotency": "yes"}}
        a = c.post("/api/decision", json=q).json()
        p = export_payload(q, a)
        for key in ["content_revision", "result_id"]:
            missing = dict(p)
            missing.pop(key)
            assert c.post("/api/export", json=missing).status_code == 422
            forged = {**p, key: "fake"}
            assert c.post("/api/export", json=forged).status_code == 409
        changed = copy.deepcopy(p)
        changed["request"]["constraints"]["approval"] = "no"
        assert c.post("/api/export", json=changed).status_code == 409
        original = api.decide

        def race(request, cards):
            path = root / "stable-idempotency.md"
            path.write_text(path.read_text(encoding="utf8") + "\nnew body", encoding="utf8")
            indexing.rebuild(root, db)
            return original(request, cards)

        monkeypatch.setattr(api, "decide", race)
        r = c.post("/api/export", json=p)
        assert r.status_code == 200
        assert r.json()["content_revision"] == a["content_revision"]
        assert "new body" not in r.json()["comparison"][0]["card"]["body"]


def test_locale_exact_id_filter_and_markdown(isolated):
    root, db = isolated
    text = (root / "stable-idempotency.md").read_text(encoding="utf8").replace("locale: zh-CN", "locale: en")
    (root / "english.md").write_text(text, encoding="utf8")
    with TestClient(app, base_url="http://127.0.0.1") as c:
        assert c.get("/api/cases/stable-idempotency?locale=zh-CN").json()["locale"] == "zh-CN"
        assert c.get("/api/cases/stable-idempotency?locale=en").json()["locale"] == "en"
        assert c.get("/api/cases?validation=local_passed").json() == []
        assert c.get("/api/cases?validation=nonsense").status_code == 422
        q = {
            "question": "工单",
            "locale": "en",
            "validation": "not_run",
            "constraints": {"approval": "yes", "idempotency": "yes"},
        }
        a = c.post("/api/decision", json=q).json()
        ids = [x["card"]["id"] for x in a["candidates"]]
        assert len(ids) == len(set(ids))
        r = c.post("/api/export", json=export_payload(q, a))
        assert r.status_code == 200
        card = r.json()["comparison"][0]["card"]
        assert card["content_revision"] == a["content_revision"]
        assert card["locale"] == "en"
        three = export_payload(q, a)
        three["selected"] = ["stable-idempotency", "approval-before-effect", "session-checkpoint"]
        compared = c.post("/api/export", json=three).json()["comparison"]
        assert len(compared) == 3
        assert len({item["card"]["id"] for item in compared}) == 3
        assert next(item for item in compared if item["card"]["id"] == "stable-idempotency")["card"]["locale"] == "en"
        md = c.post("/api/export", json=export_payload(q, a, "markdown")).text
        for value in [
            "source_checked",
            "not_run",
            "current",
            a["content_revision"],
            "unknown",
            "not_run",
            card["review"]["scope"],
            "independent",
        ]:
            assert value in md
        bad = export_payload(q, a)
        bad["selected"] = [card["title"]]
        assert c.post("/api/export", json=bad).status_code == 422


def test_validation_synthetic_states(cards):
    for state in ["not_run", "local_passed", "independently_reproduced"]:
        fixtures = copy.deepcopy(cards)
        fixtures[0]["validation"] = {"status": state, "environment": "synthetic fixture", "command": "fixture only", "result": "fixture only; no actual upstream run"}
        fixtures[0] = Card.model_validate(fixtures[0]).model_dump()
        r = decide(Question(question="工单 检索 工具", validation=state), fixtures)
        assert r["candidates"]
        assert all(c["card"]["validation"]["status"] == state for c in r["candidates"])


def test_markdown_states(cards):
    r = decide(Question(question="工单", constraints={"approval": "yes", "idempotency": "yes"}), cards)
    report, md = export_report(r, ["stable-idempotency"])
    for value in [
        "source_checked",
        "not_run",
        "current",
        report.get("content_revision", "MISSING"),
        "适用版本",
        "原创实验",
    ]:
        assert value in md


def test_claim_mapping(cards):
    b = next(c for c in cards if c["id"] == "bound-approval")
    p = next(c for c in cards if c["id"] == "permission-filter")
    assert set(b["claims"][0]["evidence_ids"]) == {"langgraph-types", "haystack-tool"}
    assert set(p["claims"][0]["evidence_ids"]) == {"haystack-bm25", "haystack-embedding"}
    assert "61-65" in p["sources"][0]["lines"]
    assert "75-79" in p["sources"][1]["lines"]


@pytest.mark.parametrize("size", [31999, 32000, 32001, 40075])
@pytest.mark.parametrize("streamed", [False, True])
def test_body_real_entry(client, size, streamed):
    base = json.dumps({"question": "工具"}, ensure_ascii=False).encode()
    body = base + b" " * (size - len(base))
    data = iter([body[:100], body[100:]]) if streamed else body
    r = client.post("/api/decision", content=data, headers={"Content-Type": "application/json"})
    assert r.status_code == (413 if size > 32000 else 200)
    assert client.post("/api/decision", json={"question": "工具"}).status_code == 200


def test_encoding_and_element_limits(client):
    assert client.post("/api/decision", content=b"{}", headers={"Content-Encoding": "gzip"}).status_code == 415
    assert (
        client.post(
            "/api/decision", json={"question": "工具", "constraints": {"forbidden_components": ["x" * 81]}}
        ).status_code
        == 422
    )


def test_asgi_actual_bytes_and_disconnect():
    async def run(chunks, headers=None, disconnect=False):
        events = []
        reads = 0

        async def receive():
            nonlocal reads
            reads += 1
            if chunks:
                data = chunks.pop(0)
                return {"type": "http.request", "body": data, "more_body": bool(chunks) or disconnect}
            return {"type": "http.disconnect"}

        async def send(event):
            events.append(event)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/decision",
            "raw_path": b"/api/decision",
            "query_string": b"",
            "root_path": "",
            "headers": [(b"host", b"127.0.0.1"), (b"content-type", b"application/json"), *(headers or [])],
            "client": ("127.0.0.1", 1),
            "server": ("127.0.0.1", 18765),
        }
        await app(scope, receive, send)
        return events, reads

    events, reads = asyncio.run(run([b" " * 20000, b" " * 20000, b"never read"], [(b"content-length", b"1")]))
    assert [x["status"] for x in events if x["type"] == "http.response.start"] == [413]
    assert reads == 2
    events, _ = asyncio.run(run(["中".encode() * 11000]))
    assert events[0]["status"] == 413
    events, _ = asyncio.run(run([b"{"], disconnect=True))
    assert not any(x.get("status") == 200 for x in events)


def test_clarified_positive_recall_without_rewriting_frozen(cards):
    from pathlib import Path
    frozen = json.loads(Path("tests/scenarios.json").read_text(encoding="utf8"))
    answers = [row for row in frozen["scenarios"] if row["kind"] == "answerable"]
    assert len(answers) == 6
    for row in answers:
        constraints = {**row["constraints"], "approval": "yes"}
        result = decide(Question(question=row["question"], cluster=row["cluster"], constraints=constraints), cards)
        supported = {c["card"]["id"] for c in result["candidates"] if c["status"] == "compatible"}
        assert set(row["expected"]).issubset(supported)
        assert not any(c["status"] == "incompatible" and c["card"]["id"] in row["expected"] for c in result["candidates"])


def test_atomic_rebuild_complete_views(isolated):
    from concurrent.futures import ThreadPoolExecutor
    root, db = isolated
    indexing.rebuild(root, db)
    original = indexing.read_cards(db)
    for p in root.glob("*.md"):
        p.write_text(p.read_text(encoding="utf8").replace("revision: 1", "revision: 3").replace("revision: 2", "revision: 3"), encoding="utf8")
    def read_repeatedly():
        return [indexing.read_cards(db) for _ in range(20)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        reads = pool.submit(read_repeatedly)
        indexing.rebuild(root, db)
        observed = reads.result()
    updated = indexing.read_cards(db)
    assert updated != original
    assert all(view == original or view == updated for view in observed)


def test_excluded_selection_with_valid_result_marker(client):
    q = {"question": "工单", "constraints": {"approval": "yes", "idempotency": "no"}}
    result = client.post("/api/decision", json=q).json()
    assert next(c for c in result["candidates"] if c["card"]["id"] == "stable-idempotency")["status"] == "incompatible"
    response = client.post("/api/export", json=export_payload(q, result))
    assert response.status_code == 422
    assert "Excluded" in response.json()["detail"]
