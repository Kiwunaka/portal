"""Server-side AWG peer removal. Input stays on SSH stdin; output is redacted."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time


CONFIG_ROOT = Path('/etc/amnezia/amneziawg')
AWG = '/usr/local/bin/awg'


class PeerRemovalError(ValueError):
    pass


def _public_key(value: str) -> str:
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, TypeError):
        raise PeerRemovalError('peer_key_invalid') from None
    if len(raw) != 32 or base64.b64encode(raw).decode() != value:
        raise PeerRemovalError('peer_key_invalid')
    return value


def without_peers(raw: bytes, keys: set[str]) -> tuple[bytes, int]:
    """Keep unrelated sections byte-for-byte, including comments and line endings."""
    sections = re.split(rb'(?m)(?=^[ \t]*\[(?:Interface|Peer)\][ \t]*\r?$)', raw)
    kept = []
    removed = 0
    for section in sections:
        if re.match(rb'[ \t]*\[Peer\]', section):
            found = re.findall(rb'(?m)^[ \t]*PublicKey[ \t]*=[ \t]*([^\r\n#]+)', section)
            if len(found) != 1:
                raise PeerRemovalError('peer_config_invalid')
            try:
                key = _public_key(found[0].strip().decode('ascii'))
            except UnicodeError:
                raise PeerRemovalError('peer_config_invalid') from None
            if key in keys:
                removed += 1
                continue
        kept.append(section)
    return b''.join(kept), removed


def _awg(*args: str) -> str:
    result = subprocess.run([AWG, *args], capture_output=True, timeout=5)
    if result.returncode or len(result.stdout) > 262144:
        raise PeerRemovalError('awg_command_failed')
    return result.stdout.decode('ascii').strip()


def remove_peers(request: dict) -> dict:
    import fcntl  # This helper runs on the owned Linux protocol server.

    interface = request.get('interface', '')
    expected = request.get('server_public_key_sha256', '')
    values = request.get('keys')
    if not isinstance(interface, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,15}', interface):
        raise PeerRemovalError('interface_invalid')
    if not isinstance(expected, str) or not re.fullmatch(r'[a-f0-9]{64}', expected):
        raise PeerRemovalError('server_identity_invalid')
    if not isinstance(values, list) or not 1 <= len(values) <= 4096:
        raise PeerRemovalError('peer_batch_invalid')
    keys = {_public_key(value) for value in values}
    path = CONFIG_ROOT / (interface + '.conf')
    lock_fd = os.open(str(CONFIG_ROOT / (interface + '.pokrov-revoke.lock')),
                      os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        deadline = time.monotonic() + 20
        server_public = _public_key(_awg('show', interface, 'public-key'))
        if hashlib.sha256(base64.b64decode(server_public)).hexdigest() != expected:
            raise PeerRemovalError('server_identity_mismatch')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise PeerRemovalError('config_not_regular')
            raw = handle.read(262145)
        if len(raw) > 262144:
            raise PeerRemovalError('config_too_large')
        updated, disk_removed = without_peers(raw, keys)
        live_before = set(_awg('show', interface, 'peers').splitlines())
        if disk_removed:
            backup_dir = CONFIG_ROOT / '.pokrov-revocations'
            backup_dir.mkdir(mode=0o700, exist_ok=True)
            if backup_dir.is_symlink():
                raise PeerRemovalError('backup_path_invalid')
            backup = backup_dir / (interface + '.' + hashlib.sha256(raw).hexdigest() + '.conf')
            try:
                backup_fd = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            except FileExistsError:
                if backup.is_symlink() or backup.read_bytes() != raw:
                    raise PeerRemovalError('backup_conflict') from None
            else:
                with os.fdopen(backup_fd, 'wb') as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=CONFIG_ROOT, prefix=interface + '.', delete=False) as handle:
                    temporary = Path(handle.name)
                    os.fchmod(handle.fileno(), stat.S_IMODE(metadata.st_mode))
                    os.fchown(handle.fileno(), metadata.st_uid, metadata.st_gid)
                    handle.write(updated)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
                temporary = None
                directory_fd = os.open(CONFIG_ROOT, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        # Persist denial first. A failed live command is retried by the worker;
        # restoring the old config here would resurrect the key after reboot.
        for key in sorted(keys & live_before):
            if time.monotonic() >= deadline:
                raise PeerRemovalError('peer_removal_deadline')
            _awg('set', interface, 'peer', key, 'remove')
        live_after = set(_awg('show', interface, 'peers').splitlines())
        if live_after & keys or not (live_before - keys).issubset(live_after):
            raise PeerRemovalError('peer_readback_failed')
        if path.read_bytes() != updated:
            raise PeerRemovalError('config_changed_during_removal')
        return {'ok': True, 'requested': len(keys), 'disk_removed': disk_removed,
                'live_removed': len(live_before & keys), 'persistent_absence_verified': True}
    finally:
        os.close(lock_fd)


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(262145)
        if len(raw) > 262144:
            raise PeerRemovalError('request_too_large')
        request = json.loads(raw)
        if not isinstance(request, dict):
            raise PeerRemovalError('request_invalid')
        result = remove_peers(request)
    except PeerRemovalError as error:
        print(json.dumps({'ok': False, 'code': str(error)}))
        return 1
    except Exception:
        print(json.dumps({'ok': False, 'code': 'peer_removal_failed'}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
