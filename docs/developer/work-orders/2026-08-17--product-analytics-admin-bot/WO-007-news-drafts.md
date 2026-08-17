# WO-007 — Daily Internet News Drafts

Status: `COMPLETED`

`news_draft_service.py` reads at most six HTTPS RSS sources, accepts only
allowlisted item hosts and bounded XML, ignores old/future entries and stores no
article body. Cross-feed item hashes deduplicate the queue. Each run retains
safe source counts, result, duration and failure code.

The worker is disabled by default and runs at most once per six hours, normally
once per day. Production enablement uses `NEWS_DRAFT_WORKER_ENABLED=true`.
Collected items are drafts only. An editor must write a Russian summary and
complete L2 approval; automatic publication and Telegram posting are excluded.

Production enablement is active with a 24-hour interval. The first live run
exposed a bounded-stream bug: one `aiohttp` read returned only the first network
chunk and truncated valid RSS. Commit `09b228e` changed collection to read every
chunk with the existing 1 MiB fail-closed limit. The exact post-deploy readback
was `runs=4`, `drafts=2`, `pending=2`, latest run `completed`, no failure code,
two drafts created in 349 ms. No draft was automatically published.
