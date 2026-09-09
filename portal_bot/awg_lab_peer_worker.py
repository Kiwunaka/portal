"""Reconcile revoked/expired owned AWG lab peers from retained material rows."""
from __future__ import annotations

import asyncio
import base64
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import shlex

import paramiko

import awg2_lab_service as awg2
import awg31_lab_service as awg31
from awg_lab_key_binding import _client_public_key, lock_awg_device_key
from models import Account, AccountDevice, Awg2LabMaterial, Awg31LabMaterial, User
from network_rollout import load_network_rollout_config
from ssh_host_keys import configure_ssh_host_key_policy


logger = logging.getLogger(__name__)
PROFILES = {'awg2_lab': (Awg2LabMaterial, awg2), 'awg31_lab': (Awg31LabMaterial, awg31)}


class PeerReconcileError(ValueError):
    pass


def configured_targets() -> list[dict]:
    raw = os.getenv('AWG_LAB_PEER_TARGETS_FILE', '').strip()
    if not raw:
        return []
    try:
        targets = json.loads(Path(raw).read_text(encoding='utf-8'))
        required = {'profile', 'node_code', 'server_record_id', 'host', 'port', 'username',
                    'key_file', 'known_hosts', 'interface', 'server_public_key_sha256'}
        if not isinstance(targets, list) or not targets:
            raise ValueError()
        identities = set()
        for target in targets:
            if not isinstance(target, dict) or set(target) != required:
                raise ValueError()
            if target['profile'] not in PROFILES or not all(target[key] for key in required):
                raise ValueError()
            if not isinstance(target['port'], int) or not 1 <= target['port'] <= 65535:
                raise ValueError()
            identity = (target['profile'], target['node_code'], target['server_record_id'])
            if identity in identities:
                raise ValueError()
            identities.add(identity)
        return targets
    except Exception:
        raise PeerReconcileError('peer_targets_invalid') from None


def _utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def _retire_binding(session, *, model, tg_id, install_id, target, policy, now) -> int:
    # Same order as guarded material replacement: user, device, then material.
    user = session.query(User).filter_by(tg_id=tg_id).with_for_update().first()
    device = None
    account = None
    if user is not None and user.account_id:
        account = session.get(Account, str(user.account_id))
        device = (session.query(AccountDevice)
                  .filter_by(account_id=str(user.account_id), install_id=install_id)
                  .with_for_update().first())
    access = bool(user is not None and user.is_active and user.expiry_at and _utc(user.expiry_at) > now)
    if user is not None and user.account_id:
        access = bool(access and account is not None and account.status == 'active'
                      and device is not None and device.state == 'active' and device.revoked_at is None)
    else:
        # Managed lab issuance requires a canonical active device claim.
        access = False
    rows = (session.query(model).filter_by(tg_id=tg_id, install_id=install_id,
            node_code=target['node_code'], server_record_id=target['server_record_id'])
            .order_by(model.id).with_for_update().all())
    cutoff = now - timedelta(hours=policy['material_max_age_hours'])
    changed = 0
    for row in rows:
        if row.is_active and row.state == 'ready' and (not access or _utc(row.provisioned_at) < cutoff):
            row.is_active = False
            row.state = 'revoked'
            row.revoked_at = row.revoked_at or now
            row.updated_at = now
            changed += 1
    return changed


def removal_keys(session, *, target: dict, now: datetime) -> tuple[list[str], int]:
    """Seal retired unique keys before sending an idempotent server deletion."""
    model, service = PROFILES[target['profile']]
    groups = defaultdict(list)
    try:
        session.flush()
        for row in session.query(model).order_by(model.id).yield_per(100):
            endpoint = service._decrypt_endpoint(row.endpoint_ciphertext)
            public = _client_public_key(endpoint)
            groups[public].append(row)
    except Exception:
        raise PeerReconcileError('material_key_binding_unavailable') from None
    keys = []
    shared = 0
    for public, rows in groups.items():
        session.flush()
        lock_awg_device_key(session, model=model, public=public)
        # A first insertion or reissue may have committed while this scan was
        # waiting for the key lock. Read that committed state before sealing it.
        try:
            rows = [row for row in session.query(model).populate_existing().order_by(model.id)
                    if _client_public_key(service._decrypt_endpoint(row.endpoint_ciphertext)) == public]
        except Exception:
            raise PeerReconcileError('material_key_binding_unavailable') from None
        selected = [row for row in rows if row.node_code == target['node_code']
                    and row.server_record_id == target['server_record_id']]
        if not selected:
            continue
        if len({(row.tg_id, row.install_id) for row in rows}) != 1:
            shared += 1
            continue
        if any(row.is_active and row.state == 'ready' for row in rows):
            continue
        # A rotated key with no active copy also becomes permanently revoked;
        # the previous rotation timestamp and encrypted bytes stay retained.
        for row in rows:
            if row.state != 'revoked':
                row.is_active = False
                row.state = 'revoked'
                row.revoked_at = row.revoked_at or now
                row.updated_at = now
        keys.append(base64.b64encode(public).decode())
    return keys, shared


def remove_remote_peers(target: dict, keys: list[str]) -> dict:
    helper = Path(__file__).with_name('awg_peer_remove.py').read_text(encoding='utf-8')
    client = configure_ssh_host_key_policy(paramiko.SSHClient(),
            known_hosts_path=target['known_hosts'], allow_trust_on_first_use=False)
    try:
        client.connect(target['host'], port=target['port'], username=target['username'],
                       key_filename=target['key_file'], allow_agent=False, look_for_keys=False,
                       timeout=10, auth_timeout=10, banner_timeout=10)
        stdin, stdout, stderr = client.exec_command('python3 -c ' + shlex.quote(helper), timeout=30)
        stdin.write(json.dumps({'interface': target['interface'], 'keys': keys,
                                'server_public_key_sha256': target['server_public_key_sha256']}))
        stdin.flush()
        stdin.channel.shutdown_write()
        raw = stdout.read(4097)
        error = stderr.read(4097)
        code = stdout.channel.recv_exit_status()
        if code or error or len(raw) > 4096:
            raise PeerReconcileError('peer_removal_failed')
        result = json.loads(raw)
        if result.get('ok') is not True or result.get('persistent_absence_verified') is not True:
            raise PeerReconcileError('peer_removal_unverified')
        return {key: int(result[key]) for key in ('requested', 'disk_removed', 'live_removed')}
    except PeerReconcileError:
        raise
    except Exception:
        raise PeerReconcileError('peer_removal_unavailable') from None
    finally:
        client.close()


def reconcile_awg_peers(session_factory, *, targets: list[dict], now=None, remove=remove_remote_peers) -> dict:
    current = _utc(now or datetime.now(timezone.utc))
    result = {'targets': len(targets), 'retired': 0, 'shared_keys_blocked': 0,
              'disk_removed': 0, 'live_removed': 0, 'failed_targets': 0, 'errors': {}}
    for target in targets:
        model, service = PROFILES[target['profile']]
        try:
            with session_factory() as session:
                config = load_network_rollout_config(session=session)
                normalize = service.normalize_awg2_lab_config if model is Awg2LabMaterial else service.normalize_awg31_lab_config
                policy = normalize(config.get(target['profile']))
                bindings = (session.query(model.tg_id, model.install_id)
                            .filter_by(node_code=target['node_code'], server_record_id=target['server_record_id'])
                            .distinct().order_by(model.tg_id, model.install_id).all())
                retired = 0
                for tg_id, install_id in bindings:
                    retired += _retire_binding(session, model=model, tg_id=tg_id,
                        install_id=install_id, target=target, policy=policy, now=current)
                keys, shared = removal_keys(session, target=target, now=current)
                # Commit denial before the network boundary. A crash leaves
                # durable revoked rows for the next scan, never a false success.
                session.commit()
            result['retired'] += retired
            result['shared_keys_blocked'] += shared
            if keys:
                removed = remove(target, keys)
                result['disk_removed'] += removed['disk_removed']
                result['live_removed'] += removed['live_removed']
        except Exception as error:
            result['failed_targets'] += 1
            code = str(error) if isinstance(error, PeerReconcileError) else 'database_or_material_failed'
            result['errors'][code] = result['errors'].get(code, 0) + 1
    return result


async def awg_lab_peer_worker_job() -> None:
    from db import SessionLocal

    while True:
        try:
            targets = configured_targets()
            report = await asyncio.to_thread(reconcile_awg_peers, SessionLocal, targets=targets)
            if any(report[key] for key in ('retired', 'shared_keys_blocked', 'disk_removed', 'live_removed', 'failed_targets')):
                logger.info('awg_lab_peer_reconcile result=%s', report)
        except Exception:
            logger.error('awg_lab_peer_reconcile code=configuration_or_database_unavailable')
        await asyncio.sleep(30)
