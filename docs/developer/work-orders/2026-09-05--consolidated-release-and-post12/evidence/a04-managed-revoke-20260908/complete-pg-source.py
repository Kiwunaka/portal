import hashlib,json,tarfile,subprocess
from pathlib import Path
import paramiko
root=Path(__file__).parent
platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
lab=Path('E:/r12-b08-linux-lab');remote='/opt/r12/a04-managed-revocation-20260908'
doc=json.loads((root/'source-manifest.json').read_text())
present={x['path'] for x in doc['files']}
names=subprocess.check_output(['git','ls-files','portal_bot'],cwd=platform,text=True).splitlines()
names=[n for n in names if n not in present and '/tests/' not in n and Path(n).suffix in ('.py','.json','.txt')]
with tarfile.open(root/'source-additional.tar','w') as tar:
    for name in names:
        raw=(platform/name).read_bytes()
        doc['files'].append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        tar.add(platform/name,arcname='source/'+name,recursive=False)
doc['additional_archive_sha256']=hashlib.sha256((root/'source-additional.tar').read_bytes()).hexdigest()
(root/'source-manifest-v2.json').write_bytes((json.dumps(doc,indent=2)+'\n').encode())
guest=(root/'guest-pg-race.py').read_text()
guest=guest.replace("'source-manifest.json'","'source-manifest-v2.json'").replace("'pg-result.json'","'pg-result-v2.json'")
start=guest.index("assert check.returncode==0 and check.stdout.strip()=='0'")
end=guest.index('import models',start)
guest=guest[:start]+'''assert check.returncode==0 and check.stdout.strip()=='1','Expected retained empty fixture database'
empty=subprocess.run(['runuser','-u','postgres','--','psql','-At','-d',DATABASE,'-c',"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"],capture_output=True,text=True)
assert empty.returncode==0 and empty.stdout.strip()=='0','Refuse nonempty fixture database'
'''+guest[end:]
(root/'guest-pg-race-v2.py').write_bytes(guest.encode())
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
    with s.open_sftp() as f:
        for name in ('source-additional.tar','source-manifest-v2.json','guest-pg-race-v2.py'):
            f.put(str(root/name),remote+'/'+name)
    i,o,e=s.exec_command('tar -xf '+remote+'/source-additional.tar -C '+remote,timeout=30)
    assert o.channel.recv_exit_status()==0
finally:s.close()
print(json.dumps({'additional_files':len(names),'total_source_files':len(doc['files'])}))
