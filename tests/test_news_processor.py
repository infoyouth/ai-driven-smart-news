from core.news_fetcher import get_by_path, get_value_by_path


def test_get_by_path_returns_list_or_empty():
    data = {"outer": {"items": [1, 2, 3]}}
    assert get_by_path(data, "outer.items") == [1, 2, 3]
    assert get_by_path(data, "outer.missing") == []
    assert get_by_path({"notdict": 1}, "notdict.x") == []


def test_get_value_by_path_returns_value_or_none():
    data = {"meta": {"published": "2025-01-01"}}
    assert get_value_by_path(data, "meta.published") == "2025-01-01"
    assert get_value_by_path(data, "meta.missing") is None
    assert get_value_by_path(data, None) is None
