from fastapi.testclient import TestClient
from backend.app import app
from backend.content import Card, load_card
from pathlib import Path
import pytest

def test_health():
    with TestClient(app,base_url="http://127.0.0.1") as client:
        assert client.get('/api/health').json()['model_api'] == 'disabled'

def test_invalid_fixture():
    with pytest.raises(Exception):
        Card.model_validate({'id':'invalid','schema_version':'1.0'})


def test_valid_fixture():
    assert load_card(Path('tests/fixtures/valid.md'), Path('tests/fixtures')).id == 'stable-idempotency'

def test_invalid_markdown():
    with pytest.raises(Exception):
        load_card(Path('tests/fixtures/invalid.md'), Path('tests/fixtures'))
