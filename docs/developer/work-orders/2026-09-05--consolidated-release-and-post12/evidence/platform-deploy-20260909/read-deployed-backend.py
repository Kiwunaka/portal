"""Verify exact runtime files, service health and a synthetic base quote."""
import hashlib,json,shlex,subprocess,sys
from pathlib import Path

out=Path(__file__).resolve().parent
manifest=json.loads((out/'backend-merged-payload-plan.json').read_bytes())
code=r'''
import datetime,hashlib,json,os,pathlib,subprocess,sys,urllib.request
manifest=json.load(sys.stdin);files=[]
for item in manifest['files']:
 path=pathlib.Path(item['remote_target'])
 assert str(path).startswith(('/root/portal_bot/','/root/shared/','/root/copy/'))
 raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 files.append({'path':item['source_path'],'sha256':digest,'same_candidate_bytes':digest==item['payload_sha256']})
assert all(row['same_candidate_bytes'] for row in files), 'runtime source differs'
units={}
for unit in ('portal-api','portal-bot','portal-helpbot','portal-feedbackbot','portal-worker'):
 raw=subprocess.check_output(['systemctl','show',unit,'-p','MainPID','-p','NRestarts','-p','ActiveState'],text=True)
 units[unit]=dict(line.split('=',1) for line in raw.splitlines())
 assert units[unit]['ActiveState']=='active' and units[unit]['NRestarts']=='0'
pid=units['portal-api']['MainPID']
for item in pathlib.Path('/proc/'+pid+'/environ').read_bytes().split(b'\0'):
 if b'=' in item:
  k,v=item.split(b'=',1);os.environ[k.decode()]=v.decode()
os.chdir('/root/portal_bot');sys.path.insert(0,'/root/portal_bot')
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
from checkout_quote_service import verify_checkout_quote
url='https://api.pokrov.space'
with urllib.request.urlopen(url+'/api/health',timeout=15) as response:
 assert response.status==200
payload={'plan_code':'1_month','buyer_email':'r12-quote-probe@example.invalid','channel':'owned_web'}
request=urllib.request.Request(url+'/api/public/offers/preview',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(request,timeout=15) as response:
 assert response.status==200
 result=json.load(response);cache=response.headers.get('Cache-Control')
assert result['ok'] and result['valid'] and result['offer_token'].startswith('bq1.')
quote=verify_checkout_quote(result['offer_token'])
assert not result.get('reservation_id') and not result.get('campaign_id')
assert result['final_price_rub']>0 and result['currency']=='RUB'
assert cache=='no-store, private'
print(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin',
 'source_revision':manifest['source_revision'],'source_tree':manifest['source_tree'],'files':files,'services':units,
 'all_candidate_bytes_equal':True,'health':'PASS','synthetic_base_quote':{'status':'PASS','signature_verified':True,
 'ttl_seconds':quote['expires']-quote['issued'],'currency':result['currency'],'price_positive':True,'no_commercial_reservation':True,
 'cache_control':cache,'token_exported':False,'order_created':False,'provider_operation':False},
 'support_model_process_env':os.environ.get('SUPPORT_AI_MODEL'),
 'peer_worker_targets_enabled':bool(os.environ.get('AWG_LAB_PEER_TARGETS_FILE')),'release_proven':False}))
'''
target=out/sys.argv[1];assert not target.exists()
r=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],input=json.dumps(manifest),capture_output=True,text=True,timeout=120)
assert r.returncode==0, {'exit':r.returncode,'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()}
report=json.loads(r.stdout);target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='files'}))
