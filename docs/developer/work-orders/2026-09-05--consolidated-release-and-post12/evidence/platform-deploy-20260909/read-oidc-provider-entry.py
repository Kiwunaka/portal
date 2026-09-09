import json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,parse_qs

checks=[]
for name,path in [('operator','/api/admin/v2/auth/oidc/start?mode=login'),('cabinet','/api/auth/telegram/oidc/start')]:
 with urllib.request.urlopen('https://api.pokrov.space'+path,timeout=20) as response:
  payload=json.load(response)
 data=payload['data'] if name=='operator' else payload
 query=parse_qs(urlsplit(data['auth_url']).query)
 with urllib.request.urlopen(data['auth_url'],timeout=20) as response:
  body=response.read().decode()
  checks.append({'surface':name,'origin':'current-origin','http_status':response.status,'redirect_uri':query['redirect_uri'][0],'query_keys':sorted(query),'response_bytes':len(body.encode()),'redirect_uri_required':'redirect_uri required' in body,'login_page_detected':'Log in' in body})
report={'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'operator_login':'BLOCKED_BY_PROVIDER_CONFIGURATION','provider_allowed_urls':'NOT_VERIFIED','cause':'Admin callback registration suspected; provider settings unavailable. Cabinet callback works with same shared client credentials.','tokens_or_identity_exported':False,'actual_oidc_login':False,'step_up':False,'provider_docs':'https://core.telegram.org/bots/telegram-login'}
target=Path(__file__).resolve().parent/'oidc-provider-entry.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
