from pathlib import Path
import concurrent.futures
import hashlib
import hmac
import json
import sys
import time
import uuid
from urllib.parse import urlencode
import requests
from dotenv import dotenv_values
from sqlalchemy import create_engine, text

ROOT=Path('/opt/r12/integrated-compat-20260908')
phase=sys.argv[1]
assert phase in ('previous-before','concurrent','previous-after','previous-restarted')
env=dotenv_values(ROOT/'config.env')
user=json.dumps({'id':6201,'first_name':'Synthetic','username':'b08_linux_fixture'},separators=(',',':'))
params={'auth_date':str(int(time.time())),'query_id':'r12-integrated-compat','user':user}
check='\n'.join(k+'='+v for k,v in sorted(params.items()))
key=hmac.new(b'WebAppData',env['BOT_TOKEN'].encode(),hashlib.sha256).digest()
params['hash']=hmac.new(key,check.encode(),hashlib.sha256).hexdigest()
headers={'X-Telegram-Init-Data':urlencode(params)}

def probe(label,port):
    client=requests.Session();client.trust_env=False
    base=f'http://127.0.0.1:{port}'
    result={'source':label,'port':port,'checks':{}}
    response=client.get(base+'/api/health',timeout=15);assert response.status_code==200 and response.json()['status']=='ok';result['checks']['health']=200
    response=client.get(base+'/api/public/plans',timeout=15);assert response.status_code==200;result['checks']['plans']=200;result['plans_body_sha256']=hashlib.sha256(response.content).hexdigest()
    denial=client.get(base+'/api/tickets',timeout=15);assert denial.status_code==401;result['checks']['unauthenticated_ticket_denial']=401
    response=client.get(base+'/api/tickets',headers=headers,timeout=15);assert response.status_code==200,(label,'tickets',response.status_code)
    body=response.json();assert body.get('tickets') and any(t['id']==1 for t in body['tickets']);result['checks']['authenticated_ticket_read']=200
    event=str(uuid.uuid4());payload={'event_name':'config_import_attempted','event_id':event,'source':'webapp','platform':'windows','build_number':'r12-b08-'+label,'meta':{'surface':'dashboard'}}
    response=client.post(base+'/api/events',headers=headers,json=payload,timeout=15);assert response.status_code==200 and response.json().get('ok'),(label,'event',response.status_code);result['checks']['authenticated_event_write']=200;result['event_id']=event
    client.close();return result

targets=[('previous',18083),('current',18084)] if phase=='concurrent' else [('previous',18083)]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda pair:probe(*pair),targets))
e=create_engine(env['DATABASE_URL'],hide_parameters=True)
with e.connect() as c:
    for result in results:
        rows=c.execute(text('SELECT tg_id,event_name,build_number FROM events WHERE event_id=:id'),{'id':result['event_id']}).all();assert len(rows)==1 and rows[0][0]==6201 and rows[0][1]=='config_import_attempted';result['db_write_verified']=True
e.dispose()
report={'phase':phase,'result':'PASS','requests':results}
(ROOT/(phase+'-http.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
