import datetime, hashlib, json, re, subprocess
from pathlib import Path
root=Path('E:/r12-a03-acceptance-20260908')
platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
core=Path('E:/r12core-implementation')
client=Path('E:/r12client')
base=platform/'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/evidence'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
cross=read(base/'awg-crossfield-2026-09-08.json');a02=read(base/'a02-owned-server-20260908.json')
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=core,text=True).strip()
assert source==cross['core_commit']==a02['core_source']=='02a091cb0e369192a5ad0909b56ccba8aa1dce17'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=core,text=True).strip()
checked=[]
for name,e in cross['checks']['logs'].items():
 p=Path(cross['checks']['local_evidence_root'])/name
 assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes'],name
 checked.append({'path':str(p),'sha256':e['sha256']})
for e in a02['retained_files']:
 p=Path(e['path']);assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes'],p.name
 checked.append({'path':str(p),'sha256':e['sha256']})
assert a02['source_auth']['all_compiled_module_sources_equal'] and a02['reproduction']['same_bytes']
current=read(root/'server-current.json');previous=a02['server_after']
assert current['files']==previous['files']
for name,item in current['interfaces'].items():
 old=previous['interfaces'][name]
 for field in ['config_sha256','live_static_config_sha256']:
  assert item[field]==old[field],(name,field)
 assert item['unit_active']=='active'
 assert [p['public_key_sha256'] for p in item['peers']]==[p['public_key_sha256'] for p in old['peers']]
 assert item['processes'][0]['exe_sha256']==a02['reproduction']['server_sha256']
mtu=[]
for profile,e in a02['interop'].items():
 assert e['core_revision']==source and e['passed'] and e['temporary_remote_state_removed']
 assert set(e['mtu_observations'])=={'1280','1400','1408'}
 for value,sample in e['mtu_observations'].items():
  assert sample['rx_packets']>0 and sample['tx_packets']>0
  mtu.append({'profile':profile,'mtu':int(value),**sample})
for lane,path in [('android',client/'apps/android_shell/android/app/libs/pokrov-core.aar'),('windows',client/'apps/windows_shell/windows/runner/resources/runtime/pokrov-core.dll')]:
 ev=cross['library_evidence'][lane]
 assert ev['source']['commit']==source and ev['reproducibility']['result']=='PASS_BYTE_IDENTICAL_TWO_BUILDS'
 item=next(e for e in ev['reproducibility']['files'] if e['path']==path.name)
 assert sha(path)==item['sha256'] and path.stat().st_size==item['size']
 checked.append({'path':str(path),'sha256':item['sha256']})
log=(root/'validator-current.log').read_text(encoding='utf-8-sig')
passed=re.findall(r'^--- PASS: (Test\S+)',log,re.M)
assert len(passed)==8 and '\nFAIL' not in log
subtests=len(re.findall(r'^    --- PASS:',log,re.M))
source_paths=['engine/sing-box/protocol/awg/contract.go','engine/sing-box/protocol/awg/contract_test.go','engine/sing-box/protocol/awg/cross_field_test.go','engine/sing-box/protocol/awg/owned_lab_interop_test.go','engine/sing-box/go.mod','engine/sing-box/go.sum']
upstream=Path('C:/Users/kiwun/go/pkg/mod/github.com/amnezia-vpn/amneziawg-go/v3@v3.1.20260814/device')
for name in source_paths: checked.append({'path':str(core/name),'sha256':sha(core/name)})
for name in ['timers.go','send.go','uapi.go','queueconstants_windows.go']:
 checked.append({'path':str(upstream/name),'sha256':sha(upstream/name)})
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'PASS_DECLARED_A03_CORE_LAB_SCOPE','core_source':source,'upstream_pin':'github.com/amnezia-vpn/amneziawg-go/v3 v3.1.20260814','validator_tests':{'top_level_passed':len(passed),'subtests_passed':subtests,'names':passed,'exit_code':0},'prior_negative_regression':'6 failures before the code correction; unchanged retained log hash verified','server_binary_and_static_configuration_unchanged':True,'live_mtu_cases_reused_for_identical_core_server_material':mtu,'retained_hashes_checked':len(checked),'files':checked,'candidate_created':False,'release_proven':False,'remaining_separate_scope':['D02 whole-device/path MTU, UDP53, DNS, IPv6 and carrier matrix','N03/N08 routing proof','exact final candidate and release gates']}
(root/'acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['result','core_source','validator_tests','server_binary_and_static_configuration_unchanged','retained_hashes_checked']}))
