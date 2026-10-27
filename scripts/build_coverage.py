"""Build the 25 x 27 review ledger without treating discovery as verification."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = Path('/tmp/eu-update-chain-systematic')
selected = json.loads((ROOT / 'research/selected-acts.json').read_text())
review_snapshot = selected['snapshot']
discovery = {a['celex']: a for a in json.loads((ROOT / 'research/official-discovery.json').read_text())['acts']}
findings = json.loads((ROOT / 'docs/data/findings.json').read_text())['findings']
decisions_path = ROOT / 'research/catalogue-decisions.json'
catalogue_decisions = json.loads(decisions_path.read_text()) if decisions_path.exists() else {}
countries = [
    ('AT','AUT','Austria'),('BE','BEL','Belgium'),('BG','BGR','Bulgaria'),('HR','HRV','Croatia'),
    ('CY','CYP','Cyprus'),('CZ','CZE','Czechia'),('DK','DNK','Denmark'),('EE','EST','Estonia'),
    ('FI','FIN','Finland'),('FR','FRA','France'),('DE','DEU','Germany'),('GR','GRC','Greece'),
    ('HU','HUN','Hungary'),('IE','IRL','Ireland'),('IT','ITA','Italy'),('LV','LVA','Latvia'),
    ('LT','LTU','Lithuania'),('LU','LUX','Luxembourg'),('MT','MLT','Malta'),('NL','NLD','Netherlands'),
    ('PL','POL','Poland'),('PT','PRT','Portugal'),('RO','ROU','Romania'),('SK','SVK','Slovakia'),
    ('SI','SVN','Slovenia'),('ES','ESP','Spain'),('SE','SWE','Sweden')]
aliases = {value: code for code, iso, name in countries for value in (code,iso,name)}
aliases.update({'BUL':'BG','ELL':'GR','LAV':'LV','LIT':'LT','SLK':'SK','SLV':'SI','SPA':'ES','CES':'CZ'})
titles = {'2012/39':'Tissue and cell donor testing','2024/299':'Air-pollutant projections','2024/1416':'Cadmium quantum-dot exemptions','2024/505':'Romanian nursing qualifications','2024/2839':'Reporting simplification','2024/2994':'Financial counterparty-risk plans','2026/192':'Cobalt uses in toys','2001/113':'Fruit jams and marmalades','2024/884':'Electrical-waste financing','1996/71':'Posted workers','1993/13':'Unfair consumer terms','1998/26':'Settlement finality','1991/477':'Firearms','2019/983':'Occupational carcinogen limits: fourth amendment','1992/83':'Alcohol excise structures','2017/2398':'Occupational carcinogen limits: first amendment','2019/130':'Occupational carcinogen limits: second amendment','2008/99':'Environmental crime','2004/37':'Carcinogens at work','2003/4':'Environmental information','2000/78':'Equal treatment in employment','2009/148':'Asbestos at work','2024/869':'Lead and diisocyanate exposure','2020/1151':'Alcohol excise amendments','2022/2556':'Digital operational resilience amendments'}

reviews = {}
# Keep completed research usable after temporary working files are cleared.
prior_path = ROOT / 'research/coverage.json'
if prior_path.exists():
    for prior in json.loads(prior_path.read_text()).get('acts', []):
        recovered = dict(prior)
        recovered['countryChecks'] = [cell['review'] for cell in prior.get('countries', []) if cell.get('review')]
        reviews.setdefault(prior.get('celex'), []).append(('retained-ledger', recovered))
for path in sorted(WORK.glob('*bundle*.json')) + sorted((ROOT / 'research').glob('*bundle*.json')):
    try:
        doc = json.loads(path.read_text())
    except (ValueError, OSError):
        continue  # A researcher may be writing; the next build picks it up.
    if not isinstance(doc, dict):
        continue
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(doc.get('snapshot', ''))):
        review_snapshot = max(review_snapshot, doc['snapshot'])
    for act in doc.get('acts', []):
        reviews.setdefault(act.get('celex'), []).append((path.name, act))

def act_ids(text):
    return {f'{int(y)+(1900 if len(y)==2 else 0)}/{int(n)}' for y,n in re.findall(r'(\d{4}|9\d)/(\d+)',text)}

acts = []
for selection in selected['selected']:
    celex = selection['celex']
    row = {'id': selection['id'], 'celex': celex, 'rank': selection['rank'], 'title': titles[selection['id']],
           'wordCount': selection['wordCount'], 'originalSource': selection['source'],
           'inventoryStatus': 'pending substantive review', 'changeInventory': [], 'history': [], 'countries': []}
    country_reviews = {}
    for file, reviewed in reviews.get(celex, []):
        row['changeInventory'] = reviewed.get('changeInventory', reviewed.get('changes', row['changeInventory']))
        row['inventoryStatus'] = reviewed.get('inventoryStatus', reviewed.get('historyStatus', 'full original read; history review in progress'))
        row['history'] = reviewed.get('history', reviewed.get('historyMetadata', reviewed.get('laterChanges', row['history'])))
        for key in ('originalRead', 'originalFullTextRead', 'originalReadScope', 'qualifications', 'deadline', 'laterChangeSearch', 'dependentTransitions', 'sourceFormatAudit'):
            if key in reviewed:
                row[key] = reviewed[key]
        checks = reviewed.get('countryChecks', reviewed.get('countryRows', reviewed.get('countryMatrix', [])))
        if isinstance(checks, dict):
            checks = [dict(value, country=key) for key,value in checks.items()]
        for check in checks:
            value = check.get('countryCode', check.get('country', check.get('code')))
            code = aliases.get(value)
            if code:
                country_reviews[code] = (file, check)
    national = discovery.get(celex, {}).get('nationalMeasures', [])
    for code, iso, name in countries:
        measures = [m for m in national if m.get('country','').rsplit('/',1)[-1] in (iso, code)]
        cell = {'countryCode': code, 'country': name, 'status': 'pending',
                'discovery': {'measureCount': len({m['nim'] for m in measures}),
                              'url': f'https://eur-lex.europa.eu/legal-content/EN/NIM/?uri=CELEX%3A{celex}'},
                'findingIds': [f['id'] for f in findings if f['countryCode'] == code and (f['celex'] == celex or selection['id'] in act_ids(f['baseAct']))]}
        if code in country_reviews:
            file, check = country_reviews[code]
            cell['review'] = check
            cell['reviewNote'] = file
            status = check.get('assessmentStatus', check.get('status','pending'))
            actually_started = re.search(r'(?<![a-z])(reviewed|supported|partial|partially|inconclusive|gap|read|verified|mapped)(?![a-z])', str(status).lower())
            cell['status'] = 'complete' if check.get('reviewComplete') is True else ('in-progress' if actually_started else 'pending')
        exclusions = [item for item in catalogue_decisions.get('exclusions', [])
                      if item['countryCode'] == code and celex in item.get('coverageActs', [])]
        if exclusions:
            # Apply editorial decisions after all research merges so an older bundle cannot hide them.
            review = dict(cell.get('review', {}))
            review['catalogueReview'] = ' '.join(item['reason'] for item in exclusions)
            review['catalogueReviewEvidence'] = [
                {'title': 'Catalogue review source', 'url': source['url'],
                 'locator': source.get('locator', ''), 'assessment': source.get('finding', '')}
                for item in exclusions for source in item['evidence']]
            cell['review'] = review
        row['countries'].append(cell)
    acts.append(row)

output = {'snapshot': review_snapshot, 'selectionSnapshot': selected['snapshot'], 'status': 'in-progress', 'scope': selected['scope'],
          'selectionRule': selected['selectionRule'], 'poolCount': selected['poolCount'],
          'selectionAudit': 'Independent identity, all-annex and cutoff review; incomplete legacy tables remeasured from official PDFs.',
          'completenessRule': 'A cell is complete only when its researcher explicitly certifies every applicable changed obligation and currentness checks. NIM notifications, existing findings or an initialized row alone do not complete it.',
          'acts': acts, 'counts': {'acts': len(acts), 'countries': len(countries), 'countryActPairs': len(acts)*len(countries),
                                  'complete': sum(c['status']=='complete' for a in acts for c in a['countries']),
                                  'inProgress': sum(c['status']=='in-progress' for a in acts for c in a['countries'])}}
(ROOT / 'research/coverage.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
# Publish the comparisons and source references without duplicating NIM discovery metadata.
public_keys = {'status', 'assessmentStatus', 'legalConclusion', 'conclusion', 'assessmentScope', 'scope',
               'reviewScope', 'currentness', 'changes', 'changeAssessments', 'provisionChecks',
               'currentNationalEvidence', 'nationalSources', 'evidence', 'limitations',
               'uncertainties', 'blockers', 'independentReview', 'peerReview', 'reviewComplete',
               'nationalLaw', 'laterRemedySearch', 'completionBlocker', 'adverseReview',
               'catalogueReview', 'catalogueReviewEvidence'}
public = {key: value for key, value in output.items() if key != 'acts'}
public['acts'] = []
for act in acts:
    item = {key: value for key, value in act.items() if key not in {'history', 'countries'}}
    item['countries'] = [{key: value for key, value in cell.items() if key in {'countryCode', 'country', 'status', 'findingIds'}} |
                         {'review': {key: value for key, value in cell.get('review', {}).items() if key in public_keys}}
                         for cell in act['countries']]
    public['acts'].append(item)
(ROOT / 'docs/data/systematic.json').write_text(json.dumps(public, ensure_ascii=False, separators=(',', ':'))+'\n')
print(output['counts'])
