"""Owned Brain durable-file recovery, with encrypted archives retained on Brain."""
from pathlib import Path
import json, shlex, subprocess, sys

root = Path(__file__).parent
mode = sys.argv[1]
assert mode in ('plan', 'apply')
code = r'''
import datetime,hashlib,json,os,pathlib,shlex,subprocess,sys,uuid
from dotenv import dotenv_values
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
mode=MODE
env=dotenv_values('/root/portal_bot/.env')
base=pathlib.Path('/root/portal_bot')
specs={
 'support':('SUPPORT_UPLOAD_DIR',base/'uploads/support'),
 'promos':('PROMO_MEDIA_DIR',base/'uploads/promos'),
 'bundle_quarantine':('POKROV_SUPPORT_BUNDLE_QUARANTINE_DIR',base/'private/support-bundle-quarantine'),
 'bundle_accepted':('POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR',base/'private/support-bundle-accepted'),
}
roots={}
for label,(key,default) in specs.items():
 p=pathlib.Path(env.get(key) or default)
 if not p.is_absolute() or p.is_symlink() or not p.is_relative_to(base) or p==base:
  raise RuntimeError('volume_path_guard')
 roots[label]=p
def inventory(paths):
 result={}
 for label,p in paths.items():
  entries=[]
  if p.exists():
   if not p.is_dir():raise RuntimeError('volume_directory_guard')
   for item in sorted(p.rglob('*')):
    if item.is_symlink():raise RuntimeError('volume_symlink_guard')
    if item.is_dir():continue
    if not item.is_file():raise RuntimeError('volume_regular_file_guard')
    digest=hashlib.sha256()
    with item.open('rb') as f:
     for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    entries.append([hashlib.sha256(item.relative_to(p).as_posix().encode()).hexdigest(),item.stat().st_size,digest.hexdigest()])
  result[label]={'present':p.exists(),'files':len(entries),'bytes':sum(e[1] for e in entries),
                 'manifest_sha256':hashlib.sha256(json.dumps(entries,separators=(',',':')).encode()).hexdigest()}
 return result
live=make_url(str(env['DATABASE_URL']))
if live.get_backend_name()!='postgresql' or live.database!='portal':raise RuntimeError('source_database_guard')
def settings(database):
 engine=create_engine(live.set(database=database),hide_parameters=True)
 try:
  with engine.connect() as c:
   c.exec_driver_sql('SET TRANSACTION READ ONLY')
   row=c.execute(text("SELECT value_json FROM app_settings WHERE key='promo_slots_config_v1'")).scalar_one_or_none()
   attachments=c.execute(text('SELECT count(*) FROM support_attachments')).scalar_one()
  return {'promo_config_present':row is not None,'promo_config_sha256':hashlib.sha256((row or '').encode()).hexdigest(),
          'support_attachment_rows':attachments}
 finally:engine.dispose()
before=inventory(roots)
bindings_before={'source':settings('portal'),'restored':settings('portal_r12_20260909_rehearsal')}
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':mode,'source_files':before,
        'database_binding':bindings_before,'source_mutated':False,'raw_file_names_or_content_returned':False}
if mode=='plan':
 result['status']='PLAN_ONLY'
else:
 secret=sys.stdin.buffer.read(4097)
 if not 32<=len(secret)<=4096 or b'\n' in secret or b'\r' in secret:raise RuntimeError('passphrase_input_guard')
 if bindings_before['source']!=bindings_before['restored']:raise RuntimeError('database_binding_changed')
 token=uuid.uuid4().hex
 backup=pathlib.Path('/root/backups/r12-20260909')
 if not backup.is_dir() or backup.is_symlink():raise RuntimeError('backup_directory_guard')
 archive=backup/('volumes-'+token+'.tar.enc')
 restored=backup/('volumes-'+token+'-restored')
 if archive.exists() or restored.exists():raise RuntimeError('volume_no_clobber_guard')
 names=[p.relative_to(base).as_posix() for p in roots.values() if p.exists()]
 if not names:raise RuntimeError('no_volumes_to_restore')
 source_args=' '.join(shlex.quote(n) for n in names)
 enc='openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -md sha256 -pass fd:3'
 dec='openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -md sha256 -pass fd:3'
 def pipeline(command):
  r=subprocess.run(['bash','-c','set -Eeuo pipefail\numask 077\nexec 3<&0 0</dev/null\n'+command],input=secret,capture_output=True,timeout=300)
  if r.returncode:raise RuntimeError('encrypted_volume_pipeline_failed')
 pipeline('tar -C '+shlex.quote(str(base))+' -cf - -- '+source_args+' 3<&- | '+enc+' -out '+shlex.quote(str(archive)))
 restored.mkdir(mode=0o700)
 pipeline(dec+' -in '+shlex.quote(str(archive))+' | tar -C '+shlex.quote(str(restored))+' -xf - 3<&-')
 restored_roots={label:restored/p.relative_to(base) for label,p in roots.items()}
 observed=inventory(restored_roots)
 after=inventory(roots)
 bindings_after={'source':settings('portal'),'restored':settings('portal_r12_20260909_rehearsal')}
 if before!=after or before!=observed or bindings_before!=bindings_after:raise RuntimeError('volume_or_binding_changed')
 if archive.stat().st_mode&0o777!=0o600:raise RuntimeError('archive_mode_guard')
 result.update(status='PASS_ENCRYPTED_VOLUME_RESTORE',restored_files=observed,
  source_unchanged_during_capture=True,database_binding_unchanged=True,
  archive={'path':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'mode':'0600'},
  restore_root=str(restored),restore_root_mode='0700',archives_and_restore_retained=True,
  consistency_scope='Separate DB snapshot and file capture; exact config hashes and source file manifests remained equal, no cross-store atomic snapshot claimed')
print(json.dumps(result))
'''.replace('MODE', repr(mode), 1)
secret = sys.stdin.buffer.read() if mode == 'apply' else None
r = subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe', '-T', '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10', 'pokrov-brain',
    '/root/portal_bot/venv/bin/python -c ' + shlex.quote(code)],
    input=secret, capture_output=True, timeout=350)
if r.returncode:
    import hashlib
    report={'status':'FAIL','exit_code':r.returncode,'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
else:
    report=json.loads(r.stdout)
path=root/('volume-'+mode+'-v2.json')
with path.open('xb') as f:f.write((json.dumps(report,indent=2)+'\n').encode())
print(json.dumps(report))
raise SystemExit(r.returncode)
