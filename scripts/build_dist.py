import base64
import gzip
import os
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"

EXCLUDE_DIRS = {".git", ".idea", ".pytest_cache", "__pycache__", "backups", "dist", "workspace"}

def obfuscate_code(code: str) -> str:
    compressed = gzip.compress(code.encode("utf-8"))
    b64_payload = base64.b85encode(compressed).decode("ascii")
    runner = (
        "# Protected by Vibecode Obfuscator [Nikita-Etinger]\n"
        "import gzip as _g, base64 as _b\n"
        f"exec(_g.decompress(_b.b85decode('{b64_payload}')).decode('utf-8'))\n"
    )
    return runner

def build():
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[*] Building release in: {DIST_DIR}")

    for current, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_path = Path(current).relative_to(ROOT_DIR)
        target_path = DIST_DIR / rel_path
        target_path.mkdir(parents=True, exist_ok=True)

        for f in files:
            src_file = Path(current) / f
            dst_file = target_path / f

            if f.endswith(".py") and not f.startswith("test_") and f != "build_dist.py":
                src_code = src_file.read_text(encoding="utf-8")
                obf_code = obfuscate_code(src_code)
                dst_file.write_text(obf_code, encoding="utf-8")
                print(f"  [PY-OBF] {rel_path / f}")
            elif not f.startswith("test_") and not f.endswith(".pyc"):
                shutil.copy2(src_file, dst_file)
                print(f"  [COPY]   {rel_path / f}")

    print("\n[+] Release build complete!")

if __name__ == "__main__":
    build()
