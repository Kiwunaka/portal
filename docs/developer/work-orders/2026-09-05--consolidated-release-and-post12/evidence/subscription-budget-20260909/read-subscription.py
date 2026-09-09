import json,subprocess,hashlib,shlex
from pathlib import Path
out=Path(__file__).resolve().parent
code=r'''
import datetime,hashlib,hmac,json,os,time,urllib.request,urllib.parse,urllib.error
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
params={'auth_date':str(int(time.time())),'user':json.dumps({'id':int(os.environ['ADMIN_ID']),'first_name':'POKROV'},separators=(',',':'))}
check='\n'.join(f'{k}={v}' for k,v in sorted(params.items()));key=hmac.new(b'WebAppData',os.environ['BOT_TOKEN'].encode(),hashlib.sha256).digest();params['hash']=hmac.new(key,check.encode(),hashlib.sha256).hexdigest()
request=urllib.request.Request('https://api.pokrov.space/api/client/subscription',headers={'X-Telegram-Init-Data':urllib.parse.urlencode(params)})
started=time.monotonic();report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin','scope':'owned admin account GET client subscription','credentials_exported':False}
try:
 with urllib.request.urlopen(request,timeout=55) as response:
  data=json.load(response);report.update(http_status=response.status,lane=data.get('lane'),access_state=data.get('accessState'),expiry_present=bool(data.get('expiresAt')),days_left_positive=isinstance(data.get('daysLeft'),int) and data['daysLeft']>0,usage_source=(data.get('usage') or {}).get('source'),telegram_linked=((data.get('identities') or {}).get('telegram') or {}).get('linked'))
except urllib.error.HTTPError as exc:report.update(http_status=exc.code)
except Exception as exc:report.update(exception_type=type(exc).__name__)
report['elapsed_seconds']=round(time.monotonic()-started,3);print(json.dumps(report))
'''
target=out/'subscription-server-readback.json';assert not target.exists()
r=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,timeout=65)
assert r.returncode==0,{'exit':r.returncode,'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()}
report=json.loads(r.stdout);target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
