"""Refused decisions remain explicit owned work, including on terminal files."""

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from credentialing.engine import ELEMENTS, process_batch, project
from credentialing.io import load_batch, load_sources


ROOT = Path(__file__).resolve().parents[1]
MSP_OWNERS = {"Medical Services Professional", "MSP"}


def matching_actions(actions, decision_id, reason):
    return [action for action in actions if action["owner"] in MSP_OWNERS
            and decision_id in action["item"] and reason in action["item"]]


class RealRefusalActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = process_batch(load_batch(ROOT / "inputs/batch-01"), load_sources(ROOT / "sources"))

    def test_all_six_real_refusals_have_one_owned_action_and_no_invented_due_date(self):
        count = 0
        for app in self.result["applications"]:
            recorded = self.result["history"]["applications"][app["application_id"]]["decisions"]
            for decision in recorded:
                if decision["admitted"]:
                    continue
                count += 1
                decision_id = decision["fields"]["decision_id"]
                reason = decision["failures"][0]
                with self.subTest(application=app["application_id"], decision=decision_id):
                    actions = matching_actions(app["action_queue"], decision_id, reason)
                    self.assertEqual(len(actions), 1)
                    self.assertIsNone(actions[0]["due"])
                    published = next(row for row in app["decisions"] if row["decision_id"] == decision_id)
                    self.assertFalse(published["admitted"])
                    self.assertEqual(published["reason"], reason)
        self.assertEqual(count, 6)


class RefusalProjectionTests(unittest.TestCase):
    def setUp(self):
        self.app = {"application_id": "SYNTHETIC-APP", "revision": "1"}
        self.assessed = {"intake": {"missing": [], "notices": []},
                         "packet_presentable": True, "elements": {key: "resolved" for key in ELEMENTS},
                         "licensure": {"wa": None}, "action_queue": []}
        self.reason = "4 prior presentability: required evidence was not established"
        self.decision = {"fields": {"decision_id": "SYNTHETIC-MEC-001", "revision": "1",
                                    "body": "Executive Committee of the Medical Staff", "outcome": "recommended"},
                         "admitted": False, "failures": [self.reason, "6 criteria version: not established"]}

    def project(self, decisions=None):
        return project(self.app, self.assessed, [self.decision] if decisions is None else decisions,
                       [], {}, "2026-03-16")

    def refusal_actions(self, result):
        return matching_actions(result["action_queue"], self.decision["fields"]["decision_id"], self.reason)

    def test_refused_decision_has_exact_id_first_reason_and_no_invented_deadline(self):
        result = self.project()
        actions = self.refusal_actions(result)
        self.assertEqual(len(actions), 1)
        self.assertIsNone(actions[0]["due"])
        self.assertEqual(result["decisions"][0]["reason"], self.reason)

    def test_admitted_recommendation_creates_no_refusal_action(self):
        admitted = deepcopy(self.decision)
        admitted.update(admitted=True, failures=[])
        result = self.project([admitted])
        self.assertEqual(result["action_queue"], [])
        self.assertTrue(result["decisions"][0]["admitted"])
        self.assertIsNone(result["decisions"][0]["reason"])

    def test_equivalent_existing_msp_action_retains_recorded_deadline(self):
        for owner in sorted(MSP_OWNERS):
            existing = {"item": f"Review SYNTHETIC-MEC-001: {self.reason}", "owner": owner, "due": "2026-03-20"}
            self.assessed["action_queue"] = [existing]
            with self.subTest(owner=owner):
                result = self.project()
                self.assertEqual(self.refusal_actions(result), [existing])
                self.assertEqual(result["action_queue"], [existing])
                self.assertEqual(result["action_queue"][0]["due"], "2026-03-20")

    def test_other_owner_or_missing_reason_does_not_replace_refusal_escalation(self):
        for action in ({"item": f"SYNTHETIC-MEC-001: {self.reason}", "owner": "Applicant", "due": None},
                       {"item": "Review SYNTHETIC-MEC-001", "owner": "MSP", "due": None}):
            self.assessed["action_queue"] = [action]
            with self.subTest(action=action):
                result = self.project()
                self.assertIn(action, result["action_queue"])
                self.assertEqual(len(self.refusal_actions(result)), 1)
                self.assertIsNone(self.refusal_actions(result)[0]["due"])

    def test_repeated_projection_does_not_duplicate_actions_or_mutate_sources(self):
        source = deepcopy((self.app, self.assessed, self.decision))
        first = self.project()
        self.assertEqual((self.app, self.assessed, self.decision), source)
        self.assertEqual(self.project(), first)
        self.assessed["action_queue"] = deepcopy(first["action_queue"])
        source_with_existing = deepcopy((self.app, self.assessed, self.decision))
        second = self.project()
        self.assertEqual(second["action_queue"], first["action_queue"])
        self.assertEqual(len(self.refusal_actions(second)), 1)
        self.assertEqual((self.app, self.assessed, self.decision), source_with_existing)

    def test_terminal_status_preserves_recording_and_refusal_escalation(self):
        self.assessed["intake"]["missing"] = ["application signature evidence"]
        self.assessed["packet_presentable"] = False
        self.assessed["action_queue"] = [{"item": "Pending applicant outreach", "owner": "Applicant", "due": None}]
        for status in ("withdrawn", "discontinued"):
            source = deepcopy((self.app, self.assessed, self.decision))
            with self.subTest(status=status), patch("credentialing.engine.terminal_status", return_value=(status, "synthetic/terminal.md")):
                result = self.project()
                self.assertEqual(result["status"], status)
                self.assertFalse(result["packet_presentable"])
                self.assertFalse(result["decisions"][0]["admitted"])
                self.assertEqual(len(self.refusal_actions(result)), 1)
                self.assertIsNone(self.refusal_actions(result)[0]["due"])
                self.assertTrue(any(status in action["item"] and "synthetic/terminal.md" in action["item"]
                                    for action in result["action_queue"]))
                self.assertEqual((self.app, self.assessed, self.decision), source)

    def test_terminal_retains_equivalent_refusal_action_and_its_recorded_due_date(self):
        existing = {"item": f"SYNTHETIC-MEC-001: {self.reason}", "owner": "MSP", "due": "2026-03-20"}
        self.assessed["action_queue"] = [existing,
            {"item": "Pending applicant outreach", "owner": "Applicant", "due": None}]
        with patch("credentialing.engine.terminal_status", return_value=("withdrawn", "synthetic/withdrawal.md")):
            result = self.project()
            self.assertEqual(self.refusal_actions(result), [existing])
            self.assertEqual(self.refusal_actions(result)[0]["due"], "2026-03-20")
            self.assertEqual(result["status"], "withdrawn")


if __name__ == "__main__":
    unittest.main()
