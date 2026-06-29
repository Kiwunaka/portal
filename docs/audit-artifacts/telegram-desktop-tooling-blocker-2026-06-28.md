# Telegram Desktop Tooling Blocker

Date: 2026-06-28

Classification: `BLOCKED_BY_ACCESS`

Scope: Q-004 real Telegram WebApp/session execution attempt from the current
Codex session.

## Checks

Telegram Desktop process check:

```powershell
Get-Process | Where-Object { $_.MainWindowTitle -match 'POKROV|Telegram' } | Select-Object ProcessName, Id, MainWindowTitle
```

Observed process:

```text
ProcessName: Telegram
MainWindowTitle: TelegramDesktop
```

Tool discovery:

```text
tool_search query: computer-use Telegram Desktop desktop control app plugin screenshot click installed
```

Callable tools exposed after discovery:

```text
mcp__node_repl
mcp__next_devtools
mcp__playwright
mcp__codex_apps__netlify
```

Install candidate check:

```text
list_available_plugins_to_install
```

Result: no `computer-use`, `Telegram`, or `Telegram Desktop` plugin candidate was
available to install or make callable in this session.

## Result

The agent can see that Telegram Desktop is running, but this Codex session does
not expose a callable desktop-control tool for opening the real Telegram WebApp,
capturing redacted screenshots, or executing the real user-session flow. Browser
and synthetic signed-initData checks do not replace this gate because they do not
prove a real Telegram WebApp user session.

## Remaining Evidence Needed

Provide one of:

- redacted owner/operator evidence for `OWNER-GATE-TELEGRAM-WEBAPP-SESSION`
- a future session where a callable desktop-control tool is exposed and the
  owner explicitly allows opening the POKROV Telegram WebApp
- an explicit owner skip/attestation for this gate

Do not store raw Telegram WebApp `initData`, bearer tokens, private messages, or
unredacted personal data in repo evidence.
