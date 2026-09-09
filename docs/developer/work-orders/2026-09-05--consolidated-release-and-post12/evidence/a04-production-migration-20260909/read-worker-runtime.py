import base64,hashlib,importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('migration_plan',out/'plan-migration.py');plan=importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)
code=r'''
import ast,datetime,json,pathlib,subprocess
state=dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show','portal-worker','-p','MainPID','-p','NRestarts','-p','ActiveState'],text=True).splitlines())
assert state['ActiveState']=='active' and state['NRestarts']=='0'
assert b'AWG_LAB_PEER_TARGETS_FILE=/root/portal_bot/runtime-config/awg-peer-targets.json' in pathlib.Path('/proc/'+state['MainPID']+'/environ').read_bytes().split(b'\0')
raw=subprocess.check_output(['journalctl','-u','portal-worker','--since','2026-09-09 05:22:16 UTC','-o','json','--no-pager'],text=True)
reports=[]
for line in raw.splitlines():
 entry=json.loads(line);message=entry.get('MESSAGE','');marker='awg_lab_peer_reconcile result='
 if marker in message and str(entry.get('_PID'))==state['MainPID']:
  report=ast.literal_eval(message.split(marker,1)[1]);assert set(report)=={'targets','retired','shared_keys_blocked','disk_removed','live_removed','failed_targets','errors'}
  reports.append({'journal_timestamp_us':entry['__REALTIME_TIMESTAMP'],'result':report})
assert len(reports)>=2 and all(r['result']['failed_targets']==0 and r['result']['targets']==2 for r in reports)
print(json.dumps({'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin','worker_state':state,'periodic_run_count':len(reports),'latest_runs':reports[-3:],'configuration_loaded':True,'status':'PASS'}))
'''
runtime=plan.remote('pokrov-brain',code);servers=plan.remote('pokrov-de',plan.server)
expected=json.loads((out/'migration-applied-v2.json').read_text())['material_changes'];readback=[]
for profile,interface in [('awg2_lab','pokrovawg2'),('awg31_lab','pokrovawg31')]:
 state=servers[interface];parts=plan.parse(state['persisted'])
 live_hashes={hashlib.sha256(base64.b64decode(k)).hexdigest() for k in state['peers']}
 saved_hashes={hashlib.sha256(base64.b64decode(p['PublicKey'])).hexdigest() for p in parts if p['section']=='[Peer]'}
 wanted={r['new_public_key_sha256'] for r in expected if r['profile']==profile};assert len(wanted)==2 and live_hashes==saved_hashes==wanted
 readback.append({'profile':profile,'service_state':state['service_state'],'live_peer_count':len(live_hashes),'saved_peer_count':len(saved_hashes),'only_migrated_keys_present':True,'config_sha256':state['persisted_sha256']})
runtime['server_readback']=readback;runtime['historically_shared_keys_blocked_explanation']='Retained historical rows remain classified as shared; direct migration removed these peers. Count is not active peer count.'
target=out/'worker-runtime-verified.json';assert not target.exists();target.write_text(json.dumps(runtime,indent=2)+'\n');print(json.dumps(runtime,indent=2))
