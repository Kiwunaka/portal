#!/usr/bin/env python3
"""Collect the public censorship-research corpus outside the repository.

The raw corpus is intentionally not a repository artifact.  This helper records
enough metadata to prove source coverage while omitting author identities and
redacting proxy URLs that may contain reusable connection material.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
from html.parser import HTMLParser
import json
import random
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode

import requests


DISCOURSE_BASE = "https://ntc.rkn.quest"
DISCOURSE_CATEGORIES = {
    42: "manuals",
    21: "cloak",
    8: "goodbyedpi",
    7: "runet-censorship-bypass-extension",
    26: "tools-for-researchers-and-developers",
    24: "tunneling-software",
    12: "russia",
}
DISCOURSE_EXPLICIT_TOPICS = {23843, 23018}
HABR_ARTICLE_IDS = [985674, 1021160, 1014038, 1027276, 1055176, 1020080, 1052536]
HABR_REFERENCE_COUNTS = {1021160: 2}
USER_AGENT = "Mozilla/5.0 (compatible; POKROV-Research/1.0; +https://pokrov.space/)"
REPO_ROOT = Path(__file__).resolve().parents[1]
PROXY_URL_RE = re.compile(
    r"(?i)\b(?:vless|vmess|trojan|hysteria2?|tuic|ss|ssr|wireguard)://[^\s<>\"']+"
)
WHITESPACE_RE = re.compile(r"[ \t\f\v]+")
BLANK_LINES_RE = re.compile(r"\n{3,}")


class TextExtractor(HTMLParser):
    _BLOCK_TAGS = {
        "p",
        "div",
        "br",
        "li",
        "pre",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        value = html.unescape("".join(self.parts)).replace("\r\n", "\n").replace("\r", "\n")
        value = "\n".join(WHITESPACE_RE.sub(" ", line).strip() for line in value.splitlines())
        return BLANK_LINES_RE.sub("\n\n", value).strip()


class JsonFetcher:
    def __init__(self, *, timeout: float, attempts: int, min_interval: float) -> None:
        self.timeout = timeout
        self.attempts = attempts
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._next_request_at = 0.0

    def _throttle(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self._next_request_at - now
            if delay > 0:
                time.sleep(delay)
            self._next_request_at = time.monotonic() + self.min_interval

    def get(self, url: str, *, allow_status: set[int] | None = None) -> tuple[int, Any]:
        allowed = allow_status or set()
        last_error: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            self._throttle()
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                    timeout=(min(10.0, self.timeout), self.timeout),
                )
                status = int(response.status_code)
                if status in allowed:
                    try:
                        return status, response.json()
                    except Exception:
                        return status, {"http_status": status}
                response.raise_for_status()
                return status, response.json()
            except requests.HTTPError as exc:
                last_error = exc
                response = exc.response
                retry_after = response.headers.get("Retry-After") if response is not None else None
                status = int(response.status_code) if response is not None else 0
                if status not in {429, 500, 502, 503, 504}:
                    break
                try:
                    wait = float(retry_after) if retry_after else min(30.0, 1.5**attempt)
                except ValueError:
                    wait = min(30.0, 1.5**attempt)
            except (requests.RequestException, OSError, json.JSONDecodeError) as exc:
                last_error = exc
                wait = min(30.0, 1.5**attempt)
            if attempt < self.attempts:
                time.sleep(wait + random.random() * 0.25)
        raise RuntimeError(f"fetch failed after {self.attempts} attempts: {url}: {last_error}")


def html_to_text(value: Any) -> str:
    parser = TextExtractor()
    parser.feed(str(value or ""))
    parser.close()
    return PROXY_URL_RE.sub("[REDACTED_PROXY_URL]", parser.text())


def batched(values: list[int], size: int) -> Iterable[list[int]]:
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


def collect_category_topics(fetcher: JsonFetcher) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    topics: dict[int, dict[str, Any]] = {}
    categories: dict[str, Any] = {}
    for category_id, slug in DISCOURSE_CATEGORIES.items():
        category_topic_ids: list[int] = []
        page = 0
        while page < 250:
            _status, payload = fetcher.get(f"{DISCOURSE_BASE}/c/{category_id}.json?page={page}")
            topic_list = payload.get("topic_list") or {}
            rows = topic_list.get("topics") or []
            for row in rows:
                topic_id = int(row.get("id") or 0)
                if topic_id <= 0:
                    continue
                if topic_id not in category_topic_ids:
                    category_topic_ids.append(topic_id)
                if topic_id not in topics:
                    topics[topic_id] = dict(row)
                memberships = topics[topic_id].setdefault("_research_category_ids", [])
                if category_id not in memberships:
                    memberships.append(category_id)
            if not topic_list.get("more_topics_url") or not rows:
                break
            page += 1
        categories[str(category_id)] = {
            "slug": slug,
            "pages": page + 1,
            "topic_ids": category_topic_ids,
            "topic_count": len(category_topic_ids),
        }
        print(f"category {category_id}: {len(category_topic_ids)} topics", flush=True)
    for topic_id in DISCOURSE_EXPLICIT_TOPICS:
        topics.setdefault(topic_id, {"id": topic_id, "_research_category_ids": []})
    return topics, categories


def compact_discourse_post(post: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(post.get("id") or 0),
        "post_number": int(post.get("post_number") or 0),
        "reply_to_post_number": post.get("reply_to_post_number"),
        "created_at": post.get("created_at"),
        "updated_at": post.get("updated_at"),
        "reads": post.get("reads"),
        "score": post.get("score"),
        "text": html_to_text(post.get("cooked")),
    }


def fetch_discourse_topic(fetcher: JsonFetcher, seed: dict[str, Any]) -> dict[str, Any]:
    topic_id = int(seed["id"])
    _status, payload = fetcher.get(f"{DISCOURSE_BASE}/t/{topic_id}.json")
    post_stream = payload.get("post_stream") or {}
    expected_ids = [int(item) for item in (post_stream.get("stream") or [])]
    posts_by_id = {
        int(post.get("id") or 0): post
        for post in (post_stream.get("posts") or [])
        if int(post.get("id") or 0) > 0
    }
    missing_ids = [post_id for post_id in expected_ids if post_id not in posts_by_id]
    for group in batched(missing_ids, 20):
        query = urlencode([("post_ids[]", post_id) for post_id in group])
        _status, extra = fetcher.get(f"{DISCOURSE_BASE}/t/{topic_id}/posts.json?{query}")
        for post in ((extra.get("post_stream") or {}).get("posts") or []):
            post_id = int(post.get("id") or 0)
            if post_id > 0:
                posts_by_id[post_id] = post
    actual_ids = [post_id for post_id in expected_ids if post_id in posts_by_id]
    missing_after_fetch = [post_id for post_id in expected_ids if post_id not in posts_by_id]
    posts = [compact_discourse_post(posts_by_id[post_id]) for post_id in actual_ids]
    return {
        "source": "ntc.rkn.quest",
        "topic_id": topic_id,
        "url": f"{DISCOURSE_BASE}/t/{payload.get('slug') or 'topic'}/{topic_id}",
        "title": html_to_text(payload.get("title")),
        "category_id": payload.get("category_id"),
        "research_category_ids": sorted(set(seed.get("_research_category_ids") or [])),
        "created_at": payload.get("created_at"),
        "last_posted_at": payload.get("last_posted_at"),
        "views": payload.get("views"),
        "tags": payload.get("tags") or [],
        "visible_post_ids_expected": len(expected_ids),
        "visible_posts_collected": len(posts),
        "missing_post_ids": missing_after_fetch,
        "highest_post_number": payload.get("highest_post_number"),
        "posts": posts,
    }


def compact_habr_comment(comment: dict[str, Any]) -> dict[str, Any]:
    message = comment.get("message")
    if isinstance(message, dict):
        message = message.get("html") or message.get("text") or ""
    return {
        "id": str(comment.get("id") or ""),
        "parent_id": comment.get("parentId"),
        "level": comment.get("level"),
        "created_at": comment.get("timePublished"),
        "updated_at": comment.get("timeChanged"),
        "score": comment.get("score"),
        "is_article_author": bool(comment.get("isAuthor")),
        "text": html_to_text(message),
    }


def collect_habr(fetcher: JsonFetcher) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for article_id in HABR_ARTICLE_IDS:
        article_url = f"https://habr.com/ru/articles/{article_id}/"
        article_status, article = fetcher.get(
            f"https://habr.com/kek/v2/articles/{article_id}/", allow_status={451}
        )
        _comments_status, comments_payload = fetcher.get(
            f"https://habr.com/kek/v2/articles/{article_id}/comments/"
        )
        comments_raw = comments_payload.get("comments") or {}
        if isinstance(comments_raw, dict):
            comments_iter = comments_raw.values()
        else:
            comments_iter = comments_raw
        comments = [compact_habr_comment(dict(item)) for item in comments_iter if isinstance(item, dict)]
        statistics = article.get("statistics") if isinstance(article, dict) else {}
        rows.append(
            {
                "source": "habr.com",
                "article_id": article_id,
                "url": article_url,
                "input_reference_count": HABR_REFERENCE_COUNTS.get(article_id, 1),
                "article_api_status": article_status,
                "article_body_available_via_api": article_status == 200,
                "title": html_to_text(article.get("titleHtml")) if article_status == 200 else "",
                "published_at": article.get("timePublished") if article_status == 200 else None,
                "article_text": html_to_text(article.get("textHtml")) if article_status == 200 else "",
                "statistics_comments_count": (statistics or {}).get("commentsCount"),
                "comments_collected": len(comments),
                "comments": comments,
            }
        )
        print(f"habr {article_id}: {len(comments)} comments, article status {article_status}", flush=True)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def read_jsonl(path: Path, *, id_key: str) -> dict[int, dict[str, Any]]:
    if not path.exists():
        return {}
    rows: dict[int, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                row_id = int(row[id_key])
            except Exception as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
            rows[row_id] = row
    return rows


def repository_roots() -> set[Path]:
    roots = {REPO_ROOT}
    git_marker = REPO_ROOT / ".git"
    if not git_marker.is_file():
        return roots
    marker = git_marker.read_text(encoding="utf-8").strip()
    prefix = "gitdir:"
    if not marker.lower().startswith(prefix):
        return roots
    git_dir = Path(marker[len(prefix) :].strip())
    if not git_dir.is_absolute():
        git_dir = (REPO_ROOT / git_dir).resolve()
    for parent in (git_dir, *git_dir.parents):
        if parent.name == ".git":
            roots.add(parent.parent.resolve())
            break
    return roots


def run(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).resolve()
    for repository_root in repository_roots():
        try:
            output_dir.relative_to(repository_root)
        except ValueError:
            continue
        raise ValueError("output directory must stay outside the repository")
    output_dir.mkdir(parents=True, exist_ok=True)
    fetcher = JsonFetcher(timeout=args.timeout, attempts=args.attempts, min_interval=args.min_interval)

    topic_seeds, categories = collect_category_topics(fetcher)
    discourse_path = output_dir / "discourse-topics.jsonl"
    discourse_by_id = read_jsonl(discourse_path, id_key="topic_id")
    discourse_rows: list[dict[str, Any]] = list(discourse_by_id.values())
    errors: list[dict[str, Any]] = []
    pending_seeds = {
        topic_id: seed
        for topic_id, seed in topic_seeds.items()
        if topic_id not in discourse_by_id
    }
    print(
        f"discourse resume: {len(discourse_by_id)} collected, {len(pending_seeds)} pending",
        flush=True,
    )
    append_handle = discourse_path.open("a", encoding="utf-8", newline="\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(fetch_discourse_topic, fetcher, seed): topic_id
            for topic_id, seed in sorted(pending_seeds.items())
        }
        completed = 0
        for future in concurrent.futures.as_completed(future_map):
            topic_id = future_map[future]
            try:
                row = future.result()
                discourse_rows.append(row)
                append_handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                append_handle.flush()
            except Exception as exc:
                errors.append({"source": "ntc.rkn.quest", "topic_id": topic_id, "error": str(exc)})
            completed += 1
            if completed % 25 == 0 or completed == len(future_map):
                print(
                    f"discourse progress {completed}/{len(future_map)}; errors={len(errors)}",
                    flush=True,
                )
    append_handle.close()

    discourse_rows.sort(key=lambda item: int(item["topic_id"]))
    habr_rows = collect_habr(fetcher)
    habr_path = output_dir / "habr-articles.jsonl"
    write_jsonl(discourse_path, discourse_rows)
    write_jsonl(habr_path, habr_rows)

    discourse_expected_posts = sum(int(item["visible_post_ids_expected"]) for item in discourse_rows)
    discourse_collected_posts = sum(int(item["visible_posts_collected"]) for item in discourse_rows)
    discourse_missing_posts = sum(len(item["missing_post_ids"]) for item in discourse_rows)
    habr_comments = sum(int(item["comments_collected"]) for item in habr_rows)
    coverage = {
        "schema_version": 1,
        "generated_at_epoch": int(time.time()),
        "raw_corpus_location": str(output_dir),
        "raw_corpus_policy": "local temporary evidence; do not commit",
        "discourse": {
            "base_url": DISCOURSE_BASE,
            "categories": categories,
            "explicit_topic_ids": sorted(DISCOURSE_EXPLICIT_TOPICS),
            "unique_topics_discovered": len(topic_seeds),
            "topics_collected": len(discourse_rows),
            "visible_posts_expected": discourse_expected_posts,
            "visible_posts_collected": discourse_collected_posts,
            "missing_posts": discourse_missing_posts,
            "sha256": sha256_file(discourse_path),
        },
        "habr": {
            "input_article_references": 8,
            "unique_articles": len(HABR_ARTICLE_IDS),
            "article_ids": HABR_ARTICLE_IDS,
            "comments_collected": habr_comments,
            "sha256": sha256_file(habr_path),
        },
        "errors": errors,
    }
    coverage_path = output_dir / "coverage.json"
    coverage_path.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(coverage, ensure_ascii=False, indent=2), flush=True)
    return 0 if not errors and discourse_missing_posts == 0 else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--min-interval", type=float, default=0.06)
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
