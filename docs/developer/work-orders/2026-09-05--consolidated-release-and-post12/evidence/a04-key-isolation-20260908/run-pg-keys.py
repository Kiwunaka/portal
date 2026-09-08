import hashlib,json
from pathlib import Path
import paramiko
root=Path(__file__).parent;lab=Path('E:/r12-b08-linux-lab')
remote='/opt/r12/a04-key-isolation-20260908'
assert not (root/'pg-execution.json').exists(),'Preserve execution evidence'
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
 i,o,e=s.exec_command('/root/portal_bot/venv/bin/python -B '+remote+'/guest-pg-keys.py',timeout=180)
 code=o.channel.recv_exit_status();out=o.read();err=e.read()
 result={'exit_code':code,'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_sha256':hashlib.sha256(err).hexdigest()}
 (root/'pg-execution.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
 if code==0:
  for line in out.decode().splitlines():print(json.dumps(json.loads(line)),flush=True)
 else:print(json.dumps({**result,'raw_output_withheld':True}))
 with s.open_sftp() as f:
  try:f.get(remote+'/pg-result.json',str(root/'pg-result.json'))
  except FileNotFoundError:pass
finally:s.close()
raise SystemExit(code)
