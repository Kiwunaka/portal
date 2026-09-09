"""Initialize the absent dedicated key on Brain; return presence only."""
import hashlib,json,shlex,subprocess
from pathlib import Path

code=r'''
import datetime,json,os,pathlib,secrets,stat,subprocess,sys,tempfile
from dotenv import dotenv_values
key='COMMERCIAL_OFFER_HMAC_SECRET';path=pathlib.Path('/root/portal_bot/.env')
pid=subprocess.check_output(['systemctl','show','portal-api','-p','MainPID','--value'],text=True).strip()
assert pid.isdigit() and int(pid)>0
for item in pathlib.Path('/proc/'+pid+'/environ').read_bytes().split(b'\0'):
 if b'=' in item:
  k,v=item.split(b'=',1);os.environ[k.decode()]=v.decode()
assert not os.environ.get(key), 'process key already present'
assert key not in dotenv_values(path), 'dotenv key already declared'
before=path.read_bytes();metadata=path.stat()
assert stat.S_IMODE(metadata.st_mode)==0o600 and metadata.st_uid==0
os.chdir('/root/portal_bot');sys.path.insert(0,'/root/portal_bot')
from db import SessionLocal
from sqlalchemy import text
with SessionLocal() as session:
 session.execute(text('SET TRANSACTION READ ONLY'))
 session.execute(text("SET LOCAL statement_timeout = '5000ms'"))
 assert session.execute(text("SELECT count(*) FROM commercial_reservations WHERE status='held' AND hold_expires_at > CURRENT_TIMESTAMP")).scalar_one()==0
 session.rollback()
newline=b'\r\n' if b'\r\n' in before else b'\n'
prefix=before if before.endswith(b'\n') else before+newline
updated=prefix+key.encode()+b'='+secrets.token_urlsafe(48).encode()+newline
fd,tmp=tempfile.mkstemp(prefix='.env.r12-',dir=path.parent)
try:
 os.fchmod(fd,0o600);os.fchown(fd,metadata.st_uid,metadata.st_gid)
 with os.fdopen(fd,'wb') as handle:
  handle.write(updated);handle.flush();os.fsync(handle.fileno())
 assert path.read_bytes()==before, 'concurrent dotenv change'
 os.replace(tmp,path)
 directory=os.open(str(path.parent),os.O_DIRECTORY)
 try: os.fsync(directory)
 finally: os.close(directory)
finally:
 if os.path.exists(tmp): os.unlink(tmp)
values=dotenv_values(path)
assert len(values[key].encode())>=32 and path.read_bytes().startswith(before)
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'action':'INITIALIZE_ABSENT_DEDICATED_KEY','key_version':'r12-commercial-20260909',
 'dotenv_key_present':True,'dotenv_mode':oct(stat.S_IMODE(path.stat().st_mode)),
 'previous_dotenv_bytes_preserved':True,'prior_unexpired_holds':0,
 'services_restarted':False,'secret_exported':False,'api_pid_before':int(pid)}))
'''
out=Path(__file__).resolve().parent/'commercial-key-initialized.json';assert not out.exists()
r=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,timeout=90)
assert r.returncode==0, {'exit':r.returncode,'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()}
report=json.loads(r.stdout);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
