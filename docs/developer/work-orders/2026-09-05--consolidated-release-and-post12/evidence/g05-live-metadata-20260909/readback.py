"""Read public release metadata and compare its separate declared owners."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import urllib.error
import urllib.parse
import urllib.request

root = pathlib.Path(__file__).parent
client = pathlib.Path('E:/r12client')
platform = pathlib.Path('C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start')
checks = []


def check(name, condition):
    checks.append({'name': name, 'result': 'PASS' if condition else 'FAIL'})


def save(name, value):
    (root / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def github(endpoint):
    result = subprocess.run(['gh', 'api', endpoint], capture_output=True, text=True, encoding='utf-8')
    return result.returncode, json.loads(result.stdout)


def get_apps(label, params=None):
    url = 'https://app.pokrov.space/api/public/client-apps'
    if params:
        url += '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        body = response.read()
        metadata = {'url': url, 'http_status': response.status,
                    'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'date': response.headers.get('Date'), 'cache_control': response.headers.get('Cache-Control'),
                    'response_sha256': hashlib.sha256(body).hexdigest()}
    (root / f'{label}-body.json').write_bytes(body)
    save(f'{label}-request.json', metadata)
    return json.loads(body)


owners = {}
for name in ['release-handoff.seed.json', 'cutover-readiness.seed.json', 'runtime-artifacts.seed.json']:
    path = client / 'config' / name
    owners[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'data': json.loads(path.read_text(encoding='utf-8'))}
release = owners['release-handoff.seed.json']['data']
cutover = owners['cutover-readiness.seed.json']['data']
runtime = owners['runtime-artifacts.seed.json']['data']
public = release['latest_repo_backed_release']
target = release['release_truth']['development_target']
candidate = cutover['exact_replacement_candidate']

exit_code, latest = github('repos/Kiwunaka/pokrov/releases/latest')
assert exit_code == 0
safe_latest = {key: latest[key] for key in ['id', 'tag_name', 'draft', 'prerelease', 'published_at']}
safe_latest['assets'] = [{key: asset[key] for key in ['id', 'name', 'size', 'digest', 'browser_download_url']}
                         for asset in latest['assets']]
save('github-latest-release.json', safe_latest)
check('latest_public_release_matches_owner', latest['tag_name'] == public['tag'] and not latest['draft'] and not latest['prerelease'])
remote_assets = {asset['name']: asset for asset in latest['assets']}
for asset in public['artifacts']:
    live = remote_assets.get(asset['file_name'], {})
    check('public_asset:' + asset['file_name'], live.get('size') == asset['size_bytes']
          and live.get('digest', '').lower() == 'sha256:' + asset['sha256'].lower()
          and live.get('browser_download_url') == asset['url'])

exit_code, listed = github('repos/Kiwunaka/pokrov/releases?per_page=100')
assert exit_code == 0 and len(listed) < 100, 'Complete release listing required'
save('github-release-list.json', [{k: item[k] for k in ['id', 'tag_name', 'draft', 'prerelease', 'published_at']} for item in listed])
check('no_new_target_or_candidate_release_object', not any(target['product_version'] in item['tag_name'] or candidate['id'] == item['tag_name'] for item in listed))
exit_code, artifact = github(f'repos/Kiwunaka/pokrov/actions/artifacts/{candidate["signed_contract"]["actions_artifact_id"]}')
assert exit_code == 0
save('candidate-artifact.json', {k: artifact[k] for k in ['id', 'name', 'digest', 'expired', 'expires_at', 'workflow_run']})
check('private_candidate_artifact_matches_owner', not artifact['expired']
      and artifact['digest'] == candidate['signed_contract']['actions_artifact_digest']
      and artifact['workflow_run']['head_sha'] == candidate['sources']['release_index'])

apps = get_apps('public-catalog')
check('api_platform_versions_match_public_owner', apps['android']['version'] == apps['windows']['version'] == public['version'])
by_abi = {asset.get('abi'): asset for asset in public['artifacts'] if asset['platform'] == 'android'}
for variant in apps['android']['apk_variants']:
    expected = by_abi.get(variant['abi'], {})
    check('api_android_variant:' + variant['abi'], variant['url'] == expected.get('url')
          and variant['sha256'].lower() == expected.get('sha256', '').lower()
          and variant['size'] == expected.get('size_bytes'))
check('api_all_direct_android_variants_present', {x['abi'] for x in apps['android']['apk_variants']} == set(by_abi))
check('api_primary_is_arm64', apps['android']['apk_url'] == by_abi['arm64-v8a']['url'])
windows = next(asset for asset in public['artifacts'] if asset['file_name'] == 'pokrov-windows-setup-x64.exe')
check('api_windows_matches_owner', apps['windows']['exe_url'] == windows['url']
      and apps['windows']['sha256'].lower() == windows['sha256'].lower()
      and apps['windows']['size'] == windows['size_bytes'])
check('no_store_or_private_candidate_in_public_catalog', not apps['android']['play_url']
      and candidate['id'] not in json.dumps(apps) and target['product_version'] not in json.dumps(apps))
pointer_path = client / 'artifacts/releases/release-handoff.json'
pointer = json.loads(pointer_path.read_text(encoding='utf-8'))
check('legacy_pointer_matches_public_version', pointer['schema_version'] == 1 and pointer['version'] == public['version'])
check('legacy_public_release_has_no_false_v2_manifest', apps['release_manifest'] is None)

newer = get_apps('development-version-query', {'platform': 'windows', 'current_version': target['product_version']})
check('development_version_is_not_forced_back_to_public', newer['windows']['update']['latest_version'] == public['version']
      and newer['windows']['update']['update_policy'] == 'none')
older = get_apps('old-version-query', {'platform': 'android', 'current_version': '1.1.5'})
check('old_version_gets_actual_public_update', older['android']['update']['latest_version'] == public['version']
      and older['android']['update']['update_policy'] == 'required')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

redirects = []
opener = urllib.request.build_opener(NoRedirect())
for kind, expected in [('android-arm64', by_abi['arm64-v8a']['url']), ('windows-x64', windows['url'])]:
    url = 'https://app.pokrov.space/api/public/downloads/' + kind
    try:
        response = opener.open(url, timeout=30)
    except urllib.error.HTTPError as response:
        status, location = response.code, response.headers.get('Location')
        response.close()
    else:
        status, location = response.status, response.headers.get('Location')
        response.close()
    redirects.append({'url': url, 'status': status, 'location': location})
    check('current_download_redirect:' + kind, status == 307 and location == expected)
save('download-redirects.json', redirects)

exit_code, latest_core = github('repos/Kiwunaka/pokrov-core/releases/latest')
assert exit_code == 0
save('github-latest-core.json', {k: latest_core[k] for k in ['id', 'tag_name', 'draft', 'prerelease', 'published_at']})
exit_code, tag = github('repos/Kiwunaka/pokrov-core/git/ref/tags/v' + runtime['core']['version'])
save('development-core-tag.json', {'exit_code': exit_code, 'response': tag})
check('current_core_is_distinct_from_published_core', latest_core['tag_name'] == runtime['core']['retained_public_release']['release_tag']
      and exit_code != 0 and tag.get('status') == '404' and runtime['core']['release_tag_created'] is False)
check('development_is_not_candidate_or_promotion', target['candidate_created'] is False
      and runtime['core']['artifact_provenance']['candidate_created'] is False
      and runtime['core']['artifact_provenance']['promotion_authorized'] is False)
check('private_candidate_is_not_public_or_promoted', candidate['public_release_created'] is False
      and candidate['promotion_authorized'] is False and candidate['stable_pointer_mutated'] is False)
check('private_candidate_core_differs_from_development', candidate['sources']['core'] != runtime['core']['source_commit'])
signature = json.loads((root / 'windows-candidate-authenticode-named.json').read_text(encoding='utf-8-sig'))
check('manifest_signature_is_not_authenticode', signature['status'] == 'NotSigned'
      and signature['sha256'] == candidate['windows_setup']['sha256']
      and candidate['windows_setup']['signing'] == 'SKIPPED_BY_OWNER_DIRECT_BETA_ONLY')

report = {'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'origin': 'current-origin anonymous production HTTP and authenticated GitHub API',
          'owner_file_hashes': {name: item['sha256'] for name, item in owners.items()},
          'legacy_pointer_sha256': hashlib.sha256(pointer_path.read_bytes()).hexdigest(),
          'public_version': public['version'], 'development_target': target,
          'private_candidate': {'id': candidate['id'], 'sources': candidate['sources'],
                                'windows_signing': candidate['windows_setup']['signing']},
          'runtime_core': {'version': runtime['core']['version'], 'source_commit': runtime['core']['source_commit']},
          'source_heads': {name: subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
                           for name, path in [('platform', platform), ('client', client)]},
          'checks': checks, 'result': 'PASS' if all(x['result'] == 'PASS' for x in checks) else 'FAIL',
          'mutation_performed': False, 'binary_download_performed': False}
save('result.json', report)
print(json.dumps({'result': report['result'], 'checks': len(checks), 'failures': [x['name'] for x in checks if x['result'] != 'PASS']}))
raise SystemExit(0 if report['result'] == 'PASS' else 1)
