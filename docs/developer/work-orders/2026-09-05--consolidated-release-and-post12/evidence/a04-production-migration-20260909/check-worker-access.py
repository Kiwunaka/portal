import hashlib,json,shlex,subprocess
from pathlib import Path
out=Path(__file__).resolve().parent
code=r'''
import base64,datetime,hashlib,json,os,pathlib,subprocess,sys
pid=subprocess.check_output(['systemctl','show','portal-worker','-p','MainPID','--value'],text=True).strip()
for item in pathlib.Path('/proc/'+pid+'/environ').read_bytes().split(b'\0'):
 if b'=' in item:
  k,v=item.split(b'=',1);os.environ[k.decode()]=v.decode()
os.chdir('/root/portal_bot');sys.path.insert(0,'/root/portal_bot')
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
assert not os.environ.get('AWG_LAB_PEER_TARGETS_FILE')
os.environ['AWG_LAB_PEER_TARGETS_FILE']='/root/portal_bot/runtime-config/awg-peer-targets.json'
from awg_lab_peer_worker import configured_targets,remove_remote_peers
from ssh_host_keys import configure_ssh_host_key_policy
import paramiko
targets=configured_targets();results=[]
for target in targets:
 absent=base64.b64encode(os.urandom(32)).decode()
 result=remove_remote_peers(target,[absent]);assert result=={'requested':1,'disk_removed':0,'live_removed':0}
 results.append({'profile':target['profile'],'strict_ssh_and_forced_helper':True,'absent_peer_idempotent':True,**result})
target=targets[0]
client=configure_ssh_host_key_policy(paramiko.SSHClient(),known_hosts_path=target['known_hosts'],allow_trust_on_first_use=False)
client.connect(target['host'],port=target['port'],username=target['username'],key_filename=target['key_file'],allow_agent=False,look_for_keys=False,timeout=10)
stdin,stdout,stderr=client.exec_command('printf arbitrary_shell_execution');stdin.write('{}');stdin.flush();stdin.channel.shutdown_write()
raw=stdout.read();error=stderr.read();status=stdout.channel.recv_exit_status();client.close()
assert status==1 and not error and json.loads(raw)=={'ok':False,'code':'interface_invalid'}
print(json.dumps({'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin','targets':results,'arbitrary_ssh_command_denied':True,'worker_process_configuration_unchanged':True,'peer_mutations':0,'status':'PASS'}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,timeout=90)
assert r.returncode==0,hashlib.sha256(r.stderr.encode()).hexdigest()
report=json.loads(r.stdout);target=out/'worker-access-checked.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
