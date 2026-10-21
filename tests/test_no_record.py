"""Missing verification values are outstanding evidence, not competing dates."""

import copy
import csv
from pathlib import Path
import unittest

from credentialing.engine import gaps_for
from credentialing.evidence import evaluate_replies


ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ('2026-03-16', '2026-04-20', '2026-05-18')


def tables_through(batch):
    tables = {}
    for number in range(1, batch + 1):
        for path in (ROOT / f'inputs/batch-{number:02}').glob('*.csv'):
            with path.open(encoding='utf-8-sig', newline='') as stream:
                tables.setdefault(path.stem, []).extend(csv.DictReader(stream))
    return tables


class NoRecordTests(unittest.TestCase):
    def setUp(self):
        self.tables = tables_through(1)
        self.app = next(row for row in self.tables['applications']
                        if row['application_id'] == 'APP-2026-021')

    def evaluate(self, tables=None, as_of=EXPORTS[0], before=False):
        return evaluate_replies(self.app, self.tables if tables is None else tables, as_of, before)

    def entry(self, result, entry_id='ENT-2100'):
        return next(row for row in result['entry_checks'] if row['entry_id'] == entry_id)

    def residency_reply(self):
        return next(row for row in self.tables['verification-replies'] if row['reply_id'] == 'VR-2101')

    def test_real_app021_across_exports_has_no_invented_date_discrepancy(self):
        for batch, as_of in enumerate(EXPORTS, 1):
            with self.subTest(batch=batch):
                tables = tables_through(batch)
                original = copy.deepcopy(tables)
                result = self.evaluate(tables, as_of)
                check = self.entry(result)
                self.assertFalse(check['unresolved_discrepancy'])
                self.assertFalse(check['dates_verified'])
                self.assertFalse(check['accreditation_verified'])
                self.assertEqual(check['accepted_reply_ids'], [])
                self.assertTrue(check['secondary_route_candidate'])
                self.assertFalse(any(issue['kind'] == 'discrepancy' for issue in result['issues']))
                self.assertTrue(any(issue['rule'] == 'B07' and 'MSP assessment' in issue['detail']
                                    and 'does not establish that no equivalent' in issue['detail']
                                    for issue in result['issues']))
                self.assertTrue(any(issue['rule'] == 'B17/B40' and 'ENT-2100' in issue['detail']
                                    for issue in result['issues']))
                if batch > 1:
                    raw = next(row for row in check['verification_rows'] if row['reply_id'] == 'VR-2104')
                    self.assertEqual((raw['outcome'], raw['verified_from'], raw['verified_to']),
                                     ('no-record', '', ''))
                    self.assertTrue(any('VR-2104: Reply does not confirm' in f for f in check['failures']))
                    self.assertTrue(any('VR-2100: Source is not an accepted direct source' in f
                                        for f in check['failures']))
                    current = self.entry(result, 'ENT-2103')
                    self.assertEqual(current['accepted_reply_ids'], ['VR-2103'])
                    self.assertTrue(current['dates_verified'])
                gaps = gaps_for(self.app, tables, [], as_of, result['entry_checks'])
                self.assertEqual(gaps['basis'], 'declared inclusive timeline')
                self.assertFalse(gaps['issues'])
                self.assertEqual(tables, original)

    def test_no_record_cannot_extend_old_employment_scope_without_competing_facts(self):
        base = self.residency_reply()
        row = dict(base, reply_id='NO-RECORD', entry_id='ENT-2102',
                   outcome='no-record', verified_from='', verified_to='')
        self.tables['verification-replies'].append(row)
        check = self.entry(self.evaluate(), 'ENT-2102')
        self.assertFalse(check['in_scope'])
        self.assertFalse(check['unresolved_discrepancy'])
        self.assertEqual(check['verification_rows'], [row])
        row['verified_to'] = '2015-08-30'
        check = self.entry(self.evaluate(), 'ENT-2102')
        self.assertTrue(check['in_scope'])
        self.assertTrue(check['unresolved_discrepancy'])

    def test_no_record_does_not_cancel_independent_matching_verification(self):
        row = dict(self.residency_reply(), reply_id='NO-RECORD', outcome='no-record',
                   verified_from='', verified_to='')
        self.tables['verification-replies'].append(row)
        result = self.evaluate()
        check = self.entry(result, 'ENT-2101')
        self.assertEqual(check['accepted_reply_ids'], ['VR-2101'])
        self.assertTrue(check['dates_verified'])
        self.assertFalse(check['unresolved_discrepancy'])
        self.assertFalse(check['accreditation_verified'])
        retained = next(issue for issue in result['issues']
                        if 'verification-replies.csv#NO-RECORD' in issue['source_refs'])
        self.assertEqual(retained['kind'], 'pending-work')
        self.assertIn('verification-replies.csv#VR-2101', retained['source_refs'])

    def test_missing_confirmed_boundaries_do_not_verify_or_invent_conflicts(self):
        reply = self.residency_reply()
        original = dict(reply)
        for boundary in ('verified_from', 'verified_to'):
            with self.subTest(boundary=boundary):
                reply.update(original)
                reply[boundary] = ''
                check = self.entry(self.evaluate(), 'ENT-2101')
                self.assertEqual(check['accepted_reply_ids'], [])
                self.assertFalse(check['dates_verified'])
                self.assertFalse(check['unresolved_discrepancy'])
                self.assertTrue(any('does not establish the declared interval' in f
                                    for f in check['failures']))

    def test_actual_date_conflict_and_explicit_discrepancy_still_block(self):
        reply = self.residency_reply()
        original = dict(reply)
        for changes in ({'verified_to': '2005-07-01'},
                        {'outcome': 'confirmed-with-discrepancy'},
                        {'outcome': 'no-record', 'verified_from': '', 'verified_to': '2005-07-01'}):
            with self.subTest(changes=changes):
                reply.update(original)
                reply.update(changes)
                result = self.evaluate()
                check = self.entry(result, 'ENT-2101')
                self.assertTrue(check['unresolved_discrepancy'])
                self.assertFalse(check['dates_verified'])
                self.assertTrue(any(issue['kind'] == 'discrepancy' for issue in result['issues']))
                self.assertTrue(gaps_for(self.app, self.tables, [], EXPORTS[0],
                                         result['entry_checks'])['issues'])

    def test_no_record_and_actual_conflict_obey_receipt_cutoff(self):
        row = dict(self.residency_reply(), reply_id='NO-RECORD', outcome='no-record',
                   verified_from='', verified_to='2005-07-01', received_date=EXPORTS[0])
        self.tables['verification-replies'].append(row)
        self.assertFalse(self.entry(self.evaluate(before=True), 'ENT-2101')['unresolved_discrepancy'])
        self.assertTrue(self.entry(self.evaluate(), 'ENT-2101')['unresolved_discrepancy'])

    def test_partial_reply_cannot_reconcile_explicit_discrepancy_after_date_revision(self):
        current = next(row for row in self.tables['declared-history'] if row['entry_id'] == 'ENT-2101')
        revised = dict(current, revision='2', from_date='2002-07-02')
        self.tables['declared-history'].append(revised)
        self.app = dict(self.app, revision='2', revision_reason='Correct from date to 2002-07-02')
        self.residency_reply().update(verified_from='2002-07-02', verified_to='',
                                     outcome='confirmed-with-discrepancy')
        check = self.entry(self.evaluate(), 'ENT-2101')
        self.assertEqual(check['accepted_reply_ids'], [])
        self.assertTrue(check['unresolved_discrepancy'])
        self.assertFalse(check['dates_verified'])


if __name__ == '__main__':
    unittest.main()
