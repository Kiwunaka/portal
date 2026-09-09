import hashlib,json,shlex,subprocess
from pathlib import Path

code=r'''
import datetime,hashlib,hmac,http.cookiejar,json,os,pathlib,subprocess,time,urllib.request,urllib.parse
from dotenv import load_dotenv
load_dotenv('/root/portal_bot/.env')
owner=int(os.environ['ADMIN_ID']);params={'auth_date':str(int(time.time())),'user':json.dumps({'id':owner,'first_name':'POKROV','username':'operator'},separators=(',',':'))}
check='\n'.join(f'{k}={v}' for k,v in sorted(params.items()))
key=hmac.new(b'WebAppData',os.environ['BOT_TOKEN'].encode(),hashlib.sha256).digest()
params['hash']=hmac.new(key,check.encode(),hashlib.sha256).hexdigest()
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def request(method,path,body=None,headers=None):
 request=urllib.request.Request('https://api.pokrov.space'+path,data=None if body is None else json.dumps(body).encode(),method=method,
  headers={'Origin':'https://admin.pokrov.space','Content-Type':'application/json',**(headers or {})})
 with client.open(request,timeout=25) as response: assert response.status==200;return json.load(response)
session=request('POST','/api/admin/v2/auth/bootstrap',{},headers={'X-Telegram-Init-Data':urllib.parse.urlencode(params)})['data']['session']
try:
 meta=request('GET','/api/admin/v2/meta')['data']
 assert meta['portal_commit']=='d3eba8945e74eca025e2a8589be110d070fb562d'
 assert meta['api_schema']=='admin-v2.1' and meta['expected_frontend_app']=='pokrov-operator-center'
 assert meta['deployed_at']==os.environ['PORTAL_DEPLOYED_AT']
 report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'origin':'brain-origin','status':'PASS',
  'data':meta,'credentials_exported':False,'external_oidc_login_proven':False}
finally:
 request('POST','/api/admin/v2/auth/logout',{},headers={'X-Pokrov-Admin-CSRF':session['csrf_token']})
 report['session_logged_out']=True
print(json.dumps(report))
'''
target=Path(__file__).resolve().parent/'operator-build-meta.json';assert not target.exists()
r=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','pokrov-brain','/root/portal_bot/venv/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,timeout=90)
assert r.returncode==0, {'exit':r.returncode,'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()}
report=json.loads(r.stdout);target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
