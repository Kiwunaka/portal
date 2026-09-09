"""Isolated ASGI/PostgreSQL lifecycle. Runtime payloads only use the SSH pipe."""
import datetime,hashlib,hmac,json,logging,os,secrets,subprocess,sys,time,traceback,uuid
from pathlib import Path
from urllib.parse import urlencode
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url

logging.disable(logging.CRITICAL)
root=Path(__file__).parent;source=root/'source'
sys.path.insert(0,str(source/'portal_bot'));os.chdir(source)
initial=json.loads(sys.stdin.readline())
profile=initial['profile'];assert profile in ('awg2','awg31')
DATABASE='portal_r12_a04_http_keys_'+profile+'_20260908'
result_path=root/('http-'+profile+'-result.json')
assert not result_path.exists(),'Preserve previous result'
report={'profile':profile,'database':DATABASE,'result':'RUNNING','http':[],'raw_material_returned_to_evidence':False,'source_files_checked':0}
phase='init'
def save():result_path.write_bytes((json.dumps(report,indent=2)+'\n').encode())
def emit(payload):print('__A04__'+json.dumps(payload,separators=(',',':')),flush=True)
def status(response,label):
 report['http'].append({'label':label,'status':response.status_code});save()
 return response
def main():
 global phase
 manifest=json.loads((root/'source-manifest.json').read_text())
 for item in manifest['files']:
  raw=(source/item['path']).read_bytes()
  assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
 report['source_files_checked']=len(manifest['files']);report['source_parent']=manifest['source_parent']
 dsn=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL']).set(database=DATABASE)
 check=subprocess.run(['runuser','-u','postgres','--','psql','-At','-d','postgres','-c',"SELECT count(*) FROM pg_database WHERE datname='"+DATABASE+"'"],capture_output=True,text=True)
 assert check.returncode==0 and check.stdout.strip()=='0','Refuse existing fixture database'
 created=subprocess.run(['runuser','-u','postgres','--','createdb','--owner=r12_linux_app',DATABASE],capture_output=True)
 assert created.returncode==0,'Fixture database creation failed'
 os.environ['DATABASE_URL']=dsn.render_as_string(hide_password=False)
 for name in ['WEBAPP_SESSION_SECRET','AWG2_LAB_MATERIAL_SECRET','AWG31_LAB_MATERIAL_SECRET','BOT_TOKEN']:
  os.environ[name]=secrets.token_hex(32)
 os.environ.update(ADMIN_ID='9999',ADMIN_IDS='9999',PUBLIC_CHANNEL='fixture')
 phase='import_api'
 import api,models,auth_session_service as auth
 import awg2_lab_service as awg2,awg31_lab_service as awg31
 from fastapi.testclient import TestClient
 from network_rollout import normalized_network_rollout_config
 client=TestClient(api.app)
 service=awg2 if profile=='awg2' else awg31
 model=models.Awg2LabMaterial if profile=='awg2' else models.Awg31LabMaterial
 revision=getattr(service,profile.upper()+'_ENDPOINT_REVISION')
 now=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
 device_ids={};accounts={};sessions={};tg_ids={'a':930001,'b':930002}
 phase='seed'
 with api.SessionLocal() as s:
  for label in ('a','b'):
   account_id=str(uuid.uuid4());accounts[label]=account_id
   s.add(models.Account(id=account_id,status='active',created_source='fixture',created_at=now,updated_at=now))
   for suffix in ('','-actor'):
    device_id=str(uuid.uuid4());device_ids[label+suffix]=device_id
    s.add(models.AccountDevice(id=device_id,account_id=account_id,install_id='a04-http-'+label+suffix,label='Isolated lab fixture',platform='windows',state='active',credential_version=1,first_seen_at=now,last_seen_at=now,created_at=now,updated_at=now))
   user=models.User(tg_id=tg_ids[label],account_id=account_id,uuid=str(uuid.uuid4()),email='a04-http-'+label+'@example.test',sub_type='PAID',is_active=True,app_install_id='a04-http-'+label,app_platform='windows',expiry_at=now+datetime.timedelta(days=1),created_at=now)
   s.add(user);s.flush()
   for suffix in ('','-actor'):
    sessions[label+suffix]=auth.issue_device_session(s,user=user,install_id='a04-http-'+label+suffix,now=now,fresh_auth_at=now)
  config=normalized_network_rollout_config({'version':'a04-http-v1'})
  config['cohort_overrides']={'isolated-a04-http':{'transport_profile':profile+'_lab','install_ids':['a04-http-a','a04-http-b'],'tg_ids':[],'linked_tg_ids':[],'platforms':[]}}
  config[profile+'_lab'].update(enabled=True,kill_switch_engaged=False,allowlist_install_ids=['a04-http-a','a04-http-b'],allowlist_tg_ids=[],allowlist_node_codes=['de'],allowed_platforms=['windows'],generation='fixture-v1',server_record_id='fixture-de',server_owner='pokrov',server_state='ready',expires_at=(now+datetime.timedelta(hours=1)).isoformat()+'Z')
  api._set_app_setting_json(s=s,key='network_rollout_config',value=config)
  s.commit()
 def admin_headers():
  params={'auth_date':str(int(time.time())),'query_id':'a04-isolated-http','user':json.dumps({'id':9999,'first_name':'Fixture'},separators=(',',':'))}
  check='\n'.join(f'{k}={v}' for k,v in sorted(params.items()))
  secret=hmac.new(b'WebAppData',os.environ['BOT_TOKEN'].encode(),hashlib.sha256).digest()
  params['hash']=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
  return {'X-Telegram-Init-Data':urlencode(params)}
 def payload(label,key_label):
  return {'tg_id':tg_ids[label],'install_id':'a04-http-'+label,'generation':'fixture-v1','endpoint_revision':revision,'server_record_id':'fixture-de','node_code':'de','endpoint':initial['endpoints'][key_label]}
 path='/api/admin/client/'+('awg2' if profile=='awg2' else 'awg31')+'-lab/material'
 def guarded(label,key_label,*,expect=200,repeat=False):
  body=payload(label,key_label)
  prepared=status(client.post('/api/admin/action-intents',headers=admin_headers(),json={'action':profile+'_lab_material.replace','target':{'type':profile+'_lab_material','id':str(tg_ids[label])},'payload':body}),'prepare_'+label+'_'+key_label)
  assert prepared.status_code==200,'Intent preparation failed'
  p=prepared.json()
  headers={**admin_headers(),'X-Admin-Intent-Id':p['intent_id'],'X-Admin-Idempotency-Key':str(uuid.uuid4()),'X-Admin-Confirmation-SHA256':hashlib.sha256(p['confirmation_challenge'].encode()).hexdigest()}
  completed=status(client.put(path,headers=headers,json=body),'execute_'+label+'_'+key_label)
  assert completed.status_code==expect,'Unexpected guarded material response'
  if repeat:
   repeated=status(client.put(path,headers=headers,json=body),'repeat_'+label+'_'+key_label)
   assert repeated.status_code==200 and repeated.json()==completed.json(),'Idempotent repeat changed result'
  for response in (prepared,completed):
   for endpoint in initial['endpoints'].values():
    assert endpoint['private_key'] not in response.text,'Private key in operator response'
   assert 'a04-http-'+label not in response.text,'Install identifier in operator response'
 def manifest(label):
  response=status(client.get('/api/client/profile/managed',headers={'Authorization':'Bearer '+sessions[label].access_token}),'manifest_'+label)
  assert response.status_code==200,'Managed profile unavailable'
  body=response.json()
  assert body['transport_profile']==profile+'_lab' and body['config_format']=='singbox-json'
  endpoint=body['config_payload']['endpoints'][0]
  assert endpoint['private_key']==initial['endpoints']['c' if label=='a' and report.get('rotated') else label]['private_key']
  return endpoint
 def revoke(label):
  response=status(client.delete('/api/client/devices/'+device_ids[label],headers={'Authorization':'Bearer '+sessions[label+'-actor'].access_token}),'revoke_'+label)
  assert response.status_code==200,'Device revoke failed'
  denied=status(client.get('/api/client/profile/managed',headers={'Authorization':'Bearer '+sessions[label].access_token}),'denied_'+label)
  assert denied.status_code in (401,403),'Revoked device still authenticated'
  with api.SessionLocal() as s:
   rows=s.query(model).filter_by(tg_id=tg_ids[label],install_id='a04-http-'+label,is_active=True).all()
   assert not rows,'Revoked device has active material'
  return {'status':denied.status_code,'active_materials':0}
 phase='initial_material'
 direct=status(client.put(path,headers=admin_headers(),json=payload('a','a')),'unguarded')
 assert direct.status_code==428,'L3 guard not required'
 guarded('a','a',repeat=True)
 guarded('b','a',expect=422)
 guarded('b','b',repeat=True)
 with api.SessionLocal() as s:
  assert s.query(model).count()==2,'Repeat or rejected duplicate added material'
 report['initial_rows']=2
 endpoints={'a':manifest('a'),'b':manifest('b')}
 emit({'phase':'ready','endpoints':endpoints,'safe':{'initial_rows':2,'guard_required':True,'duplicate_rejected':True,'repeat_idempotent':True}})
 for line in sys.stdin:
  command=json.loads(line);phase=command['action']
  if phase=='revoke_a':
   outcome=revoke('a');emit({'phase':phase,**outcome})
  elif phase=='rotate_a':
   with api.SessionLocal() as s:
    sessions['a']=auth.issue_authenticated_device_session(s,account_id=accounts['a'],install_id='a04-http-a',device_name='Recovered fixture',platform='windows')
    s.commit()
   guarded('a','a',expect=422)
   guarded('a','c',repeat=True)
   report['rotated']=True
   emit({'phase':phase,'endpoint':manifest('a'),'safe':{'revoked_key_rejected':True,'new_key_issued':True}})
  elif phase=='finish':
   outcomes={label:revoke(label) for label in ('a','b')}
   with api.SessionLocal() as s:
    rows=s.query(model).all()
    assert len(rows)==3 and all(not row.is_active and row.state=='revoked' for row in rows)
    forbidden=[e['private_key'] for e in initial['endpoints'].values()]
    for row in s.query(models.AdminActionIntent):
     record=json.dumps({c.name:str(getattr(row,c.name)) for c in row.__table__.columns})
     assert not any(key in record for key in forbidden),'Private material in intent persistence'
   report.update(result='PASS_GUARDED_HTTP_DEVICE_KEY_LIFECYCLE',final_material_rows=3,final_active_material_rows=0,operator_payload_secret_check=True)
   save();emit({'phase':'finished','outcomes':outcomes,'safe':report});break
  else:raise ValueError('Unsupported fixture action')
 client.close()
 api.engine.dispose() if hasattr(api,'engine') else None
try:main()
except BaseException as exc:
 report.update(result='FAILED',failed_phase=phase,error_type=type(exc).__name__,traceback_sha256=hashlib.sha256(traceback.format_exc().encode()).hexdigest())
 save();emit({'phase':'error','safe':report});sys.exit(1)
