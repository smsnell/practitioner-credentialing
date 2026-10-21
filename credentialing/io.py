"""Input validation and an unsealed, first-batch output lifecycle.

Source text is data. This module never executes instructions from records or
documents, sends correspondence, commits results, or continues a later batch.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import sys
import tempfile

from jsonschema import Draft202012Validator, FormatChecker


# The native export supplies these tables even when a table has no rows.
REQUIRED_TABLES = frozenset({
    "applications", "application-disclosures", "certification-replies", "correspondence",
    "declared-credentials", "declared-history", "licence-lookup-other-states", "licence-lookup-wa",
    "peer-reference-replies", "peer-referees", "privilege-requests", "verification-attempts", "verification-replies",
})


class InputError(ValueError):
    """The supplied export or candidate cannot safely be consumed."""


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                       allow_nan=False) + "\n").encode("utf-8")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _relative_name(name):
    path = PurePosixPath(name)
    if not name or "\\" in name or path.is_absolute() or ".." in path.parts:
        raise InputError(f"Unsafe relative input path: {name!r}")
    return path.as_posix()


def _read(root, path):
    if not path.resolve().is_relative_to(root.resolve()):
        raise InputError(f"Input escapes its directory: {path.name}")
    return path.read_bytes()


def _parse_csv(data, name):
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
        columns = reader.fieldnames
        if not columns or any(not item for item in columns) or len(set(columns)) != len(columns):
            raise InputError(f"Missing or duplicate CSV headers: {name}")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise InputError(f"Wrong column count in {name}, line {reader.line_num}")
            rows.append(dict(row))
        return rows
    except (UnicodeError, csv.Error) as exc:
        raise InputError(f"Invalid CSV {name}: {exc}") from exc


def load_batch(path):
    """Load one export, preserving raw values and relative document names."""
    root = Path(path)
    if not root.is_dir():
        raise InputError(f"Batch directory does not exist: {root}")
    tables, documents, hashes, record_files = {}, {}, {}, []
    for file in sorted(root.rglob("*.csv")):
        name = _relative_name(file.relative_to(root).as_posix())
        if file.stem in tables:
            raise InputError(f"Duplicate table basename: {file.stem}")
        data = _read(root, file)
        tables[file.stem] = _parse_csv(data, name)
        hashes[name] = _sha(data)
        record_files.append(name)
    missing = REQUIRED_TABLES - tables.keys()
    if missing:
        raise InputError(f"Missing required tables: {', '.join(sorted(missing))}")
    revisions = set()
    for row in tables["applications"]:
        if not row.get("application_id") or not re.fullmatch(r"[1-9][0-9]*", row.get("revision", "")):
            raise InputError("Applications require application_id and positive integer revision")
        key = (row["application_id"], row["revision"])
        if key in revisions:
            raise InputError(f"Duplicate application revision: {key}")
        revisions.add(key)
    if not tables["applications"]:
        raise InputError("Applications table has no caseload")
    readme_dates = set()
    for file in sorted(root.rglob("*.md")):
        name = _relative_name(file.relative_to(root).as_posix())
        data = _read(root, file)
        hashes[name] = _sha(data)
        try:
            text = data.decode("utf-8-sig")
        except UnicodeError as exc:
            raise InputError(f"Invalid UTF-8 document: {name}") from exc
        if file.name.lower() == "readme.md":
            readme_dates.update(re.findall(r"(?im)export[ _-]*date\s*[:=|]?\s*[*`_]*\s*(\d{4}-\d{2}-\d{2})", text))
        else:
            documents[name] = text
    manifest = root / "manifest.json"
    if manifest.is_file():
        data = _read(root, manifest)
        hashes["manifest.json"] = _sha(data)
        try:
            info = json.loads(data)
        except (ValueError, UnicodeError) as exc:
            raise InputError("Invalid input manifest JSON") from exc
        if not isinstance(info, dict):
            raise InputError("Input manifest must be an object")
        if "export_date" in info:
            readme_dates.add(info["export_date"])
        listed = set()
        for item in info.get("files", []):
            name = _relative_name(item["path"])
            if name in listed:
                raise InputError(f"Duplicate input manifest path: {name}")
            listed.add(name)
            if name not in hashes or hashes[name] != item["sha256"]:
                raise InputError(f"Input manifest hash mismatch or missing file: {name}")
        if "files" in info and listed != set(hashes) - {"manifest.json"}:
            raise InputError("Input manifest inventory differs from batch files")
    if len(readme_dates) != 1:
        raise InputError("Batch needs one unambiguous export_date in README.md or manifest.json")
    export_date = readme_dates.pop()
    if not isinstance(export_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", export_date):
        raise InputError("Invalid export_date")
    try:
        date.fromisoformat(export_date)
    except ValueError as exc:
        raise InputError(f"Invalid export date: {export_date}") from exc
    for row in tables["correspondence"]:
        name = _relative_name(row.get("document_path", ""))
        if name not in documents:
            raise InputError(f"Indexed document is missing: {name}")
    return {"export_date": export_date, "tables": tables, "documents": documents,
            "record_files": record_files, "document_files": sorted(documents), "input_hashes": hashes}


def _load_source_capture(path):
    root = Path(path)
    if not root.is_dir():
        raise InputError(f"Sources directory does not exist: {root}")
    result, raw_hashes = {}, {}
    for file in sorted(root.rglob("*")):
        if file.is_file() and file.suffix.lower() in {".md", ".txt"}:
            name = _relative_name(file.relative_to(root).as_posix())
            data = _read(root, file)
            raw_hashes[name] = _sha(data)
            result[name] = data.decode("utf-8-sig")
    if not result:
        raise InputError("No standing source text was supplied")
    manifest_hash = None
    manifest = root / "manifest.json"
    if manifest.is_file():
        data = _read(root, manifest)
        manifest_hash = _sha(data)
        try:
            info = json.loads(data)
        except (ValueError, UnicodeError) as exc:
            raise InputError("Invalid source manifest JSON") from exc
        if not isinstance(info, dict) or not isinstance(info.get("files"), list):
            raise InputError("Source manifest must contain a files list")
        listed = set()
        for item in info["files"]:
            name = _relative_name(item["path"])
            if name in listed:
                raise InputError(f"Duplicate source manifest path: {name}")
            listed.add(name)
            if name not in raw_hashes or raw_hashes[name] != item["sha256"]:
                raise InputError(f"Source manifest hash mismatch or missing file: {name}")
        if listed != set(raw_hashes):
            raise InputError("Source manifest inventory differs from standing source files")
    text_hashes = {name: _sha(text.encode("utf-8")) for name, text in result.items()}
    return result, raw_hashes, text_hashes, manifest_hash


def load_sources(path):
    """Verify captured bytes, then return UTF-8 text with any initial BOM removed."""
    return _load_source_capture(path)[0]


def _processor_hashes():
    package = Path(__file__).resolve().parent
    return {"credentialing/" + path.relative_to(package).as_posix(): _sha(path.read_bytes())
            for path in sorted(package.rglob("*.py"))}


def _validate_applications(applications, schema_path):
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/application"},
                                     format_checker=FormatChecker())
    for app in applications:
        for error in validator.iter_errors(app):
            # Null is an explicit internal hold, never a public schema status.
            if list(error.path) == ["status"] and error.validator == "enum" and error.instance is None:
                continue
            raise InputError(f"Application schema failure at {'/'.join(map(str, error.path))}: {error.message}")


def validate_snapshot(snapshot, batch, schema_path, root):
    """Check the public contract and cross-record invariants before writing."""
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(snapshot), key=lambda e: str(list(e.path)))
    if errors:
        error = errors[0]
        raise InputError(f"Snapshot schema failure at {'/'.join(map(str, error.path))}: {error.message}")
    if snapshot["as_of"] != batch["export_date"]:
        raise InputError("Snapshot as_of differs from batch export date")
    if snapshot["batch"] != 1 or snapshot["predecessor"] is not None:
        raise InputError("G1 permits only batch 1 with no predecessor")
    expected = {}
    for row in batch["tables"]["applications"]:
        app_id = row["application_id"]
        expected[app_id] = max(expected.get(app_id, 0), int(row["revision"]))
    actual = snapshot["applications"]
    if len(actual) != len(expected) or {app["application_id"] for app in actual} != set(expected):
        raise InputError("Snapshot does not cover the complete, unique caseload")
    records = {}
    received = []
    for row in batch["tables"]["correspondence"]:
        text = batch["documents"][row["document_path"]]
        fields = dict(re.findall(r"(?m)^\*\*([^*]+):\*\*[ \t]*([^\r\n]*)", text))
        if fields.get("Decision ID"):
            decision_id = fields["Decision ID"].strip()
            if decision_id in records:
                raise InputError(f"Duplicate source decision ID: {decision_id}")
            records[decision_id] = {key: value.strip() for key, value in fields.items()}
            received.append(decision_id)
    for app in actual:
        if app["revision"] != expected[app["application_id"]]:
            raise InputError(f"Not latest revision: {app['application_id']}")
        ids = [item["decision_id"] for item in app["decisions"]]
        if len(ids) != len(set(ids)):
            raise InputError(f"Duplicate decision IDs: {app['application_id']}")
        expected_decisions = [item for item in received if records[item].get("Application") == app["application_id"]]
        if ids != expected_decisions:
            raise InputError(f"Decision history is incomplete or out of received order: {app['application_id']}")
        for decision in app["decisions"]:
            record = records.get(decision["decision_id"])
            if record is None or record.get("Application") != app["application_id"]:
                raise InputError(f"Decision has no source record: {decision['decision_id']}")
            if decision["admitted"] and decision["reason"] is not None:
                raise InputError("An admitted decision must have null refusal reason")
        approval = app["approval_decision_id"]
        if approval is not None and not any(item["decision_id"] == approval and item["admitted"] for item in app["decisions"]):
            raise InputError("Approval pointer must name an admitted decision of this application")
        activation = app["activation"]
        if (approval is None) != (activation is None):
            raise InputError("Approval and activation must both be present or both null")
        if activation:
            source = records[approval]
            if source.get("Revision") != str(app["revision"]):
                raise InputError("Approval belongs to a different application revision")
            granted = {value.strip() for value in source.get("Privileges", "").split(";") if value.strip()}
            if source.get("Outcome", "").lower() not in {"approved", "approved-with-conditions"} or source.get("Body") != "Governing Body":
                raise InputError("Activation requires an actual Governing Body approval")
            if set(activation["privileges"]) != granted:
                raise InputError("Activation privileges differ from the actual approval")
            permitted_date = max(source.get("Decision date", ""), source.get("Effective date", ""))
            if activation["effective_date"] != permitted_date:
                raise InputError("Activation date differs from the later of decision and recorded effective date")
            if activation["cycle_end"] < activation["effective_date"]:
                raise InputError("Appointment cycle ends before effective date")
            active = activation["effective_date"] <= snapshot["as_of"] <= activation["cycle_end"]
            if activation["active_at_export"] != active:
                raise InputError("Activation conflicts with export-date clock")
        if app["status"] in {"active", "active-with-conditions"} and not (activation and activation["active_at_export"]):
            raise InputError("Active status lacks currently effective approval")
    for name in [snapshot["rules_file"], *snapshot["produced"]]:
        _relative_name(name)
    if snapshot["consumed"] != {"record_files": batch["record_files"], "documents": batch["document_files"]}:
        raise InputError("Snapshot consumed inventory differs from opened batch inputs")
    if not (Path(root) / snapshot["rules_file"]).is_file():
        raise InputError("Rules register does not exist")


def _atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".staging-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _sealed(path, root):
    name = path.relative_to(root).as_posix()
    result = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"HEAD:{name}"], capture_output=True)
    return result.returncode == 0


def run_batch(batch_path, sources_path, output_path, batch_number=1,
              schema_path="snapshot.schema.json", *, root=None, command=None, processor=None):
    """Consume batch 1 and write working evidence; never seal an occurrence."""
    root = Path(root or Path.cwd()).resolve()
    output = Path(output_path).resolve()
    if not output.is_relative_to(root):
        raise InputError("Output directory must be inside the repository")
    relative = lambda path: path.relative_to(root).as_posix()
    log = output / "run-log.md"
    written, consumed, batch = [], [], None
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    command = command or shlex.join([sys.executable, "-m", "credentialing", "run", "--batch", str(batch_path),
                                    "--sources", str(sources_path), "--output", str(output_path),
                                    "--batch-number", str(batch_number), "--schema", str(schema_path)])
    report = {"batch": batch_number, "outcome": "Blocked", "produced": written, "snapshot": None,
              "input_parsed": False, "contract_batch_complete": False, "diagnostics_retained": False}
    try:
        if batch_number != 1:
            raise InputError("G1 supports batch 1 only; continuation requires the next owner gate")
        batch = load_batch(batch_path)
        report["input_parsed"] = True
        consumed = [str(Path(batch_path) / name) for name in batch["input_hashes"]]
        sources, source_raw_hashes, source_text_hashes, source_manifest_hash = _load_source_capture(sources_path)
        consumed.extend(str(Path(sources_path) / name) for name in sources)
        if source_manifest_hash:
            consumed.append(str(Path(sources_path) / "manifest.json"))
        schema = Path(schema_path).resolve()
        consumed.append(str(schema))
        processor_hashes = _processor_hashes()
        rules_file = output / "rules.md"
        rules_hash = _sha(rules_file.read_bytes())
        consumed.extend([str(rules_file), *[str(Path(__file__).resolve().parent.parent / name) for name in processor_hashes]])
        fingerprint = _sha(_json_bytes({"batch": batch["input_hashes"], "source_raw_hashes": source_raw_hashes,
                                        "source_text_hashes": source_text_hashes, "source_manifest_sha256": source_manifest_hash,
                                        "processor_hashes": processor_hashes, "rules_sha256": rules_hash,
                                        "schema": _sha(schema.read_bytes()), "batch_number": batch_number}))
        working = output / "working" / "batch-01"
        metadata_path = working / "run.json"
        snapshot_path = output / "snapshots" / "batch-01.json"
        if _sealed(snapshot_path, root):
            prior = json.loads(metadata_path.read_text()) if metadata_path.is_file() else {}
            if prior.get("fingerprint") != fingerprint or prior.get("snapshot_sha256") != _sha(snapshot_path.read_bytes()):
                raise InputError("Sealed snapshot cannot be overwritten; correction requires an authorized supersession")
            report.update(outcome=prior["outcome"], snapshot=relative(snapshot_path), unchanged=True,
                          contract_batch_complete=True, diagnostics_retained=prior.get("diagnostics_retained", True))
        else:
            if processor is None:
                from .engine import process_batch
                processor = process_batch
            result = processor(batch, sources)
            applications = result["applications"]
            if not applications:
                raise InputError("Engine returned an empty caseload")
            _validate_applications(applications, schema)
            expected = {row["application_id"] for row in batch["tables"]["applications"]}
            if len(applications) != len(expected) or {app["application_id"] for app in applications} != expected:
                raise InputError("Engine result does not preserve the complete, unique caseload")
            unrepresented = [app["application_id"] for app in applications if app.get("status") is None]
            limitations = list(result.get("limitations", []))
            if unrepresented:
                limitations.append({"kind": "schema-status-unrepresentable", "applications": unrepresented,
                                    "reason": "Computed pre-dispatch hold has no truthful status in unchanged snapshot schema; no contract snapshot produced."})
            outcome = "Blocked" if unrepresented else "Partial"
            report["outcome"] = outcome
            report["limitations"] = limitations
            if unrepresented:
                report.update(blocked_stage="snapshot-production", affected_applications=unrepresented,
                              error="Snapshot production blocked: application statuses cannot be truthfully represented in the unchanged schema; input parsed but contract batch incomplete. Diagnostic working results are retained, not a contract snapshot.")
            staged = {
                working / "results.json": {"batch": 1, "as_of": batch["export_date"], "applications": applications,
                                             "outcome": outcome, "artifact_kind": "diagnostic-working-results" if unrepresented else "working-results",
                                             "limitations": limitations, "rules_used": result.get("rules_used", [])},
                working / "history.json": result["history"],
                working / "packets.json": result["packets"],
            }
            metadata = {"batch": 1, "export_date": batch["export_date"], "fingerprint": fingerprint,
                        "input_hashes": batch["input_hashes"], "source_raw_hashes": source_raw_hashes,
                        "source_text_hashes": source_text_hashes, "source_manifest_sha256": source_manifest_hash,
                        "processor_hashes": processor_hashes, "rules_sha256": rules_hash,
                        "outcome": outcome, "snapshot": None, "snapshot_sha256": None,
                        "input_parsed": True, "contract_batch_complete": not unrepresented,
                        "diagnostics_retained": True}
            if unrepresented:
                metadata.update({key: report[key] for key in ("blocked_stage", "affected_applications", "error")})
            if not unrepresented:
                produced = [relative(path) for path in [*staged, metadata_path, snapshot_path, log]]
                snapshot = {"schema_version": "credentialing-snapshot/1", "snapshot_id": f"batch-01-{fingerprint[:20]}",
                            "predecessor": None, "batch": 1, "as_of": batch["export_date"],
                            "consumed": {"record_files": batch["record_files"], "documents": batch["document_files"]},
                            "produced": produced, "rules_file": relative(output / "rules.md"), "applications": applications}
                validate_snapshot(snapshot, batch, schema, root)
                staged[snapshot_path] = snapshot
                metadata["snapshot"] = relative(snapshot_path)
                metadata["snapshot_sha256"] = _sha(_json_bytes(snapshot))
                report["snapshot"] = relative(snapshot_path)
            elif snapshot_path.exists():
                raise InputError("An earlier unsealed snapshot exists; preserve it and resolve the changed input before producing diagnostic work")
            # Serialize everything before mutation; promote the snapshot last.
            staged[metadata_path] = metadata
            encoded = {path: _json_bytes(value) for path, value in staged.items()}
            for path in [item for item in encoded if item != snapshot_path] + ([snapshot_path] if snapshot_path in encoded else []):
                _atomic_write(path, encoded[path])
                written.append(relative(path))
            report.update(contract_batch_complete=not unrepresented, diagnostics_retained=True)
    except Exception as exc:
        report.update(outcome="Blocked", error=f"{type(exc).__name__}: {exc}", snapshot=None)
    report["produced"] = [*written, relative(log)]
    entry = {"execution_time": timestamp, "command": command, "batch": batch_number,
             "input_scope": {"batch": str(batch_path), "sources": str(sources_path), "schema": str(schema_path)},
             "export_date": batch["export_date"] if batch else None, "consumed": consumed, **report}
    prior_log = log.read_text(encoding="utf-8") if log.exists() else "# Run log\n"
    _atomic_write(log, (prior_log + "\n```json\n" + json.dumps(entry, ensure_ascii=False, indent=2) + "\n```\n").encode("utf-8"))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    run = subparsers.add_parser("run", help="consume one closed batch without sealing it")
    run.add_argument("--batch", required=True)
    run.add_argument("--sources", required=True)
    run.add_argument("--output", default="deliverables")
    run.add_argument("--batch-number", type=int, required=True)
    run.add_argument("--schema", default="snapshot.schema.json")
    args = parser.parse_args(argv)
    tokens = sys.argv[1:] if argv is None else argv
    try:
        report = run_batch(args.batch, args.sources, args.output, args.batch_number, args.schema,
                           command=shlex.join([sys.executable, "-m", "credentialing", *tokens]))
    except (OSError, InputError) as exc:
        print(f"Blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["outcome"] == "Blocked" else 0
