"""Source worker loop + real PostgreSQL + persisted owned DE peers + exact RU Pi Core."""
import ast,asyncio,base64,datetime,hashlib,json,logging,os,queue,shlex,subprocess,sys,threading,uuid
from pathlib import Path
import paramiko
from sqlalchemy.orm import sessionmaker
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,PublicFormat,NoEncryption
from pg_lab import postgres_lab

root=Path(__file__).parent;profile=sys.argv[1]
assert profile in ('awg2','awg31')
output=root/('server-'+profile+'-result-v2.json');assert not output.exists(),'Preserve prior result'
platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
os.environ['DATABASE_URL']='sqlite:///:memory:'
for name in ('WEBAPP_SESSION_SECRET','AWG2_LAB_MATERIAL_SECRET','AWG31_LAB_MATERIAL_SECRET'):
 os.environ[name]=os.urandom(32).hex()
sys.path.insert(0,str(platform/'portal_bot'));sys.path.insert(0,str(platform/'scripts'))
import remote_run_owned_awg_core_interop as op
from node_access import connect_node
import models,auth_session_service as auth,awg_lab_peer_worker as worker,db

build=json.loads(Path('E:/r12-a04-peer-lifecycle-20260908/build.json').read_text())
binary=Path('E:/r12-a04-peer-lifecycle-20260908/owned-awg.test')
assert op._file_sha256(binary)==build['binary_sha256']
baseline=json.loads((root/'server-before.json').read_text())
interface={'awg2':'pokrovawg2','awg31':'pokrovawg31'}[profile]
prefix={'awg2':'10.203.20.','awg31':'10.203.31.'}[profile]
ssh=Path('C:/Windows/System32/OpenSSH/ssh.exe');scp=Path('C:/Windows/System32/OpenSSH/scp.exe')
config=Path('C:/Users/kiwun/.ssh/config');known=Path('C:/Users/kiwun/.ssh/known_hosts')
base=op._ssh_base(ssh,'shrek',config,known)
preflight=op._run_process(base+[op._RU_PI_PREFLIGHT],timeout=20)
assert preflight.returncode==0 and preflight.stdout.strip()==op._RU_PI_PREFLIGHT_MARKER
os.environ['POKROV_SSH_KNOWN_HOSTS']=str(known)
brain,_=connect_node(code='brain',host='82.21.114.104',passwords_path=platform.parent/'VPN/VPN NODE SSH KEYS/PASSWORDS.txt')
try:template=json.loads(op._load_material(brain,profile+'_lab'))
finally:brain.close()
private={};public={};endpoints={}
for label in ('a','b','c'):
 key=X25519PrivateKey.generate()
 private[label]=base64.b64encode(key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())).decode()
 public[label]=base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()
 endpoint=json.loads(json.dumps(template));endpoint.update(private_key=private[label],address=[prefix+('249/32' if label=='b' else '248/32')])
 for peer in endpoint['peers']:peer.pop('pre_shared_key',None);peer.pop('preshared_key',None)
 endpoints[label]=endpoint
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profile':profile,
 'scope':'Source worker loop on current-origin control plane, isolated PostgreSQL, real SSH removal and lab service restart on owned DE; exact Core on RU Pi',
 'build':build,'public_key_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in public.items()},
 'server':[],'worker_runs':[],'core_tests':[],'raw_material_retained':False,'result':'RUNNING'}
def save():output.write_bytes((json.dumps(result,indent=2)+'\n').encode())
save()
# Reuse the previously retained exact-Core oracle and pipe controller functions.
oracle=Path('E:/r12-a04-key-isolation-20260908/run-http-peer-lifecycle-v3.py')
retained=platform/'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/evidence/a04-key-isolation-20260908/run-http-peer-lifecycle-v3.py'
assert oracle.read_bytes()==retained.read_bytes()
nodes=[n for n in ast.parse(oracle.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in {'start','receive','send','server_action','core_test'}]
assert len(nodes)==5
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(oracle),'exec'),globals())
result['oracle_source_sha256']=hashlib.sha256(oracle.read_bytes()).hexdigest()

ssh_config=paramiko.SSHConfig.from_path(str(config)).lookup('pokrov-de')
assert not any(k in ssh_config for k in ('proxycommand','proxyjump'))
record={'awg2':'de-awg2-20260827-01','awg31':'de-awg31-20260829-04-mobile-safe-trailers'}[profile]
target={'profile':profile+'_lab','node_code':'de','server_record_id':record,
 'host':ssh_config['hostname'],'port':int(ssh_config['port']),'username':ssh_config['user'],
 'key_file':str(Path(ssh_config['identityfile'][0]).expanduser()),'known_hosts':str(known),'interface':interface,
 'server_public_key_sha256':hashlib.sha256(base64.b64decode(template['peers'][0]['public_key'])).hexdigest()}
target_file=root/('.targets-'+profile+'.private.json');assert not target_file.exists()
target_file.write_text(json.dumps([target]))
os.environ['AWG_LAB_PEER_TARGETS_FILE']=str(target_file)
server=None;remote_root=op._remote_root();remote_binary=remote_root+'/owned-awg.test';copied=False
NOW=lambda:datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

def worker_loop_once():
 reports=queue.Queue()
 class Observe(logging.Handler):
  def emit(self,record):
   if record.msg=='awg_lab_peer_reconcile result=%s':reports.put(dict(record.args[0] if isinstance(record.args,tuple) else record.args))
   elif record.levelno>=logging.ERROR:reports.put({'failed_targets':1,'error':'worker_loop_failed'})
 handler=Observe();previous=worker.logger.level;worker.logger.setLevel(logging.INFO);worker.logger.addHandler(handler)
 async def run():
  task=asyncio.create_task(worker.awg_lab_peer_worker_job())
  try:return await asyncio.to_thread(reports.get,True,50)
  finally:
   task.cancel()
   try:await task
   except asyncio.CancelledError:pass
 try:report=asyncio.run(run())
 finally:worker.logger.removeHandler(handler);worker.logger.setLevel(previous)
 result['worker_runs'].append(report);save();print(json.dumps({'profile':profile,'worker':report}),flush=True)
 assert report['failed_targets']==0 and report['live_removed']==1,report

try:
 with postgres_lab('portal_r12_a04_auto_20260909_live_'+profile+'_v2') as (engine,vm):
  models.Base.metadata.create_all(engine);Session=sessionmaker(bind=engine,autoflush=False);db.SessionLocal=Session
  worker.load_network_rollout_config=lambda **_: {profile+'_lab':{'material_max_age_hours':168}}
  model,service=worker.PROFILES[profile+'_lab']
  replace=service.replace_awg2_lab_material if profile=='awg2' else service.replace_awg31_lab_material
  revision=service.AWG2_ENDPOINT_REVISION if profile=='awg2' else service.AWG31_ENDPOINT_REVISION
  account=str(uuid.uuid4());devices={k:str(uuid.uuid4()) for k in ('a','b')};tg={'a':990001,'b':990002}
  def issue(session,label,endpoint):
   return replace(session,tg_id=tg[label],install_id='r12-auto-'+label,generation='fixture-v1',
    endpoint_revision=revision,server_record_id=record,node_code='de',endpoint=endpoint,now=NOW())
  with Session.begin() as session:
   session.add(models.Account(id=account,status='active',created_source='fixture'))
   for label in ('a','b'):
    session.add(models.AccountDevice(id=devices[label],account_id=account,install_id='r12-auto-'+label,platform='windows',state='active',credential_version=1))
    session.add(models.User(tg_id=tg[label],account_id=account,uuid=str(uuid.uuid4()),email='r12-auto-'+label+'@example.test',
     app_install_id='r12-auto-'+label,app_platform='windows',sub_type='PAID',is_active=True,expiry_at=NOW()+datetime.timedelta(days=1)))
   session.flush()
   for label in ('a','b'):issue(session,label,endpoints[label])
   actor=auth.issue_device_session(session,user=session.get(models.User,tg['b']),install_id='r12-auto-b',now=NOW(),fresh_auth_at=NOW())
  created=op._run_process(base+['set -eu; umask 077; install -d -m 0700 '+shlex.quote(remote_root)],timeout=20);assert created.returncode==0
  copied=True
  transfer=op._run_process(op._scp_base(scp,ssh,config,known)+[str(binary),'shrek:'+remote_binary],timeout=180);assert transfer.returncode==0
  checked=op._run_process(base+['set -eu; chmod 0700 '+shlex.quote(remote_binary)+'; sha256sum '+shlex.quote(remote_binary)+" | cut -d' ' -f1"],timeout=20)
  assert checked.returncode==0 and checked.stdout.strip()==build['binary_sha256']
  server,server_messages=start(op._ssh_base(ssh,'pokrov-de',config,known)+['python3 -u -c '+shlex.quote((root/'server-controller.py').read_text())])
  initial={'interface':interface,**{k:baseline['interfaces'][interface][k] for k in ('config_sha256','live_static_config_sha256')},
   'server_sha256':baseline['files']['/usr/local/libexec/pokrov/amneziawg-go-v3.1.20260814'],'helper_source':(platform/'portal_bot/awg_peer_remove.py').read_text()}
  first=send(server,server_messages,initial);assert first['phase']=='ready';result['server'].append(first);save()
  server_action('add','a');server_action('add','b')
  core_test('a_initial','a','accepted',endpoints['a']);core_test('b_initial','b','accepted',endpoints['b'])
  with Session.begin() as session:auth.revoke_device(session,account_id=account,device_id=devices['a'],actor_session_id=actor.session_id,now=NOW())
  worker_loop_once()
  repeated=worker.reconcile_awg_peers(Session,targets=worker.configured_targets())
  assert repeated['live_removed']==repeated['disk_removed']==repeated['failed_targets']==0
  result['idempotent_retry']=repeated;save()
  core_test('a_after_automatic_revoke','a','rejected',endpoints['a'])
  core_test('b_survives_a_revoke','b','accepted',endpoints['b'])
  server_action('restart')
  core_test('a_denied_after_server_restart','a','rejected',endpoints['a'])
  core_test('b_survives_server_restart','b','accepted',endpoints['b'])
  with Session.begin() as session:session.get(models.User,tg['b']).expiry_at=NOW()-datetime.timedelta(seconds=1)
  worker_loop_once()
  core_test('b_after_automatic_expiry','b','rejected',endpoints['b'])
  with Session.begin() as session:
   auth.issue_authenticated_device_session(session,account_id=account,install_id='r12-auto-a',device_name='Synthetic recovered device',platform='windows',now=NOW())
   issue(session,'a',endpoints['c'])
  server_action('add','c');core_test('a_fresh_key_after_reauth','c','accepted',endpoints['c'])
  with Session.begin() as session:
   row=session.query(model).filter_by(tg_id=tg['a'],is_active=True).one();row.state='revoked';row.is_active=False;row.revoked_at=NOW()
  worker_loop_once()
  result['result']='PASS_SOURCE_WORKER_PERSISTENT_REVOKE_EXPIRY_AND_RESTART';save()
except BaseException as error:
 result['result']='FAILED_WORKER_OR_INTEROP';result['error_type']=type(error).__name__
finally:
 if server is not None:
  try:
   if server.poll() is None:server.stdin.write('{"action":"finish"}\n');server.stdin.flush()
   cleanup=receive(server_messages);result['server'].append(cleanup)
   result['server_cleanup_verified']=cleanup.get('phase')=='cleanup' and cleanup.get('passed') is True
   server.stdin.close();result['server_exit_code']=server.wait(timeout=25)
  except Exception:
   result['server_cleanup_verified']=False
   try:server.stdin.close()
   except Exception:pass
 if copied:
  assert op._REMOTE_ROOT_PATTERN.fullmatch(remote_root)
  cleaned=op._run_process(base+['set -eu; rm -rf -- '+shlex.quote(remote_root)+'; test ! -e '+shlex.quote(remote_root)],timeout=25)
  result['pi_temporary_state_removed']=cleaned.returncode==0
 target_file.unlink(missing_ok=True)
 if server is not None and (not result.get('server_cleanup_verified') or result.get('server_exit_code')!=0):result['result']='FAILED_SERVER_CLEANUP'
 save()
print(json.dumps({'profile':profile,'result':result['result'],'error_type':result.get('error_type'),'cleanup':result.get('server_cleanup_verified')}),flush=True)
raise SystemExit(0 if result['result']=='PASS_SOURCE_WORKER_PERSISTENT_REVOKE_EXPIRY_AND_RESTART' else 1)
