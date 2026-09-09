import hashlib,json,shlex,subprocess
from pathlib import Path
out=Path(__file__).resolve().parent
assert json.loads((out/'shared-keys-retired.json').read_text())['status']=='PASS_SHARED_PEERS_DECOMMISSIONED'
target=out/'worker-activated.json';assert not target.exists()
code=r'''
import datetime,hashlib,json,os,pathlib,subprocess,time
def states():
 return {unit:dict(line.split('=',1) for line in subprocess.check_output(['systemctl','show',unit,'-p','MainPID','-p','NRestarts','-p','ActiveState'],text=True).splitlines()) for unit in ('portal-api','portal-bot','portal-helpbot','portal-feedbackbot','portal-worker')}
before=states();pid=before['portal-worker']['MainPID']
assert b'AWG_LAB_PEER_TARGETS_FILE=' not in pathlib.Path('/proc/'+pid+'/environ').read_bytes()
targets=pathlib.Path('/root/portal_bot/runtime-config/awg-peer-targets.json');assert targets.is_file()
config=json.loads(targets.read_text());assert len(config)==2
dropin=pathlib.Path('/etc/systemd/system/portal-worker.service.d');dropin.mkdir(exist_ok=True)
path=dropin/'91-awg-peer-worker.conf';assert not path.exists()
raw=b'[Service]\nEnvironment=AWG_LAB_PEER_TARGETS_FILE=/root/portal_bot/runtime-config/awg-peer-targets.json\n'
with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as handle:handle.write(raw)
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
subprocess.run(['systemctl','daemon-reload'],check=True,capture_output=True)
subprocess.run(['systemctl','restart','portal-worker'],check=True,capture_output=True)
time.sleep(3)
after=states();assert after['portal-worker']['MainPID']!=pid
for unit,state in after.items():
 assert state['ActiveState']=='active' and state['NRestarts']=='0'
 if unit!='portal-worker':assert state['MainPID']==before[unit]['MainPID']
env=pathlib.Path('/proc/'+after['portal-worker']['MainPID']+'/environ').read_bytes().split(b'\0')
assert b'AWG_LAB_PEER_TARGETS_FILE=/root/portal_bot/runtime-config/awg-peer-targets.json' in env
print(json.dumps({'activated_at':started,'origin':'brain-origin','source_revision':'7d37005e4260995ab44ec3adb14bbffa3d42738b','dropin':str(path),'dropin_sha256':hashlib.sha256(raw).hexdigest(),'target_count':2,'before':before,'after':after,'only_worker_restarted':True,'worker_env_loaded':True,'public_awg_enabled':False,'status':'ACTIVATED_AWAITING_PERIODIC_READBACK'}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=60)
assert r.returncode==0,hashlib.sha256(r.stderr.encode()).hexdigest()
report=json.loads(r.stdout);target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
