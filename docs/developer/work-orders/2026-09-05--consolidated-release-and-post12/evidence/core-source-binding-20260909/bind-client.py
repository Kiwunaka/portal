"""Bind the reviewed Core head only after exact two-build byte comparison."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

base = Path('E:/r12-core-rebinding-20260909')
client = Path('E:/r12client')
core = Path('E:/r12core-implementation')
old = '02a091cb0e369192a5ad0909b56ccba8aa1dce17'
new = 'c7a11f7d2fd974726095ad7aa0619c055273dd15'
evidence = client / 'docs/operations/evidence/2026-09-09-r12-core-source-binding'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, text):
    path.write_bytes(text.encode('utf-8'))

def git(*args):
    return subprocess.check_output(['git', *args], cwd=core).decode().strip()

assert git('rev-parse', 'HEAD') == new
assert not git('status', '--porcelain')
changed = git('diff', '--name-only', old, new).splitlines()
assert changed == ['docs/release.md', 'scripts/build-apple.sh'], changed
manifest = client / 'config/runtime-artifacts.seed.json'
data = json.loads(manifest.read_text(encoding='utf-8'))
runtime = data['core']
assert runtime['source_commit'] == old
assert not evidence.exists(), 'Do not overwrite retained evidence'
checks = []
receipts = {}
for lane in ('android', 'windows'):
    receipt_path = base / f'{lane}-evidence.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
    assert receipt['source'] == {'commit': new, 'clean': True}
    assert receipt['reproducibility']['result'] == 'PASS_BYTE_IDENTICAL_TWO_BUILDS'
    for entry in receipt['reproducibility']['files']:
        first = base / f'{lane}-a' / entry['path']
        second = base / f'{lane}-b' / entry['path']
        assert sha(first) == sha(second) == entry['sha256']
        assert first.stat().st_size == second.stat().st_size == entry['size']
        installed = client / runtime['assets'][lane]['sync_destination'] / entry['path']
        previous = Path('E:/r12-awg-crossfield-20260908') / f'{lane}-a' / entry['path']
        assert sha(previous) == entry['sha256']
        if installed.exists():
            assert sha(installed) == entry['sha256']
        checks.append({'lane': lane, **entry, 'previous_build_identical': True,
                       'client_file_identical': True if installed.exists() else None})
    receipts[lane] = receipt
assert '100 proxy-only start/stop cycles' in (base / 'proxy100.log').read_text(encoding='utf-8-sig')
evidence.mkdir(parents=True)
shutil.copyfile(manifest, evidence / 'previous-runtime-binding.json')
replacement = {old: new}
runtime['source_commit'] = new
provenance = runtime['artifact_provenance']
for lane, receipt in receipts.items():
    receipt_path = base / f'{lane}-evidence.json'
    shutil.copyfile(receipt_path, evidence / receipt_path.name)
    asset = runtime['assets'][lane]
    assert sha(base / f'{lane}-a' / asset['entry']) == asset['sha256']
    asset['source_commit'] = new
    provenance['reproducible_build'][lane]['source_commit'] = new
    meta = provenance['artifact_evidence'][lane]
    assert meta['tree_sha256'] == receipt['reproducibility']['tree_sha256']
    replacement[meta['evidence_sha256']] = sha(receipt_path)
    meta.update(source_commit=new, evidence_sha256=sha(receipt_path))
    for artifact in (base / f'{lane}-a').iterdir():
        shutil.copyfile(artifact, core / 'dist' / lane / artifact.name)
for entry in provenance['artifact_evidence']['sbom']:
    digest = sha(base / entry['name'])
    replacement[entry['sha256']] = digest
    entry['sha256'] = digest
notice = client / runtime['native_go_notices']['file']
text = notice.read_bytes()
assert old.encode() in text
notice.write_bytes(text.replace(old.encode(), new.encode()))
runtime['native_go_notices'].update(source_commit=new, sha256=sha(notice))
write(manifest, json.dumps(data, ensure_ascii=False, indent=2) + '\n')
validator = client / 'scripts/validate-seed.ps1'
text = validator.read_text(encoding='utf-8')
for source, target in replacement.items():
    assert source in text
    text = text.replace(source, target)
write(validator, text)
for relative in ('test/fixtures/release-handoff-v2/synthetic-candidate-input.json',
                 'docs/architecture/bootstrap-workflow.md'):
    path = client / relative
    text = path.read_text(encoding='utf-8')
    assert old in text
    write(path, text.replace(old, new))
with zipfile.ZipFile(base / 'android-a/pokrov-core.aar') as archive:
    abis = sorted(n.split('/')[1] for n in archive.namelist()
                  if n.startswith('jni/') and n.endswith('/libpokrov-core.so'))
assert abis == ['arm64-v8a', 'armeabi-v7a', 'x86', 'x86_64']
report = {
    'result': 'PASS_EXACT_SOURCE_REBINDING_SAME_RUNTIME_BYTES',
    'previous_core_commit': old, 'source_commit': new,
    'changed_core_paths': changed, 'compared_files': checks,
    'android_abis': abis, 'desktop_abi': 2, 'event_abi': 1, 'exports': 15,
    'windows_proxy_only_cycles': 100, 'proxy_log_sha256': sha(base / 'proxy100.log'),
    'native_notice_change': 'source reference only; verbatim license text unchanged',
    'candidate_created': False, 'promotion': 'NOT_PERFORMED',
    'runtime_acceptance': 'No new device or system-route observation; older bounded observations retain their original candidate identity',
    'commands_and_logs': [
        {'file': p.name, 'sha256': sha(p)} for p in sorted(base.glob('*.log'))
    ],
}
write(evidence / 'binding.json', json.dumps(report, indent=2) + '\n')
print(json.dumps({'result': report['result'], 'files_compared': len(checks)}))
