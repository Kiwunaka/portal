import base64,hashlib,importlib.util,json,shlex,sys
from datetime import datetime,timezone
from pathlib import Path
out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('migration_plan',out/'plan-migration.py');plan=importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)
sys.path.insert(0,'E:/r12-integrated-platform-20260909/scripts')
import remote_run_owned_awg_core_interop as op
build=json.loads((out/'build.json').read_text());binary=out/'owned-awg.test';assert op._file_sha256(binary)==build['binary_sha256']
selector=r'''
from awg_lab_key_binding import _client_public_key
old_sha={'awg2_lab':'057f641915d6b87c2f462d95f142bfa3a78247cd267bbe689316c5a759623638','awg31_lab':'16f627d7597017ec7a12e130d274906d40d85cd2fa54f011d1a85950a6bcbcda'}
chosen=[]
with SessionLocal() as session:
 session.execute(text('SET TRANSACTION READ ONLY'))
 for profile,model,decrypt in [('awg2_lab',Awg2LabMaterial,decrypt2),('awg31_lab',Awg31LabMaterial,decrypt31)]:
  new=next(r for r in records if r['profile']==profile and r['install_sha256']=='64a9c9b73d01eedf96a7377df0b1c1c49d023546217184671b57cdd56750943b')
  old=next(r for r in session.query(model).filter_by(tg_id=new['tg_id'],install_id=new['install_id'],state='revoked').order_by(model.id.desc()) if hashlib.sha256(_client_public_key(decrypt(r.endpoint_ciphertext))).hexdigest()==old_sha[profile])
  chosen.append({'profile':profile,'expected':'rejected','key_kind':'retired_shared','endpoint':decrypt(old.endpoint_ciphertext)})
  chosen.append({'profile':profile,'expected':'accepted','key_kind':'new_unique','endpoint':new['endpoint']})
 session.rollback()
print(json.dumps(chosen))
'''
marker="print(json.dumps({'records':records,'policies':policies}))";assert plan.brain.count(marker)==1
records=plan.remote('pokrov-brain',plan.brain.replace(marker,selector),'/root/portal_bot/venv/bin/python');assert len(records)==4
ssh=Path('C:/Windows/System32/OpenSSH/ssh.exe');scp=Path('C:/Windows/System32/OpenSSH/scp.exe');config=Path('C:/Users/kiwun/.ssh/config');known=Path('C:/Users/kiwun/.ssh/known_hosts')
base=op._ssh_base(ssh,'shrek',config,known)
preflight=op._run_process(base+[op._RU_PI_PREFLIGHT],timeout=20);assert preflight.returncode==0 and preflight.stdout.strip()==op._RU_PI_PREFLIGHT_MARKER
remote_root=op._remote_root();remote_binary=remote_root+'/owned-awg.test';copied=False
target=out/'retired-core-interop.json';assert not target.exists()
report={'started_at':datetime.now(timezone.utc).isoformat(),'origin':'RU-origin','execution':'owned RU Pi, synthetic test of retained old and active new material; not installed device proof','build':build,'checks':[],'raw_material_retained':False,'status':'RUNNING'}
def save():target.write_text(json.dumps(report,indent=2)+'\n')
save()
try:
 result=op._run_process(base+['set -eu; umask 077; install -d -m 0700 '+shlex.quote(remote_root)],timeout=20);assert result.returncode==0;copied=True
 result=op._run_process(op._scp_base(scp,ssh,config,known)+[str(binary),'shrek:'+remote_binary],timeout=180);assert result.returncode==0
 result=op._run_process(base+['set -eu; chmod 0700 '+shlex.quote(remote_binary)+'; sha256sum '+shlex.quote(remote_binary)+" | cut -d' ' -f1"],timeout=20);assert result.returncode==0 and result.stdout.strip()==build['binary_sha256']
 for row in records:
  command="set -eu; IFS= read -r POKROV_OWNED_AWG_ENDPOINT_B64; export POKROV_OWNED_AWG_ENDPOINT_B64; exec "+shlex.quote(remote_binary)+" -test.run '^TestOwnedAWGLabAuthenticatedEgress$/^mtu_1280$' -test.count=1 -test.timeout=60s -test.v"
  raw=json.dumps(row['endpoint'],separators=(',',':')).encode();result=op._run_process(base+[command],input_text=base64.b64encode(raw).decode()+'\n',timeout=80)
  combined=result.stdout+'\n'+result.stderr;observations=op._interop_mtu_observations(combined);classification=op._classify(combined,result.returncode)
  ran='=== RUN   TestOwnedAWGLabAuthenticatedEgress/mtu_1280' in combined
  accepted=result.returncode==0 and '--- PASS: TestOwnedAWGLabAuthenticatedEgress/mtu_1280 ' in combined and set(observations)=={'1280'}
  rejected=result.returncode==1 and '--- FAIL: TestOwnedAWGLabAuthenticatedEgress/mtu_1280 ' in combined and classification=='failed_no_outer_response' and not observations
  passed=ran and (accepted if row['expected']=='accepted' else rejected)
  check={k:row[k] for k in ('profile','expected','key_kind')};check.update(returncode=result.returncode,status='PASS' if passed else 'FAIL',classification=classification,output_sha256=hashlib.sha256(combined.encode()).hexdigest(),mtu_observations=observations)
  report['checks'].append(check);save();print(json.dumps(check),flush=True);assert passed
 report['status']='PASS_OLD_DENIED_NEW_ACCEPTED'
except BaseException as error:
 report['status']='FAIL';report['failure_class']=type(error).__name__
finally:
 if copied:
  assert op._REMOTE_ROOT_PATTERN.fullmatch(remote_root)
  result=op._run_process(base+['set -eu; rm -rf -- '+shlex.quote(remote_root)+'; test ! -e '+shlex.quote(remote_root)],timeout=25)
  report['temporary_pi_binary_removed']=result.returncode==0
  if result.returncode:report['status']='FAIL_CLEANUP'
 report['completed_at']=datetime.now(timezone.utc).isoformat();save()
print(json.dumps({'status':report['status'],'checks':len(report['checks'])}));raise SystemExit(0 if report['status'].startswith('PASS') else 1)
