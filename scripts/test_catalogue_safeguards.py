"""Black-box checks that editorial withdrawals survive validation and research merges."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CatalogueSafeguards(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='eu-catalogue-check-')
        self.root = Path(self.temporary.name)
        for directory in ('scripts', 'docs/data', 'research', 'work'):
            (self.root / directory).mkdir(parents=True)
        self.decisions = json.loads((ROOT / 'research/catalogue-decisions.json').read_text())

    def tearDown(self):
        self.temporary.cleanup()

    def write_json(self, relative, value):
        (self.root / relative).write_text(json.dumps(value))

    def run_script(self, name):
        return subprocess.run([sys.executable, str(self.root / 'scripts' / name)],
                              capture_output=True, text=True)

    def test_validator_rejects_restored_withdrawal(self):
        for relative in ('scripts/validate.py', 'docs/app.js', 'docs/index.html',
                         'docs/data/findings.json', 'research/catalogue-decisions.json'):
            shutil.copyfile(ROOT / relative, self.root / relative)
        audit_files = {path for item in self.decisions['exclusions'] + self.decisions.get('revisions', [])
                       for path in item.get('auditFiles', [])}
        for relative in audit_files:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        baseline = self.run_script('validate.py')
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        data = json.loads((self.root / 'docs/data/findings.json').read_text())
        # A past revision is historical evidence, not a requirement to list a resolved case forever.
        resolved_id = self.decisions['revisions'][0]['id']
        resolved = dict(data, findings=[row for row in data['findings'] if row['id'] != resolved_id])
        self.write_json('docs/data/findings.json', resolved)
        legitimate_removal = self.run_script('validate.py')
        self.assertEqual(legitimate_removal.returncode, 0, legitimate_removal.stderr)
        restored = dict(data['findings'][0])
        restored['id'] = self.decisions['exclusions'][0]['id']
        data['findings'].append(restored)
        self.write_json('docs/data/findings.json', data)
        rejected = self.run_script('validate.py')
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn('Withdrawn concerns restored without a new review', rejected.stderr)

    def test_later_research_bundle_cannot_hide_catalogue_correction(self):
        # Isolate the builder from ongoing researchers' temporary working files.
        source = (ROOT / 'scripts/build_coverage.py').read_text()
        work_location = "WORK = Path('/tmp/eu-update-chain-systematic')"
        self.assertIn(work_location, source, 'Update the fixture isolation when the builder working directory changes')
        source = source.replace(work_location, "WORK = ROOT / 'work'")
        (self.root / 'scripts/build_coverage.py').write_text(source)
        shutil.copyfile(ROOT / 'research/selected-acts.json', self.root / 'research/selected-acts.json')
        self.write_json('research/official-discovery.json', {'acts': []})
        self.write_json('docs/data/findings.json', {'findings': []})
        self.write_json('research/catalogue-decisions.json', self.decisions)
        decision = next(item for item in self.decisions['exclusions'] if item.get('coverageActs'))
        celex = decision['coverageActs'][0]
        self.write_json('research/stale-bundle.json', {'acts': [{
            'celex': celex,
            'countryChecks': [{'countryCode': decision['countryCode'],
                               'status': 'reviewed', 'reviewComplete': True,
                               'conclusion': 'An older research conclusion without the later correction.'}]
        }]})
        result = self.run_script('build_coverage.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        for relative in ('research/coverage.json', 'docs/data/systematic.json'):
            data = json.loads((self.root / relative).read_text())
            act = next(row for row in data['acts'] if row['celex'] == celex)
            cell = next(row for row in act['countries'] if row['countryCode'] == decision['countryCode'])
            self.assertIn(decision['reason'], cell['review']['catalogueReview'])
            self.assertEqual(cell['review']['catalogueReviewEvidence'][0]['url'], decision['evidence'][0]['url'])
            self.assertEqual(cell['findingIds'], [])
            self.assertEqual(cell['status'], 'complete')


if __name__ == '__main__':
    unittest.main()
