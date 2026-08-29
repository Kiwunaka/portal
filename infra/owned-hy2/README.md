# POKROV owned HY2 server bundle

This directory is the reviewed source for the first bounded Hysteria2 server
artifact. It is not a deployment and does not contain runtime material.

`config.template.json` accepts exactly one UDP listener on port 443, verified
TLS 1.3 with ALPN `h3`, one password-authenticated owner user and Salamander
obfuscation. Port hopping, Gecko, Mimic, raw URIs, integrated TUN and plaintext
runtime credentials in the bundle are out of scope.

Build and verify from the platform root:

```powershell
python -B scripts/build_owned_hy2_server_bundle.py build --core-root E:\path\to\POKROV-core --go-executable E:\path\to\go.exe --output E:\safe\pokrov-hy2-server.zip
python -B scripts/build_owned_hy2_server_bundle.py verify --bundle E:\safe\pokrov-hy2-server.zip
python -B scripts/build_owned_hy2_server_bundle.py plan --bundle E:\safe\pokrov-hy2-server.zip --operation install --node-code de
python -B scripts/build_owned_hy2_server_bundle.py plan --bundle E:\safe\pokrov-hy2-server.zip --operation rollback --node-code de
```

The build requires clean candidate.6 Core commit
`a45d69e40ed7d892619a2b5c4592a527f630665e`, compiles the pinned embedded
sing-box source twice for Linux amd64, requires byte-identical binaries and
runs `sing-box check` on a temporary synthetic configuration using the same
source and build tag. The deterministic ZIP retains the GPL license and exact
source/toolchain provenance.

Runtime material must be generated or obtained outside the repository and
written directly to `/etc/pokrov-hy2/config.json` with owner-only permissions.
Never store the rendered config, certificate key, passwords, endpoint or raw
device identity in Git, the bundle, command-line arguments or retained JSON.

The service is packaged but not enabled. An authorized installer must retain
the previous current-pointer/config/unit/firewall receipt under the declared
backup root before mutation. Rollback first kills the lab, proves its UDP
listener absent, restores only the exact receipt-bound previous state and then
re-runs inactive/health readback. No Brain or delivery-node mutation is
authorized by these files.
