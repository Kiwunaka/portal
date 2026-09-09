"""Copy bounded source/CI receipts; keep runtime binaries and full logs outside Git."""
import hashlib
import json
from pathlib import Path
import re
import shutil

base = Path(__file__).resolve().parent
target = Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/evidence/core-source-binding-20260909')
assert not target.exists()
snapshot = json.loads((base / 'snapshot-final.json').read_bytes())
runs = {x['databaseId']: x for x in snapshot['runs']}
assert runs[34304294175]['status'] == 'completed' and runs[34304294175]['conclusion'] == 'success'
assert runs[34304280737]['conclusion'] == runs[34304277115]['conclusion'] == 'failure'
selected = (base / 'selected-ci-output.log').read_text(encoding='utf-8')
counts = [int(x) for x in re.findall(r'(\d+) tests passed', selected)]
assert counts == [3, 29, 6, 15, 473, 81, 8, 5, 24]
assert '1 skipped.' in selected
assert 'SKIPPED_BY_PLATFORM' in selected
assert 'BUILD SUCCESSFUL' in selected
for name in ('core-source.cdx.json.delta.json', 'engine-source.cdx.json.delta.json'):
    changes = json.loads((base / name).read_bytes())
    assert len(changes) == 5
    assert all(re.fullmatch(r'/metadata/tools/0/hashes/[0-4]/content', c['path']) for c in changes)
target.mkdir(parents=True)
def item(path):
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
files = ['snapshot-final.json', 'selected-ci-output.log', 'pr-failure.log',
         'short-ref-failure.log', 'seed-after.log', 'proxy100.log', 'collect-ci.py',
         'bind-client.py', 'retain.py', 'core-source.cdx.json.delta.json',
         'engine-source.cdx.json.delta.json']
manifest = []
for name in files:
    shutil.copyfile(base / name, target / name)
    entry = item(target / name)
    entry['path'] = name
    manifest.append(entry)
client = Path('E:/r12client')
client_receipts = client / 'docs/operations/evidence/2026-09-09-r12-core-source-binding'
receipt = {
    'status':'PASS_SOURCE_BINDING_AND_EXACT_TUPLE_CI', 'sources':snapshot['sources'],
    'retained_files':manifest,
    'client_receipts':[item(p) for p in sorted(client_receipts.glob('*.json'))],
    'local_result':'two builds per platform match each other, old build trees and client runtime bytes; seed exit 0; 100 Windows proxy cycles PASS',
    'hosted_result':{'run':34304294175,'watcher_exit_code':0,'flutter_passed':sum(counts),'flutter_skipped':1,
                     'windows_signing_runtime_negatives':'SKIPPED_BY_PLATFORM',
                     'android':'direct/store unit tasks PASS, no inferred JVM test count',
                     'linux':'conditional daemon gofmt/test/vet/build PASS'},
    'raw_retained_files':[item(base / name) for name in [
        'client-ci-full.log','ci-watch.log','android-a.log','android-b.log',
        'windows-a.log','windows-a-retry.log','windows-b-retry.log',
        'android-evidence.json','windows-evidence.json','core-source.cdx.json',
        'engine-source.cdx.json','core-sbom.log','engine-sbom.log','release-handoff-contract.log']],
    'ordinary_pr_checks':'FAIL_OLD_PROMOTION_BINDINGS', 'source_promotion':False,
    'deploy':False,'candidate_created':False,'signing':False,'release_pass':False,
}
(target / 'receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(f'PASS: {len(manifest)} retained files; {sum(counts)} Flutter tests, one explicit runtime skip')
