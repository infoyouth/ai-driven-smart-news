from core.discord_poster import NewsDiscordFormatter


def test_format_one_liner_basic():
    items = [
        {"title": "Hello", "url": "http://a", "emoji": "🔥"},
        {"title": "World", "url": "http://b"},
    ]
    out = NewsDiscordFormatter.format_one_liner(items)
    assert "🔥 [Hello](http://a)" in out
    assert "📰 [World](http://b)" in out


def test_format_one_liner_skips_missing_fields(caplog):
    items = [{"title": "NoUrl"}, {"url": "http://b"}]
    out = NewsDiscordFormatter.format_one_liner(items)
    # Should be empty since both items are missing either title or url
    assert out == ""


def test_default_emoji_and_none_emoji(caplog):
    items = [
        {"title": "T1", "url": "http://1"},
        {"title": "T2", "url": "http://2", "emoji": None},
    ]
    out = NewsDiscordFormatter.format_one_liner(items)
    # default emoji should be used for both
    assert "📰 [T1](http://1)" in out
    assert "📰 [T2](http://2)" in out


def test_skipped_items_logged(caplog):
    caplog.clear()
    items = [{"title": "Ok", "url": "http://ok"}, {"title": None, "url": "http://no"}]
    out = NewsDiscordFormatter.format_one_liner(items)
    assert "[Ok]" in out
    # ensure a warning was emitted for the missing title/url
    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) >= 1
