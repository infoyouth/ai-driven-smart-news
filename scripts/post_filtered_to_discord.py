#!/usr/bin/env python3
"""
Post filtered_*.json files to Discord with robust handling and debug logging.
Usage: set environment variable DISCORD_WEBHOOK_URL and run this script from the repo root.
"""
import os
import sys
import glob
import json
import hashlib
import base64
import argparse

try:
    import requests
except Exception:
    requests = None

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true', help='Do not POST to Discord; only print payloads')
parser.add_argument('--webhook', help='Discord webhook URL (overrides DISCORD_WEBHOOK_URL env var)')
args = parser.parse_args()

WEBHOOK = args.webhook or os.environ.get("DISCORD_WEBHOOK_URL")
if not WEBHOOK and not args.dry_run:
    print("DISCORD_WEBHOOK_URL not set (use --webhook or set the env var), or run with --dry-run", file=sys.stderr)
    sys.exit(2)

files = sorted(glob.glob("filtered_*.json"))
if not files:
    print("No filtered_*.json files found", file=sys.stderr)
    sys.exit(0)

for f in files:
    try:
        size = os.path.getsize(f)
        print(f"\n--- Processing {f} ---")
        print(f"File size: {size} bytes")
        sha = hashlib.sha256()
        with open(f, "rb") as fh:
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

        text = data.decode("utf-8", errors="replace")
        title = f"AI-Driven Breaking News — {os.path.basename(f)}"
        marker_start = "\n```json\n"
        marker_end = "\n```"
        content = title + marker_start + text + marker_end
        max_len = 1900
        truncated = False
        if len(content) > max_len:
            reserve = len(title) + len(marker_start) + len(marker_end) + len("\n... (truncated)")
            allowed = max_len - reserve
            if allowed < 0:
                allowed = max_len
            text = text[:allowed]
            content = title + marker_start + text + "\n... (truncated)" + marker_end
            truncated = True
        payload = {"username": "Youth Innovations", "content": content}
        print("Payload byte size:", len(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
        if truncated:
            print("CONTENT_TRUNCATED", file=sys.stderr)

        # If dry-run, just print the payload summary and skip network calls
        if args.dry_run:
            print("DRY_RUN: would POST payload (first 200 chars):")
            print(payload["content"][:200])
            continue

        # Validate requests and webhook
        if requests is None:
            print("The 'requests' package is required to post to Discord. Install it or run with --dry-run", file=sys.stderr)
            continue
        if not WEBHOOK or not (WEBHOOK.startswith('http://') or WEBHOOK.startswith('https://')):
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
