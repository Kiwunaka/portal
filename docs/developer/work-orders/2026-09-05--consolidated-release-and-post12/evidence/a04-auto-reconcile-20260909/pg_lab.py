"""Temporary localhost SSH forwarding to a new database in the owned lab VM."""
from contextlib import contextmanager
import json
import logging
from pathlib import Path
import select
import shlex
import socketserver
import threading

import paramiko
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

logging.getLogger('paramiko.transport').setLevel(logging.CRITICAL)
LAB = Path('E:/r12-b08-linux-lab')


@contextmanager
def postgres_lab(database):
    assert database.startswith('portal_r12_a04_auto_20260909_') and database.replace('_', '').isalnum()
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(str(LAB / 'known_hosts'))
    ssh.connect('127.0.0.1', port=55228, username='root', key_filename=str(LAB / 'private/client.key'),
                allow_agent=False, look_for_keys=False, timeout=10,
                disabled_algorithms={'keys':['ssh-ed25519','ecdsa-sha2-nistp256','ecdsa-sha2-nistp384','ecdsa-sha2-nistp521']})
    prepare = '''
import json,subprocess,sys
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
url=make_url(dotenv_values('/root/portal_bot/.env')['DATABASE_URL'])
database=sys.argv[1]
check=subprocess.run(['runuser','-u','postgres','--','psql','-At','-d','postgres','-c',
    "SELECT count(*) FROM pg_database WHERE datname='"+database+"'"],capture_output=True,text=True)
assert check.returncode==0 and check.stdout.strip()=='0','Preserve existing database'
create=subprocess.run(['runuser','-u','postgres','--','createdb','-O',url.username,database],capture_output=True)
assert create.returncode==0,'Create isolated fixture database failed'
print(json.dumps({'url':url.set(database=database).render_as_string(hide_password=False)}))
'''
    engine = server = None
    try:
        _, out, err = ssh.exec_command('/root/portal_bot/venv/bin/python -B -c ' + shlex.quote(prepare) + ' ' + shlex.quote(database), timeout=30)
        output = out.read()
        if out.channel.recv_exit_status() != 0:
            raise RuntimeError('isolated_database_prepare_failed')
        dsn = make_url(json.loads(output)['url'])

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                channel = ssh.get_transport().open_channel('direct-tcpip', ('127.0.0.1', dsn.port or 5432), self.request.getpeername(), timeout=10)
                try:
                    while True:
                        ready, _, _ = select.select([self.request, channel], [], [], 10)
                        if self.request in ready:
                            data = self.request.recv(65536)
                            if not data: break
                            channel.sendall(data)
                        if channel in ready:
                            data = channel.recv(65536)
                            if not data: break
                            self.request.sendall(data)
                finally:
                    channel.close()

        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True

        server = Server(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        engine = create_engine(dsn.set(host='127.0.0.1', port=server.server_address[1]), hide_parameters=True,
                               connect_args={'options': '-c lock_timeout=15000 -c statement_timeout=20000'})
        yield engine, ssh
    finally:
        if engine is not None: engine.dispose()
        if server is not None:
            server.shutdown()
            server.server_close()
        ssh.close()
