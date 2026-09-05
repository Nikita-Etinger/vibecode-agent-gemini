import pytest
from pathlib import Path
from main import validate_python_ast, BACKUP_DIR, SCRIPTS_DIR, LOG_FILE

def test_validate_ast_valid():
    code = "def sample():\n    return 42\n"
    validate_python_ast(Path("dummy.py"), code)

def test_validate_ast_invalid():
    code = "def sample():\nreturn 42\n"
    with pytest.raises(SyntaxError):
        validate_python_ast(Path("dummy.py"), code)

def test_directories_structure():
    assert BACKUP_DIR.name == "backups"
    assert SCRIPTS_DIR.name == "scripts"
    assert BACKUP_DIR.exists()
    assert SCRIPTS_DIR.exists()

def test_log_file_definition():
    assert LOG_FILE.name == "main.log"


def test_canonical_json_hashing():
    import json
    import hashlib
    raw_gui = '{\n  "summary": "test",\n  "actions": [{"cmd": "ping", "type": "query"}]\n}'
    raw_ext = '{"actions":[{"type":"query","cmd":"ping"}],"summary":"test"}'
    obj1 = json.loads(raw_gui)
    obj2 = json.loads(raw_ext)
    c1 = json.dumps(obj1, sort_keys=True, ensure_ascii=False)
    c2 = json.dumps(obj2, sort_keys=True, ensure_ascii=False)
    assert hashlib.sha256(c1.encode("utf-8")).hexdigest() == hashlib.sha256(c2.encode("utf-8")).hexdigest()
