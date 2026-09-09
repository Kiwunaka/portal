"""Verify and retain aggregate readiness evidence; exclude archives and secret stores."""
from pathlib import Path
import hashlib,json,subprocess

root=Path(__file__).parent
platform=Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
wo=platform/'docs/developer/work-orders/2026-09-05--consolidated-release-and-post12'
quality=Path('E:/r12-integrated-quality-20260909')
def read(path):return json.loads(path.read_text())
def meta(path):
 raw=path.read_bytes()
 return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
gate=read(quality/'010I-local-quality-gate.json')
assert gate['local_status']=='PASS' and len(gate['steps'])==15
assert all(s['status']=='PASS' for s in gate['steps'])
assert all(s['working_tree_state']=='clean' for s in gate['sources'].values())
assert gate['sources']['platform']['revision']=='235e8a49e94261f39b1166b152fe547fe95da740'
preflight=read(quality/'preflight.json')
assert preflight['status']=='READY_LOCAL_FREEZE'
backup=read(root/'backup-restore-v2.json')
assert backup['status']==backup['backup_restore_status']==backup['target_role_status']=='PASS'
assert backup['source_integrity']['tables']==backup['target_integrity']['tables']
assert backup['snapshot_cleanup_outcome']=='committed' and not backup['target_was_reset']
candidate=read(root/'candidate-apply.json')
assert candidate['status']=='PASS' and candidate['synthetic_cleanup']=='confirmed'
assert candidate['candidate']['commit']==gate['sources']['platform']['revision']
assert candidate['candidate']['archive_sha256']==meta(root/'backend-candidate.tar')['sha256']
volume=read(root/'volume-apply-v2.json')
assert volume['status']=='PASS_ENCRYPTED_VOLUME_RESTORE'
assert volume['source_files']==volume['restored_files']
assert volume['source_unchanged_during_capture'] and volume['database_binding_unchanged']
assert read(root/'readiness-before.json')['services']==read(root/'readiness-after.json')['services']
assert read(root/'readiness-after.json')['database']['source_lock_waiters']==0
dest=wo/'evidence/brain-rehearsal-20260909';dest.mkdir(exist_ok=True)
names='''backup-plan.json backup-restore.json backup-restore-v2.json candidate-plan.json candidate-apply.json
source-before.json readiness-before.json readiness-after.json ssh-auth-diagnostic.json
volume-plan.json volume-plan-v2.json volume-apply-v2.json run-backup.ps1 retry-backup.ps1
run-volume.ps1 volume-snapshot.py volume-snapshot-v1.py read-readiness-before.py read-readiness.py retain-readiness.py'''.split()
retained=[]
for name in names:
 p=root/name;(dest/name).write_bytes(p.read_bytes());retained.append({'path':name,**meta(p)})
qdest=wo/'evidence/integrated-quality-20260909';qdest.mkdir(exist_ok=True)
qfiles=[]
for name in ['010I-local-quality-gate.json','010I-local-web-performance-evidence.json','010I-local-web-performance-gate.json','preflight.json']:
 p=quality/name;(qdest/name).write_bytes(p.read_bytes());qfiles.append({'path':name,**meta(p)})
receipt={'status':'PASS_BOUNDED_BRAIN_SNAPSHOT_CANDIDATE_AND_VOLUMES','sources':gate['sources'],
 'origin':'brain','database_tables':backup['source_integrity']['public_table_count'],
 'database_rows':sum(row.get('count',row.get('row_count',0)) for row in backup['source_integrity']['tables']),
 'backup':backup['backup'],'volume_backup':volume['archive'],'restored_media_files':sum(v['files'] for v in volume['restored_files'].values()),
 'support_attachment_rows':backup['source_integrity']['support_attachments']['total'],
 'production_services_unchanged':True,'production_code_deployed':False,'source_database_writes_by_gate':False,
 'target_retained':True,'retained_files':retained,
 'external_files':[{'path':str(root/n),**meta(root/n)} for n in ['backend-candidate.tar','backup-restore.log','backup-restore-v2.log','candidate-apply.log','volume-apply-v2.log']],
 'protected_passphrase':'Retained in per-user DPAPI store outside Git; no plaintext retained',
 'historical_failures':['First backup attempt failed at SSH before snapshot or target creation; retry succeeded with same credentials.',
 'First volume PLAN used incorrect default accepted-directory spelling; superseded by canonical-path v2 before any volume mutation.',
 'Initial local DPAPI retry read included a trailing newline and failed before Python; corrected by trimming encrypted text.'],
 'limits':['No atomic cross-store snapshot claimed; compared retained config and file manifests.',
 'Zero production support attachments and no promo config; no filled attachment recovery claim.',
 'Candidate gate runs current db/cleanup source on a restored DB; not a deployed API/bot/worker process proof.',
 'Full B08, A04 and release gates remain open.']}
(dest/'receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
(qdest/'receipt.json').write_bytes((json.dumps({'status':'PASS_LOCAL_ONLY','sources':gate['sources'],
 'retained_files':qfiles,'external_log':{'path':'E:/r12-integrated-quality-20260909.log',**meta(Path('E:/r12-integrated-quality-20260909.log'))},
 'candidate_created':False,'production_deploy':False},indent=2)+'\n').encode())
print(json.dumps({'brain_files':len(retained),'quality_files':len(qfiles),'rows':receipt['database_rows'],'result':'PASS'}))
