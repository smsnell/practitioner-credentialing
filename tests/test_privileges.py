"""Synthetic facts exercise privilege mapping without filling batch evidence gaps."""

import copy
from pathlib import Path
import unittest

from credentialing.policy import registry
from credentialing.privileges import evaluate_privileges


class PrivilegeTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.registry = registry({p.stem: p.read_text() for p in (root / 'sources').glob('*.md')})
        self.app = {'application_id': 'TEST-A', 'revision': '1', 'first_received_date': '2026-01-01'}
        self.tables = {'declared-credentials': [], 'certification-replies': [], 'privilege-requests': []}
        self.entries = [self.entry('medical-school', 'Degree — Doctor of Medicine', '2006-09-01', '2010-06-30'),
                        self.entry('residency', 'Residency — Family Medicine', '2010-07-01', '2013-06-30')]
        self.add_cert('ABFM', 'American Board of Family Medicine', 'Family Medicine')
        self.request('PRIV-FM')

    def entry(self, kind, credential, start, end, accredited=True):
        key = kind + credential
        return {'entry_id': key, 'declared': {'application_id': 'TEST-A', 'revision': '1', 'entry_type': kind},
                'accepted_reply_ids': [key], 'accreditation_verified': accredited,
                'dates_verified': True, 'unresolved_discrepancy': False,
                'verification_rows': [{'reply_id': key, 'verified_credential': credential,
                                       'verified_from': start, 'verified_to': end, 'received_date': '2026-02-01'}]}

    def add_cert(self, board, name, specialty, status='Active', expiry='2030-12-31'):
        key = 'CERT-' + str(len(self.tables['declared-credentials']))
        self.tables['declared-credentials'].append({'declaration_id': key, 'application_id': 'TEST-A', 'revision': '1',
            'credential_class': 'certification', 'issuer': name, 'jurisdiction_or_board': board})
        row = {'reply_id': key, 'application_id': 'TEST-A', 'declaration_id': key, 'board_code': board,
               'board_name': name, 'received_from': 'Certifying board — ' + name,
               'certificate_specialty': specialty, 'certification_status': status,
               'initial_certification_date': '2013-07-01', 'expiry_date': expiry,
               'received_date': '2026-02-01', 'reply_method': 'secure portal', 'notes': ''}
        self.tables['certification-replies'].append(row)
        return row

    def request(self, code):
        self.tables['privilege-requests'].append({'request_id': code, 'application_id': 'TEST-A', 'revision': '1',
            'privilege_code': code, 'criteria_version_cited': self.registry['criteria_version']})

    def evaluate(self, **kwargs):
        return evaluate_privileges(self.app, self.tables, '2026-03-16', self.registry, self.entries, **kwargs)

    def test_positive_verified_accredited_training_and_active_certification(self):
        result = self.evaluate()
        self.assertEqual(result['supported'], ['PRIV-FM'])
        self.assertEqual(result['unsupported'], [])
        self.assertEqual(result['issues'], [])

    def test_missing_accreditation_never_inferred_from_accepted_reply(self):
        for entry in self.entries:
            with self.subTest(kind=entry['declared']['entry_type']):
                changed = copy.deepcopy(self.entries)
                self.entries[self.entries.index(entry)]['accreditation_verified'] = False
                result = self.evaluate()
                self.assertEqual(result['supported'], [])
                self.assertTrue(any(i['kind'] == 'outstanding' for i in result['issues']))
                self.assertTrue(any(i['kind'] == 'eligibility-question' and i['owner'] == 'Clinical Director'
                                    for i in result['issues']))
                self.entries = changed

    def test_inactive_expired_and_not_certified_preserved_without_support(self):
        row = self.tables['certification-replies'][0]
        for status, expiry in [('Inactive', '2030-12-31'), ('Active', '2026-03-15'), ('Not certified', '')]:
            with self.subTest(status=status, expiry=expiry):
                row.update(certification_status=status, expiry_date=expiry)
                result = self.evaluate()
                self.assertEqual(result['supported'], [])
                self.assertEqual(result['certification_checks'][0]['accepted_reply_ids'], [row['reply_id']])
                self.assertEqual(result['certification_checks'][0]['verification_rows'][0]['certification_status'], status)
                self.assertFalse(any(i['kind'] == 'outstanding' for i in result['issues']))

    def test_expiry_day_inclusive_and_nonexpiring_active(self):
        row = self.tables['certification-replies'][0]
        for expiry in ['2026-03-16', '']:
            row['expiry_date'] = expiry
            self.assertEqual(self.evaluate()['supported'], ['PRIV-FM'])

    def test_missing_initial_certification_date_is_outstanding(self):
        row = self.tables['certification-replies'][0]
        row['initial_certification_date'] = ''
        result = self.evaluate()
        self.assertEqual(result['supported'], [])
        self.assertEqual(result['certification_checks'][0]['accepted_reply_ids'], [row['reply_id']])
        self.assertTrue(any(issue['kind'] == 'outstanding' and 'initial certification date' in issue['detail']
                            for issue in result['issues']))

    def test_old_accepted_education_rows_do_not_override_unverified_or_disputed_dates(self):
        for entry_number in [0, 1]:
            for changed in [{'dates_verified': False}, {'unresolved_discrepancy': True}]:
                with self.subTest(entry=entry_number, changed=changed):
                    entries = copy.deepcopy(self.entries)
                    entries[entry_number].update(changed)
                    result = evaluate_privileges(self.app, self.tables, '2026-03-16', self.registry, entries)
                    self.assertEqual(result['supported'], [])
                    self.assertTrue(entries[entry_number]['accepted_reply_ids'])

    def test_board_eligible_requires_issuing_board_notes_and_future_end(self):
        row = self.tables['certification-replies'][0]
        row.update(certification_status='Not certified', expiry_date='', initial_certification_date='')
        row['notes'] = 'Candidate in good standing; board eligible through 2027-06-30.'
        self.assertEqual(self.evaluate()['supported'], ['PRIV-FM'])
        for notes in ['', 'Candidate in good standing.', 'Board eligible through 2027-06-30.',
                      'Candidate in good standing; board eligible through 2026-03-16.',
                      'Not a candidate in good standing; board eligible through 2027-06-30.']:
            row['notes'] = notes
            self.assertEqual(self.evaluate()['supported'], [])

    def test_equivalent_certification_source_cannot_attest_board_eligibility(self):
        row = self.tables['certification-replies'][0]
        row['received_from'] = 'CertiFACTS'
        self.assertEqual(self.evaluate()['supported'], ['PRIV-FM'])
        row.update(certification_status='Not certified', notes='Candidate in good standing; board eligible through 2027-06-30.')
        self.assertEqual(self.evaluate()['supported'], [])

    def test_inactive_or_expired_certificate_does_not_use_old_eligibility_notes(self):
        row = self.tables['certification-replies'][0]
        row['notes'] = 'Candidate in good standing; board eligible through 2027-06-30.'
        for status in ['Inactive', 'Expired']:
            row['certification_status'] = status
            self.assertEqual(self.evaluate()['supported'], [])

    def test_telephone_does_not_establish_written_board_eligibility(self):
        row = self.tables['certification-replies'][0]
        row.update(certification_status='Not certified', reply_method='telephone',
                   notes='Candidate in good standing; board eligible through 2027-06-30.')
        self.assertEqual(self.evaluate()['supported'], [])

    def test_latest_status_replaces_old_active_support_but_preserves_both_replies(self):
        later = dict(self.tables['certification-replies'][0], reply_id='LATER',
                     received_date='2026-03-01', certification_status='Inactive')
        self.tables['certification-replies'].append(later)
        result = self.evaluate()
        self.assertEqual(result['supported'], [])
        self.assertEqual(len(result['certification_checks'][0]['accepted_reply_ids']), 2)

    def test_conflicting_same_day_certification_status_remains_outstanding(self):
        conflicting = dict(self.tables['certification-replies'][0], reply_id='CONFLICT', certification_status='Inactive')
        self.tables['certification-replies'].append(conflicting)
        result = self.evaluate()
        self.assertEqual(result['supported'], [])
        self.assertTrue(any('same-day' in issue['detail'] for issue in result['issues']))

    def test_eligible_not_permitted_for_emergency_medicine(self):
        self.tables = {'declared-credentials': [], 'certification-replies': [], 'privilege-requests': []}
        row = self.add_cert('ABEM', 'American Board of Emergency Medicine', 'Emergency Medicine', 'Not certified', '')
        row['notes'] = 'Candidate in good standing; board eligible through 2027-06-30.'
        self.request('PRIV-EM')
        self.entries[1] = self.entry('residency', 'Residency — Emergency Medicine', '2010-07-01', '2013-06-30')
        self.assertEqual(self.evaluate()['supported'], [])

    def test_matching_board_with_wrong_specialty_does_not_support(self):
        self.tables['certification-replies'][0]['certificate_specialty'] = 'Sports Medicine'
        self.assertEqual(self.evaluate()['supported'], [])

    def test_applicant_routed_and_unlisted_source_rejected(self):
        for source in ['Applicant — certifying board original', 'Specialty society membership roster']:
            self.tables['certification-replies'][0]['received_from'] = source
            result = self.evaluate()
            self.assertEqual(result['certification_checks'][0]['accepted_reply_ids'], [])
            self.assertEqual(result['supported'], [])

    def test_receipt_cutoff_and_first_receipt(self):
        row = self.tables['certification-replies'][0]
        row['received_date'] = '2026-03-16'
        self.assertEqual(self.evaluate()['supported'], ['PRIV-FM'])
        self.assertEqual(self.evaluate(before=True)['supported'], [])
        row['received_date'] = '2025-12-31'
        self.assertEqual(self.evaluate()['supported'], [])

    def test_training_requires_verified_specialty_full_duration_and_completion(self):
        for credential, start, end in [
            ('Residency — Pediatrics', '2010-07-01', '2013-06-30'),
            ('Residency — Family Medicine', '2010-07-01', '2012-06-30'),
            ('Residency — Family Medicine', '2010-07-02', '2013-06-30'),
            ('Residency — Family Medicine', '2024-07-01', '2027-06-30'),
        ]:
            self.entries[1] = self.entry('residency', credential, start, end)
            self.assertEqual(self.evaluate()['supported'], [])

    def test_cardiology_requires_fellowship_after_internal_medicine_residency(self):
        self.tables = {'declared-credentials': [], 'certification-replies': [], 'privilege-requests': []}
        self.add_cert('ABIM', 'American Board of Internal Medicine', 'Cardiovascular Disease')
        self.request('PRIV-CARD')
        self.entries[1] = self.entry('fellowship', 'Fellowship — Cardiovascular Disease', '2013-07-01', '2016-06-30')
        self.assertEqual(self.evaluate()['supported'], [])
        self.entries.append(self.entry('residency', 'Residency — Internal Medicine', '2010-07-01', '2013-06-30'))
        self.assertEqual(self.evaluate()['supported'], ['PRIV-CARD'])
        # CARD requires a completed preceding IM residency; its row does not
        # import PRIV-IM's distinct 36-month threshold.
        self.entries[-1] = self.entry('residency', 'Residency — Internal Medicine', '2012-07-01', '2013-06-30')
        self.assertEqual(self.evaluate()['supported'], ['PRIV-CARD'])
        self.entries[-1] = self.entry('residency', 'Residency — Internal Medicine', '2014-07-01', '2017-06-30')
        self.assertEqual(self.evaluate()['supported'], [])

    def test_partial_month_cardiology_fellowship_does_not_invent_duration(self):
        self.tables = {'declared-credentials': [], 'certification-replies': [], 'privilege-requests': []}
        self.add_cert('ABIM', 'American Board of Internal Medicine', 'Cardiovascular Disease')
        self.request('PRIV-CARD')
        self.entries[1] = self.entry('residency', 'Residency — Internal Medicine', '2010-07-01', '2013-06-30')
        self.entries.append(self.entry('fellowship', 'Fellowship — Cardiovascular Disease', '2013-07-02', '2016-06-30'))
        result = self.evaluate()
        self.assertEqual(result['supported'], [])
        self.assertTrue(any(issue['kind'] == 'outstanding' and 'Q04' in issue['detail'] for issue in result['issues']))

    def test_partial_support_finding_does_not_disqualify_supported_group(self):
        self.request('PRIV-PED')
        result = self.evaluate()
        self.assertEqual(result['supported'], ['PRIV-FM'])
        self.assertEqual(result['unsupported'], ['PRIV-PED'])
        self.assertTrue(any(i['kind'] == 'finding' for i in result['issues']))
        self.assertFalse(any(i['kind'] == 'eligibility-question' for i in result['issues']))

    def test_old_revision_requests_and_credentials_do_not_leak(self):
        self.tables['privilege-requests'][0]['revision'] = '0'
        result = self.evaluate()
        self.assertEqual(result['supported'], [])
        self.assertEqual(result['unsupported'], [])


if __name__ == '__main__':
    unittest.main()
