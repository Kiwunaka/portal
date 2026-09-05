# WO-013HM — candidate.33 fresh npm advisory audit

Date: 2026-09-05. Status: `PASS_EXACT_LOCKFILES_FRESH_NPM_AUDIT`.

## Scope and result

The canonical npm registry now answers the exact candidate.33 audit requests.
This supersedes only WO-013GU's fresh-npm-audit timeout boundary. All three
commands exit 0 and report zero known advisories at every severity, including
development dependencies. This is a point-in-time npm advisory result, not
proof that the applications have no defects or that all supply-chain gates pass.

Source: `f5300053026d32826e54c02202303e1f68c65bc1`, detached clean worktree
`E:/POKROV-tools/wt/platform-candidate33-merged-source`.
Toolchain: Node `v22.14.0`, npm `10.9.2` from
`E:/POKROV-tools/runtimes/node-v22.14.0-win-x64`.
Origin: current local Windows host, not Brain or RU-device origin evidence.

Run independently in `webapp`, `adminapp`, and `marketing`:

```text
node.exe <runtime>/node_modules/npm/bin/npm-cli.js audit --json --package-lock-only --ignore-scripts --registry=https://registry.npmjs.org --fetch-retries=0 --fetch-timeout=25000
```

| Lane | Lockfile SHA-256 before and after | npm dependency total | Known advisories |
| --- | --- | --- | --- |
| webapp | `6b303f41e2a39f4767d72c3f0fe48e52fa2ba2d64637fb4e7b0bb6fcaf2e1aa4` | 474 | 0 |
| adminapp | `ce55397a7e036ddf6e29c1e0a0754c71e8f636f2b96a0bf7b2f5ebe36c29cf6a` | 488 | 0 |
| marketing | `b7545ef35566448fc6e7794fc6c094fb31fd9b982f869631a1d19e5d2269452d` | 448 | 0 |

Full npm JSON stdout is retained under
`evidence/013HM-candidate33-fresh-npm-audit/`:

| Report | Bytes | SHA-256 |
| --- | --- | --- |
| `webapp-npm-audit.json` | 364 | `f7546173c7a595b4cb6fedd8f0b0f824d2e17267a8bafe36e52d614a90dcf39e` |
| `adminapp-npm-audit.json` | 364 | `4ba7cb83fbc05f670d7ce1d4f90e6f8bb551cb9ba3b04a1e98da41b8d11fa0ca` |
| `marketing-npm-audit.json` | 364 | `e399ef1aec675eae273b5f6524935bde86b35fb4acfc0f5578a84a7d015daa42` |

## Boundaries

No dependency install, update, audit fix, source edit, build, deployment,
publication, host/guest network change or new candidate occurred. The exact
source worktree remains clean and all three lockfile hashes are unchanged.
Prior timeout evidence is retained. This result updates the dependency and
Gate E execution notes without changing their levels or aggregate Gate F.
Managed Windows/Android, first-connect scope, authenticated journeys,
provider/Operator and named-origin gates remain open independently.
