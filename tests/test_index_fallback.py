import sqlite3
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from backend import indexing
from backend.app import app
from backend.content import CONTENT


def test_fts_unavailable_is_diagnostic_and_search_works(tmp_path):
    real = sqlite3.connect
    class Connection:
        def __init__(self, *args, **kwargs):
            self.connection = real(*args, **kwargs)
        def execute(self, sql, *args):
            if 'fts5' in sql:
                raise sqlite3.OperationalError('fts unavailable')
            return self.connection.execute(sql, *args)
        def __enter__(self):
            return self.connection.__enter__()
        def __exit__(self, *args):
            return self.connection.__exit__(*args)
        def close(self):
            self.connection.close()
    with patch.object(indexing.sqlite3, 'connect', Connection):
        result = indexing.rebuild(CONTENT, tmp_path / 'index.db')
    assert result['fts5_available'] is False
    assert len(indexing.read_cards(tmp_path / 'index.db')) == 10


def test_bad_content_restart_uses_previous_index():
    from backend import app as module
    indexing.rebuild()
    with patch.object(module, 'rebuild', side_effect=ValueError('bad content')):
        with TestClient(app, base_url='http://127.0.0.1') as client:
            assert 'previous index' in client.get('/api/health').json()['index_warning']
            assert len(client.get('/api/cases').json()) == 10


def test_first_start_invalid_content_fails(tmp_path):
    from backend import app as module
    with patch.object(module, 'rebuild', side_effect=ValueError('bad content')), patch.object(indexing, 'DB', tmp_path / 'missing.db'):
        with pytest.raises(ValueError, match='bad content'):
            with TestClient(app, base_url='http://127.0.0.1'):
                pass
