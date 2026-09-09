from __future__ import annotations

import base64
from datetime import datetime, timedelta
from pathlib import Path
import sys
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'portal_bot'))
import awg_lab_peer_worker as worker
from awg_lab_key_binding import AwgDeviceKeyError, _client_public_key, require_awg_device_key_binding
from awg_peer_remove import without_peers
from models import Account, AccountDevice, Base, User


NOW = datetime(2026, 9, 9, 0, 0, 0)


@pytest.fixture(params=['awg2_lab', 'awg31_lab'])
def lab(request, monkeypatch):
    profile = request.param
    model, service = worker.PROFILES[profile]
    monkeypatch.setenv(profile.upper() + '_MATERIAL_SECRET', 'peer-worker-isolated-fixture')
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    target = {'profile': profile, 'node_code': 'fixture', 'server_record_id': 'fixture-server'}
    policy = {profile: {'material_max_age_hours': 168}}
    monkeypatch.setattr(worker, 'load_network_rollout_config', lambda **_: policy)

    def seed(index, *, private=None, state='ready', age_days=0, expired=False):
        account_id = str(uuid.uuid4())
        endpoint = {'private_key': base64.b64encode(private or bytes([index]) * 32).decode()}
        with Session.begin() as session:
            session.add(Account(id=account_id, status='active'))
            session.add(AccountDevice(id=str(uuid.uuid4()), account_id=account_id,
                install_id='fixture-' + str(index), state='active', credential_version=1))
            session.add(User(tg_id=index, uuid=str(uuid.uuid4()), account_id=account_id,
                app_install_id='fixture-' + str(index), is_active=True, sub_type='PAID',
                expiry_at=NOW + timedelta(days=-1 if expired else 1)))
            row = model(tg_id=index, install_id='fixture-' + str(index),
                contract_id='fixture', contract_sha256='a' * 64, generation='fixture',
                endpoint_revision='fixture', server_record_id='fixture-server', node_code='fixture',
                endpoint_ciphertext=service._encrypt_endpoint(endpoint), material_hash='b' * 64,
                is_active=state == 'ready', state=state, provisioned_at=NOW - timedelta(days=age_days))
            session.add(row)
            session.flush()
            return row.id, base64.b64encode(_client_public_key(endpoint)).decode(), endpoint

    try:
        yield Session, target, model, service, seed
    finally:
        engine.dispose()


def test_revoke_survives_remote_failure_then_retries_without_removing_other_device(lab):
    Session, target, model, service, seed = lab
    first_id, first_key, first_endpoint = seed(1)
    second_id, second_key, _ = seed(2)
    with Session.begin() as session:
        device = session.query(AccountDevice).filter_by(install_id='fixture-1').one()
        device.state = 'revoked'
        device.revoked_at = NOW
    calls = []

    def remote(_target, keys):
        calls.append(keys)
        assert keys == [first_key] and second_key not in keys
        with Session() as session:
            assert session.get(model, first_id).state == 'revoked'
            assert session.get(model, second_id).is_active
        if len(calls) == 1:
            raise RuntimeError('synthetic transport failure')
        return {'requested': 1, 'disk_removed': 1, 'live_removed': 1}

    failed = worker.reconcile_awg_peers(Session, targets=[target], now=NOW, remove=remote)
    assert failed['failed_targets'] == 1 and failed['live_removed'] == 0
    passed = worker.reconcile_awg_peers(Session, targets=[target], now=NOW, remove=remote)
    assert passed['failed_targets'] == 0 and passed['live_removed'] == 1
    with Session() as session:
        with pytest.raises(AwgDeviceKeyError, match='material_key_revoked'):
            require_awg_device_key_binding(session, model=model, decrypt_endpoint=service._decrypt_endpoint,
                endpoint=first_endpoint, tg_id=1, install_id='fixture-1')


def test_expiry_retires_entitlement_and_material_age_but_shared_key_is_blocked(lab):
    Session, target, model, _, seed = lab
    expired_id, expired_key, _ = seed(1, expired=True)
    aged_id, aged_key, _ = seed(2, age_days=8)
    shared_id, shared_key, _ = seed(3, private=bytes([5]) * 32, expired=True)
    other_id, _, _ = seed(4, private=bytes([5]) * 32)
    seen = []

    def remote(_target, keys):
        seen.extend(keys)
        return {'requested': len(keys), 'disk_removed': len(keys), 'live_removed': len(keys)}

    report = worker.reconcile_awg_peers(Session, targets=[target], now=NOW, remove=remote)
    assert set(seen) == {expired_key, aged_key} and shared_key not in seen
    assert report['retired'] == 3 and report['shared_keys_blocked'] == 1
    with Session() as session:
        assert all(session.get(model, key).state == 'revoked' for key in (expired_id, aged_id, shared_id))
        assert session.get(model, other_id).is_active


def test_rotation_removes_retired_key_but_keeps_active_key_and_ciphertext(lab):
    Session, target, model, service, seed = lab
    old_id, old_key, _ = seed(1, state='rotated')
    with Session.begin() as session:
        old = session.get(model, old_id)
        ciphertext = old.endpoint_ciphertext
        old.revoked_at = NOW - timedelta(hours=1)
        fresh_endpoint = {'private_key': base64.b64encode(bytes([9]) * 32).decode()}
        fresh = model(tg_id=old.tg_id, install_id=old.install_id,
            contract_id=old.contract_id, contract_sha256=old.contract_sha256, generation='fresh',
            endpoint_revision=old.endpoint_revision, node_code=old.node_code,
            server_record_id=old.server_record_id, material_hash='c' * 64,
            endpoint_ciphertext=service._encrypt_endpoint(fresh_endpoint), is_active=True,
            state='ready', provisioned_at=NOW)
        session.add(fresh)
    seen = []
    def remote(_target, keys):
        seen.extend(keys)
        return {'requested': len(keys), 'disk_removed': len(keys), 'live_removed': len(keys)}
    report = worker.reconcile_awg_peers(Session, targets=[target], now=NOW, remove=remote)
    assert seen == [old_key] and report['failed_targets'] == 0
    with Session() as session:
        old = session.get(model, old_id)
        assert old.endpoint_ciphertext == ciphertext and old.state == 'revoked'
        assert old.revoked_at == NOW - timedelta(hours=1)
        assert session.query(model).filter_by(is_active=True).count() == 1


def test_server_config_removes_only_selected_peer_and_preserves_other_bytes():
    a = base64.b64encode(bytes([1]) * 32).decode()
    b = base64.b64encode(bytes([2]) * 32).decode()
    interface = b'[Interface]\r\n# keep original formatting\r\nListenPort = 4500\r\n\r\n'
    first = ('[Peer]\r\nPublicKey = ' + a + '\r\nAllowedIPs = 10.0.0.2/32\r\n\r\n').encode()
    second = ('[Peer]\r\nPublicKey = ' + b + '\r\nAllowedIPs = 10.0.0.3/32\r\n').encode()
    updated, removed = without_peers(interface + first + second, {a})
    assert removed == 1 and updated == interface + second
    assert without_peers(updated, {a}) == (updated, 0)
