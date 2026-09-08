import hashlib,json
from pathlib import Path
import paramiko
root=Path(__file__).parent
lab=Path('E:/r12-b08-linux-lab')
remote='/opt/r12/a04-managed-revocation-20260908'
s=paramiko.SSHClient();s.load_host_keys(str(lab/'known_hosts'))
s.connect('127.0.0.1',port=55228,username='root',key_filename=str(lab/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
    i,o,e=s.exec_command('/root/portal_bot/venv/bin/python -B '+remote+'/guest-pg-race-v2.py',timeout=180)
    code=o.channel.recv_exit_status();out=o.read();err=e.read()
    # Successful structured output contains only synthetic case summaries.
    if code==0:
        for line in out.decode().splitlines():
            item=json.loads(line);print(json.dumps(item),flush=True)
    else:
        print(json.dumps({'exit_code':code,'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_sha256':hashlib.sha256(err).hexdigest(),'error_tail':err.decode(errors='replace').splitlines()[-2:]}))
    with s.open_sftp() as f:
        try:f.get(remote+'/pg-result-v2.json',str(root/'pg-result-v2.json'))
        except FileNotFoundError:pass
    (root/'pg-execution-v2.json').write_bytes((json.dumps({'exit_code':code,'stdout_sha256':hashlib.sha256(out).hexdigest(),'stderr_sha256':hashlib.sha256(err).hexdigest()},indent=2)+'\n').encode())
finally:s.close()
raise SystemExit(code)
