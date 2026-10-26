"""Measure original English EU publications without retaining source archives."""
import concurrent.futures
import argparse
import hashlib
import io
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'research/act-lengths.json'
POOL = json.loads((ROOT / 'research/act-inventory.json').read_text())['acts']
parser = argparse.ArgumentParser()
parser.add_argument('--only', help='Comma-separated act IDs to remeasure and merge into an existing result')
args = parser.parse_args()
if args.only:
    wanted = set(args.only.split(','))
    POOL = [row for row in POOL if row['id'] in wanted]
ENDPOINT = 'https://publications.europa.eu/webapi/rdf/sparql'

def get(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'EUUpdateChainResearch/0.1', 'Accept': '*/*'})
            with urllib.request.urlopen(req, timeout=80) as response:
                return response.read(), response.headers.get('Content-Type', '')
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))

query = '''PREFIX cdm:<http://publications.europa.eu/ontology/cdm#>
SELECT DISTINCT ?c ?i ?mt WHERE {
 ?w cdm:resource_legal_id_celex ?c.
 FILTER(STR(?c) IN (%s))
 ?e cdm:expression_belongs_to_work ?w;
    cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG>.
 ?m cdm:manifestation_manifests_expression ?e; cdm:manifestation_type ?mt.
 ?i cdm:item_belongs_to_manifestation ?m.
}''' % ','.join(json.dumps(row['celex']) for row in POOL)
url = ENDPOINT + '?' + urllib.parse.urlencode({'query': query, 'format': 'application/sparql-results+json'})
metadata = json.loads(get(url)[0])['results']['bindings']
by_id = {}
for row in metadata:
    by_id.setdefault(row['c']['value'], []).append({'url': row['i']['value'].replace('http://', 'https://', 1), 'format': row['mt']['value'].rsplit('/', 1)[-1]})

def measure(row):
    result = dict(row)
    options = sorted(by_id.get(row['celex'], []), key=lambda x: {'xhtml': 0, 'html': 1, 'html_simpl': 2, 'pdf': 3, 'pdfa1a': 4}.get(x['format'], 20))
    errors = []
    for option in options:
        if option['format'] not in ('xhtml', 'html', 'html_simpl', 'pdf', 'pdfa1a'):
            continue
        try:
            raw, content_type = get(option['url'])
            if raw.startswith(b'%PDF'):
                text = subprocess.run(['pdftotext', '-layout', '-', '-'], input=raw, capture_output=True, check=True).stdout.decode('utf-8')
                info = subprocess.run(['pdfinfo', '-'], input=raw, capture_output=True).stdout.decode('utf-8')
                pages = re.search(r'^Pages:\s+(\d+)', info, re.M)
                if pages:
                    result['pages'] = int(pages.group(1))
            else:
                soup = BeautifulSoup(raw, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                # Annexes are often siblings of the first eli-container. Taking
                # only the first container silently truncates the publication.
                containers = [node for node in soup.select('.eli-container') if not node.find_parent(class_='eli-container')]
                text = ' '.join(node.get_text(' ', strip=True) for node in containers) if containers else (soup.body or soup).get_text(' ', strip=True)
                if re.search(r'>\s*(TABLE|PICFILE)\b', text, re.I):
                    raise ValueError('Legacy HTML omits table/image content; use another original manifestation')
            if len(text) < 200 or "verify that you're not a robot" in text.lower():
                raise ValueError('No legislative body retrieved')
            words = re.findall(r"\b\w+(?:[’'-]\w+)*\b", text, flags=re.UNICODE)
            result.update({'wordCount': len(words), 'characterCount': len(text), 'source': option['url'], 'format': option['format'], 'sourceBytes': len(raw), 'textSha256': hashlib.sha256(text.encode()).hexdigest(), 'opening': text[:480], 'measurementStatus': 'measured'})
            print(f"{row['celex']} {len(words)} words", flush=True)
            return result
        except Exception as error:
            errors.append(str(error)[:180])
    result.update({'measurementStatus': 'unavailable', 'errors': errors, 'formatsLocated': options})
    print(f"{row['celex']} unavailable: {errors}", flush=True)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(measure, POOL))
if args.only and DEST.exists():
    previous = json.loads(DEST.read_text())['acts']
    results = [row for row in previous if row['id'] not in wanted] + results
results.sort(key=lambda r: (r.get('wordCount', 10**10), r['celex']))
output = {'date': '2026-10-26', 'measurementVersion': 2, 'measure': 'Original official English publication word count: all outermost eli-container blocks including recitals, provisions, annexes and notes, counted once; whole body fallback for older unstructured texts. Standalone corrigenda excluded. Unicode words/numbers counted. Script/style/navigation elements excluded. Counts require independent ranking audit.', 'selectionStatus': 'provisional', 'measured': sum(r['measurementStatus'] == 'measured' for r in results), 'acts': results}
DEST.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(f'Saved {output["measured"]}/{len(results)} measurements to {DEST}', flush=True)
