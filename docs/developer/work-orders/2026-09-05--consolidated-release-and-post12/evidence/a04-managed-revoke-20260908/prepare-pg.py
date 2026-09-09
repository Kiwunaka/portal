import ast,hashlib,json,tarfile,subprocess
from pathlib import Path
import paramiko
root=Path(__file__).parent
platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
lab=Path('E:/r12-b08-linux-lab')
remote='/opt/r12/a04-managed-revocation-20260908'
archive=root/'source.tar'
assert not archive.exists(),'Preserve source archive'
names=subprocess.check_output(['git','ls-files','portal_bot','shared'],cwd=platform,text=True).splitlines()
names=[n for n in names if Path(n).suffix in ('.py','.json','.txt') and (n.startswith('shared/') or '/' not in n[len('portal_bot/'):])]
inventory=[]
with tarfile.open(archive,'w') as tar:
    for name in names:
        path=platform/name
        raw=path.read_bytes()
        inventory.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        tar.add(path,arcname='source/'+name,recursive=False)
endpoints={}
for profile in ('awg2','awg31','hy2'):
    path=platform/f'tests/test_{profile}_lab_service.py'
    source=path.read_text(encoding='utf-8')
    node=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='_endpoint')
    namespace={'AWG31_CONTRACT_ID':'pokrov.awg31.endpoint.v1'}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    endpoints[profile]=namespace['_endpoint']()
doc={'source_parent':subprocess.check_output(['git','rev-parse','HEAD'],cwd=platform,text=True).strip(),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':inventory}
(root/'source-manifest.json').write_bytes((json.dumps(doc,indent=2)+'\n').encode())
(root/'synthetic-endpoints.json').write_bytes((json.dumps(endpoints,indent=2)+'\n').encode())
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
    i,o,e=s.exec_command('test ! -e '+remote+' && install -d -m 0700 '+remote,timeout=20)
    assert o.channel.recv_exit_status()==0,'Preserve existing guest directory'
    f=s.open_sftp()
    for name in ('source.tar','source-manifest.json','synthetic-endpoints.json','guest-pg-race.py'):
        f.put(str(root/name),remote+'/'+name)
    f.close()
    i,o,e=s.exec_command('tar -xf '+remote+'/source.tar -C '+remote,timeout=60)
    assert o.channel.recv_exit_status()==0,'Guest extraction failed'
finally:s.close()
print(json.dumps({'source_files':len(inventory),'archive_sha256':doc['archive_sha256'],'guest_root':remote,'raw_material':'synthetic fixture only'}))
