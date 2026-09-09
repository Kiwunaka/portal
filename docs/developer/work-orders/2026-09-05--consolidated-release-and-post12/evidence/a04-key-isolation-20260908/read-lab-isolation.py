"""Owned-lab readback. Decrypted material never leaves the Brain process."""
import json,os,shlex,sys
from pathlib import Path
sys.path.insert(0,'C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/scripts')
from node_access import connect_node

REMOTE=r'''
import base64,collections,datetime,json,os,subprocess,sys
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
pid=subprocess.check_output(['systemctl','show','portal-api','-p','MainPID','--value'],text=True).strip()
assert pid.isdigit() and int(pid)>1
with open('/proc/'+pid+'/environ','rb') as f:
 for pair in f.read().split(b'\0'):
  if b'=' in pair:
   k,v=pair.split(b'=',1);os.environ[k.decode()]=v.decode()
os.chdir('/root/portal_bot');sys.path.insert(0,'/root/portal_bot')
from db import SessionLocal
from models import Awg2LabMaterial,Awg31LabMaterial
from awg2_lab_service import _decrypt_endpoint as decrypt2
from awg31_lab_service import _decrypt_endpoint as decrypt31
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'READ_ONLY','origin':'brain-origin','raw_material_returned':False,'profiles':{}}
with SessionLocal() as s:
 s.execute(__import__('sqlalchemy').text('SET TRANSACTION READ ONLY'))
 for name,model,decrypt in [('awg2_lab',Awg2LabMaterial,decrypt2),('awg31_lab',Awg31LabMaterial,decrypt31)]:
  rows=s.query(model).order_by(model.id).all();groups=collections.defaultdict(set);active=collections.defaultdict(set)
  for row in rows:
   endpoint=decrypt(row.endpoint_ciphertext)
   public=X25519PrivateKey.from_private_bytes(base64.b64decode(endpoint['private_key'],validate=True)).public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
   identity=(int(row.tg_id),str(row.install_id));groups[public].add(identity)
   if row.is_active and row.state=='ready':active[public].add(identity)
  report['profiles'][name]={'material_rows':len(rows),'distinct_device_bindings':len(set().union(*groups.values())) if groups else 0,'distinct_client_public_keys':len(groups),'keys_shared_across_device_bindings':sum(len(x)>1 for x in groups.values()),'active_material_rows':sum(bool(x.is_active and x.state=='ready') for x in rows),'active_keys_shared_across_device_bindings':sum(len(x)>1 for x in active.values()),'largest_shared_device_group':max(map(len,groups.values()),default=0)}
 s.rollback()
print(json.dumps(report))
'''
root=Path(__file__).parent;output=root/'brain-key-isolation-before.json'
assert not output.exists(),'Preserve existing readback'
os.environ['POKROV_SSH_KNOWN_HOSTS']='C:/Users/kiwun/.ssh/known_hosts'
s,_=connect_node(code='brain',host='82.21.114.104',passwords_path=Path('C:/Users/kiwun/Documents/ai/VPN/VPN NODE SSH KEYS/PASSWORDS.txt'))
try:
 i,o,e=s.exec_command('/root/portal_bot/venv/bin/python -B -c '+shlex.quote(REMOTE),timeout=45)
 code=o.channel.recv_exit_status();raw=o.read()
 assert code==0,'Owned lab readback failed; raw output withheld'
 report=json.loads(raw);assert report['raw_material_returned'] is False
 output.write_bytes((json.dumps(report,indent=2)+'\n').encode())
 print(json.dumps(report))
finally:s.close()
