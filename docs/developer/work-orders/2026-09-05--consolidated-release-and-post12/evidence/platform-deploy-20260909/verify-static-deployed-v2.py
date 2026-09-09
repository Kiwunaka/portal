import hashlib,json,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path

out=Path(__file__).resolve().parent
expected=json.loads((out/'static-payload.json').read_text())
remote=r'''
import hashlib,json,subprocess
from pathlib import Path
root=Path('/var/www/portal');release=root/'releases/20260909045925'
files=[];pointers={}
for surface in ('marketing','webapp','adminapp'):
 base=root/surface;pointers[surface]=str(base.resolve())
 assert base.resolve()==release/surface
 for path in sorted(base.rglob('*')):
  if path.is_file():
   raw=path.read_bytes();files.append({'surface':surface,'path':path.relative_to(base).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
assert (root/'adminapp.rollback').resolve()==root/'releases/20260819120323/adminapp'
print(json.dumps({'files':files,'pointers':pointers,'admin_rollback':str((root/'adminapp.rollback').resolve()),'caddy_state':subprocess.check_output(['systemctl','is-active','caddy'],text=True).strip()}))
'''
proc=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','python3 -'],input=remote,text=True,capture_output=True,check=True)
runtime=json.loads(proc.stdout)
assert runtime['files']==expected['files'] and runtime['caddy_state']=='active'
checks=[]
for url,surface,relative in [
 ('https://pokrov.space/','marketing','index.html'),
 ('https://pokrov.space/checkout/','marketing','checkout/index.html'),
 ('https://app.pokrov.space/','webapp','index.html'),
 ('https://admin.pokrov.space/','adminapp','index.html'),
 ('https://admin.pokrov.space/__build.json','adminapp','__build.json'),
 ('https://admin.pokrov.space/__routes.json','adminapp','__routes.json')]:
 with urllib.request.urlopen(url,timeout=30) as resp:
  body=resp.read();digest=hashlib.sha256(body).hexdigest()
  wanted=next(row for row in expected['files'] if row['surface']==surface and row['path']==relative)
  checks.append({'url':url,'origin':'current-origin','status':resp.status,'sha256':digest,'matches_deployed_file':digest==wanted['sha256'],'cache_control':resp.headers.get('Cache-Control'),'content_type':resp.headers.get('Content-Type')})
with urllib.request.urlopen('https://api.pokrov.space/api/health',timeout=30) as resp:
 health={'origin':'current-origin','status':resp.status,'ok':json.load(resp).get('status')=='ok'}
report={'checked_at':datetime.now(timezone.utc).isoformat(),'release':'20260909045925','frontend_revision':expected['frontend_source_revision'],'backend_revision':expected['backend_source_revision'],'remote_file_count':len(runtime.pop('files')),'all_remote_file_hashes_match':True,**runtime,'public_checks':checks,'api_health':health,'oidc_login':'MANUAL_OWNER_TEST','status':'PASS' if all(row['matches_deployed_file'] and row['status']==200 for row in checks) and health['ok'] else 'FAIL'}
target=out/'static-deployed-verified-v2.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['status']=='PASS'
