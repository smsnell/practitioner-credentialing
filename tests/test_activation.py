"""Explicitly synthetic appointment projections using the actual authority roster.

These fixtures establish a ready packet only for exercising the admitted-outcome
projection. They do not establish readiness or approval for any supplied file.
No real batch is processed and no output artifact is written.
"""

from copy import deepcopy
from pathlib import Path
import unittest

from credentialing.documents import parse_document
from credentialing.engine import ELEMENTS, check_decision, decision_conditions, project
from credentialing.io import load_sources
from credentialing.policy import registry


ROOT = Path(__file__).resolve().parents[1]
EXECUTIVE = "Executive Committee of the Medical Staff"
GOVERNING = "Governing Body"


class ActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = registry(load_sources(ROOT / "sources"))

    def setUp(self):
        self.app = {"application_id": "SYNTHETIC-ACTIVATION-APP", "revision": "1",
                    "received_date": "2026-01-01", "first_name": "Test", "middle_name": "", "last_name": "Applicant"}
        self.assessed = {"intake": {"missing": [], "notices": []}, "packet_presentable": True,
                         "elements": {element: "resolved" for element in ELEMENTS}, "action_queue": [],
                         "licensure": {"wa": None},
                         "privileges": {"requested": ["PRIV-FM", "PRIV-IM"], "supported": ["PRIV-FM", "PRIV-IM"]}}
        self.recommendation = self.decision(decision_id="SYNTHETIC-MEC-001", body=EXECUTIVE,
                                            outcome="recommended", when="2026-04-01", privileges="PRIV-FM; PRIV-IM")
        self.assertTrue(self.recommendation["admitted"], self.recommendation["failures"])

    def decision(self, *, decision_id="SYNTHETIC-GB-001", body=GOVERNING, outcome="approved", when="2026-04-10",
                 privileges="PRIV-FM", effective="", reason="", conditions=(), supersedes="", prior=None, signatory=None):
        role = next(row for row in self.reg["roles"] if row["role"] == f"Chair, {body}")
        name = signatory or role["name"]
        fields = {"Decision ID": decision_id, "Body": body, "Signatory": name, "Role": role["role"],
                  "Application": self.app["application_id"], "Revision": self.app["revision"], "Decision date": when,
                  "Outcome": outcome, "Privileges": privileges, "Criteria version": self.reg["criteria_version"],
                  "Reason": reason, "Effective date": effective, "Supersedes": supersedes}
        text = "# Synthetic committee fixture\n\n" + "\n".join(f"**{key}:** {value}  " for key, value in fields.items())
        if conditions:
            text += "\n\n## Conditions\n" + "\n".join("- " + condition for condition in conditions)
        text += f"\n\nSigned: {name}, {role['role']}, {when}.\n"
        doc = parse_document("synthetic/" + decision_id + ".md", text,
                             {"application_id": self.app["application_id"], "date": when, "direction": "inbound"})
        if prior is None:
            prior = [] if body == EXECUTIVE else [self.recommendation]
        failures = check_decision(doc, self.app, self.assessed, self.reg, prior)
        return {"fields": doc["fields"], "source": doc["path"], "admitted": not failures,
                "failures": failures, "conditions": decision_conditions(doc)[0]}

    def project(self, decision, *, as_of="2026-04-20", prior=None):
        decisions = [self.recommendation, *(prior or []), decision]
        return project(self.app, self.assessed, decisions, [], self.reg, as_of)

    def test_admitted_approval_activates_only_granted_subset_on_effective_day(self):
        approval = self.decision(effective="2026-05-01")
        self.assertTrue(approval["admitted"], approval["failures"])
        before = self.project(approval, as_of="2026-04-30")
        self.assertEqual(before["status"], "approved-not-yet-effective")
        self.assertEqual(before["approval_decision_id"], "SYNTHETIC-GB-001")
        self.assertEqual(before["activation"], {"active_at_export": False, "effective_date": "2026-05-01",
                                              "cycle_end": "2027-04-30", "privileges": ["PRIV-FM"]})
        active = self.project(approval, as_of="2026-05-01")
        self.assertEqual(active["status"], "active")
        self.assertTrue(active["activation"]["active_at_export"])
        self.assertEqual(active["activation"]["privileges"], ["PRIV-FM"])
        self.assertNotIn("PRIV-IM", active["activation"]["privileges"])
        self.assertEqual(active["monitored_conditions"], [])

    def test_absent_effective_date_uses_decision_date_and_one_year_inclusive_cycle(self):
        approval = self.decision()
        self.assertTrue(approval["admitted"], approval["failures"])
        result = self.project(approval, as_of="2026-04-10")
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["activation"]["effective_date"], "2026-04-10")
        self.assertEqual(result["activation"]["cycle_end"], "2027-04-09")
        self.assertTrue(self.project(approval, as_of="2027-04-09")["activation"]["active_at_export"])

    def test_explicit_condition_dates_and_general_wa_expiry_are_both_retained(self):
        self.assessed["licensure"]["wa"] = {"credentialnumber": "SYNTHETIC-WA-001", "expirationdate": "2026-11-30"}
        approval = self.decision(outcome="approved-with-conditions", reason="Synthetic recorded monitoring requirements",
                                 conditions=["Reverify Washington licence — due 2026-11-01", "Obtain documented concurrence — due 2026-06-30"])
        self.assertTrue(approval["admitted"], approval["failures"])
        original = deepcopy((self.app, self.assessed, approval))
        result = self.project(approval)
        self.assertEqual(result["status"], "active-with-conditions")
        self.assertEqual({item["due"] for item in result["monitored_conditions"]}, {"2026-06-30", "2026-11-01", "2026-11-30"})
        expiry = next(item for item in result["monitored_conditions"] if item["due"] == "2026-11-30")
        self.assertIn("SYNTHETIC-WA-001", expiry["condition"])
        self.assertEqual(result["action_queue"], [])
        self.assertEqual((self.app, self.assessed, approval), original)

    def test_due_condition_creates_owned_clinical_review_without_invented_suspension(self):
        approval = self.decision(outcome="approved-with-conditions", reason="Synthetic monitoring requirement",
                                 conditions=["Obtain documented concurrence — due 2026-06-30"])
        self.assertTrue(approval["admitted"], approval["failures"])
        for as_of in ["2026-06-30", "2026-07-01"]:
            with self.subTest(as_of=as_of):
                result = self.project(approval, as_of=as_of)
                self.assertEqual(result["status"], "active-with-conditions")
                self.assertTrue(result["activation"]["active_at_export"])
                self.assertEqual(len(result["action_queue"]), 1)
                self.assertEqual(result["action_queue"][0]["owner"], "Clinical Director")
                self.assertEqual(result["action_queue"][0]["due"], "2026-06-30")
                self.assertIn("Unmet monitored condition", result["action_queue"][0]["item"])
                self.assertEqual(len(result["monitored_conditions"]), 1)

    def test_refused_approval_never_activates_or_creates_monitoring_conditions(self):
        approval = self.decision(signatory="Unlisted person", outcome="approved-with-conditions", reason="Synthetic condition",
                                 conditions=["Obtain documented concurrence — due 2026-06-30"])
        self.assertFalse(approval["admitted"])
        result = self.project(approval)
        self.assertEqual(result["status"], "decision-inadmissible")
        self.assertIsNone(result["approval_decision_id"])
        self.assertIsNone(result["activation"])
        self.assertEqual(result["monitored_conditions"], [])
        self.assertEqual(result["action_queue"][0]["owner"], "Medical Services Professional")

    def test_explicit_superseding_approval_replaces_effective_privilege_grant(self):
        first = self.decision()
        replacement = self.decision(decision_id="SYNTHETIC-GB-002", when="2026-04-15", privileges="PRIV-IM",
                                    supersedes=first["fields"]["decision_id"], prior=[self.recommendation, first])
        self.assertTrue(replacement["admitted"], replacement["failures"])
        result = self.project(replacement, prior=[first])
        self.assertEqual(result["approval_decision_id"], "SYNTHETIC-GB-002")
        self.assertEqual(result["activation"]["privileges"], ["PRIV-IM"])
        self.assertEqual(result["activation"]["effective_date"], "2026-04-15")
        self.assertEqual(result["activation"]["cycle_end"], "2027-04-14")
        self.assertEqual([row["decision_id"] for row in result["decisions"]], ["SYNTHETIC-MEC-001", "SYNTHETIC-GB-001", "SYNTHETIC-GB-002"])

    def test_explicit_superseding_nonapproval_does_not_retain_old_authorization(self):
        first = self.decision(outcome="approved-with-conditions", reason="Synthetic monitoring requirement",
                              conditions=["Obtain documented concurrence — due 2026-06-30"])
        self.assertTrue(first["admitted"], first["failures"])
        for outcome, status in [("denied", "denied"), ("deferred-pending-information", "deferred")]:
            with self.subTest(outcome=outcome):
                replacement = self.decision(decision_id="SYNTHETIC-GB-002", when="2026-04-15", outcome=outcome,
                                            reason="Synthetic superseding human outcome", privileges="",
                                            supersedes=first["fields"]["decision_id"], prior=[self.recommendation, first])
                self.assertTrue(replacement["admitted"], replacement["failures"])
                result = self.project(replacement, prior=[first])
                self.assertEqual(result["status"], status)
                self.assertIsNone(result["approval_decision_id"])
                self.assertIsNone(result["activation"])
                self.assertEqual(result["monitored_conditions"], [])


if __name__ == "__main__":
    unittest.main()
