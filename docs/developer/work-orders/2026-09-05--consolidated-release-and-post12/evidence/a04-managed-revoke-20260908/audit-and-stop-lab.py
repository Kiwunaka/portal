import json,shlex,time
from pathlib import Path
import paramiko
root=Path(__file__).parent;lab=Path('E:/r12-b08-linux-lab')
remote='/opt/r12/a04-managed-revocation-20260908'
code=r'''
import hashlib,json,subprocess
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
root=Path('/opt/r12/a04-managed-revocation-20260908')
manifest=json.loads((root/'source-manifest-v2.json').read_text())
for item in manifest['files']:
 raw=(root/'source'/item['path']).read_bytes()
 assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
dsn=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL']).set(database='portal_r12_a04_20260908_rehearsal')
engine=create_engine(dsn,hide_parameters=True)
with engine.connect() as conn:
 conn.execute(text('BEGIN READ ONLY'))
 counts={}
 for name in ['awg2_lab_materials','awg31_lab_materials','hy2_lab_materials']:
  row=conn.execute(text('SELECT count(*), count(*) FILTER(WHERE is_active), count(*) FILTER(WHERE state=\'rotated\'), count(*) FILTER(WHERE state=\'revoked\') FROM '+name)).one()
  counts[name]=dict(zip(('rows','active','rotated','revoked'),map(int,row)))
  assert tuple(row)==(7,0,1,6)
 sessions=conn.execute(text('SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')).scalar()
 assert sessions==0
engine.dispose()
services={name:subprocess.run(['systemctl','is-active',name],capture_output=True,text=True).stdout.strip() for name in ['portal-api','portal-bot','portal-worker']}
assert all(v=='inactive' for v in services.values())
result={'source_files_unchanged':len(manifest['files']),'material_rows':counts,'other_fixture_db_sessions':sessions,'services':services,'previous_databases_recreated':False,'production_contacted':False}
(root/'final-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
'''
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
    i,o,e=s.exec_command('/root/portal_bot/venv/bin/python -c '+shlex.quote(code),timeout=45)
    assert o.channel.recv_exit_status()==0,'Audit failed; raw output withheld'
    report=json.loads(o.read());print(json.dumps(report))
    with s.open_sftp() as f:f.get(remote+'/final-audit.json',str(root/'final-audit.json'))
    i,o,e=s.exec_command('systemctl poweroff',timeout=10)
    o.channel.recv_exit_status()
finally:s.close()
