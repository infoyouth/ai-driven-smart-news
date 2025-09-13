#!/usr/bin/env python3
"""Preview Discord grouped-URL messages.

This script reads `enriched_*.json` if present, otherwise `filtered_*.json`,
and prints the exact message body (header + up to 10 URLs) that the poster
would send to Discord for each category. It's a dry-run-only helper with no
network calls and no flags — run it to see the final messages.
"""
import glob
import json
import os


def friendly_title(filename: str) -> str:
    name = os.path.basename(filename)
    display = (
        name.replace("filtered_", "")
        .replace("enriched_", "")
        .replace(".json", "")
        .replace("_", " ")
        .title()
    )
    return display


def load_articles(path: str):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return []


def build_message(title: str, urls: list) -> str:
    lines = [f"**{title}**"]
    lines.extend(urls[:10])
    return "\n".join(lines)


def main():
    files = sorted(glob.glob("filtered_*.json"))
    if not files:
        print("No filtered_*.json files found in repository root.")
        return

    for f in files:
        enriched = f.replace("filtered_", "enriched_")
        chosen = enriched if os.path.exists(enriched) else f
        articles = load_articles(chosen)
        # Extract URLs (url or link) preserving order
        urls = []
        for a in articles:
            if isinstance(a, dict):
                u = a.get("url") or a.get("link")
                if u:
                    urls.append(u)
        title = friendly_title(chosen)
        message = build_message(title, urls)
        print("\n" + "=" * 60)
        print(f"Category: {title} ({os.path.basename(chosen)})")
        print("-" * 60)
        print(message)
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
