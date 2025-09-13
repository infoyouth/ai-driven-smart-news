from core.gemini_api import GeminiApiClient


def test_extract_json_from_text_plain():
    text = '[{"title": "A", "url": "http://a"}]'
    parsed = GeminiApiClient._extract_json_from_text(text)
    assert isinstance(parsed, list)
    assert parsed[0]["title"] == "A"


def test_extract_json_from_text_with_code_fence_and_trailing_comma():
    text = '```json\n[{"title": "A", "url": "http://a",},]\n```'
    parsed = GeminiApiClient._extract_json_from_text(text)
    assert isinstance(parsed, list)
    assert parsed[0]["url"] == "http://a"


def test_parse_gemini_response_handles_wrapped_result():
    # build a fake Gemini-like response structure as a Python dict
    result = {
        "candidates": [
            {"content": {"parts": [{"text": '[ {"title": "X", "url": "http://x" } ]'}]}}
        ]
    }
    parsed = GeminiApiClient._parse_gemini_response(result)
    assert isinstance(parsed, list)
    assert parsed[0]["title"] == "X"
