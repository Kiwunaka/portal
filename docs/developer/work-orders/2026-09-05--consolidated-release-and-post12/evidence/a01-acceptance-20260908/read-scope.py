import hashlib,json,os,shlex,sys
from pathlib import Path
sys.path.insert(0,'C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start/scripts')
import remote_bind_owned_awg_lab_device as binding
from node_access import connect_node
remote=binding._REMOTE_HELPER.split('now = datetime.now',1)[0]+r'''
from sqlalchemy import text
from models import AppSetting
from network_rollout import NETWORK_ROLLOUT_CONFIG_KEY, normalized_network_rollout_config
with SessionLocal() as session:
    session.execute(text('SET TRANSACTION READ ONLY'))
    row=session.query(AppSetting).filter(AppSetting.key==NETWORK_ROLLOUT_CONFIG_KEY).one()
    raw=json.loads(row.value_json)
    assert isinstance(raw,dict)
    config=normalized_network_rollout_config(raw)
    labs=('awg2_lab','awg31_lab')
    shared=[config.get('defaults') or {}, *(config.get('carrier_overrides') or {}).values()]
    result={'utc':datetime.now(timezone.utc).isoformat(),'read_only':True,'raw_identifiers_returned':False,
      'config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
      'shared_rules_select_lab':sum(x.get('transport_profile') in labs for x in shared),
      'lab_cohort_count':sum(x.get('transport_profile') in labs for x in (config.get('cohort_overrides') or {}).values()),
      'gates':{name:{'enabled':bool(config[name].get('enabled')),'kill_switch_engaged':bool(config[name].get('kill_switch_engaged')),
          'install_allowlist_count':len(config[name].get('allowlist_install_ids') or []),'account_allowlist_count':len(config[name].get('allowlist_tg_ids') or []),
          'platform_count':len(config[name].get('allowed_platforms') or [])} for name in labs},
      'source_hashes':{name:hashlib.sha256(open('/root/portal_bot/'+name,'rb').read()).hexdigest() for name in ['network_rollout.py','awg31_lab_service.py','awg2_lab_service.py']}}
    result['status']='PASS_DEFAULT_OFF' if result['shared_rules_select_lab']==0 and result['lab_cohort_count']==0 and all((not x['enabled'] or x['kill_switch_engaged']) for x in result['gates'].values()) else 'REVIEW_REQUIRED'
    print(json.dumps(result))
'''
os.environ['POKROV_SSH_KNOWN_HOSTS']='C:/Users/kiwun/.ssh/known_hosts'
ssh,_=connect_node(code='brain',host='82.21.114.104',passwords_path=Path('C:/Users/kiwun/Documents/ai/VPN/VPN NODE SSH KEYS/PASSWORDS.txt'))
try:
 si,so,se=ssh.exec_command('/root/portal_bot/venv/bin/python -c '+shlex.quote(remote),timeout=60)
 si.write(json.dumps(dict(device_label_fragment='',candidate_rank=1,profile='default',apply=False,confirm_target_install_sha256='64a9c9b73d01eedf96a7377df0b1c1c49d023546217184671b57cdd56750943b')))
 si.channel.shutdown_write()
 if so.channel.recv_exit_status():raise SystemExit('Read-only scope inspection failed; remote output withheld')
 r=json.loads(so.read());assert r['read_only'] and r['raw_identifiers_returned'] is False
 dest=Path(__file__).with_suffix('.json')
 if dest.exists():raise SystemExit('Preserve existing output')
 dest.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(r))
finally:ssh.close()
