import argparse,json,shlex,sys
from pathlib import Path
import paramiko
ROOT=Path(__file__).parent
LAB=Path('E:/r12-b08-linux-lab')
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('command');p.add_argument('--upload',nargs='*',default=[]);p.add_argument('--download',nargs='*',default=[]);a=p.parse_args()
assert a.label.replace('-','').isalnum()
log=ROOT/(a.label+'.log');assert not log.exists()
s=paramiko.SSHClient();s.load_host_keys(str(LAB/'known_hosts'));s.connect('127.0.0.1',port=55228,username='root',key_filename=str(LAB/'private/client.key'),allow_agent=False,look_for_keys=False,timeout=10)
try:
 f=s.open_sftp()
 if a.upload:
  try:f.stat('/opt/r12/integrated-input-20260908')
  except FileNotFoundError:f.mkdir('/opt/r12/integrated-input-20260908',0o700)
 for n in a.upload:
  assert Path(n).name==n;f.put(str(ROOT/n),'/opt/r12/integrated-input-20260908/'+n)
 _,o,e=s.exec_command(a.command,timeout=180);code=o.channel.recv_exit_status();out=o.read().decode();err=e.read().decode()
 # Lab scripts emit only bounded summaries; unexpected stderr is not echoed or retained locally.
 log.write_text(out+'\nexit_code='+str(code)+'\nstderr_bytes='+str(len(err.encode()))+'\n')
 for n in a.download:
  assert Path(n).name==n;assert not (ROOT/n).exists();f.get('/opt/r12/integrated-compat-20260908/'+n,str(ROOT/n))
 print(out.strip());print('exit_code',code,'stderr_bytes',len(err.encode()));sys.exit(code)
finally:s.close()
