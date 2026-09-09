"""Retire ineligible lab material and explicitly decommission migrated shared peers."""
import hashlib,json,shlex,subprocess
from pathlib import Path
out=Path(__file__).resolve().parent
assert json.loads((out/'migrated-core-interop.json').read_text())['status']=='PASS_BOUNDED_FOUR_MIGRATED_KEYS'
target=out/'shared-keys-retired.json';assert not target.exists()
code=r'''
import base64,collections,datetime,hashlib,json,os,pathlib,subprocess,sys
pid=subprocess.check_output(['systemctl','show','portal-worker','-p','MainPID','--value'],text=True).strip()
for item in pathlib.Path('/proc/'+pid+'/environ').read_bytes().split(b'\0'):
 if b'=' in item:
  k,v=item.split(b'=',1);os.environ[k.decode()]=v.decode()
os.chdir('/root/portal_bot');sys.path.insert(0,'/root/portal_bot')
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
assert not os.environ.get('AWG_LAB_PEER_TARGETS_FILE')
os.environ['AWG_LAB_PEER_TARGETS_FILE']='/root/portal_bot/runtime-config/awg-peer-targets.json'
from db import SessionLocal
from awg_lab_peer_worker import PROFILES,configured_targets,reconcile_awg_peers,remove_remote_peers,_retire_binding
from awg_lab_key_binding import _client_public_key,lock_awg_device_key
from network_rollout import load_network_rollout_config
from sqlalchemy import text
targets=configured_targets();now=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
report={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin','current_target_pass':None,'legacy_rows_retired':0,'shared_peer_removals':[],'status':'IN_PROGRESS'}
# Retain progress on Brain even if the SSH session ends after a committed denial.
journal=pathlib.Path('/root/portal_bot/runtime-config/shared-retirement-20260909.json');assert not journal.exists()
def save():
 fd=os.open(journal,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as handle:json.dump(report,handle)
save()
try:
 result=reconcile_awg_peers(SessionLocal,targets=targets,now=now);report['current_target_pass']=result;save();assert result['failed_targets']==0
 for target in targets:
  model,service=PROFILES[target['profile']]
  with SessionLocal() as session:
   config=load_network_rollout_config(session=session);normalize=service.normalize_awg2_lab_config if target['profile']=='awg2_lab' else service.normalize_awg31_lab_config
   policy=normalize(config[target['profile']])
   bindings=session.query(model.tg_id,model.install_id,model.server_record_id).filter_by(node_code='de').distinct().order_by(model.tg_id,model.install_id,model.server_record_id).all()
   for tg_id,install_id,record in bindings:
    if record!=target['server_record_id']:
     report['legacy_rows_retired']+=_retire_binding(session,model=model,tg_id=tg_id,install_id=install_id,target={**target,'server_record_id':record},policy=policy,now=now)
   session.commit()
  save()
  with SessionLocal() as session:
   groups=collections.defaultdict(list)
   for row in session.query(model).order_by(model.id):groups[_client_public_key(service._decrypt_endpoint(row.endpoint_ciphertext))].append(row)
   selected=[]
   for public,rows in groups.items():
    if len({(r.tg_id,r.install_id) for r in rows})<=1:continue
    if not any(r.node_code=='de' and r.server_record_id==target['server_record_id'] for r in rows):continue
    lock_awg_device_key(session,model=model,public=public)
    # Re-read after key lock; issuance already forbids reusing a historically shared key.
    rows=[r for r in session.query(model).populate_existing().order_by(model.id) if _client_public_key(service._decrypt_endpoint(r.endpoint_ciphertext))==public]
    assert not any(r.is_active and r.state=='ready' for r in rows)
    assert any(hashlib.sha256(base64.b64decode(service._decrypt_endpoint(r.endpoint_ciphertext)['peers'][0]['public_key'])).hexdigest()==target['server_public_key_sha256'] for r in rows)
    for row in rows:
     row.is_active=False;row.state='revoked';row.revoked_at=row.revoked_at or now;row.updated_at=now
    selected.append(public)
   assert len(selected)==1
   session.commit()
  removed=remove_remote_peers(target,[base64.b64encode(key).decode() for key in selected])
  assert removed['requested']==removed['disk_removed']==removed['live_removed']==1
  repeated=remove_remote_peers(target,[base64.b64encode(key).decode() for key in selected]);assert repeated=={'requested':1,'disk_removed':0,'live_removed':0}
  report['shared_peer_removals'].append({'profile':target['profile'],'all_shared_rows_revoked':True,'history_preserved':True,'shared_public_key_sha256':hashlib.sha256(selected[0]).hexdigest(),**removed,'idempotent_retry':repeated});save()
 with SessionLocal() as session:
  session.execute(text('SET TRANSACTION READ ONLY'));counts={}
  for target in targets:
   model,service=PROFILES[target['profile']];ready=session.query(model).filter_by(is_active=True,state='ready').all();assert len(ready)==2
   keys=[_client_public_key(service._decrypt_endpoint(r.endpoint_ciphertext)) for r in ready];assert len(set(keys))==2
   counts[target['profile']]={'active_ready':len(ready),'unique_active_keys':len(set(keys))}
  session.rollback()
 report['remaining']=counts;report['status']='PASS_SHARED_PEERS_DECOMMISSIONED';save()
except Exception as error:
 report['status']='STOPPED_RECONCILIATION_REQUIRED';report['failure_class']=type(error).__name__;save()
print(json.dumps(report))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,timeout=120)
assert r.returncode==0,hashlib.sha256(r.stderr.encode()).hexdigest()
report=json.loads(r.stdout);target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['status']=='PASS_SHARED_PEERS_DECOMMISSIONED'
