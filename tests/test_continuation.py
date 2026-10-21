"""Synthetic retained-state fixtures; no actual batches or Git writes."""

from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from credentialing.continuation import ROW_KEYS
from credentialing.documents import parse_document
from credentialing.io import InputError, REQUIRED_TABLES, run_batch


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "snapshot.schema.json"


def synthetic_processor(batch, sources, retained_history=None):
    """A deterministic test double for the agreed continuation interface."""
    previous = (retained_history or {}).get("applications", {})
    apps, histories = [], {}
    for app_id in sorted({row["application_id"] for row in batch["tables"]["applications"]}):
        revisions = [row for row in batch["tables"]["applications"] if row["application_id"] == app_id]
        revision = max(int(row["revision"]) for row in revisions)
        old = deepcopy(previous.get(app_id, {}))
        decisions = old.get("decisions", [])
        ids = {item["fields"]["decision_id"] for item in decisions}
        for row in batch["tables"]["correspondence"]:
            if row["application_id"] != app_id:
                continue
            doc = parse_document(row["document_path"], batch["documents"][row["document_path"]], row)
            fields = doc["fields"]
            if fields.get("decision_id") and fields["decision_id"] not in ids:
                decisions.append({"fields": fields, "admitted": False, "failures": ["Synthetic prior refusal"], "source": doc["path"]})
                ids.add(fields["decision_id"])
        assessment = {"as_of": batch["export_date"], "revision": revision}
        histories[app_id] = {"assessments": old.get("assessments", []) + [assessment],
                             "readiness_history": old.get("readiness_history", []), "decisions": decisions,
                             "current_revision": revision, "revisions": revisions}
        apps.append({"application_id": app_id, "revision": revision, "status": "in-verification",
                     "elements": {key: "outstanding" for key in ["licensure", "experience", "gaps", "education", "certification", "references"]},
                     "packet_presentable": False,
                     "decisions": [{"decision_id": item["fields"]["decision_id"], "admitted": item["admitted"],
                                    "reason": item["failures"][0] if item["failures"] else None} for item in decisions],
                     "approval_decision_id": None, "activation": None, "monitored_conditions": [],
                     "action_queue": [{"item": "Synthetic evidence remains owed", "owner": "MSP", "due": None}]})
    return {"applications": apps,
            "history": {"applications": histories, "raw_tables": deepcopy(batch["tables"]),
                        "raw_documents": deepcopy(batch["documents"]), "input_hashes": batch["input_hashes"]},
            "packets": {app["application_id"]: {"revision": app["revision"]} for app in apps},
            "limitations": [], "rules_used": []}


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "deliverables"
        self.output.mkdir()
        (self.output / "rules.md").write_text("Synthetic rules\n")
        self.sources = self.root / "sources"
        self.sources.mkdir()
        (self.sources / "office.md").write_text("Synthetic office source\n")
        self.blobs = {}
        self.addCleanup(patch.stopall)
        patch("credentialing.io._sealed", side_effect=lambda path, root: path.relative_to(root).as_posix() in self.blobs).start()
        patch("credentialing.continuation._committed_bytes", side_effect=self.committed).start()
        self.batch(1, "2026-03-16")
        self.batch(2, "2026-04-20")
        self.batch(3, "2026-05-18")
        self.table(1, "applications", [{"application_id": f"APP-{number:03d}", "revision": "1", "received_date": "2026-01-01"} for number in range(1, 41)])
        self.table(1, "declared-history", [{"application_id": "APP-001", "revision": "1", "entry_id": "E1", "from_date": "2020-01-01"}])
        self.table(1, "licence-lookup-wa", [{"credentialnumber": "M1", "lookup_date": "2026-03-01", "status": "ACTIVE"}])
        self.table(1, "verification-replies", [{"reply_id": "VR1", "application_id": "APP-001"}])
        self.document(1, "D1", "2026-03-10")
        self.assertEqual(self.run_export(1)["outcome"], "Partial")
        self.seal()

    def committed(self, root, name):
        if name not in self.blobs:
            raise InputError(f"Not sealed in synthetic HEAD: {name}")
        return self.blobs[name]

    def directory(self, number):
        return self.root / "inputs" / f"batch-{number:02d}"

    def snapshot(self, number):
        return self.output / "snapshots" / f"batch-{number:02d}.json"

    def working(self, number, name):
        return self.output / "working" / f"batch-{number:02d}" / f"{name}.json"

    def batch(self, number, export_date):
        directory = self.directory(number)
        directory.mkdir(parents=True)
        (directory / "README.md").write_text(f"Export date: {export_date}\n")
        for name in REQUIRED_TABLES:
            self.table(number, name, [])

    def table(self, number, name, rows):
        columns = list(dict.fromkeys([*ROW_KEYS[name], *(key for row in rows for key in row)]))
        with (self.directory(number) / f"{name}.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    def document(self, number, decision_id, when):
        path = f"decisions/{decision_id}.md"
        file = self.directory(number) / path
        file.parent.mkdir(exist_ok=True)
        file.write_text(f"**Decision ID:** {decision_id}\n**Application:** APP-001\n**Revision:** 1\n**Decision date:** {when}\n")
        self.table(number, "correspondence", [{"letter_id": "L-" + decision_id, "application_id": "APP-001", "date": when, "document_path": path}])

    def run_export(self, number, *, processor=synthetic_processor, predecessor=None):
        return run_batch(self.directory(number), self.sources, self.output, number, SCHEMA, root=self.root,
                         processor=processor, predecessor_path=predecessor or (self.snapshot(number - 1) if number > 1 else None))

    def seal(self):
        self.blobs.update({path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.output.rglob("*.json")})

    def test_delta_merges_revisions_deduplicates_and_retains_selective_lookups_and_refusal(self):
        prior = deepcopy(self.blobs)
        self.table(2, "applications", [{"application_id": "APP-001", "revision": "2", "received_date": "2026-04-01"}])
        self.table(2, "declared-history", [{"application_id": "APP-001", "revision": "2", "entry_id": "E1", "from_date": "2020-02-01"}])
        self.table(2, "verification-replies", [{"reply_id": "VR1", "application_id": "APP-001"}, {"reply_id": "VR2", "application_id": "APP-001"}])
        self.document(2, "D2", "2026-04-10")
        report = self.run_export(2)
        self.assertEqual(report["outcome"], "Partial", report)
        snapshot = json.loads(self.snapshot(2).read_text())
        self.assertEqual(len(snapshot["applications"]), 40)
        self.assertEqual(snapshot["predecessor"], {"path": "deliverables/snapshots/batch-01.json", "sha256": hashlib.sha256(self.snapshot(1).read_bytes()).hexdigest()})
        self.assertEqual(snapshot["consumed"]["documents"], ["decisions/D2.md"])
        current = json.loads(self.working(2, "history").read_text())
        self.assertEqual(len(current["raw_tables"]["applications"]), 41)
        self.assertEqual(len(current["raw_tables"]["verification-replies"]), 2)
        self.assertEqual(len(current["raw_tables"]["licence-lookup-wa"]), 1)
        self.assertEqual([row["revision"] for row in current["raw_tables"]["declared-history"]], ["1", "2"])
        self.assertEqual([entry["batch"] for entry in current["source_batches"]], [1, 2])
        self.assertIn("batch-01/applications.csv", current["input_hashes"])
        self.assertIn("batch-02/applications.csv", current["input_hashes"])
        old_history = json.loads(self.working(1, "history").read_text())["applications"]["APP-001"]
        self.assertEqual(current["applications"]["APP-001"]["assessments"][:1], old_history["assessments"])
        self.assertEqual(current["applications"]["APP-001"]["decisions"][:1], old_history["decisions"])
        for name, data in prior.items():
            self.assertEqual((self.root / name).read_bytes(), data)

    def test_legacy_batch1_metadata_without_output_hashes_uses_sealed_bytes(self):
        path = self.working(1, "run")
        metadata = json.loads(path.read_text())
        del metadata["output_hashes"]
        path.write_text(json.dumps(metadata))
        self.seal()
        self.assertEqual(self.run_export(2)["outcome"], "Partial")

    def test_missing_or_wrong_predecessor_and_nonadvancing_export_are_blocked(self):
        for predecessor in [self.root / "missing.json", self.snapshot(1)]:
            report = self.run_export(3, predecessor=predecessor)
            self.assertEqual(report["outcome"], "Blocked")
            self.assertFalse(self.snapshot(3).exists())
        (self.directory(2) / "README.md").write_text("Export date: 2026-03-16\n")
        report = self.run_export(2)
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIn("advance strictly", report["error"])

    def test_tampered_predecessor_bytes_or_metadata_hash_blocks_without_snapshot(self):
        path = self.working(1, "history")
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        self.assertIn("differs from sealed bytes", self.run_export(2)["error"])
        self.assertFalse(self.snapshot(2).exists())
        path.write_bytes(original)
        metadata_path = self.working(1, "run")
        metadata = json.loads(metadata_path.read_text())
        metadata["snapshot_sha256"] = "0" * 64
        metadata_path.write_text(json.dumps(metadata))
        self.seal()
        self.assertIn("metadata does not match", self.run_export(2)["error"])
        self.assertFalse(self.snapshot(2).exists())

    def test_mutated_closed_row_or_document_is_rejected(self):
        self.table(2, "verification-replies", [{"reply_id": "VR1", "application_id": "APP-CHANGED"}])
        self.assertIn("Closed export row changed", self.run_export(2)["error"])
        self.table(2, "verification-replies", [])
        file = self.directory(2) / "decisions" / "D1.md"
        file.parent.mkdir()
        file.write_text("Changed earlier document")
        self.assertIn("Closed export document changed", self.run_export(2)["error"])
        self.assertFalse(self.snapshot(2).exists())

    def test_later_failure_preserves_prior_snapshot_and_logs_actual_attempt(self):
        prior = self.snapshot(1).read_bytes()
        (self.directory(2) / "verification-replies.csv").unlink()
        report = self.run_export(2)
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIsNone(report["snapshot"])
        self.assertEqual(self.snapshot(1).read_bytes(), prior)
        self.assertFalse(self.snapshot(2).exists())
        self.assertEqual(report["produced"], ["deliverables/run-log.md"])
        self.assertIn('"batch": 2', (self.output / "run-log.md").read_text())

    def test_prior_refusal_or_assessment_cannot_be_reinterpreted(self):
        def bad_processor(batch, sources, retained_history):
            result = synthetic_processor(batch, sources, retained_history)
            result["applications"][0]["decisions"][0]["admitted"] = True
            result["applications"][0]["decisions"][0]["reason"] = None
            return result
        self.assertIn("Previously received decisions changed", self.run_export(2, processor=bad_processor)["error"])
        def missing_history(batch, sources, retained_history):
            result = synthetic_processor(batch, sources, retained_history)
            result["history"]["applications"]["APP-001"]["assessments"].pop(0)
            return result
        self.assertIn("Retained assessments changed", self.run_export(2, processor=missing_history)["error"])
        self.assertFalse(self.snapshot(2).exists())

    def test_unchanged_sealed_rerun_keeps_every_output_and_checks_state(self):
        self.assertEqual(self.run_export(2)["outcome"], "Partial")
        self.seal()
        retained = deepcopy(self.blobs)
        report = self.run_export(2, processor=lambda *args, **kwargs: self.fail("sealed rerun invoked processor"))
        self.assertTrue(report["unchanged"], report)
        self.assertEqual(report["produced"], ["deliverables/run-log.md"])
        for name, data in retained.items():
            self.assertEqual((self.root / name).read_bytes(), data)
        path = self.working(2, "packets")
        path.write_bytes(path.read_bytes() + b" ")
        self.assertEqual(self.run_export(2)["outcome"], "Blocked")

    def test_batch2_output_hashes_are_required_for_batch3(self):
        self.assertEqual(self.run_export(2)["outcome"], "Partial")
        path = self.working(2, "run")
        metadata = json.loads(path.read_text())
        metadata["output_hashes"]["deliverables/working/batch-02/history.json"] = "0" * 64
        path.write_text(json.dumps(metadata))
        self.seal()
        report = self.run_export(3)
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIn("output hash mismatch", report["error"])
        self.assertFalse(self.snapshot(3).exists())

    def test_retained_input_provenance_cannot_silently_drop_earlier_exports(self):
        self.assertEqual(self.run_export(2)["outcome"], "Partial")
        path = self.working(2, "history")
        history = json.loads(path.read_text())
        history["source_batches"] = []
        path.write_text(json.dumps(history))
        metadata_path = self.working(2, "run")
        metadata = json.loads(metadata_path.read_text())
        metadata["output_hashes"][path.relative_to(self.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        metadata_path.write_text(json.dumps(metadata))
        self.seal()
        report = self.run_export(3)
        self.assertEqual(report["outcome"], "Blocked")
        self.assertIn("input provenance", report["error"])
        self.assertFalse(self.snapshot(3).exists())

    def test_batch3_resumes_header_only_delta_in_fresh_python_process(self):
        self.assertEqual(self.run_export(2)["outcome"], "Partial")
        self.seal()
        capture = self.root / "synthetic-head.json"
        capture.write_text(json.dumps({name: data.hex() for name, data in self.blobs.items()}))
        script = """
import json, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path.cwd() / 'tests'))
from test_continuation import synthetic_processor
from credentialing.io import run_batch
root = Path(sys.argv[1])
blobs = json.loads((root / 'synthetic-head.json').read_text())
with patch('credentialing.continuation._committed_bytes', side_effect=lambda root, name: bytes.fromhex(blobs[name])), patch('credentialing.io._sealed', side_effect=lambda path, root: path.relative_to(root).as_posix() in blobs):
    report = run_batch(root / 'inputs/batch-03', root / 'sources', root / 'deliverables', 3, sys.argv[2], root=root, processor=synthetic_processor, predecessor_path=root / 'deliverables/snapshots/batch-02.json')
print(json.dumps(report))
raise SystemExit(2 if report['outcome'] == 'Blocked' else 0)
"""
        child = subprocess.run([sys.executable, "-c", script, str(self.root), str(SCHEMA)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
        current = json.loads(self.snapshot(3).read_text())
        self.assertEqual(len(current["applications"]), 40)
        self.assertEqual(current["predecessor"]["sha256"], hashlib.sha256(self.snapshot(2).read_bytes()).hexdigest())
        history = json.loads(self.working(3, "history").read_text())
        self.assertEqual([entry["batch"] for entry in history["source_batches"]], [1, 2, 3])
        self.assertEqual([entry["as_of"] for entry in history["applications"]["APP-001"]["assessments"]], ["2026-03-16", "2026-04-20", "2026-05-18"])
        self.assertEqual(current["consumed"]["documents"], [])


if __name__ == "__main__":
    unittest.main()
