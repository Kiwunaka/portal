import datetime,hashlib,json,re,subprocess
from pathlib import Path
root=Path(__file__).parent
platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
work=platform/'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12'
dest=work/'evidence/a04-peer-lifecycle-20260908'
assert not (dest/'receipt.json').exists(),'Preserve completed receipt'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
read=lambda name:json.loads((root/name).read_text(encoding='utf-8-sig'))
before=read('server-before.json');after=read('server-after.json');build=read('build.json')
assert before['interfaces']==after['interfaces']
assert before['files']==after['files']
assert build['core_revision']=='02a091cb0e369192a5ad0909b56ccba8aa1dce17'
assert sha((root/'owned-awg.test').read_bytes())==build['binary_sha256']
profiles={};positive=negative=0
for profile in ('awg2_lab','awg31_lab'):
    item=read(profile+'-lifecycle.json')
    assert item['build']==build and item['result']=='PASS_BOUNDED_SERVER_PEER_LIFECYCLE'
    assert item['server_cleanup_verified'] and item['controller_exit_code']==0 and item['temporary_remote_state_removed']
    assert item['raw_material_returned'] is False
    assert item['test_key_sha256']['a']!=item['test_key_sha256']['b']
    assert [x['label'] for x in item['tests']]==['key_a_provisioned','key_a_revoked','key_b_replacement','key_a_stale_after_rotation','key_b_still_accepted']
    assert len(item['tests'])==5
    for test in item['tests']:
        assert test['oracle_passed'] and test['selected_subtest_observed']
        if test['expected']=='accepted':
            assert test['returncode']==0 and test['authenticated_egress_passed']
            assert set(test['mtu_observations'])=={'1280'}
            assert all(test['mtu_observations']['1280'][k]>0 for k in ('tx_packets','rx_packets','tx_max','rx_max'))
            positive+=1
        else:
            assert test['returncode']==1 and test['classification']=='failed_no_outer_response'
            assert test['no_outer_response_rejection'] and not test['authenticated_egress_passed']
            assert 45<=test['elapsed_seconds']<60
            negative+=1
    phases=[x['phase'] for x in item['controller']]
    assert phases==['ready','add','read','remove','read','add','read','read','read','cleanup']
    assert all(item['controller'][-1][k] for k in ['removed_test_peers','saved_configuration_unchanged','original_live_static_configuration_restored','original_peers_restored','passed'])
    reads=[x for x in item['controller'] if x['phase']=='read']
    assert reads[1]['peer_count']==1 and reads[1]['test_peers']==[]
    for i,key in [(0,'a'),(2,'b'),(4,'b')]:
        peer=reads[i]['test_peers'][0]
        assert reads[i]['original_peer_present'] and reads[i]['peer_count']==2
        assert peer['public_key_sha256']==item['test_key_sha256'][key]
        assert peer['rx_bytes']>0 and peer['tx_bytes']>0 and peer['handshake_unix']>0
    # Outbound bytes may grow after the earlier client closes. The stale-key
    # attempt must not change peer identity, accepted RX bytes or handshake.
    for field in ('public_key_sha256','rx_bytes','handshake_unix'):
        assert reads[2]['test_peers'][0][field]==reads[3]['test_peers'][0][field]
    assert reads[3]['test_peers'][0]['tx_bytes']>=reads[2]['test_peers'][0]['tx_bytes']
    assert reads[4]['test_peers'][0]['rx_bytes']>reads[3]['test_peers'][0]['rx_bytes']
    assert reads[4]['test_peers'][0]['tx_bytes']>reads[3]['test_peers'][0]['tx_bytes']
    profiles[profile]={'tests':item['tests'],'server_cleanup_verified':True,'temporary_remote_state_removed':True}
assert (positive,negative)==(6,4)
names=['prepare.py','run.py','server-controller.py','verify-and-retain.py','verify-and-retain-v2.py','verify-and-retain-v3.py','verifier-v1-result.json','verifier-v2-result.json','build.json','server-before.json','server-after.json','awg2_lab-lifecycle.json','awg31_lab-lifecycle.json']
files={name:root/name for name in names}
files['server-readback.py']=Path('E:/r12-a02-server-20260908/server-readback.py')
dest.mkdir(parents=True,exist_ok=True)
inventory=[]
for name,path in files.items():
    raw=path.read_bytes()
    assert re.search(rb'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----\r?\n[A-Za-z0-9+/=\r\n]{32,}',raw) is None
    assert re.search(rb'[\"\x27][A-Za-z0-9+/]{43}=[\"\x27]',raw) is None,'Unexpected literal key'
    if (dest/name).exists():assert (dest/name).read_bytes()==raw,'Preserve partial retained evidence'
    else:(dest/name).write_bytes(raw)
    inventory.append({'path':name,'source_path':str(path),'bytes':len(raw),'sha256':sha(raw)})
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'PASS_BOUNDED_SERVER_PEER_LIFECYCLE','platform_parent':subprocess.check_output(['git','rev-parse','HEAD'],cwd=platform,text=True).strip(),'build':build,'origin':'owned Raspberry Pi 4; direct default-route preflight; one RU lab origin','server_original_full_interfaces_equal':True,'server_files_equal':True,'positive_authenticated_exchanges':positive,'expected_stale_key_rejections':negative,'profiles':profiles,'retained_files':inventory,'local_binary':{'path':str(root/'owned-awg.test'),'sha256':build['binary_sha256'],'bytes':build['binary_bytes']},'raw_output_retained':False,'raw_material_returned':False,'backend_mutated':False,'remaining':['managed API/device rotation and revocation','expiry and device loss','PostgreSQL issuance race','installed client scope','full A04 and release gates'],'candidate_created':False,'push_merge_deploy_publication_performed':False}
(dest/'receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps({'result':receipt['result'],'positive':positive,'negative':negative,'retained_files':len(inventory),'full_server_interfaces_unchanged':True}))
