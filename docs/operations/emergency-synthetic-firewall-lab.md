# Emergency Network Synthetic Firewall Lab

This lab proves emergency routing under a controlled, carrier-like deny policy.
It does not prove behavior on a real Russian mobile network and must never be
reported as `Проверено при реальном БС`.

## Safety boundary

- Run the firewall only inside a disposable Linux network namespace, Windows
  Sandbox, or a dedicated lab VM.
- Do not change the workstation firewall, default route, DNS, or Hiddify.
- Use controlled fixtures only. Do not retain endpoints, UUIDs, Reality keys,
  raw configs, or response bodies in evidence.
- Pin the isolated executor, fixture manifest, firewall policy, payload and exact
  Core binary by SHA-256.
- A run is `PASS` only after the isolated environment reports successful
  teardown. Missing fixtures or isolation is `BLOCKED_BY_ACCESS`, not `PASS`.

## Topology and policy

The disposable lab needs separate client, RU/reserve, owned-RU-hop and
owned-foreign segments. The client segment may reach its controlled RU DNS and
reserve endpoint but must drop direct traffic to the foreign segment. The
reserve segment may reach the owned foreign fixture and the owned RU hop. The
owned RU hop may reach the owned foreign fixture.

The exact Core candidate runs in the client segment. The controlled payload is
served only in the foreign segment. These observations are mandatory:

1. the reserve endpoint is reachable from the client segment;
2. a direct client-to-foreign request is denied by the lab policy;
3. `reserve -> owned foreign` retrieves the authenticated payload and proves
   the owned foreign exit;
4. `reserve -> owned RU hop -> owned foreign` does the same;
5. DNS resolves through the intended controlled chain;
6. teardown completes and the host firewall remains untouched.

## Controller contract

`scripts/emergency_synthetic_firewall_proof.py` does not implement a host
firewall. It invokes one separately reviewed, hash-pinned isolated executor
without a shell, checks a strict redacted JSON result, and derives the verdict.
The executor receives the exact Core path, controlled fixture-manifest path and
expected payload hash on stdin. Its stdout must contain only the documented
result schema; evidence output contains hashes and booleans only.

Preflight with the exact shipped Core:

```powershell
python -B scripts/emergency_synthetic_firewall_proof.py `
  --core-dll C:\path\to\exact\pokrov-core.dll
```

Execution additionally requires absolute paths and independently calculated
SHA-256 values for `--executor` and `--fixture-manifest`, plus
`--expected-payload-sha256` and `--execute`.

## Current local status

The exact POKROV Core 1.0.3 Windows DLL is accepted by the bounded runtime
adapter. The present workstation has no reviewed isolated executor or controlled
fixture manifest, so the synthetic firewall proof remains
`BLOCKED_BY_ACCESS`. This is the expected fail-closed result until those two
dependencies are supplied.
