"""Continuation history invariants using B1 plus an explicit synthetic fixture.

No later real batch is consumed. The continuation's assessment stub deliberately
models newly established evidence; it is not a claim about the supplied files.
No fixture is written to disk or used as credentialing output.
"""

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from credentialing.engine import ELEMENTS, process_batch
from credentialing.io import load_batch, load_sources


ROOT = Path(__file__).resolve().parents[1]
NEW_ID = "SYNTHETIC-CONTINUATION-MEC-001"
DECOY_ID = "SYNTHETIC-UNINDEXED-MEC-001"


def newly_presentable_fixture(app, tables, docs, as_of, reg, before=False):
    """Test-only established evidence, isolated from business rule assessment."""
    return {"application": deepcopy(app), "as_of": as_of, "historical_before_decision": before,
            "packet_presentable": True, "issues": [], "action_queue": [],
            "elements": {element: "resolved" for element in ELEMENTS},
            "intake": {"missing": [], "notices": []}, "licensure": {"wa": None},
            "document_paths": [], "privileges": {"supported": [], "unsupported": []}}


class ContinuationHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = load_batch(ROOT / "inputs/batch-01")
        cls.sources = load_sources(ROOT / "sources")
        cls.first = process_batch(cls.batch, cls.sources)
        cls.retained = deepcopy(cls.first["history"])
        cls.continuation = deepcopy(cls.batch)
        cls.continuation["export_date"] = "2026-04-20"

        old_path = "decisions/2026-03-10_MEC-2026-011.md"
        new_path = "synthetic/2026-04-10_continuation-recommendation.md"
        cls.continuation["documents"][new_path] = cls.batch["documents"][old_path].replace(
            "MEC-2026-011", NEW_ID).replace("2026-03-10", "2026-04-10")
        cls.continuation["documents"]["synthetic/unindexed-decoy.md"] = cls.continuation["documents"][new_path].replace(NEW_ID, DECOY_ID)
        cls.continuation["tables"]["correspondence"].append({
            "letter_id": "SYNTHETIC-LTR-CONTINUATION", "date": "2026-04-10", "direction": "inbound",
            "application_id": "APP-2026-001", "correspondent": "Synthetic committee fixture",
            "subject": "Synthetic continuation recommendation", "document_path": new_path})

        # Existing real B1 revision history is preserved; this application row
        # extends it only inside the synthetic, stub-assessed fixture.
        previous = next(row for row in cls.continuation["tables"]["applications"]
                        if row["application_id"] == "APP-2026-025" and row["revision"] == "2")
        cls.continuation["tables"]["applications"].append(dict(
            previous, revision="3", received_date="2026-04-10", revision_reason="Synthetic continuation fixture"))

        cls.original_inputs = deepcopy((cls.continuation, cls.sources, cls.retained))
        with patch("credentialing.engine.assess", side_effect=newly_presentable_fixture) as assessment:
            cls.second = process_batch(cls.continuation, cls.sources, retained_history=cls.retained)
            cls.assessment_calls = [(deepcopy(call.args), deepcopy(call.kwargs))
                                    for call in assessment.call_args_list]

    def test_prior_refused_decisions_and_reasons_are_immutable_despite_new_evidence(self):
        old_count = 0
        for app_id, old in self.retained["applications"].items():
            current = self.second["history"]["applications"][app_id]
            by_id = {decision["fields"]["decision_id"]: decision for decision in current["decisions"]}
            for decision in old["decisions"]:
                old_count += 1
                decision_id = decision["fields"]["decision_id"]
                with self.subTest(decision=decision_id):
                    self.assertFalse(decision["admitted"])
                    self.assertEqual(by_id[decision_id], decision)
                    self.assertEqual(by_id[decision_id]["failures"][0], decision["failures"][0])
                    self.assertFalse(by_id[decision_id]["readiness_evidence"]["packet_presentable"])
                    self.assertTrue(current["assessments"][-1]["packet_presentable"])
        self.assertEqual(old_count, 6)

    def test_prior_assessments_and_readiness_are_exact_prefixes(self):
        for app_id, old in self.retained["applications"].items():
            current = self.second["history"]["applications"][app_id]
            with self.subTest(application=app_id):
                for field in ("assessments", "readiness_history"):
                    self.assertEqual(current[field][:len(old[field])], old[field])
                self.assertGreater(len(current["assessments"]), len(old["assessments"]))

    def test_original_receipt_anchor_and_all_revisions_survive(self):
        for app_id, old in self.retained["applications"].items():
            current = self.second["history"]["applications"][app_id]
            with self.subTest(application=app_id):
                self.assertEqual(current["first_received_date"], old["first_received_date"])
                self.assertEqual(current["revisions"][:len(old["revisions"])], old["revisions"])
        revised = self.second["history"]["applications"]["APP-2026-025"]
        self.assertEqual(revised["first_received_date"], "2024-04-22")
        self.assertEqual([row["revision"] for row in revised["revisions"]], ["1", "2", "3"])
        self.assertEqual(revised["current_revision"], 3)

    def test_only_new_indexed_decision_appends_readiness_without_backdating_old_records(self):
        old_ids = {decision["fields"]["decision_id"] for old in self.retained["applications"].values()
                   for decision in old["decisions"]}
        new_decisions = [decision for current in self.second["history"]["applications"].values()
                         for decision in current["decisions"] if decision["fields"]["decision_id"] not in old_ids]
        self.assertEqual([decision["fields"]["decision_id"] for decision in new_decisions], [NEW_ID])
        self.assertTrue(new_decisions[0]["admitted"])
        self.assertEqual(new_decisions[0]["fields"]["decision_date"], "2026-04-10")
        current = self.second["history"]["applications"]["APP-2026-001"]
        old = self.retained["applications"]["APP-2026-001"]
        appended = current["readiness_history"][len(old["readiness_history"]):]
        self.assertEqual(len(appended), 1)
        self.assertEqual(appended[0]["before_decision"], NEW_ID)
        self.assertEqual(appended[0]["decision_date"], "2026-04-10")
        self.assertTrue(appended[0]["presentable"])
        self.assertFalse(old["readiness_history"][0]["presentable"])
        historical_calls = [args for args, kwargs in self.assessment_calls if kwargs.get("before")]
        self.assertEqual(len(historical_calls), 1)
        self.assertEqual(historical_calls[0][3], "2026-04-10")

    def test_retained_state_and_input_sources_are_not_mutated(self):
        self.assertEqual((self.continuation, self.sources, self.retained), self.original_inputs)
        self.assertEqual(self.retained, self.first["history"])


if __name__ == "__main__":
    unittest.main()
