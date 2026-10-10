import socket
import pytest
from fastapi.testclient import TestClient
from backend.app import app

@pytest.fixture
def client():
    with TestClient(app,base_url="http://127.0.0.1") as c:
        yield c

def test_offline_api_export(client,monkeypatch):
    def denied(*a,**kw):
        raise AssertionError("Product attempted outbound network")
    monkeypatch.setattr(socket,"create_connection",denied)
    monkeypatch.setattr(socket.socket,"connect",denied)
    request={"question":"工单恢复", "constraints":{"idempotency":"yes"}}
    result=client.post("/api/decision",json=request).json()
    selected=[c["card"]["id"] for c in result["candidates"] if c["status"]!="incompatible"][:2]
    r=client.post("/api/export",json={"request":request,"selected":selected,"format":"json","content_revision":result["content_revision"],"result_id":result["result_id"]})
    assert r.status_code==200
    assert r.json()["question"]=="工单恢复"
    assert r.headers["Content-Disposition"].startswith("attachment")
    assert client.get("/api/cases").status_code==200
    assert client.get("/api/health").json()["model_api"]=="disabled"

def test_boundaries(client):
    assert client.get('/api/health',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/api/decision',json={'question':'工具'},headers={'Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/decision',json={'question':'x'*1001}).status_code==422
    assert client.post('/api/decision',json={'question':''}).status_code==422
    assert client.post('/api/decision',json={'question':'工具','url':'https://evil.example'}).status_code==422
    assert client.get('/api/cases/not-found').status_code==404
    assert client.get('/api/cases/../../AGENTS.md').status_code==404
    assert client.get('/api/health').headers['Content-Security-Policy'].startswith("default-src 'self'")
    assert client.post('/api/export',json={'request':{'question':'工单'},'selected':['not-a-candidate'],'format':'json'}).status_code==422
    assert client.post('/api/export',json={'request':{'question':'工单'},'selected':[],'format':'json','path':'../../escape'}).status_code==422
    assert client.post('/api/export',json={'request':{'question':'工单','constraints':{'idempotency':'no'}},'selected':['stable-idempotency'],'format':'json'}).status_code==422
