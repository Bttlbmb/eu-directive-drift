"""Optional, non-authoritative source availability check. No evidence downloads retained."""
import concurrent.futures
import json
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / 'docs/data/findings.json').read_text())
urls = sorted({s['url'] for r in data['findings'] for s in r['sources']})

def check(url):
    request = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'EUUpdateChain-MVP-LinkCheck/0.1'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, url
    except urllib.error.HTTPError as error:
        return error.code, url
    except Exception as error:
        return type(error).__name__, url

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(check, urls))
for status, url in results:
    print(f'{status} {url}')
print('HEAD status only. Anti-bot responses and redirects do not establish whether a source is valid.')
