"""Reconstruct the previously examined directives; exclude bulk discovery indexes."""
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = [Path('/tmp/eu-update-chain-research-scratch')] + [Path(f'/tmp/eu-update-chain-round{i}') for i in (2, 3, 4)]
paths = [ROOT / 'docs/data/findings.json'] + [
    p for folder in FOLDERS for p in folder.glob('*.json')
    if not any(x in p.name for x in ('baseline', 'index', 'detail', 'expression', 'files', 'meta', 'link-health'))
]
acts = {}

def add(year, number, source, basis):
    year = int(year) + (1900 if len(str(year)) == 2 else 0)
    ident = f'{year}/{int(number)}'
    row = acts.setdefault(ident, {'id': ident, 'celex': f'3{year}L{int(number):04d}', 'priorNotes': [], 'inventoryBasis': []})
    if source not in row['priorNotes']:
        row['priorNotes'].append(source)
    if basis not in row['inventoryBasis']:
        row['inventoryBasis'].append(basis)

def fields(value, source):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ('baseAct', 'amendingAct') and isinstance(child, str):
                for year, number in re.findall(r'(\d{4}|9\d)/(\d+)', child):
                    add(year, number, source, key)
            fields(child, source)
    elif isinstance(value, list):
        for child in value:
            fields(child, source)

for path in paths:
    raw = path.read_text()
    fields(json.loads(raw), path.name)
    decoded = unquote(raw)
    for year, number in re.findall(r'3(\d{4})L(\d{4})', decoded, re.I):
        add(year, number, path.name, 'case-specific EU directive identifier')
    for year, number in re.findall(r'/eli/dir(?:_del|_impl)?/(\d{4})/(\d+)', decoded):
        add(year, number, path.name, 'case-specific official directive link')

for ident, source in [('2000/14', 'research-denmark-noise-control.json'), ('2000/78', 'reference-controls.json'), ('2012/29', 'reference-controls.json'), ('2024/1346', 'reference-controls.json')]:
    add(*ident.split('/'), source, 'explicit substantive screening note')

for ident in ('2024/2994', '2014/24', '2014/25', '2014/23', '2019/1023', '2023/2225', '2024/1416', '2019/904', '2006/118', '2014/59', '2019/879', '2019/1158'):
    add(*ident.split('/'), 'independent inventory audit', 'previous substantive screening recovered by independent audit')

# The initial reconstruction treated a regulation named in an amendment chain as
# a directive. Retain this examined EU act, with its correct document type.
acts['2024/886']['celex'] = '32024R0886'
acts['2024/886']['actType'] = 'Regulation'
for row in acts.values():
    row.setdefault('actType', 'Directive')
out = {'reconstructedAt': '2026-10-26', 'scope': 'Previously examined individual EU acts, including amending directives; excludes bulk-index-only entries and standalone corrigenda.', 'status': 'independent inventory audit complete; official identity and length validation pending', 'acts': sorted(acts.values(), key=lambda x: tuple(map(int, x['id'].split('/'))))}
dest = ROOT / 'research/act-inventory.json'
dest.parent.mkdir(exist_ok=True)
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(f'Reconstructed {len(acts)} directive identifiers in {dest}')
