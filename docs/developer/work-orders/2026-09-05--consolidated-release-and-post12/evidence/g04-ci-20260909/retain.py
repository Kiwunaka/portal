"""Retain G04 receipts and selected public CI lines; keep full logs/images outside Git."""
from pathlib import Path
import hashlib
import json
import re
import shutil

raw = Path(__file__).resolve().parent
target = Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/evidence/g04-ci-20260909')
target.mkdir(parents=True, exist_ok=True)
snapshot = json.loads((raw / 'snapshot-final.json').read_bytes())
run = next(x for x in snapshot['runs'] if x['databaseId'] == 34301990803)
assert run['status'] == 'completed' and run['conclusion'] == 'success' and run['executed_step_count'] == 22
for run_id in (34301454191, 34301792472):
    item = next(x for x in snapshot['runs'] if x['databaseId'] == run_id)
    assert item['status'] == 'completed' and item['conclusion'] == 'success'

selected = []
for filename in ('platform-current-full.log', 'client-exact-full.log'):
    lines = (raw / filename).read_text(encoding='utf-8-sig').splitlines()
    for line in lines:
        if re.search(r'\d+ tests passed|\d+ passed \(|11 passed in|BUILD SUCCESSFUL|Workspace Flutter and Android unit tests passed|Windows signing runtime negatives|100 start-stop cycles \(skipped\)|> Task :app:test(?:Direct|Store)DebugUnitTest', line):
            selected.append(line)
        elif re.search(r'Set up job\t.*(?:Ubuntu$|24\.04\.4$|Image: ubuntu-24.04$|Version: 20260831.293.1$)|Setup Node\t.*(?:node: v|npm: \d)|Setup Python\t.*Successfully set up CPython|Setup Java\t.*Resolved Java|Setup Go\t.*go version go|Setup Flutter\t.*Flutter 3\.38\.5', line):
            selected.append(line)
(raw / 'selected-ci-output.log').write_text('\n'.join(selected) + '\n', encoding='utf-8')
counts = [int(re.search(r'(\d+) tests passed', line).group(1)) for line in selected if 'tests passed' in line and re.search(r'(\d+) tests passed', line)]
assert counts == [3, 29, 6, 15, 473, 81, 8, 5, 24], counts

files = ['before.log', 'after.log', 'client-push.log', 'snapshot-initial.json', 'snapshot-final.json',
         'boundary.json', 'collect.py', 'check-boundary.py', 'retain.py', 'selected-ci-output.log',
         'client-pr-failure.log', 'platform-pr-failure.log']
manifest = []
for name in files:
    src, dst = raw / name, target / name
    shutil.copyfile(src, dst)
    assert src.read_bytes() == dst.read_bytes()
    manifest.append(dict(path=name, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(), bytes=dst.stat().st_size))
receipt = dict(status='PASS_EXECUTABLE_CI_SCOPE', retained_files=manifest,
               client_flutter=dict(passed=sum(counts), skipped=1, skipped_test='real Windows POKROV Core 1.1.0 survives 100 start-stop cycles'),
               windows_signing_runtime_negatives='SKIPPED_BY_PLATFORM',
               watcher_commands=[dict(command='gh run watch 34301990803 --repo Kiwunaka/POKROV-app --interval 30 --exit-status', exit_code=0),
                                 dict(command='gh run watch 34301792472 --interval 30 --exit-status', exit_code=0)],
               raw_logs=[dict(path=str(raw / name), sha256=hashlib.sha256((raw / name).read_bytes()).hexdigest(), bytes=(raw / name).stat().st_size)
                         for name in ['client-exact-full.log', 'platform-current-full.log', 'client-exact-watch.log', 'platform-current-watch.log']],
               linux_daemon='gofmt/go test/go vet/go build PASS; conditional source foundation only',
               ordinary_pr_contracts='FAIL; retained and not overridden by exact-tuple replay',
               promotion=False, signing=False, candidate_created=False, release_pass=False)
(target / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(f'PASS: {len(manifest)} retained files; {sum(counts)} Flutter tests passed, 1 Windows runtime test skipped')
