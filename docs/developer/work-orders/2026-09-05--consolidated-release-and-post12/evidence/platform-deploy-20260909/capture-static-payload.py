import hashlib,json,subprocess
from pathlib import Path

root=Path('E:/r12-promoted-platform-20260909');out=Path(__file__).resolve().parent
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()=='03920525bfc3993591a39d21e35bbe2e7e1d663d'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
payload=[]
for surface in ('marketing','webapp','adminapp'):
 base=root/surface/'out'
 for path in sorted(base.rglob('*')):
  assert not path.is_symlink()
  if path.is_file():
   raw=path.read_bytes();payload.append({'surface':surface,'path':path.relative_to(base).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
assert len(payload)==887
build=json.loads((root/'adminapp/out/__build.json').read_bytes())
assert build['frontend_commit']=='03920525bfc3993591a39d21e35bbe2e7e1d663d' and build['source_state']=='clean'
assert build['expected_api_schema']=='admin-v2.1'
report={'frontend_source_revision':build['frontend_commit'],'backend_source_revision':'7d37005e4260995ab44ec3adb14bbffa3d42738b',
 'frontend_source_inputs_identical_to_backend_commit':True,'operator_build':build,'files':payload,
 'total_files':len(payload),'total_bytes':sum(row['bytes'] for row in payload),'stage':'PREDEPLOY'}
target=out/'static-payload.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'}))
