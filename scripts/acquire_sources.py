"""Finite allowlisted read-only fetch. Never imports or executes fetched content."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone
import httpx

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.local' / 'sources'
LEDGER = ROOT / 'docs' / 'SOURCE_ACQUISITION.json'
CACHE.mkdir(parents=True, exist_ok=True)
ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {'requests': 0, 'bytes': 0, 'items': []}

def fetch(url, name):
    parsed = urlparse(url)
    allowed_repos = ('langchain-ai/langgraph', 'langchain-ai/langchain', 'deepset-ai/haystack')
    if parsed.scheme != 'https' or parsed.hostname not in ['api.github.com', 'raw.githubusercontent.com', 'docs.langchain.com']:
        raise RuntimeError('source outside allowlist')
    if parsed.hostname == 'api.github.com' and not any(parsed.path.startswith('/repos/' + repo + '/') for repo in allowed_repos):
        raise RuntimeError('repository outside allowlist')
    if parsed.hostname == 'raw.githubusercontent.com' and not any(parsed.path.startswith('/' + repo + '/') for repo in allowed_repos):
        raise RuntimeError('repository outside allowlist')
    if Path(name).name != name:
        raise RuntimeError('cache path rejected')
    cached = next((x for x in ledger['items'] if x['url'] == url and x['status'] == 200), None)
    if cached:
        raw = (CACHE / cached['cache']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != cached['sha256']:
            raise RuntimeError('cache hash mismatch')
        return raw.decode('utf-8')
    for attempt in range(3):
        if ledger['requests'] >= 100 or ledger['bytes'] >= 50_000_000:
            raise RuntimeError('budget exhausted')
        ledger['requests'] += 1
        LEDGER.write_text(json.dumps(ledger,indent=2),encoding='utf-8')
        try:
            with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
                with client.stream('GET', url, headers={'User-Agent': 'AgentAtlas-local-source-check'}) as response:
                    chunks=[]
                    for chunk in response.iter_bytes():
                        ledger['bytes'] += len(chunk)
                        if ledger['bytes'] > 50_000_000:
                            raise RuntimeError('byte budget exhausted')
                        chunks.append(chunk)
                    raw=b''.join(chunks)
                    item={'url':url,'status':response.status_code,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cache':name,'observed_at':datetime.now(timezone.utc).isoformat()}
                    ledger['items'].append(item)
                    LEDGER.write_text(json.dumps(ledger,indent=2),encoding='utf-8')
                    print(response.status_code, name, len(raw), flush=True)
                    if response.status_code == 429:
                        raise RuntimeError('rate limited; stop')
                    if response.is_redirect:
                        return fetch(urljoin(url, response.headers['location']),name)
                    if response.status_code == 404:
                        raise RuntimeError('source not found; do not retry unchanged path')
                    response.raise_for_status()
                    (CACHE/name).write_bytes(raw)
                    return raw.decode('utf-8')
        except httpx.HTTPError as exc:
            ledger['items'].append({'url':url,'status':'error','error':type(exc).__name__,'observed_at':'2026-10-10'})
            LEDGER.write_text(json.dumps(ledger,indent=2),encoding='utf-8')
            if attempt==2:
                raise

if __name__ == '__main__':
    pins={}
    for repo in ['langchain-ai/langgraph','deepset-ai/haystack']:
        pins[repo]=json.loads(fetch('https://api.github.com/repos/'+repo+'/commits/main',repo.split('/')[1]+'-commit.json'))['sha']
    targets=[
        ('langchain-ai/langgraph','libs/langgraph/langgraph/types.py','langgraph-types.txt'),
        ('langchain-ai/langgraph','libs/langgraph/langgraph/pregel/_retry.py','langgraph-retry.txt'),
        ('deepset-ai/haystack','haystack/components/retrievers/in_memory/bm25_retriever.py','haystack-bm25.txt'),
        ('deepset-ai/haystack','haystack/components/retrievers/in_memory/embedding_retriever.py','haystack-embedding.txt'),
        ('deepset-ai/haystack','haystack/components/joiners/document_joiner.py','haystack-joiner.txt'),
        ('deepset-ai/haystack','haystack/tools/tool.py','haystack-tool.txt'),
    ]
    for repo,path,name in targets:
        fetch('https://raw.githubusercontent.com/'+repo+'/'+pins[repo]+'/'+path,name)
    for slug in ['interrupts']:
        fetch('https://docs.langchain.com/oss/python/langgraph/'+slug,slug+'.html')
    (CACHE/'pins.json').write_text(json.dumps(pins),encoding='utf-8')
