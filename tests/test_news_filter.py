from core.news_filter import filter_top_n


def _mk(article_id: int, url: str, published_at: str | None):
    art = {"id": article_id, "url": url}
    if published_at is not None:
        art["published_at"] = published_at
    return art


def test_filter_top_n_orders_by_timestamp():
    # three articles with timestamps; newest first expected
    a1 = _mk(1, "http://a", "2025-09-12T10:00:00Z")
    a2 = _mk(2, "http://b", "2025-09-12T12:00:00Z")
    a3 = _mk(3, "http://c", "2025-09-12T09:00:00Z")
    articles = [a1, a2, a3]
    mapping = {"published_at_path": "published_at"}
    out = filter_top_n(articles, mapping, n=10)
    assert [a["id"] for a in out] == [2, 1, 3]


def test_filter_top_n_respects_limit():
    # limit to top 2
    a = _mk(1, "http://a", "2025-09-12T10:00:00Z")
    b = _mk(2, "http://b", "2025-09-12T11:00:00Z")
    c = _mk(3, "http://c", "2025-09-12T09:00:00Z")
    mapping = {"published_at_path": "published_at"}
    out = filter_top_n([a, b, c], mapping, n=2)
    assert len(out) == 2
    assert [o["id"] for o in out] == [2, 1]


def test_filter_top_n_fallback_preserves_order_when_no_timestamps():
    # No timestamps at all — should preserve original order
    a = {"id": 1}
    b = {"id": 2}
    c = {"id": 3}
    mapping = {"published_at_path": None}
    out = filter_top_n([a, b, c], mapping, n=10)
    assert [o["id"] for o in out] == [1, 2, 3]


def test_filter_top_n_nested_path():
    # published_at at nested path like 'meta.published'
    a = {"id": 1, "meta": {"published": "2025-09-12T08:00:00Z"}}
    b = {"id": 2, "meta": {"published": "2025-09-12T09:00:00Z"}}
    mapping = {"published_at_path": "meta.published"}
    out = filter_top_n([a, b], mapping)
    assert [o["id"] for o in out] == [2, 1]


def test_filter_top_n_handles_invalid_dates():
    # invalid date should be treated as missing and placed after valid ones
    a = {"id": 1, "published_at": "not-a-date"}
    b = {"id": 2, "published_at": "2025-09-12T11:00:00Z"}
    mapping = {"published_at_path": "published_at"}
    out = filter_top_n([a, b], mapping)
    assert [o["id"] for o in out] == [2, 1]


def test_filter_top_n_non_string_timestamps():
    # timestamps that are non-strings should be ignored (treated as missing)
    a = {"id": 1, "published_at": 123456}
    b = {"id": 2, "published_at": "2025-09-12T07:00:00Z"}
    mapping = {"published_at_path": "published_at"}
    out = filter_top_n([a, b], mapping)
    assert [o["id"] for o in out] == [2, 1]


def test_filter_top_n_stability_with_missing_timestamps():
    # When some have timestamps and some don't, the ones without should
    # keep their original relative order among themselves
    a = {"id": 1, "published_at": "2025-09-12T12:00:00Z"}
    b = {"id": 2}
    c = {"id": 3}
    d = {"id": 4, "published_at": "2025-09-12T11:00:00Z"}
    mapping = {"published_at_path": "published_at"}
    out = filter_top_n([a, b, c, d], mapping)
    # Expect newest-first among parsed: a (12:00), d (11:00).
    # Then b and c should remain in their original order
    assert [o["id"] for o in out] == [1, 4, 2, 3]
