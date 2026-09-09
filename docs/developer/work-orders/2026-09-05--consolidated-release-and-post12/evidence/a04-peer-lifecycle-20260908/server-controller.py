"""Disposable, stdin-controlled live test peers; existing peers never mutated."""
import base64,datetime,hashlib,ipaddress,json,pathlib,signal,subprocess,sys

AWG='/usr/local/bin/awg'
def run(*args):
    return subprocess.check_output(args,stderr=subprocess.DEVNULL,timeout=15)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def live_static(interface):
    return b'\n'.join(x for x in run(AWG,'showconf',interface).splitlines() if x.split(b'=',1)[0].strip()!=b'Endpoint')
def emit(data):
    print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**data}),flush=True)
def deadline(*unused):raise TimeoutError('bounded lab deadline')
def main():
    signal.signal(signal.SIGALRM,deadline)
    signal.signal(signal.SIGTERM,deadline)
    signal.alarm(1200)
    initial=json.loads(sys.stdin.readline())
    interface=initial['interface']
    assert interface in ('pokrovawg2','pokrovawg31')
    address={'pokrovawg2':'10.203.20.250/32','pokrovawg31':'10.203.31.250/32'}[interface]
    conf=pathlib.Path('/etc/amnezia/amneziawg/'+interface+'.conf')
    original_conf=sha(conf.read_bytes())
    original_live=live_static(interface)
    original_peers=set(run(AWG,'show',interface,'peers').decode().split())
    assert len(original_peers)==1
    assert original_conf==initial['config_sha256']
    assert sha(original_live)==initial['live_static_config_sha256']
    for line in run(AWG,'show',interface,'allowed-ips').decode().splitlines():
        for net in line.split()[1:]:
            for part in net.split(','):
                if part:assert not ipaddress.ip_network(address).overlaps(ipaddress.ip_network(part))
    assert sha(run('cat','/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814'))==initial['server_sha256']
    touched=set()
    def state():
        rows=[x.split() for x in run(AWG,'show',interface,'transfer').decode().splitlines()]
        handshakes=dict(x.split() for x in run(AWG,'show',interface,'latest-handshakes').decode().splitlines())
        peers={x[0] for x in rows}
        assert original_peers.issubset(peers)
        assert peers.issubset(original_peers|touched)
        return {'peer_count':len(peers),'original_peer_present':True,'test_peers':[{'public_key_sha256':sha(x[0].encode()),'rx_bytes':int(x[1]),'tx_bytes':int(x[2]),'handshake_unix':int(handshakes[x[0]])} for x in rows if x[0] in touched]}
    try:
        emit({'phase':'ready','interface':interface,**state()})
        for line in sys.stdin:
            request=json.loads(line)
            action=request['action']
            if action=='finish':break
            assert action in ('add','remove','read')
            if action!='read':
                public=request['public']
                assert len(base64.b64decode(public,validate=True))==32
                assert public not in original_peers
                if action=='add':
                    # No address takeover from any active peer, including earlier test keys.
                    assert len(state()['test_peers'])==0
                    touched.add(public)
                    run(AWG,'set',interface,'peer',public,'allowed-ips',address)
                else:
                    assert public in touched
                    run(AWG,'set',interface,'peer',public,'remove')
            emit({'phase':action,**state()})
    finally:
        cleanup_ok=True
        for public in touched:
            try:run(AWG,'set',interface,'peer',public,'remove')
            except Exception:cleanup_ok=False
        conf_equal=sha(conf.read_bytes())==original_conf
        live_equal=live_static(interface)==original_live
        peers_equal=set(run(AWG,'show',interface,'peers').decode().split())==original_peers
        emit({'phase':'cleanup','removed_test_peers':cleanup_ok,'saved_configuration_unchanged':conf_equal,'original_live_static_configuration_restored':live_equal,'original_peers_restored':peers_equal,'passed':all((cleanup_ok,conf_equal,live_equal,peers_equal))})
        assert all((cleanup_ok,conf_equal,live_equal,peers_equal))
if __name__=='__main__':
    try:main()
    except BaseException:
        emit({'phase':'error','reason':'controller failed; raw output withheld'})
        sys.exit(1)
