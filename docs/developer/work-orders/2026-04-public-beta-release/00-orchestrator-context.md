# Orchestrator Context

Status: active
Created: 2026-04-25

## Source Request

Implement the full public beta release plan from:

`C:/Users/kiwun/Downloads/POKROV_public_beta_release_monster_plan_v3_agent_iterations_internal_commits.md`

## Public Beta Definition

This is an open public beta release candidate, not a closed or invite-limited paid beta. The release may be beta-labeled and limitation-aware, but every public claim must be backed by evidence.

## Mandatory Product Facts

- Brand: POKROV.
- Public wording: do not use `VPN` as direct public product description.
- Public scope target: Android + Windows only when gates support that claim.
- Apple scope: readiness only.
- Trial: 5 days.
- Telegram reward: +10 days.
- App-first, consumer-first, key-first.
- Public channel: @pokrov_vpn.
- Main bot: @pokrov_vpnbot.
- Support bot: @pokrov_supportbot.
- Feedback bot: @pokrov_feedbackbot.
- Official surfaces: https://pokrov.space/, https://app.pokrov.space/, https://api.pokrov.space/.
- Connect host: https://connect.pokrov.space/.
- Checkout host: https://pay.pokrov.space/checkout/.

## Worktree And Baseline

Platform worktree:

`C:/Users/kiwun/.config/superpowers/worktrees/VPN/public-beta-release-wave`

Platform branch:

`codex/public-beta-release-wave`

Baseline evidence:

- `evidence/logs/platform/platform-git-status-before.txt`
- `evidence/logs/platform/platform-git-diff-before.patch`
- `evidence/logs/client/client-git-status-before.txt`

Important baseline risk:

- The platform candidate inherits uncommitted changes from the earlier beta wave.
- The root platform `master` was behind `origin/master` at capture time.
- The active client repo also has dirty local changes; client WOs must record separate lane evidence.

## Critical Blocker Policy

Do not mark public beta ready when any of these remain true:

- Payment can double-grant access.
- Failed payment grants access.
- Public checkout is enabled without safe fulfillment evidence.
- Trial is fake or unusable while advertised.
- Managed profile delivery is broken.
- Both Android and Windows public client paths are blocked.
- Android is offered publicly before production signing and physical release-build localhost/control-surface audit.
- Windows artifact lacks checksum/metadata or unsigned warning.
- Admin auth or critical modules are fake/broken.
- Support ticket flow is fake/broken.
- Emergency controls are missing or unverified.
- Rollback path is unknown.
- Public copy promises stable release, SLA, Apple availability, stores, or guaranteed access everywhere.

## Agent Evidence Rule

Research agents must write confirmed/probable/unknown/needs local run/blocked by missing access findings only. Work agents must record iteration ledger and internal commit entries for each meaningful patch.

