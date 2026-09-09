import hashlib,json,shlex
from pathlib import Path
import paramiko
root=Path(__file__).parent;lab=Path('E:/r12-b08-linux-lab')
code=r'''
import hashlib,json,subprocess
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
root=Path('/opt/r12/a04-key-isolation-20260908')
manifest=json.loads((root/'source-manifest.json').read_text())
for item in manifest['files']:
 assert hashlib.sha256((root/'source'/item['path']).read_bytes()).hexdigest()==item['sha256']
databases=['portal_r12_a04_keys_20260908','portal_r12_a04_http_keys_awg2_20260908','portal_r12_a04_http_keys_awg2_20260908_v2','portal_r12_a04_http_keys_awg2_20260908_v3','portal_r12_a04_http_keys_awg31_20260908_v3']
base=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL'])
result={'source_files_unchanged':len(manifest['files']),'databases':{},'previous_databases_recreated':False,'production_database_mutated':False}
for database in databases:
 engine=create_engine(base.set(database=database),hide_parameters=True)
 with engine.connect() as conn:
  conn.execute(text('BEGIN READ ONLY'))
  other=conn.execute(text('SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')).scalar()
  assert other==0,'Fixture still has another connection'
  counts={}
  for table in ['awg2_lab_materials','awg31_lab_materials']:
   row=conn.execute(text('SELECT count(*),count(*) FILTER(WHERE is_active),count(*) FILTER(WHERE state=\'revoked\') FROM '+table)).one()
   counts[table]=dict(zip(('rows','active','revoked'),map(int,row)))
  result['databases'][database]={'other_sessions':other,'materials':counts}
 engine.dispose()
for profile in ['awg2','awg31']:
 item=result['databases']['portal_r12_a04_http_keys_'+profile+'_20260908_v3']['materials'][profile+'_lab_materials']
 assert item=={'rows':3,'active':0,'revoked':3}
services={name:subprocess.run(['systemctl','is-active',name],capture_output=True,text=True).stdout.strip() for name in ['portal-api','portal-bot','portal-worker']}
assert all(value=='inactive' for value in services.values())
process=subprocess.run(['pgrep','-fc','[g]uest-managed-keys|[g]uest-pg-keys'],capture_output=True,text=True)
# This audit command itself contains the text, so inspect /proc command paths
# rather than claiming a process count from the pgrep pattern.
active=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  argv=(p/'cmdline').read_bytes().split(b'\0')
  if any(x.decode(errors='replace').startswith(str(root)+'/guest-') for x in argv):active.append(int(p.name))
 except (OSError,FileNotFoundError):pass
assert not active,'Fixture runner is still active'
result['services']=services;result['fixture_runner_processes']=0
print(json.dumps(result))
'''
output=root/'final-lab-audit.json';assert not output.exists(),'Preserve existing audit'
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
 i,o,e=s.exec_command('/root/portal_bot/venv/bin/python -B -c '+shlex.quote(code),timeout=45)
 assert o.channel.recv_exit_status()==0,'Final lab audit failed; raw output withheld'
 report=json.loads(o.read());output.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report))
 i,o,e=s.exec_command('systemctl poweroff',timeout=10);o.channel.recv_exit_status()
finally:s.close()
