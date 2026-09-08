"""Control only two ephemeral client slots, preserving every original peer."""
import base64,datetime,hashlib,ipaddress,json,pathlib,signal,subprocess,sys
AWG='/usr/local/bin/awg'
def run(*args):return subprocess.check_output(args,stderr=subprocess.DEVNULL,timeout=15)
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
 original_conf=sha(conf.read_bytes());original_static=static(interface)
 original_peers=set(run(AWG,'show',interface,'peers').decode().split())
 assert len(original_peers)==1 and original_conf==initial['config_sha256']
 assert sha(original_static)==initial['live_static_config_sha256']
 assert sha(run('cat','/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814'))==initial['server_sha256']
 touched=set()
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
   assert action in ('add','remove','read')
   if action!='read':
    public=request['public'];assert len(base64.b64decode(public,validate=True))==32 and public not in original_peers
    if action=='add':
     address=request['address'];assert address in addresses
     for row in run(AWG,'show',interface,'allowed-ips').decode().splitlines():
      for item in row.split()[1:]:
       for net in item.split(','):
        if net:assert not ipaddress.ip_network(address).overlaps(ipaddress.ip_network(net)),'Address already occupied'
     touched.add(public);run(AWG,'set',interface,'peer',public,'allowed-ips',address)
    else:
     assert public in touched;run(AWG,'set',interface,'peer',public,'remove')
   emit({'phase':action,**state()})
 finally:
  cleanup=True
  for public in touched:
   try:run(AWG,'set',interface,'peer',public,'remove')
   except Exception:cleanup=False
  config_equal=sha(conf.read_bytes())==original_conf
  live_equal=static(interface)==original_static
  peers_equal=set(run(AWG,'show',interface,'peers').decode().split())==original_peers
  emit({'phase':'cleanup','removed_test_peers':cleanup,'saved_configuration_unchanged':config_equal,'original_live_static_configuration_restored':live_equal,'original_peers_restored':peers_equal,'passed':all((cleanup,config_equal,live_equal,peers_equal))})
  assert all((cleanup,config_equal,live_equal,peers_equal))
try:main()
except BaseException:
 emit({'phase':'error','reason':'controller failed; raw output withheld'});sys.exit(1)
