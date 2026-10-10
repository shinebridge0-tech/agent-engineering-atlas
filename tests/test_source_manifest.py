import json
from backend.content import ROOT, load_all


def test_checked_sources_map_to_observed_fetches():
    ledger = json.loads((ROOT / 'docs/SOURCE_ACQUISITION.json').read_text(encoding='utf-8'))
    for card in load_all():
        for source in card.sources:
            if source.source_type == 'local_experiment':
                continue
            entries = [x for x in ledger['items'] if x['url'] == source.url and x['status'] == 200]
            assert any(x['sha256'] == source.content_hash for x in entries)
            if source.source_type == 'code':
                assert source.revision in source.url
                assert source.path in source.url
    assert ledger['requests'] <= 100 and ledger['bytes'] <= 50_000_000
