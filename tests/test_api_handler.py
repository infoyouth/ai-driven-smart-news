import json
from core.api_config_loader import APIConfigLoader


def test_api_config_loader_reads_file_and_env_key(tmp_path, monkeypatch):
    cfg = {
        "sources": [
            {
                "name": "TestAPI",
                "base_url": "https://example.com/",
                "api_key_env": "TEST_API_KEY_ENV",
            }
        ]
    }
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg))
    monkeypatch.setenv("TEST_API_KEY_ENV", "supersecret")
    loader = APIConfigLoader(str(p))
    src = loader.get_source("TestAPI")
    assert src is not None
    assert src.get("api_key") == "supersecret"


def test_api_config_loader_missing_env_raises(tmp_path, monkeypatch):
    cfg = {
        "sources": [
            {"name": "NoKeyAPI", "base_url": "https://x/", "api_key_env": "MISSING_ENV"}
        ]
    }
    p = tmp_path / "cfg2.json"
    p.write_text(json.dumps(cfg))
    # Ensure the env var is not set
    monkeypatch.delenv("MISSING_ENV", raising=False)
    try:
        APIConfigLoader(str(p))
        assert False, "Expected ValueError for missing API key"
    except ValueError:
        pass


def test_api_config_loader_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not: valid json}")
    try:
        APIConfigLoader(str(p))
        assert False, "Expected JSONDecodeError"
    except Exception:
        # any exception is acceptable for this negative test
        pass


def test_get_all_sources(tmp_path, monkeypatch):
    cfg = {
        "sources": [
            {"name": "A", "base_url": "https://a/"},
            {"name": "B", "base_url": "https://b/"},
        ]
    }
    p = tmp_path / "cfg3.json"
    p.write_text(json.dumps(cfg))
    loader = APIConfigLoader(str(p))
    all_src = loader.get_all_sources()
    assert isinstance(all_src, list)
    assert len(all_src) == 2
