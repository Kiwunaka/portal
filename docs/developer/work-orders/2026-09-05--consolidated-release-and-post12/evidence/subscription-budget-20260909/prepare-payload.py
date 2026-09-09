"""Bind the support integration to the rehearsed backend with explicit deltas."""
import ast,hashlib,json,subprocess,sys
from pathlib import Path

root=Path('E:/r12-subscription-budget-20260909');out=Path(__file__).resolve().parent
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
expected_tree='d987840a039d91c0db0cfa4f2fe0e1ccf94f059d'
assert subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=root).decode().strip()==expected_tree
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
sys.path.insert(0,str(root/'scripts'))
from remote_deploy_brain_portal_code import iter_upload_mappings
base=json.loads(Path('E:/r12-internal-vision-integration-20260909/merged-payload.json').read_bytes())
before={r['source_path']:r for r in base['files']}
expected={'portal_bot/api_client_routes.py'}
rows=[];changed=set()
for source,target in iter_upload_mappings(root):
 relative=source.relative_to(root).as_posix();raw=source.read_bytes()
 committed=subprocess.check_output(['git','show',revision+':'+relative],cwd=root)
 assert raw.replace(b'\r\n',b'\n')==committed.replace(b'\r\n',b'\n'),relative
 digest=hashlib.sha256(committed).hexdigest()
 same=relative in before and before[relative]['git_sha256']==digest
 if not same: changed.add(relative)
 if source.suffix=='.py': ast.parse(raw)
 elif source.suffix=='.json': json.loads(raw)
 rows.append({'source_path':relative,'remote_target':target,'bytes':len(raw),'payload_sha256':hashlib.sha256(raw).hexdigest(),'git_sha256':digest,'same_rehearsed_git_bytes':same})
assert changed==expected, sorted(changed)
assert set(before).issubset({r['source_path'] for r in rows})
schema={name:next(r['git_sha256'] for r in rows if r['source_path']==name)==before[name]['git_sha256'] for name in base['schema_and_dependency_inputs_equal_deployed']}
assert all(schema.values())
def unchanged(path):
 return not subprocess.check_output(['git','diff','--name-only',base['source_revision'],revision,'--',path],cwd=root).strip()
frontends={name:unchanged(name) for name in ('marketing','webapp','adminapp','shared','copy')}
assert all(frontends.values())
report={'source_revision':revision,'source_tree':expected_tree,'base_source_revision':base['source_revision'],'rehearsed_revision':base['rehearsed_revision'],
 'payload_count':len(rows),'payload_bytes':sum(r['bytes'] for r in rows),'files':rows,'changed_runtime_files':sorted(changed),
 'schema_and_dependency_inputs_equal_deployed':schema,'frontend_inputs_unchanged_from_local_quality':frontends,
 'current_local_quality_15_step_reexecuted':False,'new_candidate_created':False,'production_code_deployed':False,
 'backup_retain_count':50,'normalization':'CRLF_TO_LF_ONLY'}
target=out/sys.argv[1];assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'}))
