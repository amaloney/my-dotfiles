#!/usr/bin/env python3
"""Capture a fetched web resource into .harness/research/ and link it from the chat-provenance log."""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from log_entry import append_entry
from shared import FileLock, find_repo_root, redact

RESOURCE_TYPES = ["webpage", "article", "documentation", "paper"]

FRONTMATTER_TEMPLATE = """---
title: {title}
creator: {creator}
date: {date}
source: {url}
type: {rtype}
format: {fmt}
language: en
digest: sha256:{digest}
---
"""

INDEX_HEADER = "# Research Index\n\n| Date | Type | Title | URL | Path |\n| --- | --- | --- | --- | --- |\n"


def fetch(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get_content_type()
        return resp.read().decode("utf-8", errors="replace"), content_type


def html_to_markdown(html: str) -> str | None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        return None
    proc = subprocess.run(
        [pandoc, "-f", "html", "-t", "gfm", "--wrap=none"],
        input=html,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc.stdout if proc.returncode == 0 else None


def extract_title(content: str, is_html: bool, url: str) -> str:
    if is_html:
        match = re.search(r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    else:
        match = re.search(r"(?m)^#\s+(.+)$", content)
        if match:
            return match.group(1).strip()
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}".strip("/") or parsed.netloc


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return (slug or "untitled")[:60].rstrip("-")


def atomic_write(path: Path, text: str) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        os.unlink(tmp_name)
        raise


def body_of(capture_text: str) -> str:
    parts = capture_text.split("---\n", 2)
    return parts[2] if len(parts) == 3 else capture_text


def dedupe_path(day_dir: Path, slug: str, digest: str) -> tuple[Path, bool]:
    candidate = day_dir / f"{slug}.md"
    counter = 2
    while candidate.exists():
        existing_digest = hashlib.sha256(body_of(candidate.read_text(encoding="utf-8")).encode("utf-8")).hexdigest()
        if existing_digest == digest:
            return candidate, True
        candidate = day_dir / f"{slug}-{counter}.md"
        counter += 1
    return candidate, False


def append_index(index: Path, date_str: str, rtype: str, title: str, url: str, capture_rel: Path) -> None:
    text = index.read_text(encoding="utf-8") if index.exists() else INDEX_HEADER
    safe_title = title.replace("|", "\\|")
    row = f"| {date_str} | {rtype} | {safe_title} | {url} | {capture_rel} |\n"
    atomic_write(index, text.rstrip("\n") + "\n" + row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="fetch this URL")
    parser.add_argument("--source-url", help="URL the stdin content came from")
    parser.add_argument("--title", help="override auto-detected title")
    parser.add_argument("--creator", default="unknown", help="author or site, if known")
    parser.add_argument("--type", dest="rtype", choices=RESOURCE_TYPES, default="webpage")
    parser.add_argument("--agent", default="main", help="agent name for the daily-log link entry")
    args = parser.parse_args()

    if not args.url and not args.source_url:
        print("error: pass --url to fetch, or --source-url with content on stdin", file=sys.stderr)
        return 2
    if args.url and args.source_url:
        print("error: --url and --source-url are mutually exclusive", file=sys.stderr)
        return 2

    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        print("error: not inside a git repo; skipping source capture", file=sys.stderr)
        return 1

    if args.url:
        try:
            content, content_type = fetch(args.url)
        except (urllib.error.URLError, TimeoutError) as err:
            print(f"error: fetch failed for {args.url}: {err}", file=sys.stderr)
            return 1
        url = args.url
    else:
        content = sys.stdin.read()
        if not content.strip():
            print("error: empty content on stdin", file=sys.stderr)
            return 2
        content_type = "text/markdown"
        url = args.source_url

    content = redact(content)
    is_html = "html" in content_type
    body, fmt = content, "text/html"
    if is_html:
        converted = html_to_markdown(content)
        if converted is not None:
            body, fmt = converted, "text/markdown"
    elif "markdown" in content_type or "text/plain" in content_type:
        fmt = "text/markdown"

    title = args.title or extract_title(content, is_html, url)
    slug = slugify(title)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    research_dir = repo_root / ".harness" / "research"
    day_dir = research_dir / date_str
    day_dir.mkdir(parents=True, exist_ok=True)
    log_dir = repo_root / ".harness" / "chat-provenance"
    log_dir.mkdir(parents=True, exist_ok=True)

    body_text = f"\n# {title}\n\n{body.rstrip()}\n"
    digest = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
    full_text = (
        FRONTMATTER_TEMPLATE.format(
            title=title,
            creator=args.creator,
            date=date_str,
            url=url,
            rtype=args.rtype,
            fmt=fmt,
            digest=digest,
        )
        + body_text
    )

    with FileLock(log_dir / ".lock"):
        capture_path, is_dupe = dedupe_path(day_dir, slug, digest)
        capture_rel = capture_path.relative_to(repo_root / ".harness")
        if is_dupe:
            print(f"cached: {capture_path}")
        else:
            atomic_write(capture_path, full_text)
            append_entry(
                log_dir,
                "source",
                args.agent,
                f"source: {url}\ncapture: {capture_rel}\ndigest: sha256:{digest}",
            )
            append_index(research_dir / "index.md", date_str, args.rtype, title, url, capture_rel)
            print(f"saved: {capture_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
