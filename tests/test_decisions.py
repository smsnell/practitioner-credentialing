"""Synthetic decision records checked against the supplied standing registry.

These fixtures establish only the evidence they explicitly contain. No supplied
application batch is processed, and no synthetic record becomes business state.
"""

from pathlib import Path
import unittest

from credentialing.documents import parse_document
from credentialing.engine import check_decision
from credentialing.io import load_sources
from credentialing.policy import registry


ROOT = Path(__file__).resolve().parents[1]
EXECUTIVE = "Executive Committee of the Medical Staff"
GOVERNING = "Governing Body"


class DecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = registry(load_sources(ROOT / "sources"))

    def setUp(self):
        self.app = {"application_id": "SYNTHETIC-APP-001", "revision": "2",
                    "first_name": "Test", "middle_name": "", "last_name": "Applicant",
                    "received_date": "2026-02-01"}
        self.assessed = {"packet_presentable": True}

    def document(self, **changes):
        body = changes.get("body", EXECUTIVE)
        role = next(item for item in self.reg["roles"] if item["role"] == f"Chair, {body}")
        fields = {"decision_id": "SYNTHETIC-MEC-001", "body": body, "signatory": role["name"],
                  "role": role["role"], "application": self.app["application_id"],
                  "revision": self.app["revision"], "decision_date": "2026-03-10",
                  "outcome": "recommended", "privileges": "PRIV-FM; PRIV-IM",
                  "criteria_version": self.reg["criteria_version"], "reason": "",
                  "effective_date": "", "supersedes": ""}
        fields.update(changes)
        labels = {"decision_id": "Decision ID", "decision_date": "Decision date",
                  "criteria_version": "Criteria version", "effective_date": "Effective date"}
        text = "# Synthetic decision fixture\n\n" + "\n".join(
            f"**{labels.get(key, key.capitalize())}:** {value}  " for key, value in fields.items())
        text += f"\n\nSigned: {fields['signatory']}, {fields['role']}, {fields['decision_date']}.\n"
        index = {"letter_id": "SYNTHETIC-LTR-001", "application_id": self.app["application_id"],
                 "date": fields["decision_date"], "direction": "inbound"}
        return parse_document("synthetic/decision.md", text, index)

    def failures(self, doc=None, *, app=None, assessed=None, prior=None):
        return check_decision(doc or self.document(), app or self.app, assessed or self.assessed,
                              self.reg, prior or [])

    def recommendation(self, **changes):
        doc = self.document(**{"decision_id": "SYNTHETIC-MEC-PRIOR", "decision_date": "2026-03-09", **changes})
        failures = self.failures(doc)
        return {"admitted": not failures, "fields": doc["fields"], "failures": failures}

    def approval(self, **changes):
        return self.document(**{"body": GOVERNING, "outcome": "approved", "decision_id": "SYNTHETIC-GB-001", **changes})

    def test_positive_recommendation_has_no_reason_requirement(self):
        doc = self.document()
        self.assertEqual(doc["fields"]["reason"], "")
        self.assertEqual(self.failures(doc), [])

    def test_unauthorized_committee_approval_retains_first_and_all_failures(self):
        doc = self.document(outcome="approved", role="Invented authority", revision="99",
                            criteria_version="INVENTED-VERSION")
        failures = self.failures(doc, assessed={"packet_presentable": False})
        self.assertTrue(failures[0].startswith("1 body/outcome authority"))
        self.assertEqual([item[0] for item in failures[:5]], ["1", "2", "3", "4", "6"])
        for body in [EXECUTIVE, "Credentials Committee"]:
            with self.subTest(body=body):
                self.assertTrue(self.failures(self.document(body=body, outcome="approved"))[0].startswith("1 "))

    def test_signatory_role_term_and_signature_are_verified(self):
        for doc in [self.document(signatory="An unlisted person"), self.document(role="Voting member"),
                    self.document(decision_date="2028-01-01")]:
            with self.subTest(fields=doc["fields"]):
                self.assertTrue(self.failures(doc)[0].startswith("2 signatory authority"))
        doc = self.document()
        doc["text"] = doc["text"].split("\n\nSigned:")[0]
        self.assertTrue(self.failures(doc)[0].startswith("2 signatory authority"))

    def test_wrong_revision_and_applicant_fail(self):
        for changes in [{"revision": "1"}, {"application": "SYNTHETIC-OTHER-APP"}]:
            with self.subTest(changes=changes):
                self.assertTrue(self.failures(self.document(**changes))[0].startswith("3 applicant/revision"))

    def test_missing_or_same_day_readiness_is_not_prior_presentability(self):
        self.assertTrue(self.failures(assessed={"packet_presentable": False})[0].startswith("4 prior presentability"))
        same_day_revision = dict(self.app, received_date="2026-03-10")
        self.assertTrue(self.failures(app=same_day_revision)[0].startswith("4 prior presentability"))

    def test_recorded_criteria_version_must_be_in_force(self):
        self.assertEqual(self.failures(self.document(criteria_version=self.reg["criteria_version"])), [])
        self.assertTrue(self.failures(self.document(criteria_version="LARK-PRIV-UNKNOWN"))[0].startswith("6 criteria version"))
        early = self.failures(self.document(decision_date="2025-12-31"))
        self.assertTrue(any(item.startswith("6 criteria version") for item in early))

    def test_governing_body_approval_requires_separately_valid_recommendation(self):
        approval = self.approval()
        self.assertTrue(self.failures(approval)[0].startswith("7 recommendation"))
        recommendation = self.recommendation()
        self.assertTrue(recommendation["admitted"])
        self.assertEqual(self.failures(approval, prior=[recommendation]), [])

    def test_invalid_wrong_revision_and_same_day_recommendations_do_not_substitute(self):
        invalid = self.recommendation(signatory="Unlisted chair")
        self.assertFalse(invalid["admitted"])
        wrong_revision = self.recommendation(revision="1")
        # Prior admission can be valid against its own older revision; it still
        # cannot authorize the current revision's approval.
        wrong_revision["admitted"] = True
        same_day = self.recommendation()
        same_day["fields"]["decision_date"] = "2026-03-10"
        other_app = self.recommendation()
        other_app["fields"]["application"] = "SYNTHETIC-OTHER-APP"
        for recommendation in [invalid, wrong_revision, same_day, other_app]:
            with self.subTest(recommendation=recommendation):
                self.assertTrue(self.failures(self.approval(), prior=[recommendation])[0].startswith("7 recommendation"))

    def test_duplicate_governing_decision_needs_explicit_supersession(self):
        recommendation = self.recommendation()
        earlier = self.approval(decision_date="2026-03-09", decision_id="SYNTHETIC-GB-EARLIER")
        previous = {"admitted": True, "fields": earlier["fields"], "failures": []}
        prior = [recommendation, previous]
        for supersedes in ["", "SYNTHETIC-UNKNOWN"]:
            with self.subTest(supersedes=supersedes):
                self.assertTrue(self.failures(self.approval(supersedes=supersedes), prior=prior)[0].startswith("8 duplicate/supersession"))
        self.assertEqual(self.failures(self.approval(supersedes="SYNTHETIC-GB-EARLIER"), prior=prior), [])
        # A second recommendation and a normal recommendation -> GB sequence
        # do not invoke the same-body Governing Body supersession rule.
        self.assertEqual(self.failures(self.document(), prior=[recommendation]), [])
        self.assertEqual(self.failures(self.approval(), prior=[recommendation]), [])

    def test_negative_outcomes_and_conditional_approval_require_reason(self):
        for outcome in ["denied", "deferred-pending-information", "approved-with-conditions"]:
            with self.subTest(outcome=outcome):
                doc = self.approval(outcome=outcome)
                self.assertTrue(self.failures(doc, prior=[self.recommendation()])[0].startswith("5 outcome/reason"))
                doc["fields"]["reason"] = "Synthetic recorded human disposition."
                if outcome == "approved-with-conditions":
                    doc["text"] += "\n## Conditions\n- Reverify licence by 2026-11-30.\n"
                self.assertEqual(self.failures(doc, prior=[self.recommendation()]), [])

    def test_unpublished_or_missing_privileges_are_refused(self):
        for privileges in ["", "PRIV-INVENTED", "PRIV-FM; PRIV-INVENTED"]:
            with self.subTest(privileges=privileges):
                self.assertTrue(self.failures(self.document(privileges=privileges))[0].startswith("5 outcome/reason"))

    def test_retroactive_effective_date_cannot_authorize_activation(self):
        failures = self.failures(self.approval(effective_date="2026-03-01"), prior=[self.recommendation()])
        self.assertEqual(len(failures), 1)
        self.assertIn("Effective-date backdate", failures[0])
        self.assertEqual(self.failures(self.approval(effective_date="2026-03-10"), prior=[self.recommendation()]), [])
        self.assertEqual(self.failures(self.approval(effective_date="2026-04-01"), prior=[self.recommendation()]), [])


if __name__ == "__main__":
    unittest.main()
