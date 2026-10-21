"""Admissible evidence cures missing verification without erasing real conflicts."""

import copy
import unittest

from credentialing.documents import parse_document
from credentialing.evidence import evaluate_replies
from credentialing.privileges import evaluate_privileges


class EvidenceCureTests(unittest.TestCase):
    def setUp(self):
        self.app = {'application_id': 'TEST', 'revision': '1', 'first_received_date': '2026-01-01',
                    'first_name': 'Ada', 'last_name': 'Example', 'discipline': 'Family Medicine'}
        self.entry = {'application_id': 'TEST', 'revision': '1', 'entry_id': 'SCHOOL',
                      'entry_type': 'medical-school', 'organization': 'Example School',
                      'role': 'Doctor of Medicine', 'from_date': '2000-09-01', 'to_date': '2004-06-30'}
        self.reply = {'application_id': 'TEST', 'entry_id': 'SCHOOL', 'reply_id': 'GOOD',
                      'received_from': 'Registrar — Example School', 'attester_organization': 'Example School',
                      'attester_role': 'Registrar', 'verified_credential': 'Degree — Doctor of Medicine',
                      'verified_from': '2000-09-01', 'verified_to': '2004-06-30', 'outcome': 'confirmed',
                      'received_date': '2026-02-02', 'notes': 'The school is accredited.'}
        self.tables = {'declared-history': [self.entry], 'verification-replies': [self.reply]}

    def evaluate(self, **kwargs):
        return evaluate_replies(self.app, self.tables, '2026-03-16', **kwargs)

    def education_issues(self, result):
        return [issue for issue in result['issues'] if issue['element'] == 'education']

    def test_accepted_evidence_cures_source_no_record_and_missing_boundary_in_any_order(self):
        for received in ('2026-02-01', '2026-02-02', '2026-02-03'):
            for changes in ({'received_from': 'Applicant'},
                            {'outcome': 'no-record', 'verified_from': '', 'verified_to': ''},
                            {'verified_from': ''}, {'verified_to': ''}):
                with self.subTest(received=received, changes=changes):
                    rejected = dict(self.reply, reply_id='REJECTED', received_date=received)
                    rejected.update(changes)
                    self.tables['verification-replies'] = [rejected, self.reply]
                    original = copy.deepcopy(self.tables)
                    result = self.evaluate()
                    check = result['entry_checks'][0]
                    self.assertEqual(check['accepted_reply_ids'], ['GOOD'])
                    self.assertTrue(check['dates_verified'])
                    self.assertTrue(check['accreditation_verified'])
                    self.assertTrue(check['failures'])
                    self.assertEqual(check['verification_rows'], [rejected, self.reply])
                    issues = self.education_issues(result)
                    self.assertEqual(len(issues), 1)
                    self.assertEqual(issues[0]['kind'], 'pending-work')
                    self.assertEqual(issues[0]['owner'], 'Medical Services Professional')
                    self.assertIn('verification-replies.csv#REJECTED', issues[0]['source_refs'])
                    self.assertIn('verification-replies.csv#GOOD', issues[0]['source_refs'])
                    self.assertEqual(self.tables, original)

    def test_accepted_evidence_does_not_cure_actual_competing_dates(self):
        conflicting = dict(self.reply, reply_id='CONFLICT', verified_to='2004-07-01', received_from='Applicant')
        self.tables['verification-replies'].append(conflicting)
        result = self.evaluate()
        self.assertTrue(result['entry_checks'][0]['unresolved_discrepancy'])
        self.assertFalse(result['entry_checks'][0]['dates_verified'])
        self.assertTrue(any(issue['kind'] == 'discrepancy' for issue in self.education_issues(result)))
        self.assertFalse(any(issue['kind'] == 'pending-work' for issue in self.education_issues(result)))

    def test_accepted_evidence_does_not_cure_revised_material_fact_conflict(self):
        old = dict(self.entry, role='Doctor of Osteopathic Medicine')
        self.entry['revision'] = '2'
        self.app['revision'] = '2'
        self.tables['declared-history'].append(old)
        conflicting = dict(self.reply, reply_id='CONFLICT', verified_credential='Degree — Doctor of Osteopathic Medicine')
        self.tables['verification-replies'].append(conflicting)
        result = self.evaluate()
        self.assertTrue(result['entry_checks'][0]['unresolved_discrepancy'])
        self.assertFalse(any(issue['kind'] == 'pending-work' for issue in self.education_issues(result)))

    def test_cure_requires_available_accepted_evidence_and_independent_accreditation(self):
        rejected = dict(self.reply, reply_id='REJECTED', outcome='no-record', verified_from='', verified_to='')
        self.tables['verification-replies'].append(rejected)
        self.reply['received_date'] = '2026-03-16'
        result = self.evaluate(before=True)
        self.assertFalse(result['entry_checks'][0]['dates_verified'])
        self.assertFalse(any(issue['kind'] == 'pending-work' for issue in self.education_issues(result)))
        self.reply['received_date'] = '2026-02-02'
        self.reply['notes'] = ''
        result = self.evaluate()
        self.assertTrue(any(issue['kind'] == 'pending-work' for issue in self.education_issues(result)))
        self.assertTrue(any(issue['kind'] == 'outstanding' and issue['rule'] == 'B17/B40'
                            for issue in self.education_issues(result)))

    def peers(self, count=2, duplicate=False):
        referees, replies, documents = [], [], []
        for number in range(count):
            referee_id = 'REF0' if duplicate else 'REF' + str(number)
            name, reply_id = 'Dr. Peer ' + str(number), 'PEER' + str(number)
            referees.append({'application_id': 'TEST', 'revision': '1', 'referee_id': referee_id,
                             'referee_name': name, 'first_request_date': '2026-01-01'})
            replies.append({'application_id': 'TEST', 'referee_id': referee_id, 'reply_id': reply_id,
                            'received_date': '2026-03-02', 'signature_date': '2026-03-01',
                            'related_or_partner': 'No', 'last_worked_together_end': '',
                            'referee_specialty_stated': 'Family Medicine', 'relationship_stated': 'Worked together'})
            path = reply_id + '.md'
            fields = {'Application': 'TEST', 'Referee': referee_id, 'Reply': reply_id,
                      'Received date': '2026-03-02', 'Received from': name, 'Return method': 'secure portal'}
            documents.append(parse_document(path, '\n'.join('**' + k + ':** ' + v for k, v in fields.items()),
                             {'application_id': 'TEST', 'date': '2026-03-02', 'direction': 'inbound', 'document_path': path}))
        referees.append({'application_id': 'TEST', 'revision': '1', 'referee_id': 'OPEN',
                         'referee_name': 'Dr. Open', 'first_request_date': '2026-01-01'})
        self.tables['peer-referees'], self.tables['peer-reference-replies'] = referees, replies
        return documents

    def test_two_usable_peers_make_surplus_unanswered_work_nonblocking_and_owned(self):
        result = self.evaluate(documents=self.peers())
        self.assertEqual(sum(check['usable'] for check in result['peer_checks']), 2)
        issues = [issue for issue in result['issues'] if issue['element'] == 'references']
        self.assertEqual(len(issues), 2)
        self.assertTrue(all(issue['kind'] == 'pending-work' for issue in issues))
        self.assertTrue(all(issue['surplus_referee_id'] == 'OPEN' for issue in issues))
        self.assertTrue(all(issue['owner'] == 'Medical Services Professional' and issue['due'] for issue in issues))
        self.assertTrue(all('until recorded presentation' in issue['detail'] for issue in issues))
        open_check = next(check for check in result['peer_checks'] if check['referee_id'] == 'OPEN')
        self.assertFalse(open_check['usable'])
        self.assertIsNone(open_check['reply_id'])

    def test_one_peer_duplicate_peer_and_missing_provenance_do_not_meet_minimum(self):
        for count, duplicate, provenance in ((1, False, True), (2, True, True), (2, False, False)):
            with self.subTest(count=count, duplicate=duplicate, provenance=provenance):
                docs = self.peers(count, duplicate)
                result = self.evaluate(documents=docs if provenance else [])
                issues = [issue for issue in result['issues'] if issue['element'] == 'references']
                self.assertTrue(any('At least two' in issue['detail'] for issue in issues))
                self.assertFalse(any(issue['kind'] == 'pending-work' for issue in issues))


class CertificationCureTests(unittest.TestCase):
    def setUp(self):
        self.app = {'application_id': 'TEST', 'revision': '1', 'first_received_date': '2026-01-01'}
        self.reply = {'application_id': 'TEST', 'declaration_id': 'CERT', 'reply_id': 'GOOD',
                      'board_code': 'ABFM', 'board_name': 'American Board of Family Medicine',
                      'received_from': 'Certifying board — American Board of Family Medicine',
                      'certificate_specialty': 'Family Medicine', 'certification_status': 'Active',
                      'initial_certification_date': '2010-01-01', 'expiry_date': '2027-12-31',
                      'received_date': '2026-02-02', 'notes': ''}
        self.tables = {'declared-credentials': [{'application_id': 'TEST', 'revision': '1',
                       'declaration_id': 'CERT', 'credential_class': 'certification',
                       'issuer': 'American Board of Family Medicine', 'jurisdiction_or_board': 'ABFM'}],
                       'certification-replies': [self.reply]}

    def evaluate(self, **kwargs):
        return evaluate_privileges(self.app, self.tables, '2026-03-16', {}, [], **kwargs)

    def verification_issues(self, result):
        return [issue for issue in result['issues'] if issue['rule'].startswith('B20')]

    def test_accepted_certificate_cures_missing_or_rejected_duplicate_at_any_receipt_order(self):
        for received in ('2026-02-01', '2026-02-02', '2026-02-03'):
            for changes in ({'received_from': 'Applicant'}, {'certificate_specialty': ''},
                            {'certification_status': ''}):
                with self.subTest(received=received, changes=changes):
                    rejected = dict(self.reply, reply_id='REJECTED', received_date=received)
                    rejected.update(changes)
                    self.tables['certification-replies'] = [rejected, self.reply]
                    result = self.evaluate()
                    check = result['certification_checks'][0]
                    self.assertEqual(check['accepted_reply_ids'], ['GOOD'])
                    self.assertTrue(check['failures'])
                    self.assertEqual(len(check['verification_rows']), 2)
                    issues = self.verification_issues(result)
                    self.assertEqual(len(issues), 1)
                    self.assertEqual(issues[0]['kind'], 'pending-work')
                    self.assertIn('certification-replies.csv#GOOD', issues[0]['source_refs'])

    def test_board_mismatch_and_same_day_conflicting_status_still_block(self):
        for changes in ({'board_code': 'ABIM'}, {'board_name': 'Different Board'},
                        {'certification_status': 'Inactive'}):
            with self.subTest(changes=changes):
                row = dict(self.reply, reply_id='CONFLICT')
                row.update(changes)
                self.tables['certification-replies'] = [self.reply, row]
                self.assertTrue(any(issue['kind'] == 'outstanding'
                                    for issue in self.verification_issues(self.evaluate())))

    def test_cure_requires_available_complete_current_certification_record(self):
        rejected = dict(self.reply, reply_id='REJECTED', received_from='Applicant')
        self.tables['certification-replies'].append(rejected)
        self.reply['received_date'] = '2026-03-16'
        self.assertFalse(any(issue['kind'] == 'pending-work'
                             for issue in self.verification_issues(self.evaluate(before=True))))
        self.reply.update(received_date='2026-02-02', initial_certification_date='')
        self.assertTrue(any(issue['kind'] == 'outstanding'
                            for issue in self.verification_issues(self.evaluate())))


if __name__ == '__main__':
    unittest.main()
