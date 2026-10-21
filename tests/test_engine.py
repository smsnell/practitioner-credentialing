"""Focused source-backed assertions for the actual first export (no outputs written)."""
import unittest
from copy import deepcopy
from credentialing.io import load_batch, load_sources
from credentialing.engine import process_batch, element_states, presentable, decision_conditions, intake
from credentialing.documents import indexed_documents, document_conflicts
from credentialing.policy import registry


class BatchOneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = load_batch('inputs/batch-01')
        cls.result = process_batch(cls.batch, load_sources('sources'))
        cls.apps = {a['application_id']: a for a in cls.result['applications']}
        cls.history = cls.result['history']['applications']

    def assessment(self, number):
        return self.history['APP-2026-' + number]['assessments'][-1]

    def test_complete_caseload_revision_history_and_no_inferred_evidence(self):
        self.assertEqual(len(self.apps), 40)
        self.assertEqual(sum(len(v['revisions']) for v in self.history.values()), 41)
        self.assertEqual(self.apps['APP-2026-025']['revision'], 2)
        self.assertEqual(self.history['APP-2026-025']['first_received_date'], '2024-04-22')
        self.assertTrue(all(not a['packet_presentable'] and a['approval_decision_id'] is None and a['activation'] is None for a in self.apps.values()))
        for value in self.history.values():
            self.assertIn('application signature and date evidence', value['assessments'][-1]['intake']['missing'])

    def test_recorded_request_and_return_are_not_pending_dispatch(self):
        self.assertEqual(self.apps['APP-2026-019']['status'], 'intake-incomplete')
        self.assertEqual(self.assessment('019')['intake']['notices'][0]['due'], '2026-03-20')
        self.assertFalse(self.assessment('019')['intake']['release_present'])
        self.assertEqual(self.apps['APP-2026-018']['status'], 'returned-incomplete')
        self.assertEqual(self.assessment('018')['intake']['notices'][0]['due'], '2026-04-05')
        self.assertEqual(sum(a['status'] is None for a in self.apps.values()), 0)
        self.assertEqual(sum(a['status'] == 'intake-incomplete' for a in self.apps.values()), 39)

    def test_existing_notice_deadline_covers_only_its_requested_items(self):
        actions = self.apps['APP-2026-019']['action_queue']
        for item in ('signed and dated Larkhollow release', 'current curriculum vitae'):
            matches = [a for a in actions if a['item'].startswith('Await ' + item)]
            self.assertEqual(len(matches), 1, item)
            self.assertEqual(matches[0]['due'], '2026-03-20')
            self.assertEqual(matches[0]['owner'], 'Applicant')
        pending = [a for a in actions if 'Pending MSP dispatch' in a['item']]
        self.assertEqual(len(pending), 1)
        self.assertIn('application signature and date evidence', pending[0]['item'])
        self.assertIn('two named referees', pending[0]['item'])
        self.assertNotIn('Larkhollow release', pending[0]['item'])
        self.assertNotIn('CV present at submission', pending[0]['item'])
        self.assertFalse(pending[0]['item'].startswith('Hold verification outreach'))
        self.assertIsNone(pending[0]['due'])
        self.assertFalse(any('prepare only the release request' in a['item'] for a in actions))
        self.assertFalse(any('Recorded incomplete notice remains' in a['item'] for a in actions))
        outreach = [a for a in actions if 'obtain admissible' in a['item']]
        self.assertTrue(outreach)
        self.assertTrue(all(a['item'].startswith('Hold verification outreach until signed release;') and a['due'] is None for a in outreach))

    def test_whole_month_residency_does_not_claim_q04_ambiguity(self):
        a = self.assessment('001')
        self.assertFalse(any('Q04' in i['detail'] for i in a['privileges']['issues']))
        self.assertTrue(any('accredited' in i['detail'] for i in a['privileges']['issues']))
        self.assertFalse(a['packet_presentable'])

    def test_no_notice_creates_no_clock_and_unknown_coverage_needs_review(self):
        a = self.assessment('019')
        reg = registry(load_sources('sources'))
        result = intake(a['application'], self.batch['tables'], [], '2026-03-16', reg, a['gaps'])
        self.assertEqual(result['notices'], [])
        pending = next(i for i in result['issues'] if 'Pending MSP dispatch' in i['detail'])
        for item in result['missing']:
            self.assertIn(item, pending['detail'])
        self.assertIsNone(pending['due'])
        doc = deepcopy(next(d for d in indexed_documents(self.batch) if 'missing-items' in d['path']))
        doc['text'] = doc['text'].replace('Two items are missing from your application', 'Items need clarification')
        result = intake(a['application'], self.batch['tables'], [doc], '2026-03-16', reg, a['gaps'])
        self.assertFalse(result['notices'][0]['request_coverage_known'])
        self.assertTrue(any('Review recorded notice coverage' in i['detail'] for i in result['issues']))
        self.assertFalse(any('Pending MSP dispatch' in i['detail'] for i in result['issues']))
        self.assertFalse(any(i['due'] for i in result['issues']))

    def test_explained_short_gap_and_long_gap_routing(self):
        gap = self.assessment('005')['gaps']['gaps'][0]
        self.assertEqual((gap['start'], gap['end'], gap['days']), ('2013-07-01', '2013-07-30', 30))
        self.assertEqual(len(gap['explanation_sources']), 1)
        self.assertFalse(any(i['element'] == 'gaps' for i in self.assessment('005')['issues']))
        long_gap = self.assessment('017')['gaps']['gaps'][0]
        self.assertEqual(long_gap['days'], 219)
        self.assertTrue(long_gap['explanation_sources'])
        self.assertTrue(any(i['kind'] == 'routed-to-clinical-director' for i in self.assessment('017')['issues']))
        self.assertEqual(self.assessment('018')['gaps']['gaps'][0]['days'], 31)

    def test_middle_name_omission_is_not_a_changed_applicant(self):
        app = self.assessment('019')['application']
        doc = next(d for d in indexed_documents(self.batch) if 'missing-items' in d['path'])
        self.assertEqual(document_conflicts(doc, app), [])
        altered = deepcopy(doc)
        altered['fields']['applicant'] = 'Dr. Fionn Different, MD'
        self.assertTrue(document_conflicts(altered, app))

    def test_licence_finding_and_disclosure_discrepancy_both_survive(self):
        a = self.assessment('015')
        kinds = {i['kind'] for i in a['issues'] if i['element'] == 'licensure'}
        self.assertIn('finding', kinds)
        self.assertIn('discrepancy', kinds)
        self.assertEqual(a['elements']['licensure'], 'outstanding')
        self.assertTrue(any('Clinical Director' == i['owner'] for i in a['issues'] if i['element'] == 'licensure'))

    def test_npi_does_not_supply_wa_licence_and_conflicts_stay(self):
        a = self.assessment('031')
        self.assertIsNone(a['licensure']['wa'])
        self.assertTrue(any('NPI' in i['detail'] for i in a['issues']))
        a = self.assessment('030')
        self.assertTrue(any(i['kind'] == 'discrepancy' and i['element'] == 'experience' for i in a['issues']))

    def test_six_actual_recommendations_refused_for_evidence_not_authority(self):
        decisions = [d for v in self.history.values() for d in v['decisions']]
        self.assertEqual(len(decisions), 6)
        for d in decisions:
            self.assertFalse(d['admitted'])
            self.assertTrue(d['failures'][0].startswith('4 prior presentability'))
            self.assertEqual(d['fields']['outcome'], 'recommended')
            self.assertTrue(d['readiness_evidence']['historical_before_decision'])

    def test_partial_certification_finding_does_not_erase_readiness(self):
        self.assertTrue(presentable([{'element': 'certification', 'kind': 'finding'}]))
        self.assertFalse(presentable([{'element': 'licensure', 'kind': 'finding'}]))
        self.assertFalse(presentable([{'element': 'certification', 'kind': 'eligibility-question'}]))

    def test_conditional_approval_requires_explicit_due_dates(self):
        doc = {'fields': {'outcome': 'approved-with-conditions'}, 'text': '## Conditions\n- Reverify licence by 2026-11-30.\n- Obtain gap concurrence by 2026-06-30.\n'}
        conditions, errors = decision_conditions(doc)
        self.assertFalse(errors)
        self.assertEqual([c['due'] for c in conditions], ['2026-11-30', '2026-06-30'])
        doc['text'] = '## Conditions\n- Obtain concurrence.\n'
        self.assertTrue(decision_conditions(doc)[1])

    def test_disposed_finding_projection_is_not_cleaned_by_summary(self):
        states = element_states([{'element':'licensure','kind':'finding'}, {'element':'licensure','kind':'discrepancy'}])
        self.assertEqual(states['licensure'], 'outstanding')


if __name__ == '__main__':
    unittest.main()
