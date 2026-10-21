"""Explicitly synthetic named satisfaction records, never inferred completion."""

from copy import deepcopy
import unittest

from credentialing.conditions import condition_satisfaction
from credentialing.documents import indexed_documents
try:
    from . import test_connected_workflow as connected
except ImportError:  # unittest discovery imports test modules by basename.
    import test_connected_workflow as connected


class ConditionSatisfactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        connected.ConnectedWorkflowTests.setUpClass()
        cls.workflow = connected.ConnectedWorkflowTests()
        cls.reg = cls.workflow.reg

    def setUp(self):
        self.batch = self.workflow.fixture()
        self.batch["export_date"] = "2026-06-30"
        self.batch["tables"]["licence-lookup-wa"][0]["expirationdate"] = "2026-11-30"
        self.workflow.decisions(self.batch, conditional=True)
        self.app = self.batch["tables"]["applications"][0]
        self.approval = indexed_documents(self.batch)[-1]["fields"]
        self.conditions = [{"condition": "Reverify Washington licence — due 2026-11-01", "due": "2026-11-01"},
                           {"condition": "Obtain documented concurrence — due 2026-06-30", "due": "2026-06-30"}]

    def record(self, *, condition=None, role="Clinical Director", when="2026-06-30", changes=None, signed=True):
        author = next(row for row in self.reg["roles"] if row["role"] == role)
        condition = condition or self.conditions[1]
        fields = {"Approval decision ID": "SYN-GB", "Condition": condition["condition"], "Due": condition["due"],
                  "Date": when, "Outcome": "satisfied", "Recorded by": author["name"], "Role": role}
        fields.update(changes or {})
        footer = f"Signed: {author['name']}, {role}, {when}." if signed else "Recorded for review."
        self.workflow.document(self.batch, "satisfaction", "Condition satisfaction", fields, when, footer)
        return indexed_documents(self.batch)[-1]

    def evaluate(self, doc):
        records = condition_satisfaction(self.app, self.approval, self.conditions, [doc], self.reg, self.batch["export_date"])
        self.assertEqual(len(records), 1)
        return records[0]

    def test_signed_clinical_record_matches_only_exact_named_condition(self):
        doc = self.record()
        original = deepcopy((self.app, self.approval, self.conditions, doc))
        record = self.evaluate(doc)
        self.assertTrue(record["valid"], record["failures"])
        self.assertTrue(record["satisfied"])
        self.assertEqual(record["matched_condition"], self.conditions[1])
        self.assertEqual(record["source"], "synthetic/satisfaction.md")
        self.assertEqual(record["text"], doc["text"])
        self.assertEqual((self.app, self.approval, self.conditions, doc), original)

    def test_msp_can_record_routine_wa_reverification_in_both_supported_formats(self):
        expiry = {"condition": "Reverify Washington licence SYN-WA before expiry; recorded due date is expiry under P Check 1.", "due": "2026-11-30"}
        self.conditions.append(expiry)
        for condition in (self.conditions[0], expiry):
            with self.subTest(condition=condition):
                record = self.evaluate(self.record(condition=condition, role="Medical Services Professional"))
                self.assertTrue(record["satisfied"], record["failures"])
                self.assertEqual(record["matched_condition"], condition)

    def test_unmatched_incomplete_future_unsigned_and_unrecognized_records_are_retained(self):
        cases = [
            {"changes": {"Approval decision ID": "ANOTHER-APPROVAL"}},
            {"changes": {"Revision": "2"}},
            {"changes": {"Application": "ANOTHER-APPLICATION"}},
            {"changes": {"Condition": "All conditions complete"}},
            {"changes": {"Due": "2026-07-01"}},
            {"changes": {"Outcome": "complete"}},
            {"changes": {"Recorded by": "Unlisted Person"}},
            {"changes": {"Date": "2026-06-29"}},
            {"when": "2026-04-09"},
            {"when": "2026-07-01"},
            {"signed": False},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                record = self.evaluate(self.record(**kwargs))
                self.assertFalse(record["valid"])
                self.assertFalse(record["satisfied"])
                self.assertTrue(record["failures"])
                self.assertEqual(record["source"], "synthetic/satisfaction.md")

    def test_msp_nonroutine_record_remains_for_review_as_parser_limitation(self):
        record = self.evaluate(self.record(role="Medical Services Professional"))
        self.assertFalse(record["satisfied"])
        self.assertTrue(any("parser limitation" in failure for failure in record["failures"]))
        self.assertEqual(record["matched_condition"], self.conditions[1])

    def test_connected_named_satisfaction_clears_only_its_due_action_and_preserves_history(self):
        before, before_history = self.workflow.process(self.batch)
        due_condition = self.conditions[1]
        self.assertEqual(before["status"], "active-with-conditions")
        self.assertIn(due_condition, before["monitored_conditions"])
        self.assertEqual(len(before["action_queue"]), 1)
        self.assertIn(due_condition["condition"], before["action_queue"][0]["item"])
        self.assertEqual(before["action_queue"][0]["owner"], "Clinical Director")
        self.record()
        original = deepcopy(self.batch)
        after, history = self.workflow.process(self.batch)
        self.assertEqual(after["approval_decision_id"], before["approval_decision_id"])
        self.assertEqual(after["activation"], before["activation"])
        self.assertEqual(after["status"], "active-with-conditions")
        self.assertEqual(after["monitored_conditions"], [c for c in before["monitored_conditions"] if c != due_condition])
        self.assertEqual(len(after["monitored_conditions"]), 2)
        self.assertEqual(after["action_queue"], [])
        self.assertEqual(history["decisions"][-1]["conditions"], before_history["decisions"][-1]["conditions"])
        self.assertIn(due_condition, history["decisions"][-1]["conditions"])
        records = history["assessments"][-1]["condition_satisfaction"]
        self.assertEqual(len(records), 1)
        self.assertTrue(records[0]["satisfied"])
        self.assertEqual(records[0]["matched_condition"], due_condition)
        self.assertEqual(self.batch, original)

    def test_connected_generic_completion_retains_due_condition_and_owned_review(self):
        self.record(changes={"Condition": "All conditions complete"})
        result, history = self.workflow.process(self.batch)
        self.assertTrue(result["activation"]["active_at_export"])
        self.assertIn(self.conditions[1], result["monitored_conditions"])
        self.assertEqual(len(result["monitored_conditions"]), 3)
        self.assertTrue(any(action["owner"] == "Clinical Director" and self.conditions[1]["condition"] in action["item"]
                            for action in result["action_queue"]))
        self.assertTrue(any(action["owner"] == "Medical Services Professional" and "synthetic/satisfaction.md" in action["item"]
                            for action in result["action_queue"]))
        self.assertFalse(history["assessments"][-1]["condition_satisfaction"][0]["satisfied"])


if __name__ == "__main__":
    unittest.main()
