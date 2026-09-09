"""Read aggregate owned-Brain prerequisites without customer records or secrets."""
from pathlib import Path
import json, shlex, subprocess, textwrap

root = Path(__file__).parent
code = r'''
import datetime,json,pathlib,shutil,subprocess
def run(args):
 r=subprocess.run(args,capture_output=True,text=True,timeout=20)
 if r.returncode:
  print(json.dumps({'command_failed':args[0], 'exit_code':r.returncode,
   'psql': 'psql' in args, 'database_missing':'does not exist' in r.stderr,
   'permission_denied':'Permission denied' in r.stderr, 'systemctl':'systemctl' in args,
   'stderr_sha256':__import__('hashlib').sha256(r.stderr.encode()).hexdigest()}))
  raise SystemExit(1)
 return r.stdout.strip()
sql="""SELECT json_build_object('source_bytes',pg_database_size('portal'),
'target_absent',NOT EXISTS(SELECT 1 FROM pg_database WHERE datname='portal_r12_20260909_rehearsal'),
'source_connections',(SELECT count(*) FROM pg_stat_activity WHERE datname='portal'),
'source_lock_waiters',(SELECT count(*) FROM pg_stat_activity WHERE datname='portal' AND wait_event_type='Lock'));"""
db_raw=run(['runuser','-u','postgres','--','psql','--no-psqlrc','--quiet','--tuples-only','--no-align','--set=ON_ERROR_STOP=1','--dbname=postgres','--command',sql])
try:db=json.loads(db_raw)
except ValueError:
 print(json.dumps({'aggregate_query_output':db_raw}));raise SystemExit(1)
backup=pathlib.Path('/root/backups/r12-20260909')
units=['portal-api','portal-bot','portal-helpbot','portal-feedbackbot','portal-worker']
services={unit:run(['systemctl','show',unit,'-p','ActiveState','-p','NRestarts','-p','MainPID']) for unit in units}
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'database':db,
'root_free_bytes':shutil.disk_usage('/root').free,'backup_directory_absent':not backup.exists(),
'required_tools':{n:shutil.which(n) is not None for n in ['pg_dump','pg_restore','openssl','psql','timeout','setsid']},
'services':services,'mode':'READ_ONLY'}))
'''
code = 'import json,traceback\ntry:\n' + textwrap.indent(code, ' ') + '\nexcept Exception as error:\n print(json.dumps({"error_type":type(error).__name__,"frames":[{"function":f.name,"line":f.lineno} for f in traceback.extract_tb(error.__traceback__)]}))\n raise SystemExit(1)\n'
r = subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe', '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10', 'pokrov-brain',
    'python3 -c ' + shlex.quote(code)], capture_output=True, text=True, timeout=90)
if r.returncode:
    try: safe=json.loads(r.stdout)
    except Exception: safe={'remote_stdout_json':False,'stderr_sha256':__import__('hashlib').sha256(r.stderr.encode()).hexdigest()}
    print(json.dumps({'result':'READINESS_FAILED','exit_code':r.returncode,'safe':safe}))
    raise SystemExit(1)
report = json.loads(r.stdout)
(root/'readiness-before.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
print(json.dumps(report))
