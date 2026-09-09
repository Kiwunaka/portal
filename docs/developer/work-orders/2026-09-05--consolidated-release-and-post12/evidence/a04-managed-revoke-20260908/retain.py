import csv,hashlib,json,re,subprocess
from pathlib import Path
root=Path(__file__).parent
platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
dest=platform/'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/evidence/a04-managed-revoke-20260908'
assert not dest.exists(),'Preserve existing evidence'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
read=lambda name:json.loads((root/name).read_text(encoding='utf-8-sig'))
checks={}
commands={
 'focused-after.log':'python -B -m pytest -p no:cacheprovider tests/test_auth_sessions.py tests/test_account_recovery.py tests/test_admin_action_intents.py -q',
 'backend-router.log':'python -B -m pytest -p no:cacheprovider portal_bot/tests/test_app_first_api.py portal_bot/tests/test_app_first_service.py tests/test_api_auth_and_tickets.py tests/test_subscription_preview_api.py -q',
 'auth-lab-router.log':'python -B -m pytest -p no:cacheprovider portal_bot/tests/test_email_auth.py tests/test_api_payments_callbacks.py tests/test_lavatop_payment_providers.py tests/test_payment_email_readiness_smoke.py tests/test_awg2_lab_service.py tests/test_awg31_lab_service.py tests/test_hy2_lab_service.py -q',
 'docs-tests.log':'python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q',
}
for name,command in commands.items():
    log=(root/name).read_text(encoding='utf-8-sig')
    matched=re.search(r'(\d+) passed(?:, \d+ warnings)?(?:, (\d+) subtests passed)? in ',log)
    assert matched and not re.search(r'(^FAILED |\d+ failed)',log,re.M),name
    checks[name]={'command':command,'exit_code':0,'passed':int(matched[1]),'subtests_passed':int(matched[2] or 0)}
assert checks['focused-after.log']['passed']==41 and checks['docs-tests.log']['passed']==33
for name,expected in [('negative-material.log',3),('negative-admin.log',1),('negative-lockdown.log',1)]:
    log=(root/name).read_text(encoding='utf-8-sig')
    assert re.search(r'\b'+str(expected)+r' failed\b',log)
    checks[name]={'exit_code':1,'expected_regression_failures':expected}
pg=read('pg-result-v2.json')
assert read('pg-execution-v2.json')['exit_code']==0
assert read('pg-execution.json')['exit_code']==1
assert pg['result']=='PASS_SIX_POSTGRES_REVOKE_REPLACE_RACES' and len(pg['cases'])==6
assert all(x['row_lock_observed'] and x['old_ciphertext_preserved'] and x['fresh_login_did_not_restore_material'] for x in pg['cases'])
final=read('final-audit.json')
assert final['source_files_unchanged']==195 and final['other_fixture_db_sessions']==0
assert all(x=={'rows':7,'active':0,'rotated':1,'revoked':6} for x in final['material_rows'].values())
assert 'VMState="poweroff"' in (root/'vm-final-state.txt').read_text(encoding='utf-8-sig')
source=read('source-manifest-v2.json')
for item in source['files']:
    assert sha((platform/item['path']).read_bytes())==item['sha256'],item['path']
names=['negative-material.log','negative-admin.log','negative-lockdown.log',*commands.keys(),'context-audit.log','pg-execution.json','pg-execution-v2.json','pg-result-v2.json','final-audit.json','vm-final-state.txt','source-manifest.json','source-manifest-v2.json','prepare-pg.py','guest-pg-race.py','run-pg.py','complete-pg-source.py','guest-pg-race-v2.py','run-pg-v2.py','audit-and-stop-lab.py','synthetic-endpoints.json','retain.py']
files={name:(root/name).read_bytes() for name in names}
external=[]
for name in ('source.tar','source-additional.tar'):
    p=root/name;external.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
dest.mkdir(parents=True)
inventory=[]
for name,raw in files.items():
    (dest/name).write_bytes(raw)
    inventory.append({'path':name,'bytes':len(raw),'sha256':sha(raw)})
receipt={'result':'IMPLEMENTATION_VERIFIED_I3','scope':'database material invalidation and canonical-device intent guard; no server peer enforcement','source_parent':source['source_parent'],'runtime_files':{name:sha((platform/name).read_bytes()) for name in ('portal_bot/auth_session_service.py','portal_bot/admin_action_intent_service.py')},'checks':checks,'postgres':pg,'final_lab_audit':final,'vm_poweroff':True,'fixture_setup_failure':'Initial archive omitted six admin_v2 package files; first run exited before table creation. Preserved empty database was verified and used by v2.','retained_files':inventory,'external_archives':external,'no_schema_migration':True,'production_deploy':False,'candidate_created':False,'remaining':['owned server peer removal/expiry integration','installed client revocation proof','full A04 and final integrated quality/release gates']}
(dest/'receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps({'result':receipt['result'],'retained_files':len(inventory),'checks':checks,'postgres_cases':6}))
