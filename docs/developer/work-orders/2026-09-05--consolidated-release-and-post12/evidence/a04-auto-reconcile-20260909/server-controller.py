"""Persist only ephemeral lab peers and guard exact configuration restoration."""
import base64,datetime,fcntl,hashlib,ipaddress,json,os,pathlib,signal,subprocess,sys,tempfile
AWG='/usr/local/bin/awg'
def run(*args):return subprocess.check_output(args,stderr=subprocess.DEVNULL,timeout=20)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def emit(data):print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**data}),flush=True)
def static(interface):return b'\n'.join(x for x in run(AWG,'showconf',interface).splitlines() if x.split(b'=',1)[0].strip()!=b'Endpoint')
def deadline(*unused):raise TimeoutError('Lab deadline')
def main():
 signal.signal(signal.SIGALRM,deadline);signal.signal(signal.SIGTERM,deadline);signal.alarm(1200)
 initial=json.loads(sys.stdin.readline());interface=initial['interface']
 assert interface in ('pokrovawg2','pokrovawg31')
 prefix={'pokrovawg2':'10.203.20.','pokrovawg31':'10.203.31.'}[interface]
 addresses={prefix+'248/32',prefix+'249/32'}
 conf=pathlib.Path('/etc/amnezia/amneziawg/'+interface+'.conf')
 original=conf.read_bytes();original_static=static(interface)
 original_peers=set(run(AWG,'show',interface,'peers').decode().split())
 assert len(original_peers)==1 and sha(original)==initial['config_sha256']
 assert sha(original_static)==initial['live_static_config_sha256']
 assert sha(pathlib.Path('/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814').read_bytes())==initial['server_sha256']
 helper={'__name__':'fixture_helper'};exec(initial['helper_source'],helper)
 touched=set();restarts=0
 lockpath=conf.with_suffix('.pokrov-revoke.lock')
 def write(raw):
  with tempfile.NamedTemporaryFile(dir=conf.parent,prefix=interface+'.fixture.',delete=False) as handle:
   os.fchmod(handle.fileno(),0o600);handle.write(raw);handle.flush();os.fsync(handle.fileno());temp=handle.name
  os.replace(temp,conf)
 def state():
  transfer=[x.split() for x in run(AWG,'show',interface,'transfer').decode().splitlines()]
  handshakes=dict(x.split() for x in run(AWG,'show',interface,'latest-handshakes').decode().splitlines())
  peers={x[0] for x in transfer}
  assert original_peers.issubset(peers) and peers.issubset(original_peers|touched)
  return {'peer_count':len(peers),'original_peer_present':True,'test_peers':[{'public_key_sha256':sha(x[0].encode()),'rx_bytes':int(x[1]),'tx_bytes':int(x[2]),'handshake_unix':int(handshakes[x[0]])} for x in transfer if x[0] in touched]}
 try:
  emit({'phase':'ready','interface':interface,**state()})
  for line in sys.stdin:
   request=json.loads(line);action=request['action']
   if action=='finish':break
   assert action in ('add','read','restart')
   if action=='add':
    public=request['public'];address=request['address']
    assert len(base64.b64decode(public,validate=True))==32 and public not in original_peers and address in addresses
    for row in run(AWG,'show',interface,'allowed-ips').decode().splitlines():
     for item in row.split()[1:]:
      for net in item.split(','):
       if net:assert not ipaddress.ip_network(address).overlaps(ipaddress.ip_network(net)),'Address occupied'
    with open(lockpath,'a+b') as lock:
     fcntl.flock(lock,fcntl.LOCK_EX)
     raw=conf.read_bytes();stripped,_=helper['without_peers'](raw,touched)
     assert stripped==original,'Concurrent config change'
     assert raw.endswith(b'\n'),'Unexpected original format'
     touched.add(public)
     write(raw+('[Peer]\nPublicKey = '+public+'\nAllowedIPs = '+address+'\n').encode())
     run(AWG,'set',interface,'peer',public,'allowed-ips',address)
   elif action=='restart':
    run('systemctl','restart','pokrov-awg-lab@'+interface+'.service')
    assert run('systemctl','is-active','pokrov-awg-lab@'+interface+'.service').strip()==b'active'
    restarts+=1
   emit({'phase':action,'service_restarts':restarts,**state()})
 finally:
  cleanup=True
  for public in touched:
   try:run(AWG,'set',interface,'peer',public,'remove')
   except Exception:cleanup=False
  with open(lockpath,'a+b') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   raw=conf.read_bytes();stripped,_=helper['without_peers'](raw,touched)
   assert stripped==original,'Preserve concurrent config changes'
   write(original)
  config_equal=conf.read_bytes()==original
  live_equal=static(interface)==original_static
  peers_equal=set(run(AWG,'show',interface,'peers').decode().split())==original_peers
  emit({'phase':'cleanup','removed_test_peers':cleanup,'saved_configuration_restored':config_equal,
        'original_live_static_configuration_restored':live_equal,'original_peers_restored':peers_equal,
        'service_restarts':restarts,'counters_reset_by_restart':bool(restarts),'passed':all((cleanup,config_equal,live_equal,peers_equal))})
  assert all((cleanup,config_equal,live_equal,peers_equal))
try:main()
except BaseException:
 emit({'phase':'error','reason':'controller failed; raw output withheld'});sys.exit(1)
