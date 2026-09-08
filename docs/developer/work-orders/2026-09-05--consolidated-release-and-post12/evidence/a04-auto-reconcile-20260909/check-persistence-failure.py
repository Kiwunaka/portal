"""Exercise the disk-before-live failure path on an isolated Linux fixture."""
import hashlib,json,shlex,subprocess
from pathlib import Path
root=Path(__file__).parent
output=root/'persistence-failure.json';assert not output.exists()
helper=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/portal_bot/awg_peer_remove.py').read_text()
code=r'''
import base64,hashlib,json,pathlib,sys,tempfile
source=sys.stdin.read();scope={'__name__':'fixture_helper'};exec(source,scope)
keys=[base64.b64encode(bytes([n])*32).decode() for n in (1,2,3)]
a,b,server=keys
with tempfile.TemporaryDirectory(prefix='pokrov-a04-helper-') as raw_root:
 root=pathlib.Path(raw_root);scope['CONFIG_ROOT']=root
 config=root/'r12fixture.conf'
 header=b'[Interface]\nPrivateKey = synthetic-not-a-real-key\nListenPort = 12345\n'
 peer_a=('[Peer]\nPublicKey = '+a+'\nAllowedIPs = 10.0.0.2/32\n').encode()
 peer_b=('[Peer]\nPublicKey = '+b+'\nAllowedIPs = 10.0.0.3/32\n').encode()
 original=header+peer_a+peer_b;config.write_bytes(original);config.chmod(0o600)
 live={a,b};failed=[False]
 def fake_awg(*args):
  if args==('show','r12fixture','public-key'):return server
  if args==('show','r12fixture','peers'):return '\n'.join(sorted(live))
  assert args==('set','r12fixture','peer',a,'remove')
  if not failed[0]:
   failed[0]=True;raise scope['PeerRemovalError']('awg_command_failed')
  live.remove(a);return ''
 scope['_awg']=fake_awg
 request={'interface':'r12fixture','keys':[a],'server_public_key_sha256':hashlib.sha256(base64.b64decode(server)).hexdigest()}
 try:scope['remove_peers'](request)
 except scope['PeerRemovalError'] as error:assert str(error)=='awg_command_failed'
 else:raise AssertionError('Expected live command failure')
 assert config.read_bytes()==header+peer_b and live=={a,b}
 backups=list((root/'.pokrov-revocations').glob('*.conf'))
 assert len(backups)==1 and backups[0].read_bytes()==original
 assert backups[0].stat().st_mode&0o777==0o600
 retry=scope['remove_peers'](request)
 assert retry['disk_removed']==0 and retry['live_removed']==1 and live=={b}
 assert config.read_bytes()==header+peer_b
 repeat=scope['remove_peers'](request)
 assert repeat['disk_removed']==repeat['live_removed']==0
 try:scope['remove_peers']({**request,'keys':[b],'server_public_key_sha256':'0'*64})
 except scope['PeerRemovalError'] as error:assert str(error)=='server_identity_mismatch'
 else:raise AssertionError('Expected identity rejection')
 assert config.read_bytes()==header+peer_b and live=={b}
result={'result':'PASS_PERSISTENCE_FAILURE_RETRY','scope':'isolated temporary config and synthetic AWG command fixture on owned Linux',
 'disk_denial_survives_live_failure':True,'retry_removes_live_peer':True,'unrelated_peer_preserved':True,
 'root_only_preimage_preserved':True,'repeat_idempotent':True,'wrong_server_identity_rejected':True,
 'temporary_directory_removed':not root.exists(),'source_helper_sha256':hashlib.sha256(source.encode()).hexdigest()}
print(json.dumps(result))
'''
args=['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10',
      'pokrov-de','python3 -c '+shlex.quote(code)]
run=subprocess.run(args,input=helper,text=True,capture_output=True,timeout=45)
if run.returncode==0:
 result=json.loads(run.stdout)
 assert result['temporary_directory_removed']
else:
 result={'result':'FAIL_PERSISTENCE_FIXTURE','exit_code':run.returncode,'stderr_sha256':hashlib.sha256(run.stderr.encode()).hexdigest()}
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
raise SystemExit(run.returncode)
