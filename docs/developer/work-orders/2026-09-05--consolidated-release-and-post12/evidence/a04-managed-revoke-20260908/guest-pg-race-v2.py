"""Synthetic PostgreSQL race in the owned VM; emits no DSN or private data."""
import datetime,hashlib,json,os,queue,secrets,subprocess,sys,threading,time,uuid
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

root=Path(__file__).parent
source=root/'source'
sys.path.insert(0,str(source/'portal_bot'))
os.chdir(source)
DATABASE='portal_r12_a04_20260908_rehearsal'
assert not (root/'pg-result-v2.json').exists(),'Preserve previous result'
manifest=json.loads((root/'source-manifest-v2.json').read_text())
for item in manifest['files']:
    raw=(source/item['path']).read_bytes()
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
for name in ['WEBAPP_SESSION_SECRET','AWG2_LAB_MATERIAL_SECRET','AWG31_LAB_MATERIAL_SECRET','HY2_LAB_MATERIAL_SECRET']:
    os.environ[name]=secrets.token_hex(32)
dsn=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL']).set(database=DATABASE)
os.environ['DATABASE_URL']=dsn.render_as_string(hide_password=False)
check=subprocess.run(['runuser','-u','postgres','--','psql','-At','-d','postgres','-c',"SELECT count(*) FROM pg_database WHERE datname='"+DATABASE+"'"],capture_output=True,text=True)
assert check.returncode==0 and check.stdout.strip()=='1','Expected retained empty fixture database'
empty=subprocess.run(['runuser','-u','postgres','--','psql','-At','-d',DATABASE,'-c',"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"],capture_output=True,text=True)
assert empty.returncode==0 and empty.stdout.strip()=='0','Refuse nonempty fixture database'
import models
import auth_session_service as auth
import admin_action_intent_service as admin
import awg2_lab_service as awg2
import awg31_lab_service as awg31
import hy2_lab_service as hy2

engine=create_engine(dsn,hide_parameters=True,connect_args={'options':'-c lock_timeout=12000 -c statement_timeout=20000'})
models.Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
NOW=datetime.datetime(2026,9,8,15,0,0)
endpoints=json.loads((root/'synthetic-endpoints.json').read_text())
protocols={'awg2':(models.Awg2LabMaterial,awg2.replace_awg2_lab_material,awg2.AWG2_ENDPOINT_REVISION,admin._awg2_lab_material_state),'awg31':(models.Awg31LabMaterial,awg31.replace_awg31_lab_material,awg31.AWG31_ENDPOINT_REVISION,admin._awg31_lab_material_state),'hy2':(models.Hy2LabMaterial,hy2.replace_hy2_lab_material,hy2.HY2_ENDPOINT_REVISION,admin._hy2_lab_material_state)}
result={'result':'RUNNING','database':DATABASE,'source_parent':manifest['source_parent'],'source_files_checked':len(manifest['files']),'cases':[],'synthetic_only':True,'server_network_mutation':False}
def save(): (root/'pg-result-v2.json').write_text(json.dumps(result,indent=2)+'\n')
save()
def seed(index):
    account_id=str(uuid.uuid4());target_id=str(uuid.uuid4());actor_id=str(uuid.uuid4())
    target_install='r12-a04-target-'+str(index);actor_install='r12-a04-actor-'+str(index)
    tg_id=910000+index*2
    with Session.begin() as session:
        account=models.Account(id=account_id,status='active',created_source='fixture',created_at=NOW,updated_at=NOW)
        session.add(account)
        for did,install in [(target_id,target_install),(actor_id,actor_install)]:
            session.add(models.AccountDevice(id=did,account_id=account_id,install_id=install,label='Synthetic device',platform='windows',state='active',credential_version=1,first_seen_at=NOW,last_seen_at=NOW,created_at=NOW,updated_at=NOW))
        for offset,install in [(0,target_install),(1,actor_install)]:
            session.add(models.User(tg_id=tg_id+offset,account_id=account_id,uuid=str(uuid.uuid4()),email='fixture-'+str(index)+'-'+str(offset)+'@example.test',sub_type='PAID',is_active=True,app_install_id=install,app_platform='windows',expiry_at=NOW+datetime.timedelta(days=1),created_at=NOW))
        session.flush()
        actor_user=session.get(models.User,tg_id+1)
        actor=auth.issue_device_session(session,user=actor_user,install_id=actor_install,now=NOW,fresh_auth_at=NOW)
        payloads={}
        original={}
        for name,(model,replace,revision,state) in protocols.items():
            payload={'tg_id':tg_id,'install_id':target_install,'generation':'fixture-v1','endpoint_revision':revision,'server_record_id':'fixture-server','node_code':'fixture-node','endpoint':endpoints[name]}
            row=replace(session,**payload,now=NOW)
            payloads[name]=payload
            original[name]={'id':row.id,'ciphertext_sha256':hashlib.sha256(row.endpoint_ciphertext.encode()).hexdigest()}
        return {'account_id':account_id,'device_id':target_id,'actor_session_id':actor.session_id,'install_id':target_install,'tg_id':tg_id,'payloads':payloads,'original':original}
def revoke(session,case):
    return auth.revoke_device(session,account_id=case['account_id'],device_id=case['device_id'],actor_session_id=case['actor_session_id'],now=NOW+datetime.timedelta(minutes=1))
def await_blocked(waiter,holder):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        with engine.connect() as conn:
            blockers=conn.execute(text('SELECT pg_blocking_pids(:pid)'),{'pid':waiter}).scalar()
        if holder in blockers:return True
        time.sleep(.05)
    return False
for index,(name,values) in enumerate(protocols.items()):
    model,replace,revision,state=values
    for order in ('revoke_first','replace_first'):
        case=seed(index*2+(0 if order=='revoke_first' else 1))
        main=Session();holder=main.execute(text('SELECT pg_backend_pid()')).scalar()
        payload={**case['payloads'][name],'generation':'fixture-v2'}
        if order=='revoke_first':revoke(main,case)
        else:
            state(main,str(case['tg_id']),payload,True)
            replace(main,**payload,now=NOW+datetime.timedelta(seconds=30))
        main.flush()
        started=queue.Queue();finished=queue.Queue()
        def concurrent():
            with Session() as session:
                try:
                    started.put(session.execute(text('SELECT pg_backend_pid()')).scalar())
                    if order=='revoke_first':
                        state(session,str(case['tg_id']),payload,True)
                        replace(session,**payload,now=NOW+datetime.timedelta(minutes=2))
                        outcome='unexpected_replace'
                    else:
                        revoke(session,case)
                        outcome='revoked'
                    session.commit()
                    finished.put({'outcome':outcome})
                except admin.ActionIntentError as exc:
                    session.rollback();finished.put({'outcome':'rejected','code':exc.code})
                except Exception as exc:
                    session.rollback();finished.put({'outcome':'error','type':type(exc).__name__})
        thread=threading.Thread(target=concurrent)
        thread.start();waiter=started.get(timeout=5)
        blocked=await_blocked(waiter,holder)
        if blocked:main.commit()
        else:main.rollback()
        main.close()
        outcome=finished.get(timeout=15);thread.join(timeout=1)
        assert blocked,'Expected database row lock was not observed'
        assert outcome==({'outcome':'rejected','code':'invalid_target'} if order=='revoke_first' else {'outcome':'revoked'}),outcome
        with Session.begin() as session:
            target=session.get(models.AccountDevice,case['device_id'])
            assert target.state=='revoked'
            first_revoked=target.revoked_at
            for p,(m,_,_,_) in protocols.items():
                rows=session.query(m).filter_by(tg_id=case['tg_id'],install_id=case['install_id']).all()
                assert len(rows)==(2 if order=='replace_first' and p==name else 1)
                assert not any(row.is_active for row in rows)
                old=session.get(m,case['original'][p]['id'])
                assert hashlib.sha256(old.endpoint_ciphertext.encode()).hexdigest()==case['original'][p]['ciphertext_sha256']
            revoke(session,case)
            assert target.revoked_at==first_revoked
            fresh=auth.issue_authenticated_device_session(session,account_id=case['account_id'],install_id=case['install_id'],device_name='Synthetic recovered device',platform='windows',now=NOW+datetime.timedelta(minutes=2))
            assert fresh.device_id==target.id and target.state=='active'
            for m,_,_,_ in protocols.values():
                assert session.query(m).filter_by(tg_id=case['tg_id'],install_id=case['install_id'],is_active=True).count()==0
        result['cases'].append({'profile':name,'order':order,'row_lock_observed':blocked,'outcome':outcome,'old_ciphertext_preserved':True,'fresh_login_did_not_restore_material':True,'repeat_revoke_preserved_first_timestamp':True})
        save();print(json.dumps(result['cases'][-1]),flush=True)
assert len(result['cases'])==6
with engine.connect() as conn:
    result['postgres_version']=conn.execute(text('SHOW server_version')).scalar()
    result['isolation_level']=conn.execute(text('SHOW transaction_isolation')).scalar()
engine.dispose()
result['result']='PASS_SIX_POSTGRES_REVOKE_REPLACE_RACES';save()
print(json.dumps({'result':result['result'],'cases':6}),flush=True)
