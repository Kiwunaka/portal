"""Retained G03 audit: offline inputs, exact source deltas, no runtime acceptance."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys

ROOT = Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
PACKAGE = ROOT / 'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12'
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('classifier', PACKAGE / 'classify_evidence_inputs.py')
classifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])

quality = PACKAGE / 'evidence/integrated-quality-20260909'
receipt = json.loads((quality / 'receipt.json').read_bytes())
retained = []
for row in receipt['retained_files']:
    actual = sha((quality / row['path']).read_bytes())
    assert actual == row['sha256'], row['path']
    retained.append(dict(path=row['path'], sha256=actual, matches=True))
sources = []
for lane, root in [('platform', ROOT), ('client', Path('E:/r12client')), ('core', Path('E:/r12core-implementation'))]:
    base = receipt['sources'][lane]['revision']
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    changes = []
    for name in filter(None, git(root, 'diff', '--name-only', '--no-renames', '-z', base, head).decode().split('\0')):
        result = subprocess.run(['git', '-C', str(root), 'show', head + ':' + name], capture_output=True)
        changes.append(dict(path=name, path_hint=classifier.classify_path(name), sha256=sha(result.stdout) if result.returncode == 0 else None))
    sources.append(dict(lane=lane, root=str(root), base=base, head=head, changes=changes,
                        class_counts=dict(collections.Counter(row['path_hint'] for row in changes))))

# Re-evaluate the retained samples under old/current evaluator source with one
# explicitly recorded interpreter. This does not claim an unchanged live host.
base = receipt['sources']['platform']['revision']
evaluator = 'scripts/performance_budget_gate.py'
contract = ROOT / 'shared/contracts/performance/performance-budgets.v1.json'
samples = quality / '010I-local-web-performance-evidence.json'
historical_result = json.loads((quality / '010I-local-web-performance-gate.json').read_bytes())
records = []
executions = []
for label, revision in [('previous_source', base), ('current_source', sources[0]['head'])]:
    source = git(ROOT, 'show', revision + ':' + evaluator)
    target = OUT / (label + '-evaluator.py')
    target.write_bytes(source)
    output = OUT / (label + '-gate.json')
    command = [sys.executable, '-B', str(target), '--contract', str(contract), '--evidence', str(samples), '--required-scope', 'local_static', '--output', str(output)]
    result = subprocess.run(command, capture_output=True)
    (OUT / (label + '.log')).write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, label
    parsed = json.loads(output.read_bytes())
    assert parsed == historical_result, label
    record = dict(inputs=dict(artifact=sha(samples.read_bytes()), configuration=sha(contract.read_bytes()),
                              toolchain=sha(encoded(dict(python=sys.version, executable_sha256=sha(Path(sys.executable).read_bytes())))),
                              oracle=sha(source), scope=sha(b'offline evaluation of retained local_static samples; no new collection')),
                  environment=platform.platform() + ';current-offline-replay', origin='current-origin;offline')
    records.append(record)
    executions.append(dict(label=label, command=command, exit_code=result.returncode, output_sha256=sha(output.read_bytes()),
                           historical_result_equal=True, counts=parsed['counts']))
comparison = classifier.compare_evidence_inputs(*records)
assert comparison['status'] == 'DECLARED_INPUTS_MATCH_REVIEW_REQUIRED'

# A real classifier/oracle edit must invalidate its previous path conclusions,
# even with the exact same actual source inventory as its artifact input.
classifier_path = (PACKAGE / 'classify_evidence_inputs.py').relative_to(ROOT).as_posix()
old_classifier = git(ROOT, 'show', 'HEAD:' + classifier_path)
new_classifier = (PACKAGE / 'classify_evidence_inputs.py').read_bytes()
old_record = dict(records[0], inputs=dict(records[0]['inputs'], artifact=sha(encoded(sources)), oracle=sha(old_classifier), scope=sha(b'path hints for retained source inventory')))
new_record = dict(old_record, inputs=dict(old_record['inputs'], oracle=sha(new_classifier)))
invalidation = classifier.compare_evidence_inputs(old_record, new_record)
assert invalidation['status'] == 'INVALIDATED' and invalidation['changed'] == ['inputs.oracle']
actual_paths = ['infra/owned-smart-dns/internal/smartdns/server.go', 'infra/owned-smart-dns/go.mod',
                'infra/owned-smart-dns/config.template.json', 'infra/owned-smart-dns/config.fronted.template.json']
path_review = []
for name in actual_paths:
    data = git(ROOT, 'show', 'HEAD:' + name)
    path_review.append(dict(path=name, sha256=sha(data), category=classifier.classify_path(name)))
report = dict(status='PASS_G03_BOUNDED', sources=sources, retained_quality_hashes=retained,
              classifier_sha256=sha(new_classifier), path_review=path_review,
              offline_replay=dict(records=records, comparison=comparison, executions=executions,
                                  decision='REUSE_APPROVED_ONLY_FOR_RETAINED_SAMPLE_EVALUATION',
                                  limitation='No new asset collection, browser/device measurement or release acceptance; original source/environment remain attached.'),
              classifier_oracle_change=dict(previous=old_record, current=new_record, comparison=invalidation),
              aggregate_quality_reuse='NOT_GRANTED: docs/seed/release inputs changed; Core HEAD differs from the client bound Core revision.',
              live_device_reuse='NOT_GRANTED: current server/config/device/freshness inputs have not been established.',
              release_pass=False)
(OUT / 'review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status=report['status'], sources=[dict(lane=x['lane'], head=x['head'], changed_files=len(x['changes'])) for x in sources],
                      retained_hashes=len(retained), offline_replay=comparison['status'], oracle_change=invalidation['status'], release_pass=False), indent=2))
