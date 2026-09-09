"""Verify and retain the completed, bounded A04 key-isolation evidence."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).parent
platform = Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
dest = platform / 'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/evidence/a04-key-isolation-20260908'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda name: json.loads((root / name).read_text(encoding='utf-8-sig'))
assert not dest.exists(), 'Preserve retained evidence'
source = read('source-manifest.json')
assert len(source['files']) == 196
for item in source['files']:
    assert sha((platform / item['path']).read_bytes()) == item['sha256'], item['path']

checks = {}
for name, passed, subtests in [('focused-final.log', 92, 12), ('backend-router.log', 175, 8),
                              ('auth-router.log', 138, 22), ('scripts-router.log', 44, 21),
                              ('docs-tests.log', 33, 0)]:
    log = (root / name).read_text(encoding='utf-8-sig')
    assert re.search(r'\b' + str(passed) + r' passed\b', log), name
    assert not re.search(r'(^FAILED |\d+ failed)', log, re.M), name
    if subtests:
        assert str(subtests) + ' subtests passed' in log, name
    checks[name] = {'passed': passed, 'subtests_passed': subtests, 'result': 'PASS'}
assert '6 failed' in (root / 'negative-key-binding.log').read_text(encoding='utf-8-sig')
pg = read('pg-result.json')
assert read('pg-execution.json')['exit_code'] == 0
assert pg['result'] == 'PASS_FOUR_POSTGRES_DEVICE_KEY_RACES' and len(pg['cases']) == 4
for case in pg['cases']:
    assert case['advisory_lock_observed'] and case['one_device_bound_row']
    assert case['x25519_clamped_alias_compared']
    if case['first_transaction'] == 'commit':
        assert case['contender_code'] == 'material_key_already_bound'
        assert case['committed_ciphertext_preserved']
    else:
        assert case['first_transaction'] == 'rollback' and case['contender_outcome'] == 'inserted'

http_statuses = [428, 200, 200, 200, 200, 422, 200, 200, 200, 200, 200,
                 200, 401, 200, 422, 200, 200, 200, 200, 200, 401, 200, 401]
for profile in ('awg2', 'awg31'):
    http = read(f'http-{profile}-result-v3.json')
    peer = read(f'http-peer-{profile}-v3.json')
    assert http['result'] == 'PASS_GUARDED_HTTP_DEVICE_KEY_LIFECYCLE'
    assert [x['status'] for x in http['http']] == http_statuses
    assert http['source_files_checked'] == 196 and http['final_active_material_rows'] == 0
    assert http['final_material_rows'] == 3 and http['operator_payload_secret_check']
    assert peer['result'] == 'PASS_BOUNDED_HTTP_AND_TWO_DEVICE_PEER_LIFECYCLE'
    assert peer['guest_exit_code'] == peer['server_exit_code'] == 0
    assert peer['server_cleanup_verified'] and peer['pi_temporary_state_removed']
    assert len(set(peer['public_key_sha256'].values())) == 3
    tests = peer['core_tests']
    assert len(tests) == 7 and all(x['oracle_passed'] and x['selected_subtest_observed'] for x in tests)
    assert [x['expected'] for x in tests] == ['accepted', 'accepted', 'rejected', 'accepted', 'accepted', 'rejected', 'accepted']
    for test in tests:
        assert test['returncode'] == (0 if test['expected'] == 'accepted' else 1)
        assert test['classification'] == ('passed' if test['expected'] == 'accepted' else 'failed_no_outer_response')
    assert tests[0]['payload_sha256'] == tests[2]['payload_sha256'] == tests[5]['payload_sha256']
    assert tests[1]['payload_sha256'] == tests[3]['payload_sha256'] == tests[6]['payload_sha256']
    assert peer['http_phases'][1] == {'phase': 'revoke_a', 'status': 401, 'active_materials': 0}
    assert all(x.get('original_peer_present', True) for x in peer['server'])
    assert peer['server'][-1]['passed'] and peer['server'][-1]['original_peers_restored']
    for key in peer['public_key_sha256'].values():
        assert any(p['public_key_sha256'] == key and p['rx_bytes'] > 0 and p['tx_bytes'] > 0
                   and p['handshake_unix'] > 0 for step in peer['server'] for p in step.get('test_peers', []))

before, after = read('server-before.json'), read('server-after.json')
for obj in (before, after):
    obj.pop('utc', None)
assert before == after, 'Owned server baseline changed'
audit = read('final-lab-audit.json')
assert audit['source_files_unchanged'] == 196 and audit['fixture_runner_processes'] == 0
assert not audit['previous_databases_recreated'] and not audit['production_database_mutated']
assert all(x == 'inactive' for x in audit['services'].values())
assert all(x['other_sessions'] == 0 for x in audit['databases'].values())
assert 'VMState="poweroff"' in (root / 'vm-final-state.txt').read_text(encoding='utf-8-sig')

names = sorted(p.name for p in root.iterdir() if p.suffix in ('.py', '.json', '.log')
               and p.name != 'synthetic-endpoints.json') + ['vm-final-state.txt']
files = {name: (root / name).read_bytes() for name in names}
for name, raw in files.items():
    assert not re.search(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----\s+[A-Za-z0-9+/=]{30}', raw), name
    assert not re.search(rb'postgres(?:ql)?://[^\s\"\x27]+:[^\s\"\x27]+@', raw), name
external = []
for name in ('source.tar', 'test-libs.zip', 'synthetic-endpoints.json'):
    p = root / name
    external.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())})
inventory = [{'path': name, 'bytes': len(raw), 'sha256': sha(raw)} for name, raw in files.items()]
runtime_names = ['portal_bot/awg_lab_key_binding.py', 'portal_bot/awg2_lab_service.py',
                 'portal_bot/awg31_lab_service.py', 'scripts/remote_bind_owned_awg_lab_device.py']
receipt = {
    'result': 'PASS_BOUNDED_KEY_ISOLATION', 'source_parent': source['source_parent'],
    'source_files_verified': 196, 'checks': checks, 'postgres_cases': 4,
    'http_assertions': 46, 'core_oracles': {'accepted': 10, 'expected_rejections': 4},
    'runtime_files': {n: {'worktree_sha256': sha((platform/n).read_bytes()),
                         'lf_sha256': sha((platform/n).read_bytes().replace(b'\r\n', b'\n'))} for n in runtime_names},
    'scope': 'Isolated ASGI/PostgreSQL identities; exact Core 02a091c on owned RU Pi; ephemeral DE peers. Controller applies server changes after HTTP revoke, not automatic product enforcement.',
    'retained_files': inventory, 'external_archives': external,
    'historical_failures': ['v1: TestClient lacked httpx2; no material issued',
                            'v2: fixture fresh-auth call omitted now; partial results and cleanup retained'],
    'cleanup_verified': True, 'production_deploy': False, 'candidate_created': False,
    'remaining': ['Existing shared lab key migration', 'Automatic server revoke/expiry',
                  'Installed-client revoke/expiry', 'Current integrated quality and release gates'],
}
dest.mkdir(parents=True)
for name, raw in files.items():
    (dest/name).write_bytes(raw)
(dest/'receipt.json').write_bytes((json.dumps(receipt, indent=2) + '\n').encode())
print(json.dumps({'result': receipt['result'], 'retained_files': len(files),
                  'source_files_verified': 196, 'postgres_cases': 4, 'http_assertions': 46, 'core_oracles': 14}))
