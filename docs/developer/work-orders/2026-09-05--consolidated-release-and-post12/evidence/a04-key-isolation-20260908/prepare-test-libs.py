"""Reuse exact installed pure-Python test dependencies in the isolated VM path."""
import hashlib,importlib.metadata,json,zipfile
from pathlib import Path
import paramiko
root=Path(__file__).parent;lab=Path('E:/r12-b08-linux-lab')
archive=root/'test-libs.zip';assert not archive.exists()
names=['httpx2','httpcore2','anyio','idna','truststore','h11','typing_extensions']
inventory=[];versions={}
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for name in names:
  dist=importlib.metadata.distribution(name);versions[name]=dist.version
  for item in dist.files or []:
   path=Path(str(item))
   if '..' in path.parts or path.is_absolute() or '__pycache__' in path.parts or path.name in ('direct_url.json','RECORD'):continue
   if path.suffix in ('.pyc','.pyd','.dll','.exe'):continue
   full=Path(dist.locate_file(item));raw=full.read_bytes();member=path.as_posix()
   z.writestr(member,raw);inventory.append({'path':member,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
report={'versions':versions,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':inventory,'scope':'fixture-only; system venv unchanged'}
(root/'test-libs-manifest.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
remote='/opt/r12/a04-key-isolation-20260908'
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
 with s.open_sftp() as f:f.put(str(archive),remote+'/test-libs.zip')
 command='test ! -e '+remote+'/test-libs && install -d -m 0700 '+remote+'/test-libs && /root/portal_bot/venv/bin/python -m zipfile -e '+remote+'/test-libs.zip '+remote+'/test-libs'
 i,o,e=s.exec_command(command,timeout=30);assert o.channel.recv_exit_status()==0,'Fixture library preparation failed'
finally:s.close()
print(json.dumps({'versions':versions,'files':len(inventory),'archive_sha256':report['archive_sha256']}))
