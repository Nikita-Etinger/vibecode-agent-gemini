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


def test_popup_files():
    assert Path("chrome_extension/popup.html").exists()
    assert Path("chrome_extension/popup.js").exists()


def test_content_js_contract():
    cnt_path = Path("chrome_extension/content.js")
    assert cnt_path.exists()
    content = cnt_path.read_text(encoding="utf-8")
    assert "updateButtonAppearance" in content
    assert "closest('code-block')" in content or 'closest("code-block")' in content
    assert "EXECUTE_PAYLOAD" in content
