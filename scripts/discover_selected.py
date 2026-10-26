"""Collect compact official change-history/NIM discovery metadata, not conformity findings."""
import concurrent.futures
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTS = json.loads((ROOT / 'research/selected-acts.json').read_text())['selected']
parser = argparse.ArgumentParser()
parser.add_argument('--only', help='Comma-separated act IDs to discover and merge')
args = parser.parse_args()
if args.only:
    wanted = set(args.only.split(','))
    ACTS = [row for row in ACTS if row['id'] in wanted]
ENDPOINT = 'https://publications.europa.eu/webapi/rdf/sparql'
PREFIX = '''PREFIX cdm:<http://publications.europa.eu/ontology/cdm#>
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
PREFIX owl:<http://www.w3.org/2002/07/owl#>
PREFIX ann:<http://publications.europa.eu/ontology/annotation#>\n'''

def query(text):
    url = ENDPOINT + '?' + urllib.parse.urlencode({'query': PREFIX + text, 'format': 'application/sparql-results+json'})
    req = urllib.request.Request(url, headers={'User-Agent': 'EUUpdateChainResearch/0.1'})
    with urllib.request.urlopen(req, timeout=100) as response:
        return [{k: v['value'] for k, v in row.items()} for row in json.load(response)['results']['bindings']]

def discover(act):
    celex = act['celex']
    result = {'id': act['id'], 'celex': celex}
    try:
        rows = query('''SELECT DISTINCT ?direction ?p ?v ?relatedCelex WHERE {
 ?w cdm:resource_legal_id_celex "%s"^^xsd:string .
 { { ?w ?p ?v . BIND("out" AS ?direction) }
   UNION { ?v ?p ?w . BIND("in" AS ?direction) } }
 OPTIONAL { ?v cdm:resource_legal_id_celex ?relatedCelex }
}''' % celex)
        keep = []
        for row in rows:
            p = row['p'].rsplit('#', 1)[-1]
            if any(term in p.lower() for term in ('amend', 'corrig', 'correct', 'repeal', 'consolidat', 'derogat', 'suspend', 'exten', 'complet', 'replace', 'adapt', 'applicab', 'date_', 'title', 'in-force', 'in_force', 'transpos', 'id_celex')):
                keep.append(dict(row, predicate=p))
        result['historyMetadata'] = keep
        result['historyStatus'] = 'discovered; texts and completeness require review'
    except Exception as error:
        result['historyError'] = str(error)
    try:
        result['nationalMeasures'] = query('''SELECT DISTINCT ?nim ?country ?title ?ref ?nimCelex ?notification ?nationalEli WHERE {
 ?directive cdm:resource_legal_id_celex "%s"^^xsd:string .
 ?nim cdm:measure_national_implementing_implements_resource_legal ?directive;
      cdm:measure_national_implementing_implemented_by_country ?country .
 OPTIONAL { ?nim cdm:work_title ?title }
 OPTIONAL { ?nim cdm:measure_national_implementing_reference_member-state ?ref }
 OPTIONAL { ?nim cdm:eli ?nationalEli }
 OPTIONAL { ?nim cdm:resource_legal_id_celex ?nimCelex . FILTER(STRSTARTS(STR(?nimCelex),"7%s")) }
 OPTIONAL { ?a owl:annotatedSource ?nim;
 owl:annotatedProperty cdm:measure_national_implementing_implements_resource_legal;
 owl:annotatedTarget ?directive; ann:transposition_notification ?notification }
} ORDER BY ?country ?nim''' % (celex, celex[1:]))
        result['nationalMeasuresStatus'] = 'discovery only; does not establish transposition or conformity'
    except Exception as error:
        result['nationalMeasuresError'] = str(error)
    print(f"{celex}: {len(result.get('historyMetadata', []))} history metadata rows, {len(result.get('nationalMeasures', []))} NIM rows", flush=True)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(discover, ACTS))
if args.only and (ROOT / 'research/official-discovery.json').exists():
    previous = json.loads((ROOT / 'research/official-discovery.json').read_text())['acts']
    results = [row for row in previous if row['id'] not in wanted] + results
output = {'snapshot': '2026-10-26', 'status': 'official discovery metadata; not legal conclusions', 'source': ENDPOINT, 'nationalNotificationDates': 'Directive-specific owl:Axiom annotation; not generic national-work dates', 'acts': results}
(ROOT / 'research/official-discovery.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
