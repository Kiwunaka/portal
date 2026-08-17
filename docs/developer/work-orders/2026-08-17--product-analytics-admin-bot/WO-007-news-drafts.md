# WO-007 — Daily Internet News Drafts

Status: `COMPLETED_LOCAL_PENDING_PROD_ENABLEMENT`

`news_draft_service.py` reads at most six HTTPS RSS sources, accepts only
allowlisted item hosts and bounded XML, ignores old/future entries and stores no
article body. Cross-feed item hashes deduplicate the queue. Each run retains
safe source counts, result, duration and failure code.

The worker is disabled by default and runs at most once per six hours, normally
once per day. Production enablement uses `NEWS_DRAFT_WORKER_ENABLED=true`.
Collected items are drafts only. An editor must write a Russian summary and
complete L2 approval; automatic publication and Telegram posting are excluded.
