"""Install a source-pinned peer-removal command and a dedicated forced-command SSH key."""
import base64,hashlib,importlib.util,json,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
out=Path(__file__).resolve().parent
receipt=out/'worker-access-prepared.json';assert not receipt.exists()
source=Path('E:/r12-integrated-platform-20260909/portal_bot/awg_peer_remove.py').read_bytes()
def run(host,code,payload=None,python='python3'):
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',host,python+' -c '+shlex.quote(code)],input=json.dumps(payload) if payload is not None else '',capture_output=True,text=True,timeout=90)
 if r.returncode:raise RuntimeError('remote_failure_'+host+'_'+hashlib.sha256(r.stderr.encode()).hexdigest())
 return json.loads(r.stdout)
keygen=r'''
import hashlib,json,pathlib,subprocess
p=pathlib.Path('/root/.ssh/pokrov-awg-peer-worker-20260909');assert not p.exists() and not p.with_suffix('.pub').exists()
subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-C','pokrov-awg-peer-worker-20260909','-f',str(p)],check=True,capture_output=True)
assert p.stat().st_mode&0o777==0o600
public=pathlib.Path(str(p)+'.pub').read_text().strip()
print(json.dumps({'key_path':str(p),'public':public,'private_exported':False}))
'''
key=run('pokrov-brain',keygen)
install=r'''
import base64,hashlib,json,os,pathlib,sys
p=json.load(sys.stdin);helper=base64.b64decode(p['helper']);assert hashlib.sha256(helper).hexdigest()==p['helper_sha256']
root=pathlib.Path('/usr/local/lib/pokrov');root.mkdir(parents=True,exist_ok=True)
target=root/'awg_peer_remove.py';assert not target.exists()
with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as handle:handle.write(helper)
public=p['public'];assert public.startswith('ssh-ed25519 ') and '\n' not in public
auth=pathlib.Path('/root/.ssh/authorized_keys');old=auth.read_bytes()
assert b'pokrov-awg-peer-worker-20260909' not in old
backup=pathlib.Path('/root/backups/r12-awg-migration-20260909/authorized_keys.before');assert not backup.exists()
with os.fdopen(os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as handle:handle.write(old)
line='restrict,from="82.21.114.104",command="/usr/bin/python3 /usr/local/lib/pokrov/awg_peer_remove.py" '+public+'\n'
temp=auth.with_name('authorized_keys.r12-next');assert not temp.exists()
with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as handle:handle.write(old+(b'' if old.endswith(b'\n') else b'\n')+line.encode())
os.replace(temp,auth)
host_public=pathlib.Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().strip()
print(json.dumps({'helper_sha256':hashlib.sha256(helper).hexdigest(),'authorized_keys_previous_bytes_preserved':auth.read_bytes().startswith(old),'authorized_keys_backup_sha256':hashlib.sha256(old).hexdigest(),'host_public':host_public,'forced_command':True,'source_ip_restricted':True}))
'''
server=run('pokrov-de',install,{'helper':base64.b64encode(source).decode(),'helper_sha256':hashlib.sha256(source).hexdigest(),'public':key['public']})
# Pin the host key fetched over the already trusted DE SSH session; no TOFU.
configure=r'''
import base64,hashlib,json,os,pathlib,sys
p=json.load(sys.stdin);host_key=p['host_public'].split();assert host_key[0]=='ssh-ed25519'
known=pathlib.Path('/root/.ssh/pokrov-awg-peer-worker-known-hosts');assert not known.exists()
with os.fdopen(os.open(known,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as handle:handle.write('46.247.109.132 '+host_key[0]+' '+host_key[1]+'\n')
root=pathlib.Path('/root/portal_bot/runtime-config');root.mkdir(mode=0o700,exist_ok=True)
target=root/'awg-peer-targets.json';assert not target.exists()
targets=[]
for row in p['targets']:
 targets.append({'profile':row['profile'],'node_code':'de','server_record_id':row['server_record_id'],'host':'46.247.109.132','port':22,'username':'root','key_file':'/root/.ssh/pokrov-awg-peer-worker-20260909','known_hosts':str(known),'interface':row['interface'],'server_public_key_sha256':row['server_public_key_sha256']})
with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as handle:json.dump(targets,handle)
print(json.dumps({'target_file':str(target),'target_file_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'target_count':len(targets),'known_host_key_sha256':hashlib.sha256(base64.b64decode(host_key[1])).hexdigest(),'worker_enabled':False,'private_key_exported':False}))
'''
baseline=json.loads((out/'migration-plan.json').read_text());targets=[]
for profile in ('awg2_lab','awg31_lab'):targets.append(next(r for r in baseline['targets'] if r['profile']==profile))
config=run('pokrov-brain',configure,{'host_public':server.pop('host_public'),'targets':targets})
report={'checked_at':datetime.now(timezone.utc).isoformat(),'source_revision':'7d37005e4260995ab44ec3adb14bbffa3d42738b','public_key_sha256':hashlib.sha256(base64.b64decode(key['public'].split()[1])).hexdigest(),'server':server,'config':config,'status':'PREPARED_NOT_ACTIVATED','old_authorized_keys_retained':True}
receipt.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
