"""Read-only Q07 probes against the owner-authorized APP-2026-001 mapping.

Only in-memory copies of the application are varied. No batch processor runs,
no contract is changed, and no snapshot is created by these tests.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
WORKING = ROOT / "deliverables" / "working" / "batch-01"
APP_ID = "APP-2026-001"


class Q07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "snapshot.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        # Reference the unchanged contract's own definition; this is an
        # application compatibility probe, not a fabricated complete snapshot.
        cls.validator = Draft202012Validator(
            {"$defs": cls.schema["$defs"], "$ref": "#/$defs/application"},
            format_checker=FormatChecker())
        results = json.loads((WORKING / "results.json").read_text(encoding="utf-8"))
        cls.application = next(item for item in results["applications"] if item["application_id"] == APP_ID)
        cls.export_date = results["as_of"]
        cls.history = json.loads((WORKING / "history.json").read_text(encoding="utf-8"))
        cls.assessment = next(item for item in cls.history["applications"][APP_ID]["assessments"]
                              if item["as_of"] == cls.export_date and not item["historical_before_decision"])

    def test_actual_projection_has_missing_intake_without_recorded_dispatch(self):
        self.assertEqual(self.export_date, "2026-03-16")
        self.assertEqual(self.application["revision"], 1)
        self.assertEqual(self.application["status"], "intake-incomplete")
        self.assertEqual(self.assessment["intake"]["missing"], ["application signature and date evidence"])
        self.assertEqual(self.assessment["intake"]["notices"], [])
        index = [row for row in self.history["raw_tables"]["correspondence"] if row["application_id"] == APP_ID]
        self.assertEqual([row["document_path"] for row in index], ["decisions/2026-03-10_MEC-2026-011.md"])
        self.assertTrue(all(row["direction"] == "inbound" for row in index))
        pending = [item for item in self.application["action_queue"] if item["item"].startswith("Pending MSP dispatch")]
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["owner"], "Medical Services Professional")
        self.assertIsNone(pending[0]["due"])
        self.assertIn("no response clock has started for these items", pending[0]["item"])
        self.assertFalse(self.application["packet_presentable"])
        self.assertIsNone(self.application["approval_decision_id"])
        self.assertIsNone(self.application["activation"])

    def test_null_probe_still_fails_unchanged_enum_only(self):
        probe = deepcopy(self.application)
        probe["status"] = None
        errors = list(self.validator.iter_errors(probe))
        self.assertEqual([(list(error.path), error.validator) for error in errors], [(["status"], "enum")])

    def test_omitting_status_fails_required_contract_field(self):
        probe = deepcopy(self.application)
        del probe["status"]
        errors = list(self.validator.iter_errors(probe))
        self.assertEqual([(list(error.path), error.validator) for error in errors], [([], "required")])
        self.assertIn("'status' is a required property", errors[0].message)

    def test_inventing_pending_dispatch_status_fails_unchanged_enum(self):
        probe = deepcopy(self.application)
        probe["status"] = "pending-dispatch"
        errors = list(self.validator.iter_errors(probe))
        self.assertEqual([(list(error.path), error.validator) for error in errors], [(["status"], "enum")])

    def test_owner_mapped_status_passes_structure_while_original_description_is_unchanged(self):
        self.assertEqual(self.application["status"], "intake-incomplete")
        self.assertEqual(list(self.validator.iter_errors(self.application)), [])
        description = self.schema["$defs"]["application"]["properties"]["status"]["description"]
        self.assertIn("has been requested in writing", description)
        self.assertIn("the applicant's clock is running", description)
        self.assertIn("an intake status", description)
        self.assertIn("governs whenever a completeness item is missing", description)
        self.assertEqual(self.assessment["intake"]["notices"], [])
        self.assertTrue(self.assessment["intake"]["missing"])
        # The owner-authorized semantic exception changes the projection, not
        # the historical source events, clock, or original contract description.
        self.assertFalse(self.application["packet_presentable"])
        self.assertIsNone(self.application["approval_decision_id"])
        self.assertIsNone(self.application["activation"])

    def test_actual_candidate_passes_complete_unchanged_schema_and_retains_caseload(self):
        candidate = json.loads((ROOT / "deliverables" / "snapshots" / "batch-01.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(candidate)), [])
        self.assertEqual(candidate["batch"], 1)
        self.assertEqual(candidate["as_of"], self.export_date)
        self.assertIsNone(candidate["predecessor"])
        applications = candidate["applications"]
        self.assertEqual(len(applications), len(self.history["applications"]))
        self.assertEqual({app["application_id"] for app in applications}, set(self.history["applications"]))
        self.assertEqual(next(app for app in applications if app["application_id"] == APP_ID), self.application)


if __name__ == "__main__":
    unittest.main()
