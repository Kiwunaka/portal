"""Check the retained workflow/permission readback, without accessing secrets."""
from pathlib import Path
import hashlib
import json
import re
import yaml

root = Path(__file__).resolve().parent
source = root / 'snapshot-initial.json'
data = json.loads(source.read_bytes())
workflows = {(x['repository'], x['path'].split('/')[-1]): yaml.load(x['source'], Loader=yaml.BaseLoader)
             for x in data['workflows']}
checks = []

def check(name, condition):
    checks.append(dict(name=name, passed=bool(condition)))
    assert condition, name

support = workflows['Kiwunaka/portal', 'support-signing-custody.yml']
check('support_manual_or_master_push_only', set(support['on']) == {'push', 'workflow_dispatch'} and support['on']['push']['branches'] == ['master'])
check('support_job_master_guard', support['jobs']['verify-hosted-custody']['if'] == "github.ref == 'refs/heads/master'")
check('support_checkout_exact_trigger', support['jobs']['verify-hosted-custody']['steps'][0]['with']['ref'] == '${{ github.sha }}')
signer = workflows['Kiwunaka/pokrov', 'prepare-signed-candidate.yml']
check('release_signer_manual_only', set(signer['on']) == {'workflow_dispatch'})
check('release_signer_main_guard', signer['jobs']['prepare-signed-candidate']['if'] == "github.ref == 'refs/heads/main'")
for row in data['workflows']:
    parsed = workflows[row['repository'], row['path'].split('/')[-1]]
    if 'pull_request' in parsed['on']:
        check(row['repository'] + ':' + row['path'] + ':no_signing_secret_reference',
              not re.search(r'secrets\.[A-Z_]*(?:SIGNING|CODE_SECRET)', row['source']))
    check(row['repository'] + ':' + row['path'] + ':no_privileged_pr_chain',
          not {'pull_request_target', 'workflow_run'}.intersection(parsed['on']))
for repo in data['repositories']:
    check(repo['name'] + ':read_only_default_token', repo['default_permissions'] == dict(default_workflow_permissions='read', can_approve_pull_request_reviews=False))
    check(repo['name'] + ':owner_is_only_collaborator', repo['collaborators'] == [dict(login='Kiwunaka', role='admin')])
negative = next(x for x in data['runs'] if x['databaseId'] == 34301790647)
check('non_master_custody_actual_job_skipped_without_steps', negative['conclusion'] == 'skipped' and negative['executed_step_count'] == 0)
report = dict(status='PASS_DECLARED_SIGNING_BOUNDARY', snapshot_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), checks=checks,
              secret_values_read=False, signing_executed=False,
              limitation='Declared normal PR paths and current owner-only collaborators; not isolation from an owner able to change workflows/settings.')
(root / 'boundary.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(f'PASS: {len(checks)} retained boundary checks; no secret values accessed')
