"""Retain the actual statuses for this source-binding slice."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

base = Path(__file__).resolve().parent
target = base / sys.argv[1]
assert not target.exists()
def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args]))
report = {'captured_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'sources': {'client': '5fdfc8dfd231265ea1d6c555d1ec56769c359b3b',
                      'platform': '0f6745dbe33f267d61eb0effb28afcd638e70364',
                      'core': 'c7a11f7d2fd974726095ad7aa0619c055273dd15'},
          'runs': []}
for repo, run_id in [('Kiwunaka/POKROV-app', 34304294175),
                     ('Kiwunaka/POKROV-app', 34304280737),
                     ('Kiwunaka/POKROV-app', 34304277115),
                     ('Kiwunaka/portal', 34303104311),
                     ('Kiwunaka/portal', 34303104317)]:
    run = gh('run','view',str(run_id),'--repo',repo,'--json',
             'databaseId,event,headSha,headBranch,status,conclusion,jobs,url,createdAt,updatedAt')
    run['repository'] = repo
    report['runs'].append(run)
report['pull_requests'] = []
for repo, number in [('Kiwunaka/POKROV-app',94),('Kiwunaka/portal',242),('Kiwunaka/pokrov-core',8)]:
    data = gh('api',f'repos/{repo}/pulls/{number}')
    report['pull_requests'].append({'repository':repo,'number':number,'head':data['head']['sha'],
                                   'base':data['base']['sha'],'state':data['state'],'draft':data['draft'],
                                   'mergeable':data['mergeable'],'mergeable_state':data['mergeable_state']})
report['release_pass'] = False
target.write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps([{'run':r['databaseId'],'status':r['status'],'conclusion':r['conclusion']} for r in report['runs']]))
