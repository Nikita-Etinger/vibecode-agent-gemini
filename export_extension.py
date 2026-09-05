import os
from pathlib import Path

def export_extension():
    ext_dir = Path("chrome_extension")
    output_file = Path("extension_bundle.txt")
    
    if not ext_dir.exists():
        print("Directory chrome_extension not found.")
        return

    files = sorted([f for f in ext_dir.glob("**/*") if f.is_file()])
    
    with open(output_file, "w", encoding="utf-8") as out:
        for file_path in files:
            rel_path = file_path.relative_to(ext_dir)
            out.write(f"=== FILE: {rel_path} ===\n")
            try:
                content = file_path.read_text(encoding="utf-8")
                out.write(content)
            except Exception as e:
                out.write(f"[Error reading file: {e}]")
            out.write("\n\n" + "="*40 + "\n\n")
            
    print(f"Export completed: {output_file.absolute()}")

if __name__ == "__main__":
    export_extension()
