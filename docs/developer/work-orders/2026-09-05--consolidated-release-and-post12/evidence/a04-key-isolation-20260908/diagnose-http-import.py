"""Only source-frame locations and installed package versions leave the guest."""
import json,shlex
from pathlib import Path
import paramiko
root=Path(__file__).parent;lab=Path('E:/r12-b08-linux-lab')
code=r'''
import importlib.metadata,json,os,secrets,sys,traceback
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
root='/opt/r12/a04-key-isolation-20260908/source'
os.chdir(root);sys.path.insert(0,root+'/portal_bot')
dsn=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL']).set(database='portal_r12_a04_http_keys_awg2_20260908')
os.environ['DATABASE_URL']=dsn.render_as_string(hide_password=False)
for name in ['WEBAPP_SESSION_SECRET','AWG2_LAB_MATERIAL_SECRET','AWG31_LAB_MATERIAL_SECRET','BOT_TOKEN']:
 os.environ[name]=secrets.token_hex(32)
os.environ.update(ADMIN_ID='9999',ADMIN_IDS='9999',PUBLIC_CHANNEL='fixture')
try:
 import api
 print(json.dumps({'import':'PASS'}))
except Exception as exc:
 frames=[{'file':f.filename.replace(root+'/',''),'line':f.lineno,'name':f.name} for f in traceback.extract_tb(exc.__traceback__)]
 print(json.dumps({'import':'FAILED','error_type':type(exc).__name__,'frames':frames[-8:]}))
'''
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
 i,o,e=s.exec_command('/root/portal_bot/venv/bin/python -B -c '+shlex.quote(code),timeout=60)
 exit_code=o.channel.recv_exit_status();raw=o.read();assert exit_code==0,'Diagnostic failed; raw output withheld'
 report=json.loads(raw);(root/'http-import-diagnostic.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report))
finally:s.close()
