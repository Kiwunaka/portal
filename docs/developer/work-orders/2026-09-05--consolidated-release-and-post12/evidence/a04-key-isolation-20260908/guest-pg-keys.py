"""Four real-PostgreSQL races for the device-specific AWG peer key guard."""
import base64,datetime,hashlib,json,os,queue,secrets,subprocess,sys,threading,time
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

root=Path(__file__).parent;source=root/'source'
sys.path.insert(0,str(source/'portal_bot'));os.chdir(source)
DATABASE='portal_r12_a04_keys_20260908'
assert not (root/'pg-result.json').exists(),'Preserve previous result'
manifest=json.loads((root/'source-manifest.json').read_text())
for item in manifest['files']:
 raw=(source/item['path']).read_bytes()
 assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
for name in ['AWG2_LAB_MATERIAL_SECRET','AWG31_LAB_MATERIAL_SECRET']:
 os.environ[name]=secrets.token_hex(32)
dsn=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL']).set(database=DATABASE)
os.environ['DATABASE_URL']=dsn.render_as_string(hide_password=False)
check=subprocess.run(['runuser','-u','postgres','--','psql','-At','-d','postgres','-c',"SELECT count(*) FROM pg_database WHERE datname='"+DATABASE+"'"],capture_output=True,text=True)
assert check.returncode==0 and check.stdout.strip()=='0','Refuse existing database'
created=subprocess.run(['runuser','-u','postgres','--','createdb','--owner=r12_linux_app',DATABASE],capture_output=True)
assert created.returncode==0,'Fixture database creation failed; output withheld'
import models,awg2_lab_service as awg2,awg31_lab_service as awg31
engine=create_engine(dsn,hide_parameters=True,connect_args={'options':'-c lock_timeout=12000 -c statement_timeout=20000'})
models.Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
endpoints=json.loads((root/'synthetic-endpoints.json').read_text())
protocols={'awg2':(models.Awg2LabMaterial,awg2.replace_awg2_lab_material,awg2.AWG2_ENDPOINT_REVISION,awg2.Awg2LabError),'awg31':(models.Awg31LabMaterial,awg31.replace_awg31_lab_material,awg31.AWG31_ENDPOINT_REVISION,awg31.Awg31LabError)}
result={'result':'RUNNING','database':DATABASE,'source_parent':manifest['source_parent'],'source_files_checked':len(manifest['files']),'cases':[],'synthetic_only':True,'server_network_mutation':False}
def save():(root/'pg-result.json').write_text(json.dumps(result,indent=2)+'\n')
def blocked_by(waiter,holder):
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  with engine.connect() as conn:
   blockers=conn.execute(text('SELECT pg_blocking_pids(:pid)'),{'pid':waiter}).scalar()
  if holder in blockers:return True
  time.sleep(.05)
 return False
save()
for profile,(model,replace,revision,error_type) in protocols.items():
 for index,disposition in enumerate(('commit','rollback')):
  key=bytearray(secrets.token_bytes(32))
  endpoint={**endpoints[profile],'private_key':base64.b64encode(key).decode()}
  key[0]^=1
  copied={**endpoint,'private_key':base64.b64encode(key).decode(),'address':['10.66.0.99/32']}
  options={'generation':'fixture-v1','endpoint_revision':revision,'server_record_id':'fixture-server','node_code':'fixture-node'}
  main=Session();holder=main.execute(text('SELECT pg_backend_pid()')).scalar()
  row=replace(main,tg_id=920001+index*2,install_id='holder-'+str(index),endpoint=endpoint,**options)
  first_id=row.id;ciphertext_sha=hashlib.sha256(row.endpoint_ciphertext.encode()).hexdigest()
  started=queue.Queue();finished=queue.Queue()
  def contender():
   with Session() as session:
    try:
     started.put(session.execute(text('SELECT pg_backend_pid()')).scalar())
     other=replace(session,tg_id=920002+index*2,install_id='waiter-'+str(index),endpoint=copied,**options)
     session.commit();finished.put({'outcome':'inserted','id':other.id})
    except error_type as exc:
     session.rollback();finished.put({'outcome':'rejected','code':exc.code})
    except Exception as exc:
     session.rollback();finished.put({'outcome':'error','type':type(exc).__name__})
  thread=threading.Thread(target=contender);thread.start()
  waiter=started.get(timeout=5);blocked=blocked_by(waiter,holder)
  if blocked and disposition=='commit':main.commit()
  else:main.rollback()
  main.close()
  outcome=finished.get(timeout=15);thread.join(timeout=1)
  assert blocked,'Concurrent duplicate did not wait for the first transaction'
  assert not thread.is_alive()
  if disposition=='commit':
   assert outcome=={'outcome':'rejected','code':'material_key_already_bound'},outcome
  else:assert outcome.get('outcome')=='inserted',outcome
  with Session() as session:
   rows=session.query(model).filter(model.tg_id.in_([920001+index*2,920002+index*2])).all()
   assert len(rows)==1 and rows[0].is_active and rows[0].state=='ready'
   if disposition=='commit':
    assert rows[0].id==first_id and hashlib.sha256(rows[0].endpoint_ciphertext.encode()).hexdigest()==ciphertext_sha
   else:assert rows[0].id==outcome['id']
  result['cases'].append({'profile':profile,'first_transaction':disposition,'advisory_lock_observed':blocked,'contender_outcome':outcome['outcome'],'contender_code':outcome.get('code'),'one_device_bound_row':True,'x25519_clamped_alias_compared':True,'committed_ciphertext_preserved':disposition=='commit'})
  save();print(json.dumps(result['cases'][-1]),flush=True)
engine.dispose()
with engine.connect() as conn:
 result['postgres_version']=conn.execute(text('SHOW server_version')).scalar()
 result['isolation_level']=conn.execute(text('SHOW transaction_isolation')).scalar()
 assert conn.execute(text('SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')).scalar()==0
for item in manifest['files']:
 assert hashlib.sha256((source/item['path']).read_bytes()).hexdigest()==item['sha256']
result['material_rows']={}
with Session() as s:
 for profile,(model,*_) in protocols.items():
  assert s.query(model).count()==2
  result['material_rows'][profile]=2
engine.dispose()
result['result']='PASS_FOUR_POSTGRES_DEVICE_KEY_RACES'
save();print(json.dumps({'result':result['result'],'cases':len(result['cases'])}),flush=True)
