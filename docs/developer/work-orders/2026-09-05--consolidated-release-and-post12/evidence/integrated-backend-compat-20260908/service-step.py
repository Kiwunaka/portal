import json,subprocess,sys,time
from pathlib import Path
import requests
ROOT=Path('/opt/r12/integrated-compat-20260908')
phase=sys.argv[1];assert phase in ('previous-start','current-start','current-stop','previous-restart','stop-all')
def command(*args):
 p=subprocess.run(args,capture_output=True,text=True);assert p.returncode==0,'service operation failed'
if phase=='previous-start':command('systemctl','daemon-reload')
if phase=='stop-all':command('systemctl','stop','r12-integrated-previous','r12-integrated-current')
else:
 label,action=phase.split('-');command('systemctl',action,'r12-integrated-'+label)
 if action in ('start','restart'):
  port=18083 if label=='previous' else 18084;end=time.monotonic()+45
  client=requests.Session();client.trust_env=False
  while True:
   try:
    r=client.get(f'http://127.0.0.1:{port}/api/health',timeout=2)
    if r.status_code==200 and r.json().get('status')=='ok':break
   except requests.RequestException:pass
   assert time.monotonic()<end,'API readiness deadline';time.sleep(1)
  client.close()
states={}
for label in ('previous','current'):
 p=subprocess.run(['systemctl','show','r12-integrated-'+label,'-p','ActiveState','-p','MainPID','-p','NRestarts','-p','IPAddressDeny','-p','IPAddressAllow'],capture_output=True,text=True);assert p.returncode==0
 states[label]=dict(row.split('=',1) for row in p.stdout.strip().splitlines())
if phase=='stop-all':assert all(s['ActiveState']=='inactive' and s['MainPID']=='0' for s in states.values())
report={'phase':phase,'states':states};(ROOT/(phase+'-units.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
