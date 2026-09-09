"""Bind deployed worker source and refresh public backend build metadata."""
import hashlib, json, shlex, subprocess
from pathlib import Path

out = Path(__file__).resolve().parent
manifest = json.loads((out / 'merged-payload.json').read_bytes())
code = r'''
import datetime,hashlib,json,os,pathlib,stat,subprocess,sys,tempfile,urllib.request
from dotenv import dotenv_values
manifest=json.load(sys.stdin);timestamps=[]
for item in manifest['files']:
 path=pathlib.Path(item['remote_target'])
 assert str(path).startswith(('/root/portal_bot/','/root/shared/','/root/copy/'))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==item['payload_sha256']
 timestamps.append(path.stat().st_mtime)
units=('portal-api','portal-bot','portal-helpbot','portal-feedbackbot','portal-worker')
def states():
 return {unit:dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID','-p','NRestarts','-p','ActiveState'],text=True).splitlines()) for unit in units}
before_units=states()
path=pathlib.Path('/root/portal_bot/.env');before=path.read_bytes();metadata=path.stat();old=dotenv_values(path)
assert stat.S_IMODE(metadata.st_mode)==0o600 and metadata.st_uid==0
assert old['PORTAL_BUILD_COMMIT']=='876e78da2ee5426a11d5aa74239fcff5efc9fa5d'
new={'PORTAL_BUILD_COMMIT':manifest['source_revision'],'PORTAL_DEPLOYED_AT':datetime.datetime.fromtimestamp(max(timestamps),datetime.timezone.utc).isoformat().replace('+00:00','Z')}
updated=before
for key,value in new.items():
 needle=(key+'='+old[key]).encode()
 assert updated.count(needle)==1
 updated=updated.replace(needle,(key+'='+value).encode())
fd,tmp=tempfile.mkstemp(prefix='.env.r12-subscription-build-',dir=path.parent)
try:
 os.fchmod(fd,0o600);os.fchown(fd,metadata.st_uid,metadata.st_gid)
 with os.fdopen(fd,'wb') as handle: handle.write(updated);handle.flush();os.fsync(handle.fileno())
 assert path.read_bytes()==before,'concurrent dotenv change'
 os.replace(tmp,path)
 directory=os.open(str(path.parent),os.O_DIRECTORY)
 try: os.fsync(directory)
 finally: os.close(directory)
finally:
 if os.path.exists(tmp):os.unlink(tmp)
assert {k:v for k,v in dotenv_values(path).items() if k not in new}=={k:v for k,v in old.items() if k not in new}
subprocess.run(['systemctl','restart','portal-api'],check=True)
import time
time.sleep(12)
after_units=states()
assert all(v['ActiveState']=='active' and v['NRestarts']=='0' for v in after_units.values())
assert all(before_units[u]['MainPID']==after_units[u]['MainPID'] for u in units if u!='portal-api')
with urllib.request.urlopen('https://api.pokrov.space/api/health',timeout=15) as response:assert response.status==200
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin','status':'PASS','source_revision':manifest['source_revision'],'all_204_payload_hashes_match':True,'public_build_metadata':new,'other_dotenv_values_unchanged':True,'before_services':before_units,'after_services':after_units,'restarted_units':['portal-api'],'health':'PASS','credentials_exported':False}))
'''
target=out/'build-identity-updated.json'
assert not target.exists()
result=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],input=json.dumps(manifest),capture_output=True,text=True,timeout=100)
assert result.returncode==0, {'exit':result.returncode,'stderr_sha256':hashlib.sha256(result.stderr.encode()).hexdigest()}
report=json.loads(result.stdout)
target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
