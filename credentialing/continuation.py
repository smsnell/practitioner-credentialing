"""Verify sealed retained state and append one closed export's observations."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator, FormatChecker

from .io import InputError, REQUIRED_TABLES, _relative_name


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _committed_bytes(root, name):
    result = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{name}"], capture_output=True)
    if result.returncode:
        raise InputError(f"Predecessor artifact is not sealed at HEAD: {name}")
    return result.stdout


def _sealed_bytes(root, path):
    if not path.resolve().is_relative_to(root):
        raise InputError("Predecessor artifact escapes repository")
    name = _relative_name(path.relative_to(root).as_posix())
    data = path.read_bytes()
    if data != _committed_bytes(root, name):
        raise InputError(f"Predecessor artifact differs from sealed bytes: {name}")
    return data


def verify_sealed_outputs(snapshot_path, metadata, root):
    """An unchanged rerun also verifies retained state rather than trusting it."""
    snapshot_path, root = Path(snapshot_path), Path(root)
    working = snapshot_path.parent.parent / "working" / f"batch-{metadata['batch']:02d}"
    _sealed_bytes(root, snapshot_path)
    _sealed_bytes(root, working / "run.json")
    hashes = metadata.get("output_hashes")
    if hashes is None and metadata["batch"] != 1:
        raise InputError("Sealed metadata lacks retained output hashes")
    for name in ("history", "results", "packets"):
        path = working / (name + ".json")
        data = _sealed_bytes(root, path)
        if hashes is not None and hashes.get(path.relative_to(root).as_posix()) != _sha(data):
            raise InputError(f"Sealed retained output hash mismatch: {path.name}")


def load_predecessor(path, batch_number, export_date, root, schema_path):
    """Read only an exact sealed predecessor and its matching retained files."""
    root = Path(root).resolve()
    path = Path(path).resolve()
    if not path.is_relative_to(root):
        raise InputError("Predecessor must be inside the repository")
    snapshot_data = _sealed_bytes(root, path)
    snapshot = json.loads(snapshot_data)
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(snapshot)
    if snapshot["batch"] != batch_number - 1:
        raise InputError("Predecessor must be the immediately preceding batch")
    if export_date <= snapshot["as_of"]:
        raise InputError("Export dates must advance strictly beyond the predecessor")
    # Validate the retained chain against committed bytes, never the run date.
    prior = snapshot
    seen = {path.relative_to(root).as_posix()}
    while prior["predecessor"] is not None:
        link = prior["predecessor"]
        name = _relative_name(link["path"])
        if name in seen:
            raise InputError("Predecessor chain contains a cycle")
        seen.add(name)
        ancestor_data = _sealed_bytes(root, root / name)
        if _sha(ancestor_data) != link["sha256"]:
            raise InputError(f"Predecessor chain hash mismatch: {name}")
        ancestor = json.loads(ancestor_data)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(ancestor)
        if ancestor["batch"] != prior["batch"] - 1 or ancestor["as_of"] >= prior["as_of"]:
            raise InputError("Predecessor chain sequence is invalid")
        prior = ancestor
    if prior["batch"] != 1:
        raise InputError("Predecessor chain does not begin with batch 1")
    working = path.parent.parent / "working" / f"batch-{snapshot['batch']:02d}"
    files = {name: working / (name + ".json") for name in ("run", "history", "results", "packets")}
    encoded = {name: _sealed_bytes(root, file) for name, file in files.items()}
    metadata = json.loads(encoded["run"])
    pointer = {"path": path.relative_to(root).as_posix(), "sha256": _sha(snapshot_data)}
    if (metadata.get("snapshot") != pointer["path"] or metadata.get("snapshot_sha256") != pointer["sha256"]
            or metadata.get("batch") != snapshot["batch"] or metadata.get("export_date") != snapshot["as_of"]
            or not metadata.get("contract_batch_complete")):
        raise InputError("Predecessor metadata does not match its snapshot")
    hashes = {file.relative_to(root).as_posix(): _sha(encoded[name]) for name, file in files.items()}
    hashes[pointer["path"]] = pointer["sha256"]
    outputs = metadata.get("output_hashes")
    if outputs is None and snapshot["batch"] != 1:
        raise InputError("Predecessor metadata lacks retained output hashes")
    for name in ("history", "results", "packets"):
        filename = files[name].relative_to(root).as_posix()
        if outputs is not None and outputs.get(filename) != hashes[filename]:
            raise InputError(f"Predecessor retained output hash mismatch: {filename}")
    if snapshot["batch"] > 1 and metadata.get("predecessor") != snapshot["predecessor"]:
        raise InputError("Predecessor metadata chain differs from snapshot chain")
    history = json.loads(encoded["history"])
    results = json.loads(encoded["results"])
    if results.get("applications") != snapshot["applications"] or results.get("as_of") != snapshot["as_of"]:
        raise InputError("Predecessor working results differ from its snapshot")
    ids = {app["application_id"] for app in snapshot["applications"]}
    if set(history.get("applications", {})) != ids or not REQUIRED_TABLES.issubset(history.get("raw_tables", {})):
        raise InputError("Predecessor retained history has incomplete caseload/tables")
    if not isinstance(history.get("raw_documents"), dict):
        raise InputError("Predecessor retained documents are missing")
    return {"snapshot": snapshot, "history": history, "metadata": metadata,
            "predecessor": pointer, "state_hashes": hashes}


ROW_KEYS = {
    "applications": ("application_id", "revision"),
    "application-disclosures": ("application_id", "revision", "question_code"),
    "declared-history": ("application_id", "revision", "entry_id"),
    "declared-credentials": ("application_id", "revision", "declaration_id"),
    "privilege-requests": ("application_id", "revision", "request_id"),
    "peer-referees": ("application_id", "revision", "referee_id"),
    "verification-replies": ("reply_id",), "certification-replies": ("reply_id",),
    "peer-reference-replies": ("reply_id",), "verification-attempts": ("attempt_id",),
    "correspondence": ("letter_id",),
    "licence-lookup-wa": ("credentialnumber", "lookup_date"),
    "licence-lookup-other-states": ("board_state", "licence_number", "lookup_date"),
}


def merge_batch(delta, retained, batch_number, previous_metadata):
    """Append immutable rows, retaining every revision and selective observation."""
    merged = deepcopy(delta)
    tables = {}
    for name, keys in ROW_KEYS.items():
        rows, seen = [], {}
        for row in [*retained["raw_tables"][name], *delta["tables"][name]]:
            try:
                key = tuple(row[column] for column in keys)
            except KeyError as exc:
                raise InputError(f"Missing row identity column in {name}: {exc}") from exc
            if key in seen:
                if seen[key] != row:
                    raise InputError(f"Closed export row changed for {name}: {key}")
                continue
            seen[key] = row
            rows.append(deepcopy(row))
        tables[name] = rows
    documents = deepcopy(retained["raw_documents"])
    for name, text in delta["documents"].items():
        if name in documents and documents[name] != text:
            raise InputError(f"Closed export document changed: {name}")
        documents[name] = text
    for row in tables["correspondence"]:
        if _relative_name(row["document_path"]) not in documents:
            raise InputError(f"Retained indexed document is missing: {row['document_path']}")
    if not tables["applications"]:
        raise InputError("Cumulative retained state has no caseload")
    source_batches = deepcopy(retained.get("source_batches"))
    if source_batches is None:
        if batch_number != 2:
            raise InputError("Retained input provenance is missing earlier batches")
        source_batches = [{"batch": 1, "export_date": previous_metadata["export_date"],
                           "input_hashes": previous_metadata["input_hashes"]}]
    if ([entry["batch"] for entry in source_batches] != list(range(1, batch_number))
            or source_batches[-1]["export_date"] != previous_metadata["export_date"]
            or source_batches[-1]["input_hashes"] != previous_metadata["input_hashes"]):
        raise InputError("Retained input provenance disagrees with predecessor metadata/sequence")
    source_batches.append({"batch": batch_number, "export_date": delta["export_date"],
                           "input_hashes": deepcopy(delta["input_hashes"])})
    hashes = {f"batch-{entry['batch']:02d}/{name}": digest for entry in source_batches
              for name, digest in entry["input_hashes"].items()}
    merged.update(tables=tables, documents=documents, source_batches=source_batches, input_hashes=hashes)
    return merged


def validate_retained_result(result, previous):
    """A new export cannot erase or reinterpret prior computed decisions/history."""
    current = {app["application_id"]: app for app in result["applications"]}
    for app in previous["snapshot"]["applications"]:
        new = current.get(app["application_id"])
        if new is None or new["decisions"][:len(app["decisions"])] != app["decisions"]:
            raise InputError(f"Previously received decisions changed or disappeared: {app['application_id']}")
    for app_id, old in previous["history"]["applications"].items():
        new = result["history"].get("applications", {}).get(app_id, {})
        for key in ("assessments", "readiness_history", "decisions"):
            if new.get(key, [])[:len(old.get(key, []))] != old.get(key, []):
                raise InputError(f"Retained {key} changed or disappeared: {app_id}")
