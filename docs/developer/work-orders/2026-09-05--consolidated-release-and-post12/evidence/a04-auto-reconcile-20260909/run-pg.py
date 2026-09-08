"""Current source, real PostgreSQL: expiry/retry and replacement races."""
import ast
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import subprocess
import sys
import threading
import time
import uuid

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from pg_lab import postgres_lab

root = Path(__file__).parent
platform = Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
output = root / 'pg-result.json'
assert not output.exists(), 'Preserve result'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
for name in ('WEBAPP_SESSION_SECRET', 'AWG2_LAB_MATERIAL_SECRET', 'AWG31_LAB_MATERIAL_SECRET'):
    os.environ[name] = secrets.token_hex(32)
sys.path.insert(0, str(platform / 'portal_bot'))
import models
import auth_session_service as auth
import admin_action_intent_service as admin
import awg_lab_peer_worker as worker

NOW = datetime.now(timezone.utc).replace(tzinfo=None)
report = {'result': 'RUNNING', 'cases': [], 'source_parent': subprocess.check_output(['git','rev-parse','HEAD'],cwd=platform,text=True).strip()}
def save(): output.write_text(json.dumps(report, indent=2) + '\n')
save()

def endpoint_for(name):
    path = platform / ('tests/test_' + name + '_lab_service.py')
    node = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == '_endpoint')
    scope = {'AWG31_CONTRACT_ID': 'pokrov.awg31.endpoint.v1'}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
    endpoint = scope['_endpoint']()
    endpoint['private_key'] = base64.b64encode(secrets.token_bytes(32)).decode()
    return endpoint

with postgres_lab('portal_r12_a04_auto_20260909_pg_v1') as (engine, ssh):
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    worker.load_network_rollout_config = lambda **_: {'awg2_lab': {'material_max_age_hours':168}, 'awg31_lab': {'material_max_age_hours':168}}

    def seed(profile, index, *, retired=False, expired=False, age_days=0):
        model, service = worker.PROFILES[profile]
        name = profile.removesuffix('_lab')
        account, device, actor = (str(uuid.uuid4()) for _ in range(3))
        install = 'auto-fixture-' + str(index)
        tg = 980000 + index * 2
        target = {'profile':profile, 'node_code':'fixture-' + str(index), 'server_record_id':'auto-fixture-' + str(index)}
        payload = {'tg_id':tg, 'install_id':install, 'generation':'fixture-v1',
                   'endpoint_revision':service.AWG2_ENDPOINT_REVISION if name=='awg2' else service.AWG31_ENDPOINT_REVISION,
                   'node_code':target['node_code'], 'server_record_id':target['server_record_id'], 'endpoint':endpoint_for(name)}
        replace = service.replace_awg2_lab_material if name=='awg2' else service.replace_awg31_lab_material
        state = admin._awg2_lab_material_state if name=='awg2' else admin._awg31_lab_material_state
        with Session.begin() as session:
            session.add(models.Account(id=account,status='active',created_source='fixture'))
            for did, inst in ((device, install), (actor, install+'-actor')):
                session.add(models.AccountDevice(id=did,account_id=account,install_id=inst,state='active',credential_version=1,platform='windows'))
            for offset, inst in ((0,install),(1,install+'-actor')):
                session.add(models.User(tg_id=tg+offset,account_id=account,uuid=str(uuid.uuid4()),
                    email=str(tg+offset)+'@example.test',is_active=True,sub_type='PAID',app_platform='windows',
                    app_install_id=inst,expiry_at=NOW+timedelta(days=-1 if expired and offset==0 else 1)))
            session.flush()
            row=replace(session,**payload,now=NOW-timedelta(days=age_days))
            if retired:
                row.state='rotated';row.is_active=False;row.revoked_at=NOW-timedelta(minutes=1)
            session.flush()
            actor_session=auth.issue_device_session(session,user=session.get(models.User,tg+1),install_id=install+'-actor',now=NOW,fresh_auth_at=NOW)
            return {'model':model,'service':service,'replace':replace,'state':state,'target':target,'payload':payload,
                    'account':account,'device':device,'actor_session':actor_session.session_id,'row_id':row.id,
                    'ciphertext_sha256':hashlib.sha256(row.endpoint_ciphertext.encode()).hexdigest()}

    def observed_block(waiter, holder):
        deadline=time.monotonic()+6
        while time.monotonic()<deadline:
            with engine.connect() as conn:
                if holder in conn.execute(text('SELECT pg_blocking_pids(:pid)'),{'pid':waiter}).scalar(): return True
            time.sleep(.05)
        return False

    for pindex, profile in enumerate(('awg2_lab','awg31_lab')):
        for offset, order in enumerate(('scanner_first','replacement_first')):
            case=seed(profile,pindex*10+offset+1,retired=True)
            held=Session();holder=held.execute(text('SELECT pg_backend_pid()')).scalar()
            payload={**case['payload'],'generation':'fixture-v2'}
            if order=='scanner_first':
                worker._retire_binding(held,model=case['model'],tg_id=payload['tg_id'],install_id=payload['install_id'],
                    target=case['target'],policy={'material_max_age_hours':168},now=NOW)
                keys,shared=worker.removal_keys(held,target=case['target'],now=NOW)
                assert len(keys)==1 and shared==0
                held.flush()
            else:
                case['state'](held,str(payload['tg_id']),payload,True)
                case['replace'](held,**payload,now=NOW)
                held.flush()
            started=queue.Queue();finished=queue.Queue()
            def concurrent():
                try:
                    if order=='scanner_first':
                        with Session.begin() as session:
                            started.put(session.execute(text('SELECT pg_backend_pid()')).scalar())
                            case['state'](session,str(payload['tg_id']),payload,True)
                            case['replace'](session,**payload,now=NOW)
                        finished.put({'outcome':'unexpected_reissue'})
                    else:
                        def factory():
                            session=Session()
                            started.put(session.execute(text('SELECT pg_backend_pid()')).scalar())
                            return session
                        calls=[]
                        def remove(_target, keys):
                            calls.extend(keys)
                            return {'requested':len(keys),'disk_removed':len(keys),'live_removed':len(keys)}
                        result=worker.reconcile_awg_peers(factory,targets=[case['target']],now=NOW,remove=remove)
                        finished.put({'outcome':'scan','report':result,'removal_count':len(calls)})
                except Exception as error:
                    finished.put({'outcome':'rejected','code':getattr(error,'code',type(error).__name__)})
            thread=threading.Thread(target=concurrent)
            thread.start();waiter=started.get(timeout=5)
            blocked=observed_block(waiter,holder)
            if blocked: held.commit()
            else: held.rollback()
            held.close()
            outcome=finished.get(timeout=20);thread.join(timeout=1)
            assert blocked,'Expected PostgreSQL lock not observed'
            if order=='scanner_first': assert outcome=={'outcome':'rejected','code':'material_key_revoked'},outcome
            else:
                assert outcome['outcome']=='scan' and outcome['removal_count']==0,outcome
                assert outcome['report']['failed_targets']==0,outcome
            with Session() as session:
                row=session.get(case['model'],case['row_id'])
                assert hashlib.sha256(row.endpoint_ciphertext.encode()).hexdigest()==case['ciphertext_sha256']
            report['cases'].append({'profile':profile,'order':order,'postgres_block_observed':True,'outcome':outcome,'ciphertext_preserved':True})
            save();print(json.dumps(report['cases'][-1]),flush=True)

        expiry_cases=[seed(profile,pindex*10+3,expired=True),seed(profile,pindex*10+4,age_days=8)]
        for case in expiry_cases:
            calls=[]
            def fail_remote(_target,keys):
                calls.extend(keys)
                with Session() as session: assert session.get(case['model'],case['row_id']).state=='revoked'
                raise worker.PeerReconcileError('peer_removal_unavailable')
            failed=worker.reconcile_awg_peers(Session,targets=[case['target']],now=NOW,remove=fail_remote)
            assert failed['retired']==1 and failed['failed_targets']==1 and len(calls)==1
            def good_remote(_target,keys):
                assert keys==calls
                return {'requested':len(keys),'disk_removed':1,'live_removed':1}
            passed=worker.reconcile_awg_peers(Session,targets=[case['target']],now=NOW,remove=good_remote)
            assert passed['retired']==0 and passed['failed_targets']==0 and passed['live_removed']==1
            report['cases'].append({'profile':profile,'expiry_kind':'entitlement' if case is expiry_cases[0] else 'material_age',
                                    'durable_before_network':True,'retry_same_key':True,'result':'PASS'})
            save()
    with engine.connect() as conn:
        report['postgres_version']=conn.execute(text('SHOW server_version')).scalar()
        report['isolation_level']=conn.execute(text('SHOW transaction_isolation')).scalar()
    report['result']='PASS_FOUR_RACES_AND_FOUR_EXPIRY_RETRIES';save()
print(json.dumps({'result':report['result'],'cases':len(report['cases'])}),flush=True)
