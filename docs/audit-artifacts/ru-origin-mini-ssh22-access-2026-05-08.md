# RU-Origin Mini SSH 22 Access Check

Generated: 2026-05-08

## Command

```powershell
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -p 22 root@176.123.166.119 "echo RU_ORIGIN_SSH_22_OK"
```

## Result

```text
root@176.123.166.119: Permission denied (publickey,password).
```

## Classification

RU-origin fresh rerun remains `BLOCKED_BY_ACCESS` from this workstation. Port 22 is reachable enough to request authentication, but the current shell does not have accepted non-interactive credentials for `root@176.123.166.119`.
