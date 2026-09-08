import base64,datetime,hashlib,json,os,queue,re,shlex,subprocess,sys,threading,time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,PublicFormat,NoEncryption
sys.path.insert(0,'C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/scripts')
import remote_run_owned_awg_core_interop as op
from node_access import connect_node

root=Path(__file__).parent
profile=sys.argv[1]
assert profile in ('awg2_lab','awg31_lab')
result_path=root/(profile+'-lifecycle.json')
assert not result_path.exists(),'Preserve existing evidence'
build=json.loads((root/'build.json').read_text())
baseline=json.loads((root/'server-before.json').read_text())
interface={'awg2_lab':'pokrovawg2','awg31_lab':'pokrovawg31'}[profile]
address={'awg2_lab':'10.203.20.250/32','awg31_lab':'10.203.31.250/32'}[profile]
ssh=Path('C:/Windows/System32/OpenSSH/ssh.exe')
scp=Path('C:/Windows/System32/OpenSSH/scp.exe')
config=Path('C:/Users/kiwun/.ssh/config')
known=Path('C:/Users/kiwun/.ssh/known_hosts')
binary=root/'owned-awg.test'
assert op._file_sha256(binary)==build['binary_sha256']
base=op._ssh_base(ssh,'shrek',config,known)
preflight=op._run_process(base+[op._RU_PI_PREFLIGHT],timeout=20)
assert preflight.returncode==0 and preflight.stdout.strip()==op._RU_PI_PREFLIGHT_MARKER
remote_root=op._remote_root()
remote_binary=remote_root+'/owned-awg.test'
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profile':profile,'scope':'isolated ephemeral server peers; managed device lifecycle not tested','build':build,'raw_material_returned':False,'server_config_files_mutated':False,'server_live_test_peers_mutated':True,'controller':[],'tests':[],'pi_preflight':True,'temporary_remote_state_removed':False,'result':'RUNNING'}
def save():result_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
save()
def key():
    k=X25519PrivateKey.generate()
    return (base64.b64encode(k.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())).decode(),base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode())
private_a,public_a=key();private_b,public_b=key()
assert public_a!=public_b
result['test_key_sha256']={k:hashlib.sha256(v.encode()).hexdigest() for k,v in [('a',public_a),('b',public_b)]}
os.environ['POKROV_SSH_KNOWN_HOSTS']=str(known)
brain,_=connect_node(code='brain',host='82.21.114.104',passwords_path=Path('C:/Users/kiwun/Documents/ai/VPN/VPN NODE SSH KEYS/PASSWORDS.txt'))
try:material=json.loads(op._load_material(brain,profile))
finally:brain.close()
material['address']=[address]
for peer in material['peers']:peer.pop('pre_shared_key',None);peer.pop('preshared_key',None)
payloads={}
for label,private in [('a',private_a),('b',private_b)]:
    item=dict(material);item['private_key']=private
    payloads[label]=json.dumps(item,sort_keys=True,separators=(',',':')).encode()
result['test_material_sha256']={k:hashlib.sha256(v).hexdigest() for k,v in payloads.items()}
controller=None
messages=queue.Queue()
created=False
def receive():
    raw=messages.get(timeout=40)
    assert raw,'Controller closed unexpectedly'
    data=json.loads(raw)
    assert data.get('phase')!='error','Controller error; raw output withheld'
    result['controller'].append(data);save()
    return data
def command(action,public=None):
    request={'action':action}
    if public is not None:request['public']=public
    controller.stdin.write(json.dumps(request)+'\n');controller.stdin.flush()
    data=receive();assert data['phase']==action
    return data
def test(label,key_label,expected):
    remote_command="set -eu; IFS= read -r POKROV_OWNED_AWG_ENDPOINT_B64; export POKROV_OWNED_AWG_ENDPOINT_B64; exec "+shlex.quote(remote_binary)+" -test.run '^TestOwnedAWGLabAuthenticatedEgress$/^mtu_1280$' -test.count=1 -test.timeout=60s -test.v"
    started=time.monotonic()
    finished=op._run_process(base+[remote_command],input_text=base64.b64encode(payloads[key_label]).decode()+'\n',timeout=80)
    output=finished.stdout+'\n'+finished.stderr
    observed=op._interop_mtu_observations(output)
    ran='=== RUN   TestOwnedAWGLabAuthenticatedEgress/mtu_1280' in output
    passed=finished.returncode==0 and '--- PASS: TestOwnedAWGLabAuthenticatedEgress/mtu_1280 ' in output and set(observed)=={'1280'}
    rejected=finished.returncode==1 and '--- FAIL: TestOwnedAWGLabAuthenticatedEgress/mtu_1280 ' in output and op._classify(output,finished.returncode)=='failed_no_outer_response' and not observed
    item={'label':label,'key':key_label,'expected':expected,'returncode':finished.returncode,'selected_subtest_observed':ran,'classification':op._classify(output,finished.returncode),'authenticated_egress_passed':passed,'no_outer_response_rejection':rejected,'oracle_passed':ran and (passed if expected=='accepted' else rejected),'elapsed_seconds':round(time.monotonic()-started,3),'mtu_observations':observed,'captured_output_sha256':hashlib.sha256(output.encode()).hexdigest()}
    result['tests'].append(item);save();print(json.dumps({'profile':profile,**item}),flush=True)
    assert item['oracle_passed'],'Unexpected peer lifecycle result; raw material withheld'
    return command('read')
try:
    create=op._run_process(base+['set -eu; umask 077; install -d -m 0700 '+shlex.quote(remote_root)],timeout=20)
    assert create.returncode==0
    created=True
    copied=op._run_process(op._scp_base(scp,ssh,config,known)+[str(binary),'shrek:'+remote_binary],timeout=180)
    assert copied.returncode==0
    verified=op._run_process(base+['set -eu; chmod 0700 '+shlex.quote(remote_binary)+'; sha256sum '+shlex.quote(remote_binary)+" | cut -d' ' -f1"],timeout=30)
    assert verified.returncode==0 and verified.stdout.strip()==build['binary_sha256']
    controller_code=(root/'server-controller.py').read_text(encoding='utf-8')
    controller=subprocess.Popen(op._ssh_base(ssh,'pokrov-de',config,known)+['python3 -u -c '+shlex.quote(controller_code)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf-8')
    def reader():
        for line in controller.stdout:messages.put(line)
        messages.put('')
    threading.Thread(target=reader,daemon=True).start()
    initial={'interface':interface,**{k:baseline['interfaces'][interface][k] for k in ('config_sha256','live_static_config_sha256')},'server_sha256':baseline['files']['/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814']}
    controller.stdin.write(json.dumps(initial)+'\n');controller.stdin.flush()
    assert receive()['phase']=='ready'
    command('add',public_a)
    first=test('key_a_provisioned','a','accepted')
    assert len(first['test_peers'])==1 and first['test_peers'][0]['rx_bytes']>0 and first['test_peers'][0]['tx_bytes']>0 and first['test_peers'][0]['handshake_unix']>0
    command('remove',public_a)
    test('key_a_revoked','a','rejected')
    command('add',public_b)
    second=test('key_b_replacement','b','accepted')
    assert len(second['test_peers'])==1 and second['test_peers'][0]['rx_bytes']>0 and second['test_peers'][0]['tx_bytes']>0 and second['test_peers'][0]['handshake_unix']>0
    test('key_a_stale_after_rotation','a','rejected')
    test('key_b_still_accepted','b','accepted')
    result['result']='PASS_BOUNDED_SERVER_PEER_LIFECYCLE'
finally:
    if controller is not None:
        try:
            if controller.poll() is None:
                controller.stdin.write(json.dumps({'action':'finish'})+'\n');controller.stdin.flush()
            cleanup=receive()
            result['server_cleanup_verified']=cleanup.get('phase')=='cleanup' and cleanup.get('passed') is True
            controller.stdin.close()
            result['controller_exit_code']=controller.wait(timeout=30)
        except Exception:
            result['server_cleanup_verified']=False
            # EOF triggers the server-side finally; independent 20-minute deadline also remains.
            try:controller.stdin.close()
            except Exception:pass
    if created:
        assert op._REMOTE_ROOT_PATTERN.fullmatch(remote_root)
        removed=op._run_process(base+['set -eu; rm -rf -- '+shlex.quote(remote_root)+'; test ! -e '+shlex.quote(remote_root)],timeout=30)
        result['temporary_remote_state_removed']=removed.returncode==0
    if not result.get('server_cleanup_verified') or not result['temporary_remote_state_removed'] or result.get('controller_exit_code')!=0:result['result']='FAILED_CLEANUP'
    save()
assert result['result']=='PASS_BOUNDED_SERVER_PEER_LIFECYCLE'
print(json.dumps({'profile':profile,'result':result['result'],'server_cleanup_verified':True,'temporary_remote_state_removed':True}),flush=True)
