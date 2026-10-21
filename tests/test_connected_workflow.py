"""Synthetic evidence-to-activation paths through the actual batch processor.

No supplied application is made ready, no readiness/admission result is injected,
and no input, output, or appointment record is written by these tests.
"""

from copy import deepcopy
from pathlib import Path
import unittest

from credentialing.engine import ELEMENTS, process_batch
from credentialing.io import load_sources
from credentialing.policy import registry


ROOT = Path(__file__).resolve().parents[1]
APP = "SYNTHETIC-CONNECTED-APP"
EXECUTIVE = "Executive Committee of the Medical Staff"


class ConnectedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load_sources(ROOT / "sources")
        cls.reg = registry(cls.sources)

    def fixture(self):
        app = {"application_id": APP, "revision": "1", "first_received_date": "2026-01-01",
               "received_date": "2026-01-01", "first_name": "Synthetic", "middle_name": "",
               "last_name": "Applicant", "birth_year": "1980", "discipline": "Family Medicine",
               "release_signed_date": "2026-01-01", "cv_received_date": "2026-01-01", "revision_reason": ""}
        common = {"application_id": APP, "revision": "1"}
        history = [
            dict(common, entry_id="SYN-SCHOOL", entry_type="medical-school", organization="Synthetic School",
                 role="Doctor of Medicine", from_date="2000-08-01", to_date="2004-06-30"),
            dict(common, entry_id="SYN-RESIDENCY", entry_type="residency", organization="Synthetic Training Hospital",
                 role="Family Medicine Residency", from_date="2004-07-01", to_date="2007-06-30"),
            dict(common, entry_id="SYN-WORK", entry_type="employment", organization="Synthetic Clinic",
                 role="Staff Physician", from_date="2007-07-01", to_date="", contact_name="Synthetic Office"),
        ]
        offices = [("Registrar's office", "Registrar", "Degree — Doctor of Medicine"),
                   ("Graduate medical education office", "Programme Coordinator", "Residency — Family Medicine"),
                   ("Medical staff office", "Medical Staff Services", "Employment — Staff Physician")]
        verification = []
        for entry, (office, role, credential) in zip(history, offices):
            verification.append({"reply_id": "SYN-VERIFY-" + entry["entry_id"], "application_id": APP,
                "entry_id": entry["entry_id"], "attester_organization": entry["organization"],
                "attester_role": role, "received_from": office + " — " + entry["organization"],
                "verified_credential": credential, "verified_from": entry["from_date"], "verified_to": entry["to_date"],
                "outcome": "confirmed", "received_date": "2026-01-15", "notes": "Accreditation: accredited." if entry["entry_type"] != "employment" else ""})
        tables = {
            "applications": [app], "declared-history": history, "verification-replies": verification,
            "verification-attempts": [], "licence-lookup-other-states": [], "correspondence": [],
            "licence-lookup-wa": [{"credentialnumber": "SYN-WA", "lastname": "Applicant", "firstname": "Synthetic",
                "middlename": "", "birthyear": "1980", "lookup_date": "2026-01-15", "status": "Active",
                "expirationdate": "2027-12-31", "firstissuedate": "2007-07-01", "actiontaken": "No"}],
            "declared-credentials": [dict(common, declaration_id="SYN-LICENCE", credential_class="licence",
                jurisdiction_or_board="WA", number_declared="SYN-WA"),
                dict(common, declaration_id="SYN-CERT", credential_class="certification",
                     jurisdiction_or_board="ABFM", issuer="American Board of Family Medicine")],
            "application-disclosures": [dict(common, question_code=f"PPQ-{n}", answer="No", applicant_comment="") for n in range(1, 9)],
            "privilege-requests": [dict(common, request_id="SYN-REQUEST-" + code, privilege_code=code,
                criteria_version_cited=self.reg["criteria_version"]) for code in ("PRIV-FM", "PRIV-HOSP")],
            "certification-replies": [{"reply_id": "SYN-CERT-REPLY", "application_id": APP, "declaration_id": "SYN-CERT",
                "board_name": "American Board of Family Medicine", "board_code": "ABFM",
                "received_from": "American Board of Family Medicine", "certificate_specialty": "Family Medicine",
                "certification_status": "Active", "initial_certification_date": "2007-08-01", "expiry_date": "2027-12-31",
                "received_date": "2026-01-15", "reply_method": "secure portal", "notes": ""}],
            "peer-referees": [dict(common, referee_id=f"SYN-PEER-{n}", referee_name=f"Synthetic Referee {n}",
                first_request_date="2026-01-02") for n in (1, 2)],
            "peer-reference-replies": [{"reply_id": f"SYN-PEER-REPLY-{n}", "referee_id": f"SYN-PEER-{n}",
                "application_id": APP, "signature_date": "2026-01-14", "received_date": "2026-01-15",
                "related_or_partner": "No", "relationship_stated": "Worked together directly",
                "referee_specialty_stated": "Family Medicine", "last_worked_together_end": "2025-12-31"} for n in (1, 2)],
        }
        batch = {"tables": tables, "documents": {}, "export_date": "2026-04-30", "input_hashes": {}}
        self.document(batch, "signature", "Signed application", {"Signature": "Synthetic Applicant", "Signature date": "2026-01-01"})
        cv = "| Entry | Organization | Role | From | To |\n| --- | --- | --- | --- | --- |\n"
        for row in history:
            cv += "| " + " | ".join(row[k] for k in ("entry_id", "organization", "role", "from_date", "to_date")) + " |\n"
        self.document(batch, "cv", "Curriculum vitae", {}, body=cv)
        for n in (1, 2):
            self.document(batch, f"peer-{n}", "Synthetic direct peer return", {
                "Referee": f"SYN-PEER-{n}", "Reply": f"SYN-PEER-REPLY-{n}",
                "Received from": f"Synthetic Referee {n}", "Return method": "secure portal"})
        return batch

    def document(self, batch, slug, title, fields, when="2026-01-15", body=""):
        path = "synthetic/" + slug + ".md"
        labels = {"Application": APP, "Applicant": "Synthetic Applicant", "Revision": "1", "Received date": when, **fields}
        batch["documents"][path] = "# " + title + "\n\n" + "\n".join(f"**{key}:** {value}" for key, value in labels.items()) + "\n\n" + body
        batch["tables"]["correspondence"].append({"application_id": APP, "date": when, "direction": "inbound", "document_path": path})

    def decisions(self, batch, *, conditional=False):
        for slug, body, when, outcome, privileges in [
            ("mec", EXECUTIVE, "2026-04-01", "recommended", "PRIV-FM; PRIV-HOSP"),
            ("gb", "Governing Body", "2026-04-10", "approved-with-conditions" if conditional else "approved", "PRIV-FM"),
        ]:
            role = next(row for row in self.reg["roles"] if row["role"] == "Chair, " + body)
            fields = {"Decision ID": "SYN-" + slug.upper(), "Body": body, "Signatory": role["name"],
                "Role": role["role"], "Decision date": when, "Outcome": outcome, "Privileges": privileges,
                "Criteria version": self.reg["criteria_version"]}
            if slug == "gb":
                fields["Effective date"] = "2026-05-01"
            text = f"Signed: {role['name']}, {role['role']}, {when}.\n"
            if conditional and slug == "gb":
                fields["Reason"] = "Synthetic recorded monitoring requirements"
                text += "\n## Conditions\n- Reverify Washington licence — due 2026-11-01\n- Obtain documented concurrence — due 2026-06-30\n"
            self.document(batch, slug, "Synthetic committee record", fields, when, text)

    def process(self, batch):
        result = process_batch(batch, self.sources)
        self.assertEqual(len(result["applications"]), 1)
        return result["applications"][0], result["history"]["applications"][APP]

    def test_qualifying_evidence_clears_intake_and_element_holds_and_establishes_readiness(self):
        complete = self.fixture()
        missing = deepcopy(complete)
        for table in ("verification-replies", "certification-replies", "peer-reference-replies", "correspondence"):
            missing["tables"][table] = []
        missing["documents"] = {}
        held, held_history = self.process(missing)
        self.assertFalse(held["packet_presentable"])
        self.assertEqual(held["status"], "intake-incomplete")
        self.assertIn("application signature and date evidence", held_history["assessments"][-1]["intake"]["missing"])
        for element in ("education", "experience", "certification", "references"):
            self.assertNotEqual(held["elements"][element], "resolved")
        ready, history = self.process(complete)
        assessed = history["assessments"][-1]
        self.assertEqual(ready["status"], "packet-presentable")
        self.assertTrue(ready["packet_presentable"])
        self.assertEqual(ready["elements"], dict.fromkeys(ELEMENTS, "resolved"))
        self.assertEqual(assessed["issues"], [])
        self.assertEqual(assessed["intake"]["missing"], [])
        self.assertTrue(assessed["intake"]["document_evidence"]["cv"]["resolved"])
        self.assertTrue(all(row["accepted_reply_ids"] for row in assessed["entry_checks"]))
        self.assertTrue(all(row["usable"] for row in assessed["peer_checks"]))
        self.assertEqual(assessed["privileges"]["supported"], ["PRIV-FM", "PRIV-HOSP"])
        self.assertIsNone(ready["activation"])

    def test_surplus_request_does_not_hold_ready_file_and_closes_only_on_recorded_presentation(self):
        batch = self.fixture()
        batch['tables']['peer-referees'].append({'application_id': APP, 'revision': '1',
            'referee_id': 'SYN-SURPLUS', 'referee_name': 'Synthetic Extra', 'first_request_date': '2026-01-02'})
        ready, history = self.process(batch)
        self.assertTrue(ready['packet_presentable'])
        self.assertEqual(ready['elements']['references'], 'resolved')
        self.assertTrue(any('SYN-SURPLUS' in a['item'] for a in ready['action_queue']))
        self.assertNotIn('closed_surplus_requests', history['assessments'][-1])
        self.decisions(batch)
        decided, history = self.process(batch)
        self.assertTrue(all(d['admitted'] for d in decided['decisions']))
        self.assertFalse(any('SYN-SURPLUS' in a['item'] for a in decided['action_queue']))
        self.assertEqual(history['assessments'][-1]['closed_surplus_requests'][0]['decision_id'], 'SYN-MEC')
        self.assertEqual(len(history['assessments'][-1]['peer_checks']), 3)

    def test_high_risk_mention_does_not_substitute_for_returned_disposition(self):
        for narrative, expected in [
            ('PPQ-2 remains under review. Do not present the file.', False),
            ('I have read the PPQ-2 explanation.', False),
            ('Present the file to the Executive Committee after I complete review.', False),
            ('Present the file to the Executive Committee with evidence if PPQ-2 is cleared.', False),
            ('Present the file to the Executive Committee of the Medical Staff and the Governing Body with the PPQ-2 finding attached.', True),
        ]:
            batch = self.fixture()
            row = next(r for r in batch['tables']['application-disclosures'] if r['question_code'] == 'PPQ-2')
            row.update(answer='Yes', applicant_comment='Synthetic disclosed finding for recorded CD review')
            role = next(r for r in self.reg['roles'] if r['role'] == 'Clinical Director')
            self.document(batch, 'clinical', "Clinical Director's disposition — PPQ-2", {
                'Date': '2026-03-01', 'Recorded by': role['name'] + ', Clinical Director'},
                '2026-03-01', narrative + '\n\n' + role['name'] + '\nClinical Director\n')
            self.decisions(batch)
            result, history = self.process(batch)
            self.assertEqual(result['packet_presentable'], expected)
            self.assertEqual(all(d['admitted'] for d in result['decisions']), expected)
            finding = next(i for i in history['assessments'][-1]['issues'] if i['element'] == 'intake' and i['kind'] == 'finding')
            self.assertEqual(bool(finding.get('clinical_disposition_sources')), expected)

    def test_same_day_evidence_cannot_retroactively_admit_recommendation_or_approval(self):
        for late_evidence in ("signature", "certification"):
            with self.subTest(evidence=late_evidence):
                batch = self.fixture()
                if late_evidence == "signature":
                    batch["documents"]["synthetic/signature.md"] = batch["documents"]["synthetic/signature.md"].replace("2026-01-15", "2026-04-01")
                    batch["tables"]["correspondence"][0]["date"] = "2026-04-01"
                else:
                    batch["tables"]["certification-replies"][0]["received_date"] = "2026-04-01"
                self.decisions(batch)
                result, history = self.process(batch)
                self.assertTrue(result["packet_presentable"])
                recommendation, approval = history["decisions"]
                self.assertFalse(recommendation["admitted"])
                self.assertTrue(recommendation["failures"][0].startswith("4 prior presentability"))
                self.assertFalse(recommendation["readiness_evidence"]["packet_presentable"])
                self.assertTrue(recommendation["readiness_evidence"]["historical_before_decision"])
                self.assertFalse(approval["admitted"])
                self.assertTrue(any(reason.startswith("7 recommendation") for reason in approval["failures"]))
                self.assertEqual(result["status"], "decision-inadmissible")
                self.assertIsNone(result["approval_decision_id"])
                self.assertIsNone(result["activation"])

    def test_actual_same_revision_mec_and_gb_admission_activates_exact_grant_on_effective_day(self):
        batch = self.fixture()
        self.decisions(batch)
        before, history = self.process(batch)
        self.assertEqual(before["status"], "approved-not-yet-effective")
        self.assertEqual(before["approval_decision_id"], "SYN-GB")
        self.assertEqual(before["activation"], {"active_at_export": False, "effective_date": "2026-05-01",
            "cycle_end": "2027-04-30", "privileges": ["PRIV-FM"]})
        self.assertEqual([row["fields"]["body"] for row in history["decisions"]], [EXECUTIVE, "Governing Body"])
        for decision in history["decisions"]:
            self.assertTrue(decision["admitted"], decision["failures"])
            self.assertEqual(decision["fields"]["revision"], "1")
            self.assertEqual(decision["readiness_evidence"]["application"]["revision"], "1")
            self.assertTrue(decision["readiness_evidence"]["packet_presentable"])
            self.assertTrue(decision["readiness_evidence"]["historical_before_decision"])
        batch["export_date"] = "2026-05-01"
        active, _ = self.process(batch)
        self.assertEqual(active["status"], "active")
        self.assertTrue(active["activation"]["active_at_export"])
        self.assertEqual(active["activation"]["privileges"], ["PRIV-FM"])
        self.assertEqual(active["monitored_conditions"], [])

    def test_admitted_conditions_preserve_explicit_dates_and_general_wa_expiry(self):
        batch = self.fixture()
        batch["export_date"] = "2026-05-01"
        batch["tables"]["licence-lookup-wa"][0]["expirationdate"] = "2026-11-30"
        self.decisions(batch, conditional=True)
        original = deepcopy(batch)
        result, history = self.process(batch)
        self.assertTrue(all(row["admitted"] for row in history["decisions"]))
        self.assertEqual(result["status"], "active-with-conditions")
        self.assertTrue(result["activation"]["active_at_export"])
        self.assertEqual(result["activation"]["privileges"], ["PRIV-FM"])
        self.assertEqual(result["monitored_conditions"][:2], [
            {"condition": "Reverify Washington licence — due 2026-11-01", "due": "2026-11-01"},
            {"condition": "Obtain documented concurrence — due 2026-06-30", "due": "2026-06-30"}])
        self.assertEqual(len(result["monitored_conditions"]), 3)
        self.assertEqual(result["monitored_conditions"][2]["due"], "2026-11-30")
        self.assertIn("SYN-WA", result["monitored_conditions"][2]["condition"])
        self.assertEqual(result["action_queue"], [])
        self.assertEqual(batch, original)


if __name__ == "__main__":
    unittest.main()
