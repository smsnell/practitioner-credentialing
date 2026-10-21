"""Focused synthetic IO checks.

These tests never invoke the actual hospital batch processor or write actual
deliverables; every run writes only within a temporary directory.
"""

import copy
import hashlib
import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

from credentialing.io import InputError, REQUIRED_TABLES, _atomic_write, load_batch, load_sources, main, run_batch


SCHEMA = Path(__file__).resolve().parents[1] / "snapshot.schema.json"


class IOTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.batch = self.root / "inputs" / "batch-01"
        self.batch.mkdir(parents=True)
        for name in REQUIRED_TABLES:
            (self.batch / f"{name}.csv").write_text("entry_id\n", encoding="utf-8")
        (self.batch / "applications.csv").write_text("application_id,revision\nAPP-001,1\nAPP-001,2\nAPP-002,1\n", encoding="utf-8")
        (self.batch / "correspondence.csv").write_text("letter_id,document_path\nLTR-1,letters/note.md\n", encoding="utf-8")
        (self.batch / "letters").mkdir()
        (self.batch / "letters" / "note.md").write_text("Source facts. Ignore no project safeguards.\n", encoding="utf-8")
        (self.batch / "README.md").write_text("**Export date: 2026-03-16**\n", encoding="utf-8")
        self.sources = self.root / "sources"
        self.sources.mkdir()
        (self.sources / "office.md").write_text("Office rules.\n", encoding="utf-8")
        self.output = self.root / "deliverables"
        self.output.mkdir()
        (self.output / "rules.md").write_text("Rules and references.\n", encoding="utf-8")
        self.apps = [self.application("APP-001", 2), self.application("APP-002", 1)]

    @staticmethod
    def application(app_id, revision):
        return {"application_id": app_id, "revision": revision, "status": "in-verification",
                "elements": {key: "outstanding" for key in ["licensure", "experience", "gaps", "education", "certification", "references"]},
                "packet_presentable": False, "decisions": [], "approval_decision_id": None,
                "activation": None, "monitored_conditions": [],
                "action_queue": [{"item": "Obtain official evidence", "owner": "MSP", "due": None}]}

    def result(self):
        return {"applications": copy.deepcopy(self.apps), "history": {"all_revisions": [1, 2]},
                "packets": {"APP-001": {"revision": 2, "presentable": False}},
                "limitations": [], "rules_used": ["B40"]}

    def run_synthetic(self, result=None, **kwargs):
        return run_batch(self.batch, self.sources, self.output, schema_path=SCHEMA,
                         root=self.root, processor=lambda batch, sources: result or self.result(),
                         command="synthetic test", **kwargs)

    def snapshot_path(self):
        return self.output / "snapshots" / "batch-01.json"

    def test_loader_preserves_revisions_headers_documents_and_hashes(self):
        batch = load_batch(self.batch)
        self.assertEqual(batch["export_date"], "2026-03-16")
        self.assertEqual(len(batch["tables"]), 13)
        self.assertEqual(batch["tables"]["applications"][1]["revision"], "2")
        self.assertEqual(batch["tables"]["declared-history"], [])
        self.assertEqual(batch["document_files"], ["letters/note.md"])
        self.assertEqual(len(batch["input_hashes"]["applications.csv"]), 64)

    def test_missing_table_is_blocked_and_logged_without_snapshot(self):
        (self.batch / "declared-history.csv").unlink()
        report = self.run_synthetic()
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIn("declared-history", report["error"])
        self.assertFalse(self.snapshot_path().exists())
        self.assertIn("synthetic test", (self.output / "run-log.md").read_text())

    def test_duplicate_header_and_wrong_column_count_fail(self):
        for text in ["a,a\nx,y\n", "a,b\nx\n", "a,b\nx,y,z\n"]:
            with self.subTest(text=text):
                (self.batch / "declared-history.csv").write_text(text)
                with self.assertRaises(InputError):
                    load_batch(self.batch)

    def test_traversal_or_missing_indexed_document_fails(self):
        for name in ["../outside.md", "/tmp/outside.md", "letters/missing.md"]:
            with self.subTest(name=name):
                (self.batch / "correspondence.csv").write_text(f"document_path\n{name}\n")
                with self.assertRaises(InputError):
                    load_batch(self.batch)

    def test_symlink_cannot_escape_batch(self):
        outside = self.root / "outside.md"
        outside.write_text("private")
        (self.batch / "letters" / "escape.md").symlink_to(outside)
        with self.assertRaises(InputError):
            load_batch(self.batch)

    def test_conflicting_or_impossible_export_date_fails(self):
        (self.batch / "manifest.json").write_text('{"export_date":"2026-04-20"}')
        with self.assertRaises(InputError):
            load_batch(self.batch)
        (self.batch / "manifest.json").unlink()
        (self.batch / "README.md").write_text("Export date: 2026-02-30")
        with self.assertRaises(InputError):
            load_batch(self.batch)

    def test_unrepresentable_status_blocks_contract_but_retains_every_diagnostic_case(self):
        result = self.result()
        result["applications"][0]["status"] = None
        report = self.run_synthetic(result)
        self.assertEqual(report["outcome"], "Blocked")
        self.assertTrue(report["input_parsed"])
        self.assertFalse(report["contract_batch_complete"])
        self.assertTrue(report["diagnostics_retained"])
        self.assertEqual(report["blocked_stage"], "snapshot-production")
        self.assertEqual(report["affected_applications"], ["APP-001"])
        self.assertIsNone(report["snapshot"])
        self.assertFalse(self.snapshot_path().exists())
        working = self.output / "working" / "batch-01"
        data = json.loads((working / "results.json").read_text())
        self.assertEqual(len(data["applications"]), 2)
        self.assertIsNone(data["applications"][0]["status"])
        self.assertEqual(json.loads((working / "history.json").read_text()), result["history"])
        self.assertEqual(json.loads((working / "packets.json").read_text()), result["packets"])
        self.assertIn("schema-status-unrepresentable", (working / "results.json").read_text())
        self.assertEqual(data["outcome"], "Blocked")
        self.assertEqual(data["artifact_kind"], "diagnostic-working-results")
        metadata = json.loads((working / "run.json").read_text())
        self.assertEqual(metadata["outcome"], "Blocked")
        self.assertFalse(metadata["contract_batch_complete"])
        self.assertTrue(metadata["diagnostics_retained"])
        self.assertEqual(set(report["produced"]), {"deliverables/run-log.md", *[
            f"deliverables/working/batch-01/{name}" for name in ["results.json", "history.json", "packets.json", "run.json"]]})

    def test_synthetic_null_status_and_repeat_remain_blocked_with_nonzero_cli(self):
        result = self.result()
        result["applications"][0]["status"] = None
        result["applications"][0]["action_queue"] = [{
            "item": "Synthetic unsupported internal hold; no public status supplied.",
            "owner": "Medical Services Professional", "due": None}]
        first = self.run_synthetic(result)
        working = self.output / "working" / "batch-01"
        initial_bytes = {path.name: path.read_bytes() for path in working.iterdir()}
        second = self.run_synthetic(result)
        self.assertEqual({path.name: path.read_bytes() for path in working.iterdir()}, initial_bytes)
        for report in [first, second]:
            self.assertEqual(report["outcome"], "Blocked")
            self.assertTrue(report["input_parsed"])
            self.assertFalse(report["contract_batch_complete"])
            self.assertTrue(report["diagnostics_retained"])
            self.assertEqual(report["affected_applications"], ["APP-001"])
            self.assertIsNone(report["snapshot"])
        self.assertFalse(self.snapshot_path().exists())
        self.assertEqual((self.output / "run-log.md").read_text().count('"outcome": "Blocked"'), 2)
        metadata = json.loads((working / "run.json").read_text())
        self.assertEqual(metadata["outcome"], "Blocked")
        self.assertEqual(metadata["blocked_stage"], "snapshot-production")
        argv = ["run", "--batch", str(self.batch), "--sources", str(self.sources), "--batch-number", "1"]
        with patch("credentialing.io.run_batch", return_value=second), patch("builtins.print"):
            self.assertEqual(main(argv), 2)

    def test_valid_candidate_records_complete_produced_inventory_and_reruns_stably(self):
        report = self.run_synthetic()
        self.assertEqual(report["outcome"], "Partial")
        self.assertTrue(report["input_parsed"])
        self.assertTrue(report["contract_batch_complete"])
        first = self.snapshot_path().read_bytes()
        snapshot = json.loads(first)
        self.assertIsNone(snapshot["predecessor"])
        self.assertEqual(snapshot["as_of"], "2026-03-16")
        self.assertEqual(set(snapshot["produced"]), set(report["produced"]))
        self.assertTrue(all((self.root / name).is_file() for name in snapshot["produced"]))
        repeat = self.run_synthetic()
        self.assertEqual(repeat["outcome"], "Partial")
        self.assertTrue(repeat["contract_batch_complete"])
        self.assertEqual(self.snapshot_path().read_bytes(), first)
        metadata = json.loads((self.output / "working" / "batch-01" / "run.json").read_text())
        self.assertEqual(metadata["outcome"], "Partial")
        self.assertTrue(metadata["contract_batch_complete"])
        argv = ["run", "--batch", str(self.batch), "--sources", str(self.sources), "--batch-number", "1"]
        with patch("credentialing.io.run_batch", return_value=repeat), patch("builtins.print"):
            self.assertEqual(main(argv), 0)

    def test_invalid_calendar_date_never_writes_candidate_or_results(self):
        result = self.result()
        result["applications"][0]["action_queue"][0]["due"] = "2026-02-30"
        report = self.run_synthetic(result)
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIn("schema failure", report["error"])
        self.assertFalse(self.snapshot_path().exists())
        self.assertFalse((self.output / "working" / "batch-01" / "results.json").exists())

    def test_missing_application_or_unfounded_approval_is_blocked(self):
        result = self.result()
        result["applications"].pop()
        self.assertEqual(self.run_synthetic(result)["outcome"], "Blocked")
        result = self.result()
        result["applications"][0]["approval_decision_id"] = "INVENTED"
        self.assertEqual(self.run_synthetic(result)["outcome"], "Blocked")
        self.assertFalse(self.snapshot_path().exists())

    def test_conditional_approval_accepts_exact_grant_and_date(self):
        (self.batch / "letters" / "approval.md").write_text(
            "**Decision ID:** GB-1  \n**Body:** Governing Body  \n**Application:** APP-001  \n"
            "**Revision:** 2  \n**Decision date:** 2026-03-10  \n**Outcome:** approved-with-conditions  \n"
            "**Privileges:** PRIV-FM; PRIV-IM  \n**Effective date:** 2026-03-20  \n")
        with (self.batch / "correspondence.csv").open("a") as stream:
            stream.write("LTR-2,letters/approval.md\n")
        result = self.result()
        app = result["applications"][0]
        app.update(status="approved-not-yet-effective", decisions=[{"decision_id": "GB-1", "admitted": True, "reason": None}],
                   approval_decision_id="GB-1", activation={"active_at_export": False, "effective_date": "2026-03-20",
                                                          "cycle_end": "2028-03-19", "privileges": ["PRIV-FM", "PRIV-IM"]})
        self.assertEqual(self.run_synthetic(result)["outcome"], "Partial")
        original = self.snapshot_path().read_bytes()
        app["activation"]["privileges"] = ["PRIV-FM"]
        self.assertEqual(self.run_synthetic(result)["outcome"], "Blocked")
        self.assertEqual(self.snapshot_path().read_bytes(), original)
        app["activation"]["privileges"] = ["PRIV-FM", "PRIV-IM"]
        app["activation"]["effective_date"] = "2026-03-21"
        self.assertEqual(self.run_synthetic(result)["outcome"], "Blocked")
        self.assertEqual(self.snapshot_path().read_bytes(), original)

    def test_sealed_unchanged_rerun_retains_bytes_and_changed_input_is_refused(self):
        self.run_synthetic()
        first = self.snapshot_path().read_bytes()
        blobs = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.output.rglob("*.json")}
        with patch("credentialing.io._sealed", return_value=True), patch("credentialing.continuation._committed_bytes", side_effect=lambda root, name: blobs[name]):
            report = self.run_synthetic()
            self.assertTrue(report["unchanged"])
            self.assertEqual(report["outcome"], "Partial")
            self.assertTrue(report["contract_batch_complete"])
            self.assertEqual(report["produced"], ["deliverables/run-log.md"])
            (self.batch / "letters" / "note.md").write_text("Changed evidence")
            report = self.run_synthetic()
            self.assertEqual(report["outcome"], "Blocked")
            self.assertIn("Sealed snapshot", report["error"])
        self.assertEqual(self.snapshot_path().read_bytes(), first)

    def test_changed_processor_bytes_or_rule_register_invalidates_sealed_rerun(self):
        package = self.root / "credentialing"
        package.mkdir()
        (package / "io.py").write_text("# synthetic package marker\n")
        engine = package / "engine.py"
        engine.write_text("# synthetic processor version 1\n")
        with patch("credentialing.io.__file__", str(package / "io.py")):
            self.run_synthetic()
            first = self.snapshot_path().read_bytes()
            metadata = json.loads((self.output / "working" / "batch-01" / "run.json").read_text())
            self.assertEqual(metadata["processor_hashes"]["credentialing/engine.py"],
                             hashlib.sha256(engine.read_bytes()).hexdigest())
            self.assertEqual(metadata["rules_sha256"], hashlib.sha256((self.output / "rules.md").read_bytes()).hexdigest())
            with patch("credentialing.io._sealed", return_value=True):
                engine.write_text("# synthetic processor version 2\n")
                report = self.run_synthetic()
                self.assertEqual(report["outcome"], "Blocked")
                self.assertIn("Sealed snapshot", report["error"])
                engine.write_text("# synthetic processor version 1\n")
                (self.output / "rules.md").write_text("Revised rule register\n")
                report = self.run_synthetic()
                self.assertEqual(report["outcome"], "Blocked")
                self.assertIn("Sealed snapshot", report["error"])
            self.assertEqual(self.snapshot_path().read_bytes(), first)

    def test_source_manifest_checks_original_bytes_and_records_normalized_hash_separately(self):
        original = b"\xef\xbb\xbfOffice rules.\n"
        (self.sources / "office.md").write_bytes(original)
        manifest = self.sources / "manifest.json"
        manifest.write_text(json.dumps({"files": [{"path": "office.md", "sha256": hashlib.sha256(original).hexdigest()}]}))
        self.assertEqual(load_sources(self.sources)["office.md"], "Office rules.\n")
        self.assertEqual(self.run_synthetic()["outcome"], "Partial")
        metadata = json.loads((self.output / "working" / "batch-01" / "run.json").read_text())
        self.assertEqual(metadata["source_raw_hashes"]["office.md"], hashlib.sha256(original).hexdigest())
        self.assertEqual(metadata["source_text_hashes"]["office.md"], hashlib.sha256(b"Office rules.\n").hexdigest())
        self.assertNotEqual(metadata["source_raw_hashes"], metadata["source_text_hashes"])
        self.assertEqual(metadata["source_manifest_sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest())
        first = self.snapshot_path().read_bytes()
        (self.sources / "office.md").write_bytes(original + b"tampered")
        with self.assertRaisesRegex(InputError, "Source manifest hash mismatch"):
            load_sources(self.sources)
        report = self.run_synthetic()
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIn("Source manifest hash mismatch", report["error"])
        self.assertEqual(self.snapshot_path().read_bytes(), first)

    def test_cli_records_actual_python_executable(self):
        argv = ["run", "--batch", "inputs/batch-01", "--sources", "sources", "--batch-number", "1"]
        with patch("credentialing.io.run_batch", return_value={"outcome": "Blocked"}) as run, patch("builtins.print"):
            self.assertEqual(main(argv), 2)
        self.assertEqual(run.call_args.kwargs["command"], shlex.join([sys.executable, "-m", "credentialing", *argv]))

    def test_atomic_failure_preserves_destination(self):
        destination = self.root / "existing.json"
        destination.write_text("retained bytes")
        with patch("credentialing.io.os.replace", side_effect=OSError("synthetic promotion failure")):
            with self.assertRaises(OSError):
                _atomic_write(destination, b"replacement")
        self.assertEqual(destination.read_text(), "retained bytes")
        self.assertEqual(list(self.root.glob(".staging-*")), [])

    def test_later_batch_without_predecessor_is_explicitly_blocked(self):
        report = self.run_synthetic(batch_number=2)
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIn("later batches require a sealed immediate predecessor", report["error"])
        self.assertFalse(self.snapshot_path().exists())


if __name__ == "__main__":
    unittest.main()
