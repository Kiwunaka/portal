"""Actual guarded HTTP + PostgreSQL + two independent owned AWG server peers."""
import base64,datetime,hashlib,json,os,queue,shlex,subprocess,sys,threading
from pathlib import Path
import paramiko
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,PublicFormat,NoEncryption
sys.path.insert(0,'C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/scripts')
import remote_run_owned_awg_core_interop as op
from node_access import connect_node

root=Path(__file__).parent;profile=sys.argv[1]
assert profile in ('awg2','awg31')
output=root/('http-peer-'+profile+'-v2.json');assert not output.exists(),'Preserve prior evidence'
build=json.loads(Path('E:/r12-a04-peer-lifecycle-20260908/build.json').read_text())
binary=Path('E:/r12-a04-peer-lifecycle-20260908/owned-awg.test')
assert op._file_sha256(binary)==build['binary_sha256']
baseline=json.loads((root/'server-before.json').read_text())
interface={'awg2':'pokrovawg2','awg31':'pokrovawg31'}[profile]
prefix={'awg2':'10.203.20.','awg31':'10.203.31.'}[profile]
ssh=Path('C:/Windows/System32/OpenSSH/ssh.exe');scp=Path('C:/Windows/System32/OpenSSH/scp.exe')
config=Path('C:/Users/kiwun/.ssh/config');known=Path('C:/Users/kiwun/.ssh/known_hosts')
base=op._ssh_base(ssh,'shrek',config,known)
preflight=op._run_process(base+[op._RU_PI_PREFLIGHT],timeout=20)
assert preflight.returncode==0 and preflight.stdout.strip()==op._RU_PI_PREFLIGHT_MARKER
os.environ['POKROV_SSH_KNOWN_HOSTS']=str(known)
brain,_=connect_node(code='brain',host='82.21.114.104',passwords_path=Path('C:/Users/kiwun/Documents/ai/VPN/VPN NODE SSH KEYS/PASSWORDS.txt'))
try:template=json.loads(op._load_material(brain,profile+'_lab'))
finally:brain.close()
private={};public={};endpoints={}
for label in ('a','b','c'):
 key=X25519PrivateKey.generate()
 private[label]=base64.b64encode(key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())).decode()
 public[label]=base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()
 endpoint=json.loads(json.dumps(template))
 endpoint.update(private_key=private[label],address=[prefix+('249/32' if label=='b' else '248/32')])
 for peer in endpoint['peers']:peer.pop('pre_shared_key',None);peer.pop('preshared_key',None)
 endpoints[label]=endpoint
assert len(set(public.values()))==3
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profile':profile,'scope':'isolated ASGI/PG accounts + exact Core on RU Pi + ephemeral owned DE peers; operator applies server changes','build':build,'public_key_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in public.items()},'server':[],'http_phases':[],'core_tests':[],'raw_material_retained':False,'result':'RUNNING'}
def save():output.write_bytes((json.dumps(result,indent=2)+'\n').encode())
save()
lab=Path('E:/r12-b08-linux-lab');remote='/opt/r12/a04-key-isolation-20260908'
vm=paramiko.SSHClient();vm.load_host_keys(str(lab/'known_hosts'))
vm.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
with vm.open_sftp() as f:
 f.put(str(root/'guest-managed-keys-v2.py'),remote+'/guest-managed-keys-v2.py')
 f.put(str(root/'test-libs-manifest.json'),remote+'/test-libs-manifest.json')
vm.close()
vm_args=[str(ssh),'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes','-o','UserKnownHostsFile='+str(lab/'known_hosts'),'-i',str(lab/'private/client.key'),'-p','55228','root@127.0.0.1','/root/portal_bot/venv/bin/python -B -u '+remote+'/guest-managed-keys-v2.py']
guest=None;server=None;remote_root=op._remote_root();remote_binary=remote_root+'/owned-awg.test';copied=False
def start(args,prefix=''):
 process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8')
 messages=queue.Queue()
 def read():
  for line in process.stdout:
   if prefix and not line.startswith(prefix):continue
   try:messages.put(json.loads(line[len(prefix):]))
   except Exception:messages.put({'phase':'error','reason':'invalid structured response'})
  messages.put({'phase':'error','reason':'process closed'})
 threading.Thread(target=read,daemon=True).start()
 return process,messages
def receive(messages,seconds=45):
 item=messages.get(timeout=seconds)
 assert item.get('phase')!='error','Fixture/controller error; inspect sanitized guest result'
 return item
def send(process,messages,payload):
 process.stdin.write(json.dumps(payload,separators=(',',':'))+'\n');process.stdin.flush()
 return receive(messages)
def server_action(action,label=None):
 data={'action':action}
 if label:data.update(public=public[label],address=prefix+('249/32' if label=='b' else '248/32'))
 item=send(server,server_messages,data);assert item['phase']==action
 result['server'].append(item);save();return item
def core_test(label,key_label,expected,payload):
 command="set -eu; IFS= read -r POKROV_OWNED_AWG_ENDPOINT_B64; export POKROV_OWNED_AWG_ENDPOINT_B64; exec "+shlex.quote(remote_binary)+" -test.run '^TestOwnedAWGLabAuthenticatedEgress$/^mtu_1280$' -test.count=1 -test.timeout=60s -test.v"
 raw=json.dumps(payload,separators=(',',':')).encode()
 finished=op._run_process(base+[command],input_text=base64.b64encode(raw).decode()+'\n',timeout=80)
 combined=finished.stdout+'\n'+finished.stderr
 observations=op._interop_mtu_observations(combined)
 ran='=== RUN   TestOwnedAWGLabAuthenticatedEgress/mtu_1280' in combined
 passed=finished.returncode==0 and '--- PASS: TestOwnedAWGLabAuthenticatedEgress/mtu_1280 ' in combined and set(observations)=={'1280'}
 denied=finished.returncode==1 and '--- FAIL: TestOwnedAWGLabAuthenticatedEgress/mtu_1280 ' in combined and op._classify(combined,finished.returncode)=='failed_no_outer_response' and not observations
 item={'label':label,'key':key_label,'expected':expected,'returncode':finished.returncode,'selected_subtest_observed':ran,'classification':op._classify(combined,finished.returncode),'oracle_passed':ran and (passed if expected=='accepted' else denied),'payload_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(combined.encode()).hexdigest(),'mtu_observations':observations}
 result['core_tests'].append(item);save();print(json.dumps({'profile':profile,**item}),flush=True)
 assert item['oracle_passed'],'Unexpected Core dataplane outcome'
 state=server_action('read')
 if expected=='accepted':
  observed=next(x for x in state['test_peers'] if x['public_key_sha256']==result['public_key_sha256'][key_label])
  assert observed['rx_bytes']>0 and observed['tx_bytes']>0 and observed['handshake_unix']>0
 return state
try:
 guest,guest_messages=start(vm_args,'__A04__')
 guest.stdin.write(json.dumps({'profile':profile,'endpoints':endpoints},separators=(',',':'))+'\n');guest.stdin.flush()
 ready=receive(guest_messages,180);assert ready['phase']=='ready'
 result['http_phases'].append({'phase':'ready',**ready['safe']});save();print(json.dumps({'profile':profile,'http':'ready',**ready['safe']}),flush=True)
 payloads=ready['endpoints']
 for label in ('a','b'):assert payloads[label]['private_key']==private[label]
 created=op._run_process(base+['set -eu; umask 077; install -d -m 0700 '+shlex.quote(remote_root)],timeout=20);assert created.returncode==0
 copied=True
 transfer=op._run_process(op._scp_base(scp,ssh,config,known)+[str(binary),'shrek:'+remote_binary],timeout=180);assert transfer.returncode==0
 checked=op._run_process(base+['set -eu; chmod 0700 '+shlex.quote(remote_binary)+'; sha256sum '+shlex.quote(remote_binary)+" | cut -d' ' -f1"],timeout=20)
 assert checked.returncode==0 and checked.stdout.strip()==build['binary_sha256']
 server,server_messages=start(op._ssh_base(ssh,'pokrov-de',config,known)+['python3 -u -c '+shlex.quote((root/'server-two-devices.py').read_text())])
 initial={'interface':interface,**{k:baseline['interfaces'][interface][k] for k in ('config_sha256','live_static_config_sha256')},'server_sha256':baseline['files']['/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814']}
 first=send(server,server_messages,initial);assert first['phase']=='ready';result['server'].append(first);save()
 server_action('add','a');server_action('add','b')
 core_test('device_a_initial','a','accepted',payloads['a'])
 core_test('device_b_initial','b','accepted',payloads['b'])
 revoked=send(guest,guest_messages,{'action':'revoke_a'});assert revoked['phase']=='revoke_a' and revoked['status'] in (401,403) and revoked['active_materials']==0
 result['http_phases'].append(revoked);save()
 server_action('remove','a')
 core_test('device_a_after_http_revoke_and_peer_removal','a','rejected',payloads['a'])
 core_test('device_b_survives_a_revoke','b','accepted',payloads['b'])
 rotated=send(guest,guest_messages,{'action':'rotate_a'});assert rotated['phase']=='rotate_a' and rotated['endpoint']['private_key']==private['c']
 result['http_phases'].append({'phase':'rotate_a',**rotated['safe']});save()
 payloads['c']=rotated['endpoint']
 server_action('add','c')
 core_test('device_a_reauthenticated_new_key','c','accepted',payloads['c'])
 core_test('old_a_key_still_denied','a','rejected',payloads['a'])
 core_test('device_b_survives_a_rotation','b','accepted',payloads['b'])
 done=send(guest,guest_messages,{'action':'finish'});assert done['phase']=='finished'
 result['http_phases'].append({'phase':'finished','report':done['safe']})
 guest.stdin.close();result['guest_exit_code']=guest.wait(timeout=20);assert result['guest_exit_code']==0
 result['result']='PASS_BOUNDED_HTTP_AND_TWO_DEVICE_PEER_LIFECYCLE'
except BaseException as exc:
 result['result']='FAILED_HTTP_OR_INTEROP'
 result['error_type']=type(exc).__name__
 raise
finally:
 if server is not None:
  try:
   if server.poll() is None:
    server.stdin.write('{"action":"finish"}\n');server.stdin.flush()
   cleanup=receive(server_messages);result['server'].append(cleanup)
   result['server_cleanup_verified']=cleanup.get('phase')=='cleanup' and cleanup.get('passed') is True
   server.stdin.close();result['server_exit_code']=server.wait(timeout=25)
  except Exception:
   result['server_cleanup_verified']=False
   try:server.stdin.close()
   except Exception:pass
 if guest is not None and guest.poll() is None:
  guest.stdin.close()
  try:result['guest_exit_code']=guest.wait(timeout=25)
  except subprocess.TimeoutExpired:result['guest_process_exit_unconfirmed']=True
 if copied:
  assert op._REMOTE_ROOT_PATTERN.fullmatch(remote_root)
  cleaned=op._run_process(base+['set -eu; rm -rf -- '+shlex.quote(remote_root)+'; test ! -e '+shlex.quote(remote_root)],timeout=25)
  result['pi_temporary_state_removed']=cleaned.returncode==0
 if server is not None and (not result.get('server_cleanup_verified') or result.get('server_exit_code')!=0):result['result']='FAILED_SERVER_CLEANUP'
 try:
  vm=paramiko.SSHClient();vm.load_host_keys(str(lab/'known_hosts'))
  vm.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
  with vm.open_sftp() as f:f.get(remote+'/http-'+profile+'-result-v2.json',str(root/('http-'+profile+'-result-v2.json')))
  vm.close()
 except Exception:result['guest_report_collection_failed']=True
 save()
assert result['result']=='PASS_BOUNDED_HTTP_AND_TWO_DEVICE_PEER_LIFECYCLE'
assert result.get('server_cleanup_verified') and result.get('pi_temporary_state_removed') and not result.get('guest_report_collection_failed')
print(json.dumps({'profile':profile,'result':result['result'],'server_cleanup_verified':True,'pi_temporary_state_removed':True}),flush=True)
