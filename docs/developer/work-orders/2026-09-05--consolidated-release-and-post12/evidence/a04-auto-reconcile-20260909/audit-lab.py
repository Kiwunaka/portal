"""Read only the three new fixture databases, retain safe counts, then stop the owned VM."""
import hashlib,json,shlex,subprocess
from pathlib import Path
import paramiko
root=Path(__file__).parent;lab=Path('E:/r12-b08-linux-lab')
output=root/'final-lab-audit.json';assert not output.exists(),'Preserve final audit'
code=r'''
import json,subprocess
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
base=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL'])
names=['portal_r12_a04_auto_20260909_pg_v1','portal_r12_a04_auto_20260909_live_awg2_v2','portal_r12_a04_auto_20260909_live_awg31_v2']
result={'databases':{},'previous_databases_recreated':False,'production_database_mutated':False}
for name in names:
 engine=create_engine(base.set(database=name),hide_parameters=True)
 with engine.connect() as conn:
  conn.execute(text('BEGIN READ ONLY'))
  count=conn.execute(text('SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')).scalar()
  assert count==0,'Fixture still has another connection'
  materials={}
  for table in ['awg2_lab_materials','awg31_lab_materials']:
   row=conn.execute(text("SELECT count(*),count(*) FILTER(WHERE is_active),count(*) FILTER(WHERE state='revoked'),count(*) FILTER(WHERE state='rotated') FROM "+table)).one()
   materials[table]=dict(zip(('rows','active','revoked','rotated'),map(int,row)))
  result['databases'][name]={'other_sessions':count,'materials':materials}
 engine.dispose()
for name,profile in [(names[1],'awg2'),(names[2],'awg31')]:
 assert result['databases'][name]['materials'][profile+'_lab_materials']=={'rows':3,'active':0,'revoked':3,'rotated':0}
services={name:subprocess.run(['systemctl','is-active',name],capture_output=True,text=True).stdout.strip() for name in ['portal-api','portal-bot','portal-worker']}
assert all(value=='inactive' for value in services.values())
result['services']=services
print(json.dumps(result))
'''
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10,
 disabled_algorithms={'keys':['ssh-ed25519','ecdsa-sha2-nistp256','ecdsa-sha2-nistp384','ecdsa-sha2-nistp521']})
try:
 _,o,e=s.exec_command('/root/portal_bot/venv/bin/python -B -c '+shlex.quote(code),timeout=45)
 raw=o.read();assert o.channel.recv_exit_status()==0,'Final audit failed; raw output withheld'
 result=json.loads(raw)
 result['ssh_pin']={'algorithm':s.get_transport().host_key_type,'sha256':hashlib.sha256(s.get_transport().get_remote_server_key().asbytes()).hexdigest(),
                    'original_known_hosts_unchanged':True}
 output.write_bytes((json.dumps(result,indent=2)+'\n').encode())
 print(json.dumps({'databases_checked':3,'other_connections':0,'services':result['services'],'strict_ssh_algorithm':result['ssh_pin']['algorithm']}))
 _,o,e=s.exec_command('systemctl poweroff',timeout=10);o.channel.recv_exit_status()
finally:s.close()
