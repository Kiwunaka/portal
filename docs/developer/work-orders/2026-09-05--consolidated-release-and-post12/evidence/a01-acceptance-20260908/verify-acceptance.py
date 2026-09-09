import ast,hashlib,json,subprocess,datetime
from pathlib import Path
root=Path('E:/r12-a01-acceptance-20260908');platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start');core=Path('E:/r12core-implementation');client=Path('E:/r12client')
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda b:hashlib.sha256(b).hexdigest()
observed=load(root/'read-scope-effective.json')
assert observed['status']=='PASS_PUBLIC_ACCESS_DENIED'
checks={}
functions={'awg2_lab_service.py':['default_awg2_lab_config','normalize_awg2_lab_config','awg2_lab_rollout_access'],'awg31_lab_service.py':['default_awg31_lab_config','normalize_awg31_lab_config','awg31_lab_rollout_access'],'network_rollout.py':['default_network_rollout_config','normalized_network_rollout_config']}
for file,names in functions.items():
 old=subprocess.check_output(['git','show','f530005:portal_bot/'+file],cwd=platform)
 assert sha(old.replace(b'\r\n',b'\n'))==observed['normalized_source_hashes'][file]
 current=(platform/'portal_bot'/file).read_bytes()
 oldast=ast.parse(old.decode('utf-8-sig'));newast=ast.parse(current.decode('utf-8-sig'))
 for name in names:
  a=next(x for x in oldast.body if isinstance(x,ast.FunctionDef) and x.name==name)
  b=next(x for x in newast.body if isinstance(x,ast.FunctionDef) and x.name==name)
  assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),(file,name)
  checks[file+':'+name]=sha(ast.dump(a,include_attributes=False).encode())
contracts={}
for name in ['awg2','awg31']:
 contract=load(core/'config'/f'{name}-capability.json');sync=load(root/f'{name}-sync.json')
 assert contract['status']=='lab_disabled_by_default' and contract['public_runtime_advertised'] is False
 assert sync['status']=='PASS' and sync['contract_id']==contract['contract_id']
 assert all(c['contract_sha256']==sync['contract_sha256'] for c in sync['consumers'].values())
 contracts[name]={'id':contract['contract_id'],'contract_sha256':sync['contract_sha256'],'dependency':contract['dependency'],'platforms':contract['supported_platforms'],'default_public_advertisement':False}
assert contracts['awg2']['id']!=contracts['awg31']['id']
assert load(core/'config/awg31-capability.json')['compatibility']['wire_compatible_with_awg2'] is False
assert '34 passed' in (root/'contracts-tests.log').read_text(encoding='utf-8-sig')
r={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_DECLARED_A01_BASELINE','sources':{n:subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip() for n,p in [('platform',platform),('client',client),('core',core)]},'contracts':contracts,'deployed_source_equivalent_to':'f530005','current_full_files_differ':True,'current_and_deployed_gate_ast_equal':checks,'runtime_readback':{'config_sha256':observed['config_sha256'],'public_access_denied':True,'gate_enabled_flags':True,'empty_identity_allowlists':True,'no_shared_lab_rules_or_cohorts':True},'tests_passed':34,'backend_mutated':False,'candidate_created':False,'release_proven':False}
(root/'acceptance.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':r['status'],'gates_ast_equal':len(checks),'tests_passed':34}))
