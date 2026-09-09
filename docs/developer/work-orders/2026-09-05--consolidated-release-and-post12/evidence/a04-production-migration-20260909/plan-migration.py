"""Read exact eligible owned bindings and server state; emit no connection material."""
import base64,hashlib,json,shlex,subprocess
from datetime import datetime,timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat

out=Path(__file__).resolve().parent
owned={'64a9c9b73d01eedf96a7377df0b1c1c49d023546217184671b57cdd56750943b','6c6320a20d86cc49c47e95cefa95d2ecfa3ef24a3816496458ee2f68cf46a250'}
def remote(host,code,python='python3'):
 result=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',host,python+' -c '+shlex.quote(code)],capture_output=True,text=True,timeout=90)
 if result.returncode:raise RuntimeError('remote_failed_'+host+'_'+hashlib.sha256(result.stderr.encode()).hexdigest())
 return json.loads(result.stdout)
brain=r'''
import datetime,hashlib,json,os,pathlib,subprocess,sys
pid=subprocess.check_output(['systemctl','show','portal-api','-p','MainPID','--value'],text=True).strip()
for item in pathlib.Path('/proc/'+pid+'/environ').read_bytes().split(b'\0'):
 if b'=' in item:
  key,value=item.split(b'=',1);os.environ[key.decode()]=value.decode()
os.chdir('/root/portal_bot');sys.path.insert(0,'/root/portal_bot')
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
from db import SessionLocal
from sqlalchemy import text
from models import Account,AccountDevice,Awg2LabMaterial,Awg31LabMaterial,User
from awg2_lab_service import _decrypt_endpoint as decrypt2
from awg31_lab_service import _decrypt_endpoint as decrypt31
from network_rollout import load_network_rollout_config
now=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
records=[];policies={}
with SessionLocal() as session:
 session.execute(text('SET TRANSACTION READ ONLY'))
 policy=load_network_rollout_config(session=session)
 for profile,model,decrypt in [('awg2_lab',Awg2LabMaterial,decrypt2),('awg31_lab',Awg31LabMaterial,decrypt31)]:
  config=policy[profile];policies[profile]={k:config.get(k) for k in ('material_max_age_hours','generation','endpoint_revision','server_record_id','expires_at')}
  assert not config.get('allowlist_install_ids') and not config.get('allowlist_tg_ids')
  for row in session.query(model).filter_by(is_active=True,state='ready').all():
   user=session.get(User,row.tg_id)
   if not(user and user.is_active and user.expiry_at and user.expiry_at>now and user.account_id):continue
   account=session.get(Account,str(user.account_id));device=session.query(AccountDevice).filter_by(account_id=str(user.account_id),install_id=row.install_id).first()
   if not(account and account.status=='active' and device and device.state=='active' and device.revoked_at is None):continue
   records.append({'profile':profile,'tg_id':row.tg_id,'install_id':row.install_id,'install_sha256':hashlib.sha256(row.install_id.encode()).hexdigest(),'generation':row.generation,'endpoint_revision':row.endpoint_revision,'server_record_id':row.server_record_id,'node_code':row.node_code,'endpoint':decrypt(row.endpoint_ciphertext),'provisioned_age_hours':round((now-row.provisioned_at).total_seconds()/3600,2)})
 session.rollback()
print(json.dumps({'records':records,'policies':policies}))
'''
server=r'''
import hashlib,json,pathlib,subprocess
output={}
for interface in ('pokrovawg2','pokrovawg31'):
 path=pathlib.Path('/etc/amnezia/amneziawg')/(interface+'.conf');raw=path.read_bytes()
 live=subprocess.check_output(['/usr/local/bin/awg','showconf',interface],text=True)
 public=subprocess.check_output(['/usr/local/bin/awg','show',interface,'public-key'],text=True).strip()
 peers=subprocess.check_output(['/usr/local/bin/awg','show',interface,'peers'],text=True).split()
 allowed=subprocess.check_output(['/usr/local/bin/awg','show',interface,'allowed-ips'],text=True)
 state=subprocess.check_output(['systemctl','is-active','pokrov-awg-lab@'+interface],text=True).strip()
 output[interface]={'persisted':raw.decode(),'persisted_sha256':hashlib.sha256(raw).hexdigest(),'live':live,'public':public,'peers':peers,'allowed':allowed,'service_state':state}
print(json.dumps(output))
'''
def parse(raw):
 sections=[]
 for line in raw.splitlines():
  line=line.strip()
  if line.startswith('['):sections.append({'section':line})
  elif '=' in line and sections:
   k,v=line.split('=',1);sections[-1][k.strip()]=v.strip()
 return sections
def pub(private):
 raw=X25519PrivateKey.from_private_bytes(base64.b64decode(private)).public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
 return base64.b64encode(raw).decode()
if __name__ == "__main__":
 data=remote('pokrov-brain',brain,'/root/portal_bot/venv/bin/python');servers=remote('pokrov-de',server)
 assert len(data['records'])==4 and {r['install_sha256'] for r in data['records']}==owned
 checks=[]
 for row in data['records']:
  assert row['node_code']=='de'
  interface='pokrovawg2' if row['profile']=='awg2_lab' else 'pokrovawg31';live=servers[interface];parts=parse(live['persisted'])
  endpoint=row['endpoint'];server_peer=endpoint['peers'][0];client_public=pub(endpoint['private_key'])
  checks.append({'profile':row['profile'],'install_sha256':row['install_sha256'],'server_record_id':row['server_record_id'],'generation':row['generation'],'endpoint_revision':row['endpoint_revision'],'material_age_hours':row['provisioned_age_hours'],'interface':interface,'service_active':live['service_state']=='active','persisted_config_sha256':live['persisted_sha256'],'server_public_key_sha256':hashlib.sha256(base64.b64decode(live['public'])).hexdigest(),'server_key_matches_material':server_peer['public_key']==live['public'],'old_peer_live':client_public in live['peers'],'old_peer_persisted':any(p.get('PublicKey')==client_public for p in parts),'live_peer_count':len(live['peers']),'saved_peer_count':sum(p['section']=='[Peer]' for p in parts),'all_saved_peers_live':{p.get('PublicKey') for p in parts if p['section']=='[Peer]'}==set(live['peers'])})
 report={'checked_at':datetime.now(timezone.utc).isoformat(),'mode':'READ_ONLY_MIGRATION_PLAN','targets':checks,'policies':data['policies'],'public_allowlists_empty':True,'keys_generated':False,'raw_connection_material_retained':False,'status':'PASS' if all(c['service_active'] and c['server_key_matches_material'] and c['old_peer_live'] and c['old_peer_persisted'] and c['all_saved_peers_live'] for c in checks) else 'BLOCKED_ALIGNMENT'}
 target=out/'migration-plan.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
