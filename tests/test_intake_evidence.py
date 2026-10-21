"""Synthetic supplied documents supplement real declarations; never alter inputs."""
import unittest
from copy import deepcopy

from credentialing.documents import parse_document, indexed_documents, for_application
from credentialing.engine import intake, assess, project
from credentialing.io import load_batch, load_sources
from credentialing.policy import registry


class IntakeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.batch = load_batch('inputs/batch-01')
        self.app = self.batch['tables']['applications'][0]
        self.reg = registry(load_sources('sources'))
        self.entries = [r for r in self.batch['tables']['declared-history'] if r['application_id'] == self.app['application_id']]

    def document(self, kind, body, revision='1', date='2026-02-20'):
        return parse_document('synthetic/' + kind + '.md',
            f'# {kind}\n**Application:** {self.app["application_id"]}\n**Applicant:** Marcus Holloway\n'
            f'**Revision:** {revision}\n**Date:** {date}\n' + body,
            {'application_id': self.app['application_id'], 'date': date, 'direction': 'inbound', 'document_path': 'synthetic/' + kind + '.md'})

    def signature(self, **kwargs):
        return self.document('Signed application', '**Signature:** Marcus Holloway\n**Signature date:** 2026-01-26\n', **kwargs)

    def cv(self, entries=None, **kwargs):
        text = '| Entry | Organization | Role | From | To |\n| --- | --- | --- | --- | --- |\n'
        for e in self.entries if entries is None else entries:
            text += '| ' + ' | '.join(e[k] for k in ('entry_id', 'organization', 'role', 'from_date', 'to_date')) + ' |\n'
        return self.document('Curriculum vitae', text, **kwargs)

    def evaluate(self, docs, date='2026-03-16', before=False):
        return assess(self.app, self.batch['tables'], docs, date, self.reg, before)

    def test_qualifying_signature_and_actual_cv_clear_only_their_holds(self):
        result = self.evaluate([self.signature(), self.cv()])
        self.assertNotIn('application signature and date evidence', result['intake']['missing'])
        self.assertFalse(any(i['element'] == 'reconciliation' for i in result['issues']))
        self.assertFalse(result['packet_presentable'])  # accreditation/provenance still absent
        self.assertTrue(result['intake']['document_evidence']['cv']['resolved'])

    def test_absent_wrong_revision_identity_and_future_signature_do_not_clear(self):
        wrong_name = self.signature()
        wrong_name['fields']['signature'] = 'Another Person'
        future_signature = self.signature()
        future_signature['fields']['signature_date'] = '2027-01-01'
        wrong_id = self.signature()
        wrong_id['fields']['application'] = 'APP-OTHER'
        for docs in ([], [wrong_name], [future_signature], [wrong_id], [self.signature(revision='2')], [self.signature(date='2026-03-17')]):
            with self.subTest(docs=docs):
                self.assertIn('application signature and date evidence', self.evaluate(docs)['intake']['missing'])

    def test_attestation_missing_cv_rows_and_actual_conflict_stay_unresolved(self):
        changed = deepcopy(self.entries)
        changed[1]['to_date'] = '2013-06-29'
        cases = [self.document('Office attestation', 'Application signed; CV reconciled.'),
                 self.cv(entries=self.entries[:-1]), self.cv(entries=changed)]
        for doc in cases:
            with self.subTest(doc=doc['path']):
                result = self.evaluate([doc])
                self.assertTrue(any(i['element'] == 'reconciliation' for i in result['issues']))
        self.assertTrue(any(i['kind'] == 'discrepancy' and i['element'] == 'reconciliation'
                            for i in self.evaluate([self.cv(entries=changed)])['issues']))

    def test_evidence_received_on_decision_day_cannot_retroactively_clear(self):
        docs = [self.signature(date='2026-03-10'), self.cv(date='2026-03-10')]
        self.assertIn('application signature and date evidence', self.evaluate(docs, '2026-03-10', True)['intake']['missing'])
        self.assertNotIn('application signature and date evidence', self.evaluate(docs, '2026-03-10')['intake']['missing'])

    def test_contact_scope_and_no_email_requirement(self):
        tables = deepcopy(self.batch['tables'])
        rows = [e for e in tables['declared-history'] if e['application_id'] == self.app['application_id']]
        for e in rows:
            e['contact_email'] = ''
            if e['entry_type'] in {'medical-school', 'residency'}:
                e['contact_name'] = ''
        result = intake(self.app, tables, [], '2026-03-16', self.reg, {'gaps': []})
        self.assertFalse(any(x.startswith('contact for') for x in result['missing']))
        rows[-1]['contact_name'] = ''
        result = intake(self.app, tables, [], '2026-03-16', self.reg, {'gaps': []})
        self.assertIn('contact for ' + rows[-1]['entry_id'], result['missing'])

    def test_all_four_evidence_holds_clear_in_engine_with_qualifying_sources(self):
        # Synthetic supplement; original batch files are never changed.
        tables = deepcopy(self.batch['tables'])
        for reply in tables['verification-replies']:
            if reply['reply_id'] in {'VR-0100', 'VR-0101'}:
                reply['notes'] = 'Accreditation: accredited.'
        docs = [self.signature(), self.cv()]
        for reply in tables['peer-reference-replies']:
            if reply['application_id'] != self.app['application_id']:
                continue
            referee = next(r for r in tables['peer-referees'] if r['referee_id'] == reply['referee_id'])
            text = '\n'.join(f'**{key}:** {value}' for key, value in {
                'Received date': reply['received_date'], 'Referee': reply['referee_id'], 'Reply': reply['reply_id'],
                'Received from': referee['referee_name'], 'Return method': 'secure portal'}.items())
            docs.append(self.document('Peer return ' + reply['reply_id'], text, date=reply['received_date']))
        result = assess(self.app, tables, docs, '2026-03-16', self.reg)
        self.assertEqual(result['intake']['missing'], [])
        self.assertTrue(result['intake']['document_evidence']['cv']['resolved'])
        self.assertTrue(all(c['usable'] for c in result['peer_checks']))
        self.assertEqual(result['privileges']['supported'], ['PRIV-FM'])
        self.assertTrue(result['packet_presentable'])
        self.assertEqual(result['issues'], [])

    def test_expiry_requires_outstanding_item_covered_by_actual_notice(self):
        app = next(a for a in self.batch['tables']['applications'] if a['application_id'] == 'APP-2026-019')
        docs = for_application(indexed_documents(self.batch), app['application_id'], '2026-03-21')
        for clock, expected in [('2026-03-20', 'intake-incomplete'), ('2026-03-21', 'ineligible-clock-expired')]:
            assessment = assess(app, self.batch['tables'], docs, clock, self.reg)
            self.assertEqual(project(app, assessment, [], docs, self.reg, clock)['status'], expected)
        fulfilled = dict(app, release_signed_date='2026-02-11', cv_received_date='2026-02-11')
        assessment = assess(fulfilled, self.batch['tables'], docs, '2026-03-21', self.reg)
        self.assertIn('application signature and date evidence', assessment['intake']['missing'])
        projected = project(fulfilled, assessment, [], docs, self.reg, '2026-03-21')
        self.assertEqual(projected['status'], 'intake-incomplete')
        pending = [a for a in projected['action_queue'] if a['item'].startswith('Pending MSP dispatch')]
        self.assertEqual(len(pending), 1)
        self.assertIsNone(pending[0]['due'])
        self.assertFalse(any(a['item'].startswith('Await ') for a in projected['action_queue']))

    def test_predispatch_exception_never_starts_or_expires_a_clock(self):
        for clock in ('2026-03-16', '2026-06-30'):
            assessment = self.evaluate([], clock)
            projected = project(self.app, assessment, [], [], self.reg, clock)
            self.assertEqual(projected['status'], 'intake-incomplete')
            self.assertEqual(assessment['intake']['notices'], [])
            self.assertTrue(assessment['intake']['missing'])
            pending = [a for a in projected['action_queue'] if a['item'].startswith('Pending MSP dispatch')]
            self.assertEqual(len(pending), 1)
            self.assertIsNone(pending[0]['due'])
            self.assertFalse(projected['packet_presentable'])
            self.assertIsNone(projected['approval_decision_id'])
            self.assertIsNone(projected['activation'])

    def test_unknown_notice_coverage_is_not_assumed_to_be_predispatch(self):
        # Synthetic unresolved coverage must not acquire the pending-dispatch exception.
        assessment = self.evaluate([])
        assessment['intake']['notices'] = [{'requested_items': [], 'returned': False,
                                          'request_coverage_known': False}]
        self.assertIsNone(project(self.app, assessment, [], [], self.reg, '2026-03-16')['status'])


if __name__ == '__main__':
    unittest.main()
