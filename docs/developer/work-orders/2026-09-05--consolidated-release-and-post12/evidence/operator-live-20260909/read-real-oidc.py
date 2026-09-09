"""Corroborate the owner's browser OIDC login and step-up without exporting identity."""
import hashlib,json,shlex,subprocess
from pathlib import Path

code=r'''
import datetime,json,os,sys
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
sys.path.insert(0,'/root/portal_bot')
from db import SessionLocal
from models import AdminOperator,AdminOperatorRole,AdminOperatorSession,AdminOperatorAudit
since=datetime.datetime(2026,9,9,5,55)
with SessionLocal() as db:
 operator=db.query(AdminOperator).filter(AdminOperator.legacy_actor_tg_id==int(os.environ['ADMIN_ID'])).one()
 assert operator.identity_source=='telegram_oidc' and operator.status=='active'
 login=db.query(AdminOperatorAudit).filter(AdminOperatorAudit.operator_id==operator.id,AdminOperatorAudit.action=='session.oidc',AdminOperatorAudit.reason_code=='telegram_oidc_verified',AdminOperatorAudit.created_at>=since).order_by(AdminOperatorAudit.created_at.desc()).first()
 assert login and login.result=='success'
 row=db.query(AdminOperatorSession).filter(AdminOperatorSession.id==login.session_id).one()
 step=db.query(AdminOperatorAudit).filter(AdminOperatorAudit.session_id==row.id,AdminOperatorAudit.action=='session.step_up',AdminOperatorAudit.reason_code=='telegram_oidc_verified',AdminOperatorAudit.created_at>=login.created_at).order_by(AdminOperatorAudit.created_at.desc()).first()
 assert step and step.result=='success' and row.step_up_at and row.revoked_at is None
 roles=db.query(AdminOperatorRole).filter(AdminOperatorRole.operator_id==operator.id,AdminOperatorRole.revoked_at.is_(None)).all()
 assert len(roles)==1 and roles[0].role_code=='superadmin' and roles[0].granted_at<since
 report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin','status':'PASS_REAL_OIDC_LOGIN_AND_STEP_UP','identity_source':operator.identity_source,'operator_status':operator.status,'session_environment':row.environment_scope,'session_revoked':False,'login':{'action':login.action,'result':login.result,'reason_code':login.reason_code,'created_at':login.created_at.isoformat()},'step_up':{'action':step.action,'result':step.result,'reason_code':step.reason_code,'created_at':step.created_at.isoformat()},'step_up_timestamp_present':True,'same_session_for_login_and_step_up':True,'active_roles':['superadmin'],'existing_role_only':True,'private_identity_tokens_and_cookie_exported':False,'browser_session_left_active_for_owner':True}
 print(json.dumps(report))
'''
out=Path(__file__).resolve().parent
target=out/'real-oidc-login-step-up.json';assert not target.exists()
r=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,timeout=50)
assert r.returncode==0,{'exit':r.returncode,'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()}
report=json.loads(r.stdout);target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
