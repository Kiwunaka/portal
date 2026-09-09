"""Retain only explicit redacted evidence; never rerun the live fixtures."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

root = Path(__file__).parent
platform = Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
wo = platform / 'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12'
dest = wo / 'evidence/a04-auto-reconcile-20260909'
dest.mkdir(exist_ok=True)
def read(name):
    return json.loads((root / name).read_text())
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
pg = read('pg-result.json')
assert pg['result'] == 'PASS_FOUR_RACES_AND_FOUR_EXPIRY_RETRIES' and len(pg['cases']) == 8
for case in pg['cases']:
    if 'order' in case:
        assert case['postgres_block_observed'] and case['ciphertext_preserved']
    else:
        assert case['durable_before_network'] and case['retry_same_key']
for profile in ('awg2', 'awg31'):
    r = read(f'server-{profile}-result-v2.json')
    assert r['result'] == 'PASS_SOURCE_WORKER_PERSISTENT_REVOKE_EXPIRY_AND_RESTART'
    assert r['server_cleanup_verified'] and r['pi_temporary_state_removed'] and r['server_exit_code'] == 0
    assert len(r['core_tests']) == 8 and all(t['oracle_passed'] for t in r['core_tests'])
    assert sum(t['expected'] == 'accepted' for t in r['core_tests']) == 5
    assert len(r['worker_runs']) == 3
    assert all(t['disk_removed'] == t['live_removed'] == 1 and t['failed_targets'] == 0 for t in r['worker_runs'])
    assert all(r['idempotent_retry'][k] == 0 for k in ('failed_targets', 'disk_removed', 'live_removed'))
    assert any(t['phase'] == 'restart' and t['service_restarts'] == 1 for t in r['server'])
    assert not r['raw_material_retained']
before, after = read('server-before.json'), read('server-after.json')
assert before['files'] == after['files']
for interface, old in before['interfaces'].items():
    new = after['interfaces'][interface]
    for key in ('config_sha256', 'live_static_config_sha256', 'unit_active'):
        assert old[key] == new[key]
    assert [p['public_key_sha256'] for p in old['peers']] == [p['public_key_sha256'] for p in new['peers']]
audit = read('final-lab-audit.json')
assert all(v == 'inactive' for v in audit['services'].values())
assert all(v['other_sessions'] == 0 for v in audit['databases'].values())
assert 'VMState="poweroff"' in (root / 'vm-final-state.txt').read_text()
failure = read('persistence-failure.json')
assert failure['result'] == 'PASS_PERSISTENCE_FAILURE_RETRY'
assert all(v is True for v in failure.values() if isinstance(v, bool))
# subprocess text=True on Windows sent CRLF through SSH stdin in this fixture.
helper = (platform / 'portal_bot/awg_peer_remove.py').read_text()
assert failure['source_helper_sha256'] == sha(helper.replace('\n', '\r\n').encode())
assert '99 passed, 12 subtests passed' in (root / 'focused.log').read_text()
assert '1 failed, 179 passed, 8 subtests passed' in (root / 'backend-router.log').read_text()
assert '1 passed' in (root / 'backend-failed-test-recheck.log').read_text()
old = json.loads((wo / 'evidence/a04-key-isolation-20260908/source-manifest.json').read_text())
paths = sorted({v['path'] for v in old['files']} | {'portal_bot/awg_lab_peer_worker.py', 'portal_bot/awg_peer_remove.py'})
manifest = {'captured_at': datetime.now(timezone.utc).isoformat(),
    'scope': 'Current worktree at retention; not a pre-execution source snapshot', 'files': []}
for path in paths:
    raw = (platform / path).read_bytes()
    manifest['files'].append({'path': path, 'bytes': len(raw), 'sha256': sha(raw), 'lf_sha256': sha(raw.replace(b'\r\n', b'\n'))})
(root / 'source-manifest.json').write_bytes((json.dumps(manifest, indent=2) + '\n').encode())
names = '''audit-lab.py backend-router.log backend-failed-test-recheck.log backend-failure-buckets.json
check-persistence-failure.py final-lab-audit.json focused.log persistence-failure.json pg-result.json
pg_lab.py pg_lab-before-rsa-pin.py run-pg.py run-server.py run-server-v1.py server-controller.py
server-before.json server-after.json server-awg2-result.json server-awg2-result-v2.json
server-awg31-result-v2.json vm-final-state.txt source-manifest.json retain.py'''.split()
for name in ('docs-tests.log', 'context-audit.json', 'package-validation.log', 'diff-check.log'):
    if (root / name).exists():
        names.append(name)
files = []
for name in names:
    raw = (root / name).read_bytes()
    (dest / name).write_bytes(raw)
    files.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
receipt = {'result': 'PASS_BOUNDED_SOURCE_WORKER_REVOKE_EXPIRY_RESTART',
    'source_parent': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=platform, text=True).strip(),
    'source_manifest': 'source-manifest.json', 'source_manifest_timing': 'at retention, after execution',
    'source_files': len(paths), 'postgres_races': 4, 'postgres_expiry_retry_cases': 4,
    'core_oracles': {'accepted': 10, 'expected_rejected': 6}, 'actual_worker_cycles': 6,
    'tests': {'focused': '99 passed + 12 subtests', 'backend_initial': '179 passed + 8 subtests; 1 failed across minute boundary',
              'backend_failed_test_recheck': '1 passed with test clock pinned'},
    'retained_files': files, 'cleanup_verified': True, 'original_server_files_static_config_peer_identities_restored': True,
    'server_counters_and_process_ids_unchanged': False, 'production_backend_deployed': False,
    'candidate_created': False, 'remaining': ['legacy shared-key migration', 'permanent Brain worker activation',
        'installed-client actual revoke/expiry', 'updated integrated quality and full release gates']}
(dest / 'receipt.json').write_bytes((json.dumps(receipt, indent=2) + '\n').encode())
print(json.dumps({'retained_files': len(files), 'source_files': len(paths), 'result': receipt['result']}))
