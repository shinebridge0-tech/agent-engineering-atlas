import json
import shutil
import pytest
import yaml
from backend.content import CONTENT, Card, load_all, load_card
from backend.indexing import rebuild, read_cards
from backend.decision import Constraints, Question, classify, decide, export_report

@pytest.fixture
def cards():
    return [c.model_dump() for c in load_all()]

def test_qualified_content():
    cards = load_all()
    assert len(cards) == 10
    assert {c.problem_cluster for c in cards} == {"retrieval", "recovery", "safety"}
    assert all(c.review.status == "source_checked" for c in cards)
    assert len({s.repo for c in cards for s in c.sources if s.source_type == "code"}) >= 2
    for c in cards:
        for claim in c.claims:
            assert claim.evidence_ids

def test_invalid_evidence(cards):
    cards[0]["claims"][0]["evidence_ids"] = ["missing"]
    with pytest.raises(ValueError):
        Card.model_validate(cards[0])

def test_duplicate_and_atomic_fallback(tmp_path):
    root=tmp_path / "content"
    root.mkdir()
    src=CONTENT / "stable-idempotency.md"
    shutil.copy(src, root / "one.md")
    db=tmp_path / "index.db"
    assert rebuild(root,db)["count"] == 1
    original=read_cards(db)
    shutil.copy(src, root / "two.md")
    with pytest.raises(ValueError,match="duplicate"):
        rebuild(root,db)
    assert read_cards(db)==original
    (root / "two.md").write_text("---\n!!python/object/apply:os.system ['echo BAD']\n---",encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        rebuild(root,db)
    assert read_cards(db)==original
    (root / "two.md").unlink()
    db.unlink()
    assert rebuild(root,db)["count"] == 1
    changed=(root / "one.md").read_text(encoding="utf-8").replace("revision: 1","revision: 2").replace("稳定业务幂等键 + 接收方持久化去重","本地修订可见")
    (root / "one.md").write_text(changed,encoding="utf-8")
    rebuild(root,db)
    result=decide(Question(question="幂等",constraints=Constraints(idempotency="yes")),read_cards(db))
    report,md=export_report(result,["stable-idempotency"])
    assert report["comparison"][0]["card"]["revision"]==2
    assert "本地修订可见" in md

def test_traversal_and_symlink(tmp_path):
    with pytest.raises(ValueError,match="outside"):
        load_card(CONTENT / ".." / ".." / "AGENTS.md")
    outside=tmp_path / "outside.md"
    shutil.copy(CONTENT / "stable-idempotency.md",outside)
    root=tmp_path / "allowed"
    root.mkdir()
    link=root / "escape.md"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Real symlink creation unavailable: {exc}; traversal test still executed")
    with pytest.raises(ValueError,match="outside"):
        load_card(link,root)

@pytest.mark.parametrize("query,expected",[("幂等","stable-idempotency"),("工单","stable-idempotency"),("关键词","keyword-retrieval"),("bm25","keyword-retrieval"),("工具","tool-allowlist"),("authorization","tool-allowlist")])
def test_bilingual_recall(cards,query,expected):
    result=decide(Question(question=query),cards)
    assert expected in [c["card"]["id"] for c in result["candidates"]]

@pytest.mark.parametrize("query",["' OR 1=1 --",'"*: NEAR(foo) ^',"zzznonmatching","   "])
def test_special_no_match(cards,query):
    result=decide(Question(question=query),cards)
    assert result["candidates"]==[]
    assert "证据不足" in result["recommendation"]

def test_constraints_and_freshness(cards):
    card=next(c for c in cards if c["id"]=="stable-idempotency")
    assert classify(card,Constraints(idempotency="unknown"))[0]=="conditional"
    assert classify(card,Constraints(idempotency="no"))[0]=="incompatible"
    assert classify(card,Constraints(idempotency="yes",forbidden_components=["sqlite"]))[0]=="incompatible"
    assert classify(card,Constraints(idempotency="yes",data_external="unknown"))[0]=="conditional"
    assert classify(card,Constraints(idempotency="yes",approval="unknown"))[0]=="conditional"
    assert classify(card,Constraints(idempotency="yes",latency_ms=1))[0]=="conditional"
    card["freshness"]["status"]="deprecated"
    assert classify(card,Constraints(idempotency="yes"))[0]=="conditional"
    graph=next(c for c in cards if c["id"]=="approval-before-effect")
    assert classify(graph,Constraints(framework="LangGraph",framework_version="unknown",idempotency="yes"))[0]=="conditional"
    assert classify(graph,Constraints(framework="LangGraph",framework_version="999",idempotency="yes"))[0]=="conditional"

def test_comparison_insufficient_and_export(cards):
    result=decide(Question(question="reconciliation",cluster="recovery",constraints=Constraints(idempotency="no")),cards)
    report,md=export_report(result,["reconcile-before-retry"])
    assert "不足" in report["comparison_note"]
    assert json.loads(json.dumps(report))["constraints"]["idempotency"]=="no"
    assert "Evidence:" in md and "checked=2026-10-10" in md
