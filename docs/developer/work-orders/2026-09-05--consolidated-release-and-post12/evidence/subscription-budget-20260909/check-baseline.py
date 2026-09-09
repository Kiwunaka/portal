import datetime,hashlib,json,subprocess,shlex
from pathlib import Path
out=Path(__file__).resolve().parent
repo='Kiwunaka/portal';sha='d9b25839e4c9e1b816091af6701b3723d75aa8c7'
runs=[]
for run in [34320997265,34320997295,34322293079,34322293030]:
 data=json.loads(subprocess.check_output(['gh','run','view',str(run),'--repo',repo,'--json','databaseId,headSha,event,status,conclusion,url,workflowName,jobs']))
 assert data['status']=='completed' and data['conclusion']=='success'
 runs.append(data)
assert all(r['headSha']==sha for r in runs[2:])
(out/'ci-verified.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_revision':sha,'runs':runs,'status':'PASS'},indent=2)+'\n',encoding='utf-8')
base=json.loads(Path('E:/r12-internal-vision-integration-20260909/merged-payload.json').read_bytes())
code=r'''
import datetime,hashlib,json,pathlib,subprocess,sys
from dotenv import dotenv_values
m=json.load(sys.stdin);diff=[]
for f in m['files']:
 p=pathlib.Path(f['remote_target'])
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=f['payload_sha256']:diff.append(f['source_path'])
commit=dotenv_values('/root/portal_bot/.env').get('PORTAL_BUILD_COMMIT')
units={u:dict(x.split('=',1) for x in subprocess.check_output(['systemctl','show',u,'-p','MainPID','-p','NRestarts','-p','ActiveState'],text=True).splitlines()) for u in ['portal-api','portal-bot','portal-helpbot','portal-feedbackbot','portal-worker']}
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked_files':len(m['files']),'differences':diff,'build_commit':commit,'expected_commit':m['source_revision'],'units':units,'status':'PASS' if not diff and commit==m['source_revision'] and all(x['ActiveState']=='active' for x in units.values()) else 'FAIL'}
print(json.dumps(r))
'''
r=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],input=json.dumps(base),capture_output=True,text=True,timeout=50)
assert r.returncode==0,{'exit':r.returncode,'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()}
r=json.loads(r.stdout);(out/'baseline-before-deploy.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r));assert r['status']=='PASS'
