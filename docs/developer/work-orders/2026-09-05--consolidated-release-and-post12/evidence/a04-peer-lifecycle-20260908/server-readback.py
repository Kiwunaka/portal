import hashlib
import json
import subprocess
import sys
from pathlib import Path

REMOTE = r'''
import datetime, hashlib, json, os, pathlib, subprocess
def run(*args):
    return subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=15)
def sha(data): return hashlib.sha256(data).hexdigest()
binary = '/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814'
paths = [binary, '/usr/local/bin/awg', '/usr/local/bin/awg-quick',
         '/etc/systemd/system/pokrov-awg-lab@.service']
result = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'deployment_kind':'host_native_userspace', 'container_image_digest':None,
          'files':{p:sha(pathlib.Path(p).read_bytes()) for p in paths},
          'kernel':os.uname().release, 'interfaces':{}}
for interface in ['pokrovawg2','pokrovawg31']:
    unit = 'pokrov-awg-lab@'+interface+'.service'
    live = run('/usr/local/bin/awg','showconf',interface)
    transfer = [v.split() for v in run('/usr/local/bin/awg','show',interface,'transfer').decode().splitlines()]
    handshakes = {v.split()[0]:int(v.split()[1]) for v in run('/usr/local/bin/awg','show',interface,'latest-handshakes').decode().splitlines()}
    processes=[]
    for proc in pathlib.Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try:
            exe=os.readlink(proc/'exe')
            if exe!=binary: continue
            argv=(proc/'cmdline').read_bytes().split(b'\0')
            if interface.encode() not in argv: continue
            processes.append({'pid':int(proc.name),'exe_sha256':sha((proc/'exe').read_bytes())})
        except (OSError,FileNotFoundError,PermissionError): continue
    conf=pathlib.Path('/etc/amnezia/amneziawg/'+interface+'.conf')
    item={'unit_active':run('systemctl','is-active',unit).decode().strip(),
          'config_sha256':sha(conf.read_bytes()),'live_config_sha256':sha(live),
          'live_static_config_sha256':sha(b'\n'.join(line for line in live.splitlines() if line.split(b'=',1)[0].strip()!=b'Endpoint')),
          'processes':processes,
          'peers':[{'public_key_sha256':sha(v[0].encode()),'rx_bytes':int(v[1]),'tx_bytes':int(v[2]),'latest_handshake_unix':handshakes[v[0]]} for v in transfer]}
    dropin=pathlib.Path('/etc/systemd/system/'+unit+'.d/variant.conf')
    if dropin.exists():item['variant_dropin_sha256']=sha(dropin.read_bytes())
    result['interfaces'][interface]=item
result['raw_material_returned']=False
print(json.dumps(result,sort_keys=True))
'''

path = Path(sys.argv[1])
if path.exists(): raise SystemExit('Preserve existing evidence')
result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',
                         'pokrov-de','python3 -'],input=REMOTE.encode(),
                        capture_output=True,timeout=60)
if result.returncode: raise SystemExit('Server readback failed; raw output withheld')
data=json.loads(result.stdout)
assert data['raw_material_returned'] is False
for item in data['interfaces'].values():
    assert item['unit_active']=='active' and len(item['peers'])==1
    assert len(item['processes'])==1
    assert item['processes'][0]['exe_sha256']==data['files']['/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814']
path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data,indent=2))
