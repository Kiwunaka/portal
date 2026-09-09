from pathlib import Path
import hashlib,json,os,secrets,subprocess,zipfile
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
ROOT=Path('/opt/r12/integrated-compat-20260908')
INCOMING=Path('/opt/r12/integrated-input-20260908')
assert not ROOT.exists();ROOT.mkdir(mode=0o700)
manifest=json.loads((INCOMING/'source-manifests.json').read_text())
for label in ('previous','current'):
 archive=INCOMING/(label+'.zip');assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest[label]['archive_sha256']
 dest=ROOT/label;dest.mkdir()
 with zipfile.ZipFile(archive) as z:
  for item in z.infolist():
   target=(dest/item.filename).resolve();assert target.is_relative_to(dest)
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
 for e in manifest[label]['files']:assert hashlib.sha256((dest/e['path']).read_bytes()).hexdigest()==e['sha256']
 for p in (dest/'scripts').glob('*.py'):(dest/'portal_bot'/p.name).write_bytes(p.read_bytes())
(ROOT/'source-manifests.json').write_bytes((INCOMING/'source-manifests.json').read_bytes())
db='portal_b08_integrated_20260908_rehearsal'
p=subprocess.run(['runuser','-u','postgres','--','createdb','--owner=r12_linux_app','--template=portal_b08_linux_01_rehearsal',db],capture_output=True)
assert p.returncode==0,'isolated DB creation failed'
p=subprocess.run(['runuser','-u','postgres','--','psql','--set=ON_ERROR_STOP=1','-d','postgres','-c','REVOKE ALL ON DATABASE '+db+' FROM PUBLIC'],capture_output=True);assert p.returncode==0
url=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL']).set(database=db)
values={'DATABASE_URL':url.render_as_string(hide_password=False),'BOT_TOKEN':'123456789:'+secrets.token_hex(24),'WEBAPP_SESSION_SECRET':secrets.token_hex(32),'SUPPORT_AI_ENABLED':'false','COMMERCIAL_CAPACITY_AUTOMATION_ENABLED':'false','PUBLIC_API_DOMAIN':'127.0.0.1','PUBLIC_WEB_DOMAIN':'127.0.0.1','PUBLIC_CONNECT_DOMAIN':'127.0.0.1'}
fd=os.open(ROOT/'config.env',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write(''.join(k+'='+v+'\n' for k,v in values.items()))
for label,port in (('previous',18083),('current',18084)):
 unit=f'''[Unit]
Description=R12 integrated {label} real API compatibility
After=postgresql.service
[Service]
WorkingDirectory={ROOT/label/'portal_bot'}
EnvironmentFile={ROOT}/config.env
ExecStart=/root/portal_bot/venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port {port}
IPAddressDeny=any
IPAddressAllow=localhost
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
Restart=no
'''
 path=Path('/etc/systemd/system/r12-integrated-'+label+'.service');assert not path.exists();path.write_text(unit)
e=create_engine(url,hide_parameters=True)
with e.connect() as c:
 cols=[list(r) for r in c.execute(text("SELECT table_name,column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position"))]
 indexes=[list(r) for r in c.execute(text("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname"))]
e.dispose();(ROOT/'schema-before.json').write_text(json.dumps({'columns':cols,'indexes':indexes},indent=2)+'\n')
print(json.dumps({'status':'PREPARED','database':db,'previous_files':len(manifest['previous']['files']),'current_files':len(manifest['current']['files']),'network_scope':'loopback only','synthetic_data_only':True}))
