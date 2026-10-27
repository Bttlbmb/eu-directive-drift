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
index = (root / 'docs/index.html').read_text()
evidence_filter = re.search(r'<select\b[^>]*\bid="stage"[^>]*>[\s\S]*?</select>', index).group(0)
evidence_options = set(re.findall(r'<option value="([^"]+)"', evidence_filter))
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
    assert case['stage'] in evidence_options, f"Evidence type missing from the filter: {case['id']}"
    assert case['updateType'] in {'Amendment', 'Recast', 'Corrigendum', 'Replacement', 'New framework'}
    for key in ['deadline', 'evidenceDate']:
        if case[key] is not None:
            assert date.fromisoformat(case[key]) <= snapshot
        else:
            assert key == 'deadline' and case['updateType'] == 'Corrigendum' and case.get('correctionDate')
    assert len(case['sources']) >= 2, case['id']
    for source in case['sources']:
        assert all(source.get(k) for k in ['title', 'url', 'role', 'locator']), f"Source needs a pinpoint: {case['id']}"
        url = urlparse(source['url'])
        assert url.scheme == 'https' and url.netloc, source
    dates = [t['date'] for t in case['timeline']]
    assert all(t.get('event') for t in case['timeline']), f"Empty timeline event: {case['id']}"
    assert dates == sorted(dates), f"Unordered timeline: {case['id']}"
    for value in dates:
        date.fromisoformat(value + ('-01-01' if len(value) == 4 else '-01' if len(value) == 7 else ''))
    assert case['caveat'] and case['review'], case['id']
    if case.get('comparison'):
        assert all(isinstance(case['comparison'].get(key), str) and case['comparison'][key].strip()
                   for key in ('before', 'after')), f"Both comparison columns need text: {case['id']}"
    assert case.get('statusKind') in status_kinds, f"statusKind must be one of {sorted(status_kinds)}: {case['id']}"
    assert case.get('statusDetail') is None or isinstance(case['statusDetail'], str), case['id']
    assert all(t.get('who') in who_values for t in case['timeline']), f"Timeline event without a valid 'who' {sorted(who_values)}: {case['id']}"
    if case.get('baseActPublished'):
        published = date.fromisoformat(case['baseActPublished'])
        assert published <= snapshot, case['id']
        assert case['deadline'] is None or published <= date.fromisoformat(case['deadline']), f"Original act published after the deadline: {case['id']}"
print(f"Validated {len(ids)} findings, source links, required fields and timelines.")
decisions_path = root / 'research/catalogue-decisions.json'
if decisions_path.exists():
    decisions = json.loads(decisions_path.read_text())
    assert date.fromisoformat(decisions['reviewDate']) <= snapshot
    exclusions = decisions['exclusions']
    excluded_ids = [item['id'] for item in exclusions]
    assert len(excluded_ids) == len(set(excluded_ids)), 'Duplicate catalogue exclusion'
    assert not (set(excluded_ids) & ids), f"Withdrawn concerns restored without a new review: {set(excluded_ids) & ids}"
    assert all(item.get('reason') and item.get('evidence') for item in exclusions)
    revisions = decisions.get('revisions', [])
    revised_ids = [item['id'] for item in revisions]
    assert len(revised_ids) == len(set(revised_ids)), 'Duplicate catalogue revision'
    # Revision history remains useful after a case is later resolved and removed.
    for item in exclusions + revisions:
        assert item.get('reason') and item.get('auditFiles'), f"Undocumented decision: {item['id']}"
        for path in item['auditFiles']:
            assert (root / path).is_file(), f"Missing audit record: {path}"
    for item in exclusions:
        for source in item['evidence']:
            assert source.get('locator'), f"Withdrawal source needs a pinpoint: {item['id']}"
            url = urlparse(source['url'])
            assert url.scheme == 'https' and url.netloc, source
    print(f"Validated {len(excluded_ids)} documented exclusions against the public catalogue.")
ledger_path = root / 'docs/data/systematic.json'
if ledger_path.exists():
    ledger = json.loads(ledger_path.read_text())
    assert len(ledger['acts']) == 25
    assert len({act['celex'] for act in ledger['acts']}) == 25
    cells = [cell for act in ledger['acts'] for cell in act['countries']]
    assert len(cells) == 675
    for act in ledger['acts']:
        assert len({cell['countryCode'] for cell in act['countries']}) == 27
        for cell in act['countries']:
            assert cell['status'] in {'complete', 'in-progress', 'pending'}
            assert cell['status'] != 'complete' or cell['review'].get('reviewComplete') is True
            assert set(cell['findingIds']) <= ids
    assert ledger['counts']['complete'] == sum(cell['status'] == 'complete' for cell in cells)
    assert ledger['counts']['inProgress'] == sum(cell['status'] == 'in-progress' for cell in cells)
    if decisions_path.exists():
        acts_by_celex = {act['celex']: act for act in ledger['acts']}
        for item in exclusions:
            for celex in item.get('coverageActs', []):
                if celex not in acts_by_celex:
                    continue  # A later selection may cover a different set of directives.
                act = acts_by_celex[celex]
                cell = next(cell for cell in act['countries'] if cell['countryCode'] == item['countryCode'])
                assert item['reason'] in cell.get('review', {}).get('catalogueReview', ''), f"Catalogue correction missing from coverage: {item['id']}"
    print('Validated the 25-directive, 27-country review ledger and its completion labels.')
