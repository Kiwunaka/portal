"""Migrate the four preflighted owned AWG bindings, retaining old peers and rows."""
import base64,copy,hashlib,importlib.util,ipaddress,json,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption

out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('migration_plan',out/'plan-migration.py');plan=importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)
baseline=json.loads((out/'migration-plan.json').read_text());assert baseline['status']=='PASS'
receipt=out/'migration-applied-v2.json';assert not receipt.exists()
data=plan.remote('pokrov-brain',plan.brain,'/root/portal_bot/venv/bin/python');servers=plan.remote('pokrov-de',plan.server)
assert len(data['records'])==4 and {r['install_sha256'] for r in data['records']}==plan.owned
report={'started_at':datetime.now(timezone.utc).isoformat(),'mode':'APPLY_OWNED_KEYS_ONLY','server_changes':[],'material_changes':[],'public_allowlists_changed':False,'entitlements_changed':False,'old_peers_removed':False,'private_keys_exported_to_artifacts':False,'status':'IN_PROGRESS'}
def save():receipt.write_text(json.dumps(report,indent=2)+'\n')
def invoke(host,code,payload,python='python3'):
 result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',host,python+' -c '+shlex.quote(code)],input=json.dumps(payload),text=True,capture_output=True,timeout=120)
 if result.returncode:raise RuntimeError('remote_failed_'+host+'_'+hashlib.sha256(result.stderr.encode()).hexdigest())
 return json.loads(result.stdout)
add_peers=r'''
import base64,hashlib,ipaddress,json,os,pathlib,subprocess,sys
p=json.load(sys.stdin);interface=p['interface'];assert interface in ('pokrovawg2','pokrovawg31')
root=pathlib.Path('/etc/amnezia/amneziawg');path=root/(interface+'.conf');raw=path.read_bytes()
assert hashlib.sha256(raw).hexdigest()==p['expected_config_sha256']
public=subprocess.check_output(['/usr/local/bin/awg','show',interface,'public-key'],text=True).strip()
assert hashlib.sha256(base64.b64decode(public)).hexdigest()==p['expected_server_key_sha256']
old=set(subprocess.check_output(['/usr/local/bin/awg','show',interface,'peers'],text=True).split());assert len(old)==1
backup=pathlib.Path('/root/backups/r12-awg-migration-20260909');backup.mkdir(mode=0o700,parents=True,exist_ok=True)
backup_file=backup/(interface+'.before.conf');assert not backup_file.exists()
with open(backup_file,'xb') as handle:handle.write(raw)
os.chmod(backup_file,0o600)
added=b'';new=set()
for peer in p['peers']:
 key=peer['public'];address=peer['address'];assert len(base64.b64decode(key,validate=True))==32 and key not in old|new
 assert ipaddress.ip_interface(address).network.prefixlen==32
 new.add(key);added+=('\n[Peer]\nPublicKey = '+key+'\nAllowedIPs = '+address+'\n').encode()
temp=path.with_name(interface+'.conf.r12-next');assert not temp.exists()
with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as handle:handle.write(raw+added);handle.flush();os.fsync(handle.fileno())
os.chmod(temp,0o600);os.replace(temp,path)
for peer in p['peers']:subprocess.run(['/usr/local/bin/awg','set',interface,'peer',peer['public'],'allowed-ips',peer['address']],check=True,capture_output=True)
live=set(subprocess.check_output(['/usr/local/bin/awg','show',interface,'peers'],text=True).split());assert live==old|new
assert path.read_bytes()==raw+added
print(json.dumps({'interface':interface,'backup_path':str(backup_file),'backup_sha256':hashlib.sha256(raw).hexdigest(),'new_config_sha256':hashlib.sha256(raw+added).hexdigest(),'old_peer_retained':True,'new_peers_added':len(new),'live_peer_count':len(live),'saved_config_preserves_old_bytes':True,'status':'PASS'}))
'''
put_material=r'''
import base64,datetime,hashlib,hmac,json,os,pathlib,subprocess,sys,time,urllib.error,urllib.parse,urllib.request,uuid
p=json.load(sys.stdin);profile=p.pop('profile');expected=p.pop('expected_public_sha256');install_sha=p.pop('install_sha256')
assert profile in ('awg2_lab','awg31_lab') and hashlib.sha256(p['install_id'].encode()).hexdigest()==install_sha
pid=subprocess.check_output(['systemctl','show','portal-api','-p','MainPID','--value'],text=True).strip()
for item in pathlib.Path('/proc/'+pid+'/environ').read_bytes().split(b'\0'):
 if b'=' in item:
  k,v=item.split(b'=',1);os.environ[k.decode()]=v.decode()
os.chdir('/root/portal_bot');sys.path.insert(0,'/root/portal_bot')
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
from db import SessionLocal
from models import Account,AccountDevice,Awg2LabMaterial,Awg31LabMaterial,User
from awg2_lab_service import _decrypt_endpoint as decrypt2
from awg31_lab_service import _decrypt_endpoint as decrypt31
from awg_lab_key_binding import _client_public_key
from sqlalchemy import text
model,decrypt=(Awg2LabMaterial,decrypt2) if profile=='awg2_lab' else (Awg31LabMaterial,decrypt31)
now=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
with SessionLocal() as session:
 session.execute(text('SET TRANSACTION READ ONLY'))
 user=session.get(User,p['tg_id']);assert user and user.is_active and user.expiry_at>now and user.account_id
 account=session.get(Account,str(user.account_id));device=session.query(AccountDevice).filter_by(account_id=str(user.account_id),install_id=p['install_id']).one()
 assert account.status=='active' and device.state=='active' and device.revoked_at is None
 previous=session.query(model).filter_by(tg_id=p['tg_id'],install_id=p['install_id']).all();before_ids={r.id for r in previous}
 session.rollback()
params={'auth_date':str(int(time.time())),'user':json.dumps({'id':int(os.environ['ADMIN_ID']),'first_name':'POKROV'},separators=(',',':'))}
check='\n'.join(f'{k}={v}' for k,v in sorted(params.items()));secret=hmac.new(b'WebAppData',os.environ['BOT_TOKEN'].encode(),hashlib.sha256).digest()
params['hash']=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest();init=urllib.parse.urlencode(params)
def request(method,path,body,headers=None):
 req=urllib.request.Request('https://api.pokrov.space'+path,data=json.dumps(body).encode(),method=method,headers={'X-Telegram-Init-Data':init,'Content-Type':'application/json',**(headers or {})})
 try:
  with urllib.request.urlopen(req,timeout=45) as response:return json.load(response)
 except urllib.error.HTTPError as error:raise RuntimeError('admin_http_'+str(error.code)) from None
action=profile+'_material.replace';target=profile+'_material'
prepared=request('POST','/api/admin/action-intents',{'action':action,'target':{'type':target,'id':str(p['tg_id'])},'payload':p})
challenge=prepared['confirmation_challenge'];intent=prepared['intent_id'];assert challenge and intent
response=request('PUT','/api/admin/client/'+profile.replace('_','-')+'/material',p,{'X-Admin-Intent-Id':intent,'X-Admin-Idempotency-Key':str(uuid.uuid4()),'X-Admin-Confirmation-SHA256':hashlib.sha256(challenge.encode()).hexdigest()})
with SessionLocal() as session:
 session.execute(text('SET TRANSACTION READ ONLY'))
 rows=session.query(model).filter_by(tg_id=p['tg_id'],install_id=p['install_id']).all();ready=[r for r in rows if r.is_active and r.state=='ready'];assert len(ready)==1
 row=ready[0];actual=decrypt(row.endpoint_ciphertext);public=_client_public_key(actual)
 assert hashlib.sha256(public).hexdigest()==expected
 assert actual==p['endpoint'] and before_ids.issubset({r.id for r in rows}) and row.id not in before_ids
 assert all(not r.is_active for r in rows if r.id in before_ids)
 session.rollback()
print(json.dumps({'profile':profile,'install_sha256':install_sha,'new_public_key_sha256':expected,'single_active_material':True,'old_rows_retained':True,'old_rows_inactive':True,'endpoint_readback_equal':True,'guarded_http_replace':True,'intent_id':intent,'status':'PASS'}))
'''
save()
try:
 for profile,interface in [('awg2_lab','pokrovawg2'),('awg31_lab','pokrovawg31')]:
  live=servers[interface];parts=plan.parse(live['persisted']);baseline_row=next(r for r in baseline['targets'] if r['profile']==profile)
  assert live['persisted_sha256']==baseline_row['persisted_config_sha256'] and len(live['peers'])==1
  assert live['service_state']=='active'
  network=ipaddress.ip_interface(parts[0]['Address'].split(',')[0].strip()).network
  used={ipaddress.ip_interface(parts[0]['Address'].split(',')[0].strip()).ip}
  for part in parts[1:]:
   for address in part.get('AllowedIPs','').split(','):
    if address.strip():used.add(ipaddress.ip_interface(address.strip()).ip)
  free=(host for host in network.hosts() if host not in used);rows=sorted((r for r in data['records'] if r['profile']==profile),key=lambda r:r['install_sha256']);pending=[]
  for row in rows:
   assert row['endpoint']['peers'][0]['public_key']==live['public'] and plan.pub(row['endpoint']['private_key']) in live['peers']
   body={key:copy.deepcopy(row[key]) for key in ('tg_id','install_id','generation','endpoint_revision','server_record_id','node_code','endpoint')}
   private=X25519PrivateKey.generate().private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption());private_b64=base64.b64encode(private).decode();public=plan.pub(private_b64)
   body['endpoint']['private_key']=private_b64;body['endpoint']['address']=[str(next(free))+'/32']
   pending.append((body,public,row['install_sha256']))
  result=invoke('pokrov-de',add_peers,{'interface':interface,'expected_config_sha256':live['persisted_sha256'],'expected_server_key_sha256':baseline_row['server_public_key_sha256'],'peers':[{'public':public,'address':body['endpoint']['address'][0]} for body,public,_ in pending]})
  report['server_changes'].append(result);save()
  for body,public,install_sha in pending:
   result=invoke('pokrov-brain',put_material,{**body,'profile':profile,'install_sha256':install_sha,'expected_public_sha256':hashlib.sha256(base64.b64decode(public)).hexdigest()},'/root/portal_bot/venv/bin/python')
   report['material_changes'].append(result);save()
 report['status']='PASS_BOUNDED_KEYS_MIGRATED';report['completed_at']=datetime.now(timezone.utc).isoformat();save()
except Exception as error:
 report['status']='STOPPED_RECONCILIATION_REQUIRED';report['failure_class']=type(error).__name__;report['failure_marker']=str(error) if str(error).startswith('remote_failed_') else 'local_assertion';save();raise SystemExit(json.dumps(report))
print(json.dumps(report,indent=2))
