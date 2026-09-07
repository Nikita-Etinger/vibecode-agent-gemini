import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

DEFAULT_IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "node_modules",
    "venv",
    ".venv",
    "backups",
    "dist",
    "build",
}

DEFAULT_EXTENSIONS = {".py", ".json", ".md", ".txt", ".js", ".html", ".css", ".bat", ".sh"}


def _is_ignored(path: Path, ignore_dirs: Set[str]) -> bool:
    for part in path.parts:
        if part in ignore_dirs:
            return True
    return False


def search_text(
    query: str,
    root_dir: str = ".",
    file_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    is_regex: bool = False,
    max_results: int = 50,
    context_lines: int = 1,
) -> Dict[str, Any]:
    root = Path(root_dir).resolve()
    if not root.exists():
        return {"error": f"Директория не найдена: {root_dir}", "matches": []}

    flags = 0 if case_sensitive else re.IGNORECASE
    if not is_regex:
        escaped_query = re.escape(query)
        pattern = re.compile(escaped_query, flags)
    else:
        pattern = re.compile(query, flags)

    matches = []
    files_scanned = 0

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS]
        rel_root = Path(current_root)

        for f in files:
            file_path = rel_root / f
            if file_pattern and not file_path.match(file_pattern):
                continue
            if not file_pattern and file_path.suffix.lower() not in DEFAULT_EXTENSIONS:
                continue

            files_scanned += 1
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                continue

            for line_idx, line in enumerate(lines):
                if pattern.search(line):
                    start_ctx = max(0, line_idx - context_lines)
                    end_ctx = min(len(lines), line_idx + context_lines + 1)
                    ctx = [
                        f"{i + 1}: {lines[i]}" if i != line_idx else f"{i + 1}> {lines[i]}"
                        for i in range(start_ctx, end_ctx)
                    ]
                    matches.append({
                        "file": str(file_path.relative_to(root)),
                        "line": line_idx + 1,
                        "match": line.strip(),
                        "context": ctx,
                    })
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break
        if len(matches) >= max_results:
            break

    return {
        "query": query,
        "total_matches": len(matches),
        "files_scanned": files_scanned,
        "matches": matches,
    }


def find_definitions(
    symbol_name: str,
    root_dir: str = ".",
    max_results: int = 30,
) -> Dict[str, Any]:
    root = Path(root_dir).resolve()
    if not root.exists():
        return {"error": f"Директория не найдена: {root_dir}", "definitions": []}

    regex_def = re.compile(rf"^\s*(?:async\s+def|def|class)\s+({re.escape(symbol_name)})\b", re.MULTILINE)
    definitions = []

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORE_DIRS]
        rel_root = Path(current_root)

        for f in files:
            if not f.endswith(".py"):
                continue
            file_path = rel_root / f
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                continue

            for line_idx, line in enumerate(lines):
                if regex_def.search(line):
                    definitions.append({
                        "file": str(file_path.relative_to(root)),
                        "line": line_idx + 1,
                        "code": line.strip(),
                    })
                    if len(definitions) >= max_results:
                        break
            if len(definitions) >= max_results:
                break
        if len(definitions) >= max_results:
            break

    return {
        "symbol": symbol_name,
        "total_definitions": len(definitions),
        "definitions": definitions,
    }


def get_directory_tree(
    root_dir: str = ".",
    max_depth: int = 3,
    show_files: bool = True,
) -> Dict[str, Any]:
    root = Path(root_dir).resolve()
    if not root.exists():
        return {"error": f"Директория не найдена: {root_dir}", "tree": []}

    tree_lines = []

    def _walk(current: Path, depth: int, prefix: str = ""):
        if depth > max_depth:
            return
        try:
            entries = sorted(list(current.iterdir()), key=lambda e: (e.is_file(), e.name.lower()))
        except PermissionError:
            return

        entries = [e for e in entries if e.name not in DEFAULT_IGNORE_DIRS]
        count = len(entries)
        for idx, entry in enumerate(entries):
            is_last = idx == count - 1
            connector = "└── " if is_last else "├── "
            if entry.is_dir():
                tree_lines.append(f"{prefix}{connector}{entry.name}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                _walk(entry, depth + 1, next_prefix)
            elif show_files:
                tree_lines.append(f"{prefix}{connector}{entry.name}")

    tree_lines.append(f"{root.name}/")
    _walk(root, depth=1)
    return {"root": str(root), "tree": "\n".join(tree_lines)}
