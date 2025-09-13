#!/usr/bin/env python3
"""
Post filtered_*.json files to Discord with robust handling
and debug logging.

Usage: set environment variable DISCORD_WEBHOOK_URL and run this
script from the repo root.
"""
import os
import sys
import glob
import json
from typing import Any, Dict
import hashlib
import base64
import argparse

try:
    import requests  # type: ignore
except Exception:
    from types import SimpleNamespace as _SimpleNS

    # When `requests` isn't available at runtime (e.g., in CI lint steps),
    # assign a simple sentinel object with the same name so static type
    # checkers and runtime checks can still operate. This avoids mypy
    # treating the variable as `None` which conflicts with module type.
    requests = _SimpleNS()

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Do not POST; only print payloads",
)
parser.add_argument(
    "--webhook", help="Discord webhook URL (overrides DISCORD_WEBHOOK_URL env var)"
)
parser.add_argument(
    "--no-per-article",
    action="store_true",
    help="Do not post per-article embeds; post whole file as one content block",
)
parser.add_argument(
    "--per-article-embed",
    action="store_true",
    help="Post per-article as embeds instead of markdown link content",
)
parser.add_argument(
    "--per-article",
    action="store_true",
    help=(
        "Post each article individually as markdown links. "
        "Overrides default grouped-URLs behavior."
    ),
)
parser.add_argument(
    "--urls-only",
    action="store_true",
    help="(Deprecated) alias for default grouped URLs behavior",
)
parser.add_argument(
    "--preview-length",
    type=int,
    default=300,
    help=("Number of characters to show for dry-run previews. " "Defaults to 300."),
)
args = parser.parse_args()

PREVIEW_LEN = args.preview_length

WEBHOOK = args.webhook or os.environ.get("DISCORD_WEBHOOK_URL")
if not WEBHOOK and not args.dry_run:
    print(
        "DISCORD_WEBHOOK_URL not set (use --webhook or set the env var)",
        file=sys.stderr,
    )
    print("Or run with --dry-run to avoid posting.", file=sys.stderr)
    sys.exit(2)

files = sorted(glob.glob("filtered_*.json"))
if not files:
    print("No filtered_*.json files found", file=sys.stderr)
    sys.exit(0)

for f in files:
    try:
        # Prefer enriched file when available
        enriched_candidate = f.replace("filtered_", "enriched_")
        chosen = enriched_candidate if os.path.exists(enriched_candidate) else f
        size = os.path.getsize(chosen)
        print(f"\n--- Processing {chosen} ---")
        print(f"File size: {size} bytes")
        sha = hashlib.sha256()
        with open(chosen, "rb") as fh:
            data = fh.read()
            sha.update(data)
        print(f"SHA256: {sha.hexdigest()}")
        head = data[:200]
        tail = data[-200:]
        print("First 200 bytes (base64):")
        print(base64.b64encode(head).decode("ascii"))
        print("Last 200 bytes (base64):")
        print(base64.b64encode(tail).decode("ascii"))
        print("Contains NUL bytes?", b"\x00" in data)

        # Try to parse JSON array and post per-article by default
        try:
            parsed = json.loads(data.decode("utf-8", errors="replace"))
        except Exception:
            parsed = None

        if isinstance(parsed, list):
            # Default behavior: group URLs into a single message per file (category)
            if not args.per_article:
                # Build a simple header from filename
                chosen_name = os.path.basename(chosen)
                display = (
                    chosen_name.replace("filtered_", "")
                    .replace("enriched_", "")
                    .replace(".json", "")
                    .replace("_", " ")
                    .title()
                )
                urls = [
                    a.get("url") or a.get("link")
                    for a in parsed
                    if (a.get("url") or a.get("link"))
                ]
                content_lines = ["**" + display + "**"]
                content_lines += urls
                content = "\n".join(content_lines)
                max_len = 1900
                truncated = False
                if len(content) > max_len:
                    content = content[: max_len - 20] + "\n... (truncated)"
                    truncated = True
                payload: Dict[str, Any] = {
                    "username": "Youth Innovations",
                    "content": content,
                }
                print("Posting %d URLs as a single message for:" % len(urls))
                print(display)
                size_bytes = len(
                    json.dumps(payload, ensure_ascii=False).encode("utf-8")
                )
                print("Payload byte size:", size_bytes)
                if args.dry_run:
                    print("DRY_RUN: would POST content (preview):")
                    print(content[:PREVIEW_LEN])
                    continue
                if requests is None:
                    print(
                        "Requests library not available; install or use --dry-run",
                        file=sys.stderr,
                    )
                    continue
                if not WEBHOOK or not (
                    WEBHOOK.startswith("http://") or WEBHOOK.startswith("https://")
                ):
                    print(f"Invalid or missing webhook URL: {WEBHOOK}", file=sys.stderr)
                    continue
                try:
                    r = requests.post(
                        WEBHOOK,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=15,
                    )
                    print(r.status_code, r.text)
                except Exception as e:
                    print(f"HTTP POST failed for grouped URLs: {e}", file=sys.stderr)
                continue

            # If per-article flag is set, post each article individually
            print("Posting %d articles as individual messages" % len(parsed))
            print("markdown link format")
            for idx, art in enumerate(parsed, start=1):
                a_title = art.get("title") or art.get("headline") or "Untitled"
                a_url = art.get("url") or art.get("link") or ""
                a_desc = art.get("description") or art.get("story_text") or ""
                # Default: use markdown link in message content for better
                # readability in channels
                if args.per_article_embed:
                    embed = {"title": a_title}
                    if a_url:
                        embed["url"] = a_url
                    if a_desc:
                        embed["description"] = a_desc[:2048]
                    payload = {
                        "username": "Youth Innovations",
                        "embeds": [embed],
                    }
                else:
                    # format as markdown link: [Title](url)
                    # include short description if available
                    if a_url:
                        link = "[" + a_title + "](" + a_url + ")"
                    else:
                        link = a_title
                    if a_desc:
                        content = f"{link} — {a_desc[:300]}"
                    else:
                        content = link
                    payload = {
                        "username": "Youth Innovations",
                        "content": content,
                    }

                print("Article %d: %s -> %s" % (idx, a_title, a_url))
                size_bytes = len(
                    json.dumps(payload, ensure_ascii=False).encode("utf-8")
                )
                print("Payload byte size:", size_bytes)
                if args.dry_run:
                    continue
                if requests is None:
                    print(
                        "The 'requests' package is required to post to Discord.",
                        file=sys.stderr,
                    )
                    print("Install requests or run with --dry-run", file=sys.stderr)
                    break
                if not WEBHOOK or not (
                    WEBHOOK.startswith("http://") or WEBHOOK.startswith("https://")
                ):
                    print(f"Invalid or missing webhook URL: {WEBHOOK}", file=sys.stderr)
                    break
                try:
                    r = requests.post(
                        WEBHOOK,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=15,
                    )
                    print(r.status_code, r.text)
                except Exception as e:
                    print(f"HTTP POST failed for article {idx}: {e}", file=sys.stderr)
                # avoid hitting rate limits
                import time

                time.sleep(0.4)
            continue

        # Fallback: post whole file as a single content block (truncated)
        text = data.decode("utf-8", errors="replace")
        title = f"AI-Driven Breaking News — {os.path.basename(f)}"
        marker_start = "\n```json\n"
        marker_end = "\n```"
        content = title + marker_start + text + marker_end
        max_len = 1900
        truncated = False
        if len(content) > max_len:
            reserve = (
                len(title)
                + len(marker_start)
                + len(marker_end)
                + len("\n... (truncated)")
            )
            allowed = max_len - reserve
            if allowed < 0:
                allowed = max_len
            text = text[:allowed]
            content = title + marker_start + text + "\n... (truncated)" + marker_end
            truncated = True
        payload = {"username": "Youth Innovations", "content": content}
        print(
            "Payload byte size:",
            len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
        )
        if truncated:
            print("CONTENT_TRUNCATED", file=sys.stderr)

        # If dry-run, just print the payload summary and skip network calls
        if args.dry_run:
            print(f"DRY_RUN: would POST payload (first {PREVIEW_LEN} chars):")
            print(payload["content"][:PREVIEW_LEN])
            continue

        # Validate requests and webhook
        if requests is None:
            print(
                "The 'requests' package is required to post to Discord.",
                file=sys.stderr,
            )
            print("Install requests or run with --dry-run", file=sys.stderr)
            continue
        if not WEBHOOK or not (
            WEBHOOK.startswith("http://") or WEBHOOK.startswith("https://")
        ):
            print(f"Invalid or missing webhook URL: {WEBHOOK}", file=sys.stderr)
            continue

        # Post to Discord
        headers = {"Content-Type": "application/json"}
        try:
            r = requests.post(WEBHOOK, json=payload, headers=headers, timeout=15)
        except Exception as e:
            print(f"HTTP POST failed: {e}", file=sys.stderr)
            continue
        try:
            j = r.json()
        except Exception:
            j = r.text
        print(j)
        print("HTTP_CODE:", r.status_code)
    except Exception as e:
        print(f"Error processing {f}: {e}", file=sys.stderr)

print("Done")
