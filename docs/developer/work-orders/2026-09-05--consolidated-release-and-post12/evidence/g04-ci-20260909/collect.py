"""Read-only G04 metadata collection; an executed failure remains a failure."""
from pathlib import Path
import base64
import datetime
import hashlib
import json
import subprocess
import sys

OUT = Path(__file__).resolve().parent
target = OUT / sys.argv[1]
if target.exists():
    raise SystemExit('Keep previous snapshot; choose a new output name')

def gh(*args):
    proc = subprocess.run(['gh', *args], capture_output=True)
    if proc.returncode:
        raise RuntimeError('GitHub read failed: ' + ' '.join(args[:3]))
    return json.loads(proc.stdout)

def sha(data):
    return hashlib.sha256(data).hexdigest()

runs = [
    ('Kiwunaka/portal', 34301454191),
    ('Kiwunaka/portal', 34301792472),
    ('Kiwunaka/portal', 34301792505),
    ('Kiwunaka/portal', 34301790647),
    ('Kiwunaka/POKROV-app', 34301989210),
    ('Kiwunaka/POKROV-app', 34301990803),
    ('Kiwunaka/POKROV-app', 33944971093),
    ('Kiwunaka/pokrov-core', 34296498734),
]
report = dict(captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), runs=[], repositories=[], workflows=[])
for repo, run_id in runs:
    data = gh('run', 'view', str(run_id), '--repo', repo, '--json',
              'databaseId,event,headSha,headBranch,status,conclusion,jobs,url,createdAt,updatedAt,workflowName')
    data['repository'] = repo
    data['executed_step_count'] = sum(step['status'] == 'completed' and step['conclusion'] != 'skipped'
                                      for job in data['jobs'] for step in job['steps'])
    data['evidence_label'] = ('NOT_RUN' if data['status'] == 'completed' and data['executed_step_count'] == 0
                               else ('PASS' if data['conclusion'] == 'success' else data['conclusion'].upper() or 'IN_PROGRESS'))
    report['runs'].append(data)

for repo in ('Kiwunaka/portal', 'Kiwunaka/POKROV-app', 'Kiwunaka/pokrov-core', 'Kiwunaka/pokrov'):
    details = gh('api', 'repos/' + repo)
    collaborators = gh('api', 'repos/' + repo + '/collaborators')
    report['repositories'].append(dict(name=repo, private=details['private'], default_branch=details['default_branch'],
                                       default_permissions=gh('api', 'repos/' + repo + '/actions/permissions/workflow'),
                                       collaborators=[dict(login=x['login'], role=x['role_name']) for x in collaborators]))

specs = [
    ('Kiwunaka/portal', 'd57ead0a34f6a4eaf639bc741102356f9fb2f436', ['guardrails.yml', 'release-v2-contract.yml', 'support-signing-custody.yml']),
    ('Kiwunaka/POKROV-app', 'de5d4784ecd9d1fc90575e48e16da0f90f42da41', ['release-v2-contract.yml']),
    ('Kiwunaka/pokrov-core', 'c7a11f7d2fd974726095ad7aa0619c055273dd15', ['ci.yml']),
    ('Kiwunaka/pokrov', '9169f272203ec690ab7b0e6a69e92dc2b6762cb4', ['prepare-signed-candidate.yml', 'release-index-contract.yml']),
]
for repo, revision, names in specs:
    for name in names:
        path = '.github/workflows/' + name
        data = gh('api', 'repos/' + repo + '/contents/' + path + '?ref=' + revision)
        source = base64.b64decode(data['content'])
        report['workflows'].append(dict(repository=repo, revision=revision, path=path,
                                        git_blob=data['sha'], sha256=sha(source), source=source.decode()))

report['budget'] = dict(evidence_class='OWNER_PROVIDED_SCREENSHOT', account='Kiwunaka',
                        lfs_budget_usd=0, stop_usage=True, lfs_billable_usd=0,
                        displayed_storage_gb=1.8, displayed_included_storage_gb=10,
                        displayed_bandwidth_gb=0, displayed_included_bandwidth_gb=10,
                        screenshots=[dict(name=name, sha256=sha((OUT / name).read_bytes()))
                                     for name in ('account-budget-private.png', 'lfs-usage-private.png')],
                        raw_images_in_git=False, settings_changed=False,
                        official_policy='https://docs.github.com/en/billing/concepts/product-billing/git-lfs')
report['release_pass'] = False
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps([dict(repo=x['repository'], id=x['databaseId'], status=x['status'], conclusion=x['conclusion'], executed_steps=x['executed_step_count']) for x in report['runs']], indent=2))
