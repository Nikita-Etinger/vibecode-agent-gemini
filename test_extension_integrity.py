import pytest
from pathlib import Path


def test_background_js_contract():
    bg_path = Path("chrome_extension/background.js")
    assert bg_path.exists()
    content = bg_path.read_text(encoding="utf-8")
    assert "EXECUTE_PAYLOAD" in content
    assert "INJECT_AND_SUBMIT" in content
    assert "logToAgent" in content
    assert "unhandledrejection" in content
    assert "sendPromptToTab" in content


def test_content_js_deduplication_and_scope():
    cnt_path = Path("chrome_extension/content.js")
    assert cnt_path.exists()
    content = cnt_path.read_text(encoding="utf-8")
    assert "agentExecuted" in content
    assert "lastResponse" in content
    assert "message-content" in content
