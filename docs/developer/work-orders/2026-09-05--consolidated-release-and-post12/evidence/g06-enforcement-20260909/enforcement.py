"""One-shot G06 readback/apply for the three owned promotion branches."""
import argparse
import datetime
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).parent
PLATFORM = pathlib.Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
REGISTRY = PLATFORM / 'shared/release-1.2.0-stop-ship-regressions.json'
registry = json.loads(REGISTRY.read_text(encoding='utf-8'))
controls = next(x['hosted_controls'] for x in registry['entries'] if x['id'] == 'REL-001')


def api(endpoint, method='GET', payload=None):
    args = ['gh', 'api', '--method', method, endpoint]
    if payload is not None:
        args += ['--input', '-']
    result = subprocess.run(args, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, encoding='utf-8')
    parsed = json.loads(result.stdout) if result.stdout.strip() else None
    return {'endpoint': endpoint, 'method': method, 'exit_code': result.returncode,
            'response': parsed, 'stderr': result.stderr.strip()}


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=['prepare', 'apply', 'readback'])
phase = parser.parse_args().phase
observations = []
for control in controls:
    repo, branch = control['repository'], control['branch']
    endpoint = f'repos/{repo}/branches/{branch}/protection'
    label = repo.split('/')[1]
    if phase == 'prepare':
        meta = api(f'repos/{repo}')
        assert meta['exit_code'] == 0
        data = meta['response']
        assert data['visibility'] == 'public' and data['permissions']['admin']
        protection = api(endpoint)
        assert protection['response']['message'] == 'Branch not protected'
        rules = api(f'repos/{repo}/rulesets')
        assert rules['exit_code'] == 0 and rules['response'] == []
        checks = api(f'repos/{repo}/commits/{branch}/check-runs')
        assert checks['exit_code'] == 0
        assert any(x['app']['id'] == 15368 and x['app']['slug'] == 'github-actions'
                   for x in checks['response']['check_runs'])
        payload = {
            'required_status_checks': {'strict': True, 'checks': [
                {'context': name, 'app_id': 15368} for name in control['required_checks']]},
            'enforce_admins': True,
            'required_pull_request_reviews': {
                'dismiss_stale_reviews': True, 'require_code_owner_reviews': False,
                'required_approving_review_count': 0, 'require_last_push_approval': False},
            'restrictions': None, 'required_linear_history': True,
            'allow_force_pushes': False, 'allow_deletions': False,
            'block_creations': False, 'required_conversation_resolution': True,
            'lock_branch': False, 'allow_fork_syncing': False,
        }
        save(f'{label}-request.json', payload)
        observations.append({'repository': repo, 'branch': branch,
                             'visibility': data['visibility'], 'admin_access': True,
                             'before': protection, 'rulesets': rules,
                             'request_file': f'{label}-request.json',
                             'signature_followup': {'method': 'POST', 'endpoint': endpoint + '/required_signatures'}})
    elif phase == 'apply':
        before = api(endpoint)
        assert before['response'].get('message') == 'Branch not protected', 'Concurrent protection change'
        rules = api(f'repos/{repo}/rulesets')
        assert rules['exit_code'] == 0 and rules['response'] == [], 'Concurrent ruleset change'
        payload = json.loads((ROOT / f'{label}-request.json').read_text(encoding='utf-8'))
        changed = api(endpoint, 'PUT', payload)
        save(f'{label}-put.json', changed)
        assert changed['exit_code'] == 0, changed['stderr']
        signed = api(endpoint + '/required_signatures', 'POST')
        save(f'{label}-signatures.json', signed)
        assert signed['exit_code'] == 0 and signed['response']['enabled'] is True
        observations.append({'repository': repo, 'protection': changed, 'signatures': signed})
    else:
        actual = api(endpoint)
        assert actual['exit_code'] == 0
        rules = api(f'repos/{repo}/rulesets')
        assert rules['exit_code'] == 0
        observations.append({'repository': repo, 'branch': branch, 'protection': actual, 'rulesets': rules})

save(f'{phase}.json', {'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'origin': 'current-origin GitHub REST', 'observations': observations})
print(f'{phase}: retained {len(observations)} repository observations')
