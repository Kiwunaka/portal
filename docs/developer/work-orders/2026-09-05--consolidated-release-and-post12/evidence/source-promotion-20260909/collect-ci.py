"""Retain source-promotion CI attempts and PR state without replacing failures."""
import datetime
import json
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
target = out / sys.argv[1]
assert not target.exists()
def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args]))
report = {'captured_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'runs': [], 'pull_requests': [], 'promotion_heads': [], 'release_pass': False}
runs = [
    ('Kiwunaka/portal', 34305956151, 1),
    ('Kiwunaka/portal', 34305956175, 1),
    ('Kiwunaka/portal', 34306710358, 1),
    ('Kiwunaka/portal', 34306710387, 1),
    ('Kiwunaka/POKROV-app', 34305952959, 1),
    ('Kiwunaka/POKROV-app', 34306715500, 1),
    ('Kiwunaka/POKROV-app', 34306715500, 2),
    ('Kiwunaka/pokrov-core', 34305948898, 1),
    ('Kiwunaka/pokrov-core', 34305948898, 2),
    ('Kiwunaka/portal', 34307351132, 1),
    ('Kiwunaka/POKROV-app', 34308102145, 1),
]
for repo, number, branch in [('Kiwunaka/portal',243,'master'), ('Kiwunaka/POKROV-app',95,'main'), ('Kiwunaka/pokrov-core',9,'main')]:
    pr = gh('pr', 'view', str(number), '--repo', repo, '--json',
            'headRefOid,baseRefOid,state,isDraft,mergeCommit,mergedAt,statusCheckRollup,url')
    pr['repository'] = repo
    report['pull_requests'].append(pr)
    head = gh('api', f'repos/{repo}/branches/{branch}')['commit']['sha']
    verification = gh('api', f'repos/{repo}/commits/{head}')
    report['promotion_heads'].append({'repository':repo, 'branch':branch, 'sha':head,
        'tree':verification['commit']['tree']['sha'],
        'verified':verification['commit']['verification']['verified'],
        'reason':verification['commit']['verification']['reason']})
    current = gh('run','list','--repo',repo,'--commit',head,'--limit','20','--json','databaseId,attempt,event')
    for run in current:
        if run['event'] == 'push':
            runs.append((repo, run['databaseId'], run['attempt']))
for repo, run_id, attempt in dict.fromkeys(runs):
    data = gh('run','view',str(run_id),'--repo',repo,'--attempt',str(attempt),'--json',
              'databaseId,attempt,event,headSha,headBranch,status,conclusion,jobs,url,createdAt,updatedAt,workflowName')
    data['repository'] = repo
    data['requested_attempt'] = attempt
    data['executed_step_count'] = sum(step['status'] == 'completed' and step['conclusion'] != 'skipped'
                                      for job in data['jobs'] for step in job['steps'])
    report['runs'].append(data)
target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([{'repo':r['repository'],'run':r['databaseId'],'attempt':r['requested_attempt'],
                  'status':r['status'],'conclusion':r['conclusion']} for r in report['runs']]))
