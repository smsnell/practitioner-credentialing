"""Review-only replay of real exports; no Git writes or production seal bypass.

The byte-backed checkpoint test double is the same boundary used by
test_continuation. It lets an owner inspect proposed downstream corrections
without a commit. It is NOT evidence that those candidates are sealed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from credentialing.io import run_batch, _json_bytes, load_batch, validate_snapshot
from credentialing.continuation import load_predecessor, merge_batch


def sha(data):
    return hashlib.sha256(data).hexdigest()


def artifacts(root, number):
    return [root / f'deliverables/snapshots/batch-{number:02d}.json',
            *[root / f'deliverables/working/batch-{number:02d}/{name}.json'
              for name in ('run', 'history', 'results', 'packets')]]


def worker(root, number):
    """Run the actual processor/writer in a fresh interpreter with a test boundary."""
    checkpoint = json.loads((root / 'test-checkpoints.json').read_text())
    def committed(repository, name):
        expected = checkpoint[name]
        data = (root / name).read_bytes()
        if sha(data) != expected:
            raise ValueError('Review checkpoint bytes changed: ' + name)
        return data
    with patch('credentialing.io._sealed', side_effect=lambda path, repository: path.relative_to(root).as_posix() in checkpoint), \
         patch('credentialing.continuation._committed_bytes', side_effect=committed):
        report = run_batch(root / f'inputs/batch-{number:02d}', root / 'sources', root / 'deliverables',
                           number, root / 'snapshot.schema.json', root=root,
                           predecessor_path=root / f'deliverables/snapshots/batch-{number-1:02d}.json' if number > 1 else None,
                           command=f'Review-only replay worker batch {number}; byte-backed test checkpoint, not a Git seal')
    print(json.dumps(report))
    return 2 if report['outcome'] == 'Blocked' else 0


def child(root, number):
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', str(number), '--root', str(root)],
                            capture_output=True, text=True)
    if not result.stdout.strip():
        raise RuntimeError(result.stderr)
    return result.returncode, json.loads(result.stdout)


def replay(destination):
    if not destination.is_relative_to(ROOT / 'deliverables/corrections'):
        raise ValueError('Review destination must be under deliverables/corrections')
    originals = {path.relative_to(ROOT).as_posix(): path.read_bytes()
                 for b in (1, 2, 3) for path in artifacts(ROOT, b)}
    original_log = (ROOT / 'deliverables/run-log.md').read_bytes()
    archive = ROOT / 'deliverables/archive/pre-g3-correction'
    for name, data in {**originals, 'deliverables/run-log.md': original_log}.items():
        target = archive / name
        if target.exists():
            archived = target.read_bytes()
            if archived != data and not (name == 'deliverables/run-log.md' and data.startswith(archived)):
                raise ValueError('Original archive differs: ' + name)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = {'purpose': 'Exact pre-correction bytes; B1/B2 sealed, B3 unsealed G2 candidate',
                'sha256': {name: sha(data) for name, data in originals.items()}}
    (archive / 'manifest.json').write_bytes(_json_bytes(manifest))
    reports, comparisons = [], []
    with tempfile.TemporaryDirectory(prefix='credentialing-g3-replay-') as temporary:
        root = Path(temporary)
        for folder in ('inputs', 'sources'):
            shutil.copytree(ROOT / folder, root / folder)
        (root / 'deliverables').mkdir()
        shutil.copy2(ROOT / 'deliverables/rules.md', root / 'deliverables/rules.md')
        shutil.copy2(ROOT / 'snapshot.schema.json', root / 'snapshot.schema.json')
        checkpoints = {}
        (root / 'test-checkpoints.json').write_text('{}')
        for number in (1, 2, 3):
            code, report = child(root, number)
            if code != 0 or not report.get('contract_batch_complete'):
                raise AssertionError(report)
            snapshot_path = artifacts(root, number)[0]
            snapshot = json.loads(snapshot_path.read_bytes())
            delta = load_batch(root / f'inputs/batch-{number:02d}', allow_empty_applications=number > 1)
            cumulative, pointer = delta, None
            if number > 1:
                prior_history = json.loads(artifacts(root, number-1)[2].read_bytes())
                prior_metadata = json.loads(artifacts(root, number-1)[1].read_bytes())
                cumulative = merge_batch(delta, prior_history, number, prior_metadata)
                pointer = {'path': f'deliverables/snapshots/batch-{number-1:02d}.json',
                           'sha256': sha(artifacts(root, number-1)[0].read_bytes())}
            validate_snapshot(snapshot, cumulative, root / 'snapshot.schema.json', root,
                              batch_number=number, predecessor=pointer, consumed_batch=delta)
            old = json.loads(originals[snapshot_path.relative_to(root).as_posix()])
            old_by_id = {a['application_id']: a for a in old['applications']}
            changed = {a['application_id']: [key for key in a if a[key] != old_by_id[a['application_id']][key]]
                       for a in snapshot['applications'] if a != old_by_id[a['application_id']]}
            comparisons.append({'batch': number, 'old_snapshot_id': old['snapshot_id'],
                'candidate_snapshot_id': snapshot['snapshot_id'], 'candidate_sha256': sha(snapshot_path.read_bytes()),
                'changed_application_fields': changed,
                'statuses_unchanged': all(a['status'] == old_by_id[a['application_id']]['status'] for a in snapshot['applications']),
                'decisions_unchanged': all(a['decisions'] == old_by_id[a['application_id']]['decisions'] for a in snapshot['applications'])})
            reports.append(report)
            # Test-only checkpoint after validation; never a Git operation.
            checkpoints.update({p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in artifacts(root, number)})
            (root / 'test-checkpoints.json').write_bytes(_json_bytes(checkpoints))
        # Identical replay retains existing bytes; this exercises the guard only
        # against the explicitly simulated checkpoint, not a claimed real seal.
        code, unchanged = child(root, 3)
        assert code == 0 and unchanged.get('unchanged')
        assert all(sha((root / name).read_bytes()) == digest for name, digest in checkpoints.items())
        candidate = destination / 'candidate'
        candidate.mkdir(parents=True, exist_ok=True)
        shutil.copytree(root / 'deliverables', candidate / 'deliverables', dirs_exist_ok=True)
        # Adversarial replay must leave last checked snapshot bytes untouched.
        schema_bytes = (root / 'snapshot.schema.json').read_bytes()
        (root / 'inputs/batch-03/applications.csv').write_text('broken\n')
        code, malformed = child(root, 3)
        assert code == 2 and malformed['snapshot'] is None
        assert all(sha((root / name).read_bytes()) == digest for name, digest in checkpoints.items())
        shutil.copy2(ROOT / 'inputs/batch-03/applications.csv', root / 'inputs/batch-03/applications.csv')
        old_history = artifacts(root, 2)[2].read_bytes()
        artifacts(root, 2)[2].write_bytes(old_history + b' ')
        code, tampered = child(root, 3)
        assert code == 2 and tampered['snapshot'] is None
        artifacts(root, 2)[2].write_bytes(old_history)
        assert all(sha((root / name).read_bytes()) == digest for name, digest in checkpoints.items())
        assert (root / 'snapshot.schema.json').read_bytes() == schema_bytes
        report = {'scope': 'Real-source corrected candidates; fresh processes; Git checkpoint boundary simulated only in this test harness',
                  'sealed': False, 'promotion_authorized': False,
                  'required_after_acceptance': 'Authorize promotion, real sequential sealing and fresh-process resume; preserve archived originals',
                  'runs': reports, 'comparisons': comparisons,
                  'checks': {'schema_date_cross_record': True, 'unchanged_replay': unchanged,
                             'malformed_input_preserved_checked_bytes': malformed,
                             'tampered_predecessor_rejected': tampered},
                  'original_sha256': manifest['sha256']}
        (destination / 'report.json').write_bytes(_json_bytes(report))
    assert all((ROOT / name).read_bytes() == data for name, data in originals.items())
    assert (ROOT / 'deliverables/run-log.md').read_bytes() == original_log
    print(json.dumps({'review_package': str(destination.relative_to(ROOT)), 'comparisons': comparisons}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=ROOT / 'deliverables/corrections/g3-review')
    parser.add_argument('--worker', type=int)
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    if args.worker:
        raise SystemExit(worker(args.root, args.worker))
    replay(args.destination.resolve())
