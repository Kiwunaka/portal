import ast,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).parent
REPO=Path('E:/r12-integration-platform-20260908')
sys.path.insert(0,str(REPO/'scripts'))
from remote_deploy_brain_portal_code import iter_upload_mappings
from node_access import connect_node
def read(ref,path):return subprocess.check_output(['git','-C',str(REPO),'show',ref+':'+path])
observed=json.loads((ROOT/'deployed-runtime-verified.json').read_text())
for label in ('previous','current'):
 if (ROOT/(label+'.zip')).exists():raise SystemExit('Preserve existing source archives')
os.environ['POKROV_SSH_KNOWN_HOSTS']='C:/Users/kiwun/.ssh/known_hosts'
s,_=connect_node(code='brain',host='82.21.114.104',passwords_path=Path('C:/Users/kiwun/Documents/ai/VPN/VPN NODE SSH KEYS/PASSWORDS.txt'))
old_items=[]
try:
 f=s.open_sftp()
 for e in observed['files']:
  name=e['path'];p=Path(name)
  ref='1207b63f1574a15569594c5fdbb79e4c8dff553f' if name=='portal_bot/control_panel.py' else 'f5300053026d32826e54c02202303e1f68c65bc1'
  public=read(ref,name)
  remote='/root/portal_bot/'+p.name if p.parts[0]=='scripts' else '/root/'+name
  with f.open(remote,'rb') as handle:b=handle.read()
  # Retain only bytes already proven equivalent to public Git source; no raw config/data.
  assert b.replace(b'\r\n',b'\n')==public.replace(b'\r\n',b'\n'),name
  assert hashlib.sha256(b).hexdigest()==e['sha256'],name
  old_items.append((name,ref,b))
 f.close()
finally:s.close()
manifest={}
for label in ('previous','current'):
 entries=[];archive=ROOT/(label+'.zip')
 items=old_items if label=='previous' else [(src.relative_to(REPO).as_posix(),'16407b8909508c9d533e88ba24153f8fef0314ce',read('16407b8',src.relative_to(REPO).as_posix())) for src,_ in iter_upload_mappings(REPO)]
 with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
  for name,ref,b in sorted(items):
   if name.endswith('.py'):ast.parse(b)
   elif name.endswith('.json'):json.loads(b)
   z.writestr(name,b);entries.append({'path':name,'source_commit':ref,'sha256':hashlib.sha256(b).hexdigest(),'size':len(b)})
 manifest[label]={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':entries}
keys=['models.py','migrations.py','db.py','requirements.txt','account_foundation_service.py','support_account_service.py']
with zipfile.ZipFile(ROOT/'previous.zip') as a,zipfile.ZipFile(ROOT/'current.zip') as b:
 identical={n:a.read('portal_bot/'+n).replace(b'\r\n',b'\n')==b.read('portal_bot/'+n).replace(b'\r\n',b'\n') for n in keys}
assert all(identical.values());manifest['schema_inputs_identical']=identical
(ROOT/'source-manifests.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'previous_files':len(manifest['previous']['files']),'current_files':len(manifest['current']['files']),'all_previous_bytes_match_deployed':True,'schema_inputs_identical':identical}))
