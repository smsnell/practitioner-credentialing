import copy
import csv
from pathlib import Path
import unittest

from credentialing.evidence import evaluate_replies
from credentialing.documents import parse_document


ROOT = Path(__file__).resolve().parents[1]


def real_tables():
    result = {}
    for path in (ROOT / "inputs/batch-01").glob("*.csv"):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            result[path.stem] = list(csv.DictReader(stream))
    return result


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = real_tables()

    def app(self, suffix="001"):
        return next(row for row in self.tables["applications"] if row["application_id"] == "APP-2026-" + suffix)

    def test_real_diploma_and_society_sources_rejected_and_preserved(self):
        for app_id, reply_id in (("020", "VR-2000"), ("022", "VR-2201")):
            with self.subTest(reply_id=reply_id):
                result = evaluate_replies(self.app(app_id), self.tables, "2026-03-16")
                check = next(row for row in result["entry_checks"] if any(r["reply_id"] == reply_id for r in row["verification_rows"]))
                self.assertNotIn(reply_id, check["accepted_reply_ids"])
                self.assertTrue(any("not an accepted direct source" in failure for failure in check["failures"]))
                self.assertEqual(check["verification_rows"][0]["reply_id"], reply_id)

    def test_confirmed_education_still_needs_accreditation(self):
        result = evaluate_replies(self.app(), self.tables, "2026-03-16")
        check = next(row for row in result["entry_checks"] if row["entry_id"] == "ENT-0100")
        self.assertEqual(check["accepted_reply_ids"], ["VR-0100"])
        self.assertTrue(check["dates_verified"])
        self.assertFalse(check["accreditation_verified"])
        self.assertTrue(any("accreditation" in row["detail"] for row in result["issues"]))

    def test_real_closed_school_queues_assessment_without_accepting_exception(self):
        result = evaluate_replies(self.app("021"), self.tables, "2026-03-16")
        check = next(row for row in result["entry_checks"] if row["entry_id"] == "ENT-2100")
        self.assertTrue(check["secondary_route_candidate"])
        self.assertFalse(check["dates_verified"])
        self.assertFalse(check["accreditation_verified"])
        self.assertEqual(check["accepted_reply_ids"], [])
        issue = next(row for row in result["issues"] if "recorded closure requires MSP" in row["detail"])
        self.assertIn("verification-attempts.csv#ATT-2104", issue["source_refs"])
        self.assertIn("verification-attempts.csv#ATT-2105", issue["source_refs"])
        self.assertIn("does not establish that no equivalent", issue["detail"])
        self.assertEqual({row["attempt_id"] for row in check["verification_attempts"]}, {"ATT-2100", "ATT-2104", "ATT-2105"})

    def test_nonresponse_or_no_record_alone_is_not_documented_closure(self):
        tables = copy.deepcopy(self.tables)
        tables["verification-replies"] = [row for row in tables["verification-replies"] if row["entry_id"] != "ENT-0100"]
        for comment in ("School has not replied to three requests.", "Designated equivalent source attempted. No record held."):
            tables["verification-attempts"] = [{"attempt_id": "NO-RECORD", "application_id": self.app()["application_id"],
                "subject_ref": "ENT-0100", "attempt_date": "2026-02-01", "outcome": "no response", "comment": comment}]
            with self.subTest(comment=comment):
                result = evaluate_replies(self.app(), tables, "2026-03-16")
                self.assertFalse(result["entry_checks"][0]["secondary_route_candidate"])
                self.assertFalse(any("recorded closure requires MSP" in row["detail"] for row in result["issues"]))

    def test_timeline_first_receipt_and_strict_decision_day(self):
        tables = copy.deepcopy(self.tables)
        app = self.app()
        reply = next(row for row in tables["verification-replies"] if row["reply_id"] == "VR-0100")
        for day, cutoff, before, usable in (("2026-01-25", "2026-03-16", False, False),
                                          ("2026-01-26", "2026-03-16", False, True),
                                          ("2026-03-16", "2026-03-16", True, False),
                                          ("2026-03-16", "2026-03-16", False, True),
                                          ("2026-03-17", "2026-03-16", False, False)):
            with self.subTest(day=day, before=before):
                reply["received_date"] = day
                result = evaluate_replies(app, tables, cutoff, before)
                check = next(row for row in result["entry_checks"] if row["entry_id"] == "ENT-0100")
                self.assertEqual(bool(check["accepted_reply_ids"]), usable)

    def test_unlisted_role_cannot_borrow_office_authority(self):
        tables = copy.deepcopy(self.tables)
        reply = next(row for row in tables["verification-replies"] if row["reply_id"] == "VR-0100")
        reply["attester_role"] = "Alumni Association President"
        check = evaluate_replies(self.app(), tables, "2026-03-16")["entry_checks"][0]
        self.assertEqual(check["accepted_reply_ids"], [])

    def test_conflicting_dates_do_not_replace_declaration(self):
        tables = copy.deepcopy(self.tables)
        reply = next(row for row in tables["verification-replies"] if row["reply_id"] == "VR-0100")
        reply["verified_to"] = "2010-07-01"
        result = evaluate_replies(self.app(), tables, "2026-03-16")
        check = result["entry_checks"][0]
        self.assertEqual(check["declared"]["to_date"], "2010-06-30")
        self.assertEqual(check["verification_rows"][0]["verified_to"], "2010-07-01")
        self.assertEqual(check["accepted_reply_ids"], [])
        self.assertTrue(any(row["kind"] == "discrepancy" for row in result["issues"]))

    def test_competing_clean_reply_cannot_clear_unresolved_discrepancy(self):
        for conflict_first in (False, True):
            tables = copy.deepcopy(self.tables)
            clean = next(row for row in tables["verification-replies"] if row["reply_id"] == "VR-0100")
            conflicting = dict(clean, reply_id="VR-CONFLICT", verified_to="2010-07-01")
            if conflict_first:
                tables["verification-replies"].insert(0, conflicting)
            else:
                tables["verification-replies"].append(conflicting)
            with self.subTest(conflict_first=conflict_first):
                check = evaluate_replies(self.app(), tables, "2026-03-16")["entry_checks"][0]
                self.assertEqual(check["accepted_reply_ids"], ["VR-0100"])
                self.assertTrue(check["unresolved_discrepancy"])
                self.assertFalse(check["dates_verified"])

    def test_changed_contact_reconciles_without_new_request_requirement(self):
        tables = copy.deepcopy(self.tables)
        app = dict(self.app(), revision="2", received_date="2026-03-10")
        tables["applications"].append(app)
        current = []
        for row in tables["declared-history"]:
            if row["application_id"] == app["application_id"]:
                new = dict(row, revision="2")
                if row["entry_id"] == "ENT-0100":
                    new["contact_email"] = "new@example.invalid"
                current.append(new)
        tables["declared-history"].extend(current)
        result = evaluate_replies(app, tables, "2026-03-16")
        by_id = {row["entry_id"]: row for row in result["entry_checks"]}
        self.assertEqual(by_id["ENT-0100"]["accepted_reply_ids"], ["VR-0100"])
        self.assertIn('contact_email', by_id['ENT-0100']['revision_mapping']['VR-0100']['changed_fields'])
        self.assertEqual(by_id["ENT-0101"]["accepted_reply_ids"], ["VR-0101"])
        reply = next(row for row in tables["verification-replies"] if row["reply_id"] == "VR-0100")
        reply.update(requested_date="2026-03-10", received_date="2026-03-11")
        result = evaluate_replies(app, tables, "2026-03-16")
        self.assertEqual(result["entry_checks"][0]["accepted_reply_ids"], ["VR-0100"])

    def test_unrelated_application_reply_is_never_joined(self):
        tables = copy.deepcopy(self.tables)
        for row in tables["verification-replies"]:
            if row["entry_id"] == "ENT-0100":
                row["application_id"] = "APP-2026-999"
        self.assertEqual(evaluate_replies(self.app(), tables, "2026-03-16")["entry_checks"][0]["verification_rows"], [])

    def test_revised_role_needs_matching_facts_not_a_new_request_date(self):
        tables = copy.deepcopy(self.tables)
        app = dict(self.app(), revision='2', received_date='2026-03-10')
        rows = [dict(r, revision='2') for r in tables['declared-history'] if r['application_id'] == app['application_id']]
        entry = next(r for r in rows if r['entry_id'] == 'ENT-0103')
        entry['role'] = 'Department Chair'
        tables['declared-history'].extend(rows)
        check = lambda: next(c for c in evaluate_replies(app, tables, '2026-03-16')['entry_checks'] if c['entry_id'] == entry['entry_id'])
        self.assertFalse(check()['accepted_reply_ids'])
        reply = next(r for r in tables['verification-replies'] if r['entry_id'] == entry['entry_id'])
        reply['verified_credential'] = 'Employment — Department Chair'
        self.assertLess(reply['requested_date'], app['received_date'])
        self.assertEqual(check()['accepted_reply_ids'], [reply['reply_id']])

    def test_peer_provenance_remains_outstanding_despite_eligibility(self):
        result = evaluate_replies(self.app(), self.tables, "2026-03-16")
        self.assertTrue(all(row["eligible"] for row in result["peer_checks"]))
        self.assertTrue(all(not row["usable"] and not row["provenance_verified"] for row in result["peer_checks"]))

    def test_peer_stale_signature_family_and_membership(self):
        tables = copy.deepcopy(self.tables)
        reply = next(row for row in tables["peer-reference-replies"] if row["reply_id"] == "RR-0100")
        for changes in ({"signature_date": "2024-03-15"}, {"related_or_partner": "Yes"},
                        {"relationship_stated": "We have a society membership in common."},
                        {"last_worked_together_end": "2026-02-17"},
                        {"referee_specialty_stated": "Psychiatry"}):
            original = dict(reply)
            reply.update(changes)
            with self.subTest(changes=changes):
                check = evaluate_replies(self.app(), tables, "2026-03-16")["peer_checks"][0]
                self.assertFalse(check["eligible"])
                self.assertEqual(check["reply"], reply)
            reply.clear()
            reply.update(original)

    def test_missing_peer_request_day64_is_not_a_sent_additional_request(self):
        tables = copy.deepcopy(self.tables)
        tables["peer-reference-replies"] = []
        referee = next(row for row in tables["peer-referees"] if row["referee_id"] == "REF-0100")
        referee["first_request_date"] = "2026-01-01"
        result = evaluate_replies(self.app(), tables, "2026-03-06")
        check = result["peer_checks"][0]
        self.assertEqual(check["followup_dates"], ["2026-01-22", "2026-02-12", "2026-03-06"])
        self.assertIsNone(check["reply_id"])
        self.assertTrue(any("request an additional referee" in row["detail"] and row["due"] == "2026-03-06" for row in result["issues"]))

    def test_nonresponse_after_three_attempts_is_finding(self):
        tables = copy.deepcopy(self.tables)
        tables["verification-replies"] = [row for row in tables["verification-replies"] if row["entry_id"] != "ENT-0103"]
        tables["verification-attempts"] = [dict(attempt_id=f"TEST-{index}", application_id=self.app()["application_id"],
            subject_ref="ENT-0103", attempt_date=f"2026-02-{index:02}") for index in (1, 2, 3)]
        result = evaluate_replies(self.app(), tables, "2026-03-16")
        self.assertTrue(any(row["kind"] == "finding" and row["rule"] == "B08" for row in result["issues"]))

    def test_overdue_peer_reminder_requires_actual_attempt(self):
        tables = copy.deepcopy(self.tables)
        tables["peer-reference-replies"] = []
        tables["verification-attempts"] = []
        referee = next(row for row in tables["peer-referees"] if row["referee_id"] == "REF-0100")
        referee["first_request_date"] = "2026-01-01"
        for attempts, expected_due in (([], "2026-01-22"),
            ([{"attempt_id": "FOLLOW-1", "application_id": self.app()["application_id"],
               "subject_ref": "REF-0100", "attempt_date": "2026-01-23"}], "2026-02-12"),
            ([{"attempt_id": "FOLLOW-LATE", "application_id": self.app()["application_id"],
               "subject_ref": "REF-0100", "attempt_date": "2026-02-20"}], "2026-02-12")):
            tables["verification-attempts"] = attempts
            with self.subTest(attempts=attempts):
                result = evaluate_replies(self.app(), tables, "2026-02-01")
                reminder = next(row for row in result["issues"] if row["detail"].startswith("REF-0100: peer reply"))
                # A February 20 record cannot fulfill a step at February 1.
                due = "2026-01-22" if attempts and attempts[0]["attempt_date"] > "2026-02-01" else expected_due
                self.assertEqual(reminder["due"], due)
        tables["verification-attempts"] = [{"attempt_id": "FOLLOW-LATE", "application_id": self.app()["application_id"],
            "subject_ref": "REF-0100", "attempt_date": "2026-02-20"}]
        result = evaluate_replies(self.app(), tables, "2026-03-16")
        reminder = next(row for row in result["issues"] if row["detail"].startswith("REF-0100: peer reply"))
        self.assertEqual(reminder["due"], "2026-02-12")
        escalation = next(row for row in result["issues"] if row["detail"].startswith("REF-0100: notify applicant"))
        self.assertEqual(escalation["due"], "2026-03-06")

    def supplement(self, fields, path='letters/supplement.md', index_changes=None, text=''):
        index = {'application_id': self.app()['application_id'], 'date': fields.get('Received date', '2026-03-01'),
                 'direction': 'inbound', 'document_path': path}
        index.update(index_changes or {})
        body = '\n'.join('**' + key + ':** ' + value for key, value in fields.items()) + '\n' + text
        return parse_document(path, body, index)

    def accreditation_fields(self):
        return {'Application': self.app()['application_id'], 'Entry': 'ENT-0101', 'Reply': 'VR-0101',
                'Received date': '2026-03-01', 'Accreditation': 'accredited',
                'Attester organization': 'Braypoint Regional Medical Center', 'Attester role': 'Programme Coordinator',
                'Received from': 'Graduate medical education office — Braypoint Regional Medical Center'}

    def peer_fields(self, number='0'):
        referee = next(row for row in self.tables['peer-referees'] if row['referee_id'] == 'REF-010' + number)
        reply = next(row for row in self.tables['peer-reference-replies'] if row['referee_id'] == referee['referee_id'])
        return {'Application': self.app()['application_id'], 'Referee': referee['referee_id'], 'Reply': reply['reply_id'],
                'Received date': reply['received_date'], 'Received from': referee['referee_name'], 'Return method': 'secure portal'}

    def evaluate_documents(self, *docs, before=False, as_of='2026-03-16'):
        return evaluate_replies(self.app(), self.tables, as_of, before, documents=docs)

    def residency_check(self, result):
        return next(row for row in result['entry_checks'] if row['entry_id'] == 'ENT-0101')

    def test_explicit_accreditation_note_clears_only_bound_accepted_entry(self):
        for fact in ['Accreditation: accredited.', 'The programme is accredited.', 'The program is currently accredited.']:
            tables = copy.deepcopy(self.tables)
            next(row for row in tables['verification-replies'] if row['reply_id'] == 'VR-0101')['notes'] = fact
            result = evaluate_replies(self.app(), tables, '2026-03-16')
            self.assertTrue(self.residency_check(result)['accreditation_verified'])
            self.assertEqual(self.residency_check(result)['accreditation_source_refs'], ['verification-replies.csv#VR-0101'])
            self.assertFalse(result['entry_checks'][0]['accreditation_verified'])

    def test_accreditation_notes_do_not_override_source_rejection_or_negation(self):
        for fact in ['The programme is not accredited.', 'Accreditation: unverified.',
                     'Accreditation: accredited pending confirmation.',
                     'It is not confirmed that the programme is accredited.',
                     'No source establishes accreditation; the programme is accredited.']:
            tables = copy.deepcopy(self.tables)
            next(row for row in tables['verification-replies'] if row['reply_id'] == 'VR-0101')['notes'] = fact
            self.assertFalse(self.residency_check(evaluate_replies(self.app(), tables, '2026-03-16'))['accreditation_verified'])
        tables = copy.deepcopy(self.tables)
        reply = next(row for row in tables['verification-replies'] if row['reply_id'] == 'VR-0101')
        reply.update(notes='Accreditation: accredited.', received_from='Applicant')
        self.assertFalse(self.residency_check(evaluate_replies(self.app(), tables, '2026-03-16'))['accreditation_verified'])

    def test_official_indexed_accreditation_supplement_clears_and_traces(self):
        fields = self.accreditation_fields()
        fields.update({'Applicant': 'Marcus T Holloway', 'Revision': '1'})
        doc = self.supplement(fields)
        result = self.evaluate_documents(doc)
        check = self.residency_check(result)
        self.assertTrue(check['accreditation_verified'])
        self.assertEqual(check['accreditation_source_refs'], [doc['path']])
        self.assertTrue(check['accreditation_evidence'][0]['accepted'])
        self.assertFalse(any(issue['detail'].startswith('ENT-0101: required accreditation') for issue in result['issues']))

    def test_accreditation_supplement_identity_source_and_negation_fail(self):
        for changes in ({'Application': 'APP-OTHER'}, {'Applicant': 'Someone Else'}, {'Revision': '2'},
                        {'Entry': 'ENT-OTHER'}, {'Reply': 'VR-OTHER'}, {'Received from': 'Applicant'},
                        {'Attester role': 'Medical Services Professional'}, {'Accreditation': 'not accredited'},
                        {'Accreditation': 'True'}):
            fields = self.accreditation_fields()
            fields.update(changes)
            with self.subTest(changes=changes):
                self.assertFalse(self.residency_check(self.evaluate_documents(self.supplement(fields)))['accreditation_verified'])
        self.assertFalse(self.residency_check(self.evaluate_documents(self.supplement(
            self.accreditation_fields(), index_changes={'application_id': 'APP-OTHER'})))['accreditation_verified'])

    def test_accreditation_supplement_receipt_window_and_index_availability(self):
        for received, index_date, before, expected in [
            ('2026-01-25', '2026-03-01', False, False), ('2026-03-17', '2026-03-17', False, False),
            ('2026-03-01', '2026-03-17', False, False), ('2026-03-16', '2026-03-16', True, False),
            ('2026-03-16', '2026-03-16', False, True), ('invalid', '2026-03-01', False, False),
        ]:
            fields = self.accreditation_fields()
            fields['Received date'] = received
            with self.subTest(received=received, index=index_date, before=before):
                doc = self.supplement(fields, index_changes={'date': index_date})
                self.assertEqual(self.residency_check(self.evaluate_documents(doc, before=before))['accreditation_verified'], expected)

    def test_accreditation_note_cannot_bypass_reply_receipt_window(self):
        for received, before, expected in [('2026-01-25', False, False), ('2026-03-17', False, False),
                                           ('2026-03-16', True, False), ('2026-03-16', False, True)]:
            tables = copy.deepcopy(self.tables)
            reply = next(row for row in tables['verification-replies'] if row['reply_id'] == 'VR-0101')
            reply.update(notes='Accreditation: accredited.', received_date=received)
            with self.subTest(received=received, before=before):
                result = evaluate_replies(self.app(), tables, '2026-03-16', before)
                self.assertEqual(self.residency_check(result)['accreditation_verified'], expected)

    def test_two_peer_return_records_clear_provenance_without_replacing_part_two(self):
        docs = [self.supplement(self.peer_fields(number), path='letters/peer-' + number + '.md') for number in ('0', '1')]
        result = self.evaluate_documents(*docs)
        self.assertTrue(all(check['eligible'] and check['provenance_verified'] and check['usable'] for check in result['peer_checks']))
        self.assertEqual(result['peer_checks'][0]['provenance_source_refs'], [docs[0]['path']])
        self.assertFalse(any(issue['element'] == 'references' for issue in result['issues']))
        self.assertEqual(result['peer_checks'][0]['reply'], self.tables['peer-reference-replies'][0])

    def test_peer_route_record_cannot_resolve_ineligible_part_two(self):
        tables = copy.deepcopy(self.tables)
        next(row for row in tables['peer-reference-replies'] if row['reply_id'] == 'RR-0100')['related_or_partner'] = 'Yes'
        doc = self.supplement(self.peer_fields())
        check = evaluate_replies(self.app(), tables, '2026-03-16', documents=[doc])['peer_checks'][0]
        self.assertFalse(check['eligible'])
        self.assertTrue(check['provenance_verified'])
        self.assertFalse(check['usable'])

    def test_peer_return_record_rejects_wrong_identity_applicant_route_or_missing_method(self):
        for changes in ({'Application': 'APP-OTHER'}, {'Applicant': 'Someone Else'}, {'Referee': 'REF-OTHER'},
                        {'Reply': 'RR-OTHER'}, {'Received from': 'Applicant'}, {'Return method': 'telephone'},
                        {'Return method': ''}, {'Revision': '2'}):
            fields = self.peer_fields()
            fields.update(changes)
            with self.subTest(changes=changes):
                check = self.evaluate_documents(self.supplement(fields))['peer_checks'][0]
                self.assertTrue(check['eligible'])
                self.assertFalse(check['provenance_verified'])

    def test_later_office_return_record_binds_original_return_without_backdating(self):
        fields = self.peer_fields()
        fields.update({'Return date': fields['Received date'], 'Received date': '2026-03-10'})
        doc = self.supplement(fields)
        self.assertTrue(self.evaluate_documents(doc)['peer_checks'][0]['usable'])
        self.assertFalse(self.evaluate_documents(doc, as_of='2026-03-09')['peer_checks'][0]['usable'])
        self.assertFalse(self.evaluate_documents(doc, as_of='2026-03-10', before=True)['peer_checks'][0]['usable'])
        fields.pop('Return date')
        self.assertFalse(self.evaluate_documents(self.supplement(fields))['peer_checks'][0]['usable'])

    def test_peer_return_record_dates_and_index_binding_cannot_be_bypassed(self):
        for received, index_changes in [('2026-01-25', {}), ('2026-03-17', {}),
                                       ('2026-02-18', {'date': '2026-03-17'}),
                                       ('2026-02-18', {'application_id': 'APP-OTHER'}),
                                       ('2026-02-18', {'document_path': 'letters/other.md'}),
                                       ('2026-02-18', {'direction': 'outbound'})]:
            fields = self.peer_fields()
            fields.update({'Received date': received, 'Return date': '2026-02-18'})
            with self.subTest(received=received, changes=index_changes):
                self.assertFalse(self.evaluate_documents(self.supplement(fields, index_changes=index_changes))['peer_checks'][0]['usable'])

    def test_one_usable_peer_does_not_satisfy_required_two_even_when_two_eligible(self):
        result = self.evaluate_documents(self.supplement(self.peer_fields()))
        self.assertEqual(sum(check['eligible'] is True for check in result['peer_checks']), 2)
        self.assertEqual(sum(check['usable'] for check in result['peer_checks']), 1)
        self.assertTrue(any('At least two' in issue['detail'] and 'provenance' in issue['detail'] for issue in result['issues']))
    def test_accreditation_and_route_conflicts_do_not_clear_with_one_positive_record(self):
        positive = self.supplement(self.accreditation_fields(), path='letters/accredited.md')
        negative_fields = self.accreditation_fields()
        negative_fields['Accreditation'] = 'not accredited'
        negative = self.supplement(negative_fields, path='letters/not-accredited.md')
        result = self.evaluate_documents(positive, negative)
        self.assertFalse(self.residency_check(result)['accreditation_verified'])
        self.assertTrue(any(i['kind'] == 'discrepancy' for i in result['issues']))
        direct = self.supplement(self.peer_fields(), path='letters/direct.md')
        applicant_fields = self.peer_fields()
        applicant_fields['Received from'] = 'Applicant'
        applicant = self.supplement(applicant_fields, path='letters/applicant.md')
        self.assertFalse(self.evaluate_documents(direct, applicant)['peer_checks'][0]['usable'])

    def test_unrelated_negative_sentence_does_not_erase_accreditation_fact(self):
        tables = copy.deepcopy(self.tables)
        next(r for r in tables['verification-replies'] if r['reply_id'] == 'VR-0101')['notes'] = 'Accreditation: accredited. No discrepancies.'
        self.assertTrue(self.residency_check(evaluate_replies(self.app(), tables, '2026-03-16'))['accreditation_verified'])


if __name__ == '__main__':
    unittest.main()
