import pytest
from pathlib import Path
from tools.code_search import search_text, find_definitions, get_directory_tree


@pytest.fixture
def sample_codebase(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text(
        "class MainService:\n"
        "    def __init__(self):\n"
        "        self.status = 'active'\n\n"
        "    def execute_job(self):\n"
        "        return 42\n",
        encoding="utf-8"
    )
    (src_dir / "utils.py").write_text(
        "def helper_fn():\n"
        "    # TODO: execute_job fallback\n"
        "    return 'ok'\n",
        encoding="utf-8"
    )
    ignored_dir = tmp_path / ".git"
    ignored_dir.mkdir()
    (ignored_dir / "secret.py").write_text("execute_job in git", encoding="utf-8")
    return tmp_path


def test_search_text(sample_codebase: Path):
    res = search_text("execute_job", root_dir=str(sample_codebase))
    assert res["total_matches"] == 2
    files = [m["file"] for m in res["matches"]]
    assert any("app.py" in f for f in files)
    assert any("utils.py" in f for f in files)
    assert not any(".git" in f for f in files)


def test_find_definitions(sample_codebase: Path):
    res = find_definitions("MainService", root_dir=str(sample_codebase))
    assert res["total_definitions"] == 1
    assert "app.py" in res["definitions"][0]["file"]
    assert "class MainService" in res["definitions"][0]["code"]

    res_fn = find_definitions("execute_job", root_dir=str(sample_codebase))
    assert res_fn["total_definitions"] == 1
    assert "def execute_job(self):" in res_fn["definitions"][0]["code"]


def test_get_directory_tree(sample_codebase: Path):
    res = get_directory_tree(root_dir=str(sample_codebase), max_depth=2)
    tree_str = res["tree"]
    assert "src/" in tree_str
    assert "app.py" in tree_str
    assert ".git" not in tree_str
