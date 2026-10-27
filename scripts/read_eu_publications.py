"""Temporary source reader for full original/corrigendum bodies; no project archive."""
import argparse
import concurrent.futures
import json
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument('celex', nargs='+')
parser.add_argument('--output', required=True)
args = parser.parse_args()
prefix = 'PREFIX cdm:<http://publications.europa.eu/ontology/cdm#> PREFIX xsd:<http://www.w3.org/2001/XMLSchema#> '
query = prefix + '''SELECT DISTINCT ?c ?lang ?mt ?item WHERE {
 VALUES ?c { %s }
 ?w cdm:resource_legal_id_celex ?c .
 ?e cdm:expression_belongs_to_work ?w; cdm:expression_uses_language ?lang .
 FILTER(CONTAINS(STR(?c),"R(") || ?lang=<http://publications.europa.eu/resource/authority/language/ENG>)
 ?m cdm:manifestation_manifests_expression ?e; cdm:manifestation_type ?mt .
 ?item cdm:item_belongs_to_manifestation ?m . }''' % ' '.join(json.dumps(c)+'^^xsd:string' for c in args.celex)
endpoint = 'https://publications.europa.eu/webapi/rdf/sparql'
url = endpoint + '?' + urllib.parse.urlencode({'query': query, 'format': 'application/sparql-results+json'})

def get(url):
    req = urllib.request.Request(url.replace('http://', 'https://', 1), headers={'User-Agent': 'EUUpdateChainResearch/0.1'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()

metadata = json.loads(get(url))['results']['bindings']
groups = {}
for row in metadata:
    key = (row['c']['value'], row['lang']['value'].rsplit('/', 1)[-1])
    groups.setdefault(key, []).append({k: v['value'] for k, v in row.items()})

def read(pair):
    key, versions = pair
    errors = []
    for row in sorted(versions, key=lambda r: {'xhtml': 0, 'html': 1, 'pdf': 2, 'pdfa1a': 3, 'pdfa1b': 3, 'pdfa2b': 3}.get(r['mt'].rsplit('/', 1)[-1], 20)):
        fmt = row['mt'].rsplit('/', 1)[-1]
        if fmt not in ('xhtml', 'html', 'pdf') and not fmt.startswith('pdfa'):
            continue
        try:
            raw = get(row['item'])
            if raw.startswith(b'%PDF'):
                text = subprocess.run(['pdftotext', '-layout', '-', '-'], input=raw, capture_output=True, check=True).stdout.decode()
            else:
                soup = BeautifulSoup(raw, 'html.parser')
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                nodes = [n for n in soup.select('.eli-container') if not n.find_parent(class_='eli-container')]
                text = '\n'.join(n.get_text('\n', strip=True) for n in nodes) if nodes else (soup.body or soup).get_text('\n', strip=True)
                if re.search(r'>\s*(TABLE|PICFILE)\b|PLATZ FÜR EINE TABELLE|SPAZIO PER TABELLA|ΘΕΣΗ Π[ΗΙ]ΝΑΚΑ', text, re.I):
                    raise ValueError('Incomplete legacy HTML')
            return {'celex': key[0], 'language': key[1], 'source': row['item'].replace('http://', 'https://', 1), 'format': fmt, 'text': text}
        except Exception as error:
            errors.append(str(error)[:180])
    if any('Incomplete legacy HTML' in error for error in errors):
        language = {'DEU':'DE', 'ITA':'IT', 'ELL':'EL'}.get(key[1])
        if language:
            fallback = 'https://eur-lex.europa.eu/legal-content/' + language + '/TXT/PDF/?uri=CELEX:' + urllib.parse.quote(key[0])
            try:
                raw = get(fallback)
                if not raw.startswith(b'%PDF'):
                    raise ValueError('Official PDF fallback did not return PDF')
                text = subprocess.run(['pdftotext', '-layout', '-', '-'], input=raw, capture_output=True, check=True).stdout.decode()
                return {'celex':key[0], 'language':key[1], 'source':fallback, 'format':'pdf', 'text':text}
            except Exception as error:
                errors.append(str(error)[:180])
    return {'celex': key[0], 'language': key[1], 'errors': errors}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    docs = list(pool.map(read, groups.items()))
Path(args.output).write_text(json.dumps(docs, ensure_ascii=False, indent=2) + '\n')
print(f'Read {sum("text" in d for d in docs)}/{len(docs)} publications into temporary working material.')
