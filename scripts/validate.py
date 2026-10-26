"""Validate the small editorial dataset before serving or sharing it."""
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

root = Path(__file__).resolve().parents[1]
data = json.loads((root / 'docs/data/findings.json').read_text())
required = {'id', 'title', 'country', 'countryCode', 'topic', 'baseAct', 'amendingAct',
            'celex', 'updateType', 'deadline', 'stage', 'statusLabel', 'evidenceDate',
            'summary', 'euChange', 'nationalGap', 'nationalLaw', 'provisions',
            'consequence', 'caveat', 'timeline', 'sources', 'review', 'recordKind', 'catalogueStatus', 'priorRecognition', 'recognizedBy', 'recognitionNote'}
app = (root / 'docs/app.js').read_text()
status_kinds = set(re.findall(r"(\w+):'", re.search(r"const statusKinds = \{(.*?)\};", app).group(1)))
who_values = {'eu', 'national', 'court', 'commission', 'check', 'commentary'}
ids = set()
snapshot = date.fromisoformat(data['snapshot'])
assert data['scope'] == 'unresolved-only'
for case in data['findings']:
    assert required <= case.keys(), f"Missing fields in {case.get('id')}: {required-case.keys()}"
    assert case['id'] not in ids, f"Duplicate ID: {case['id']}"
    ids.add(case['id'])
    assert case['catalogueStatus'] in {'open', 'review'}
    assert case['recordKind'] in {'finding', 'lead'}
    assert case['priorRecognition'] in {'recognized', 'not-located'}
    assert isinstance(case['recognizedBy'], list)
    assert bool(case['recognizedBy']) == (case['priorRecognition'] == 'recognized')
    assert case['recognitionNote']
    assert case['stage'] in {'judgment', 'commission', 'national', 'research', 'government'}
    assert case['updateType'] in {'Amendment', 'Recast', 'Corrigendum', 'Replacement', 'New framework'}
    for key in ['deadline', 'evidenceDate']:
        if case[key] is not None:
            assert date.fromisoformat(case[key]) <= snapshot
        else:
            assert key == 'deadline' and case['updateType'] == 'Corrigendum' and case.get('correctionDate')
    assert len(case['sources']) >= 2, case['id']
    for source in case['sources']:
        assert all(source.get(k) for k in ['title', 'url', 'role'])
        url = urlparse(source['url'])
        assert url.scheme == 'https' and url.netloc, source
    dates = [t['date'] for t in case['timeline']]
    assert all(t.get('event') for t in case['timeline']), f"Empty timeline event: {case['id']}"
    assert dates == sorted(dates), f"Unordered timeline: {case['id']}"
    for value in dates:
        date.fromisoformat(value + ('-01-01' if len(value) == 4 else '-01' if len(value) == 7 else ''))
    assert case['caveat'] and case['review'], case['id']
    assert case.get('statusKind') in status_kinds, f"statusKind must be one of {sorted(status_kinds)}: {case['id']}"
    assert case.get('statusDetail') is None or isinstance(case['statusDetail'], str), case['id']
    assert all(t.get('who') in who_values for t in case['timeline']), f"Timeline event without a valid 'who' {sorted(who_values)}: {case['id']}"
    if case.get('baseActPublished'):
        published = date.fromisoformat(case['baseActPublished'])
        assert published <= snapshot, case['id']
        assert case['deadline'] is None or published <= date.fromisoformat(case['deadline']), f"Original act published after the deadline: {case['id']}"
print(f"Validated {len(ids)} findings, source links, required fields and timelines.")
