"""
news_filter.py
---------------
Config-driven filter for selecting the top-N latest articles per source.
- Uses `published_at_path` from source `response_mapping` when available.
- Parses dates with `dateutil.parser.parse` and falls back to API order when missing.
- Default N is 10 (configurable via `filter_limit` in config).
"""
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)


def _get_by_path(obj: Dict[str, Any], path: Optional[str]):
    if not path:
        return None
    parts = path.split(".")
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
        if cur is None:
            return None
    return cur


def _parse_date(value: Optional[str]):
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except Exception:
        return None


def filter_top_n(
    articles: List[Dict[str, Any]], response_mapping: Dict[str, Any], n: int = 10
) -> List[Dict[str, Any]]:
    """Return top `n` articles ordered by parsed `published_at` where available.

    - `response_mapping` should include `published_at_path` (dot-path) if available.
    - If parsing fails or timestamp missing for an article, it will be treated as older than parsed ones but keep original relative ordering among those without timestamps.
    - Falls back to original order if no timestamps can be parsed at all.
    """
    published_path = response_mapping.get("published_at_path")

    annotated = []
    parsed_any = False

    for idx, art in enumerate(articles):
        raw_ts = _get_by_path(art, published_path) if published_path else None
        parsed = _parse_date(raw_ts) if isinstance(raw_ts, str) else None
        if parsed:
            parsed_any = True
        annotated.append({"_orig_index": idx, "_parsed_at": parsed, "article": art})

    if parsed_any:
        # Sort: parsed timestamps first (newest -> oldest), then items without parsed timestamps by original index
        from datetime import datetime

        def _key(x):
            has_parsed = x["_parsed_at"] is not None
            parsed_val = (
                x["_parsed_at"] if x["_parsed_at"] is not None else datetime.min
            )
            return (has_parsed, parsed_val)

        annotated.sort(key=_key, reverse=True)
    else:
        # No timestamps parsed — keep original order
        logger.debug("No timestamps parsed for any articles; preserving source order.")
        annotated.sort(key=lambda x: x["_orig_index"])

    top = [a["article"] for a in annotated[:n]]
    return top
