import os
import json
import re

EXCLUDE_DIRS = {"__pycache__", "cache", ".update_staging", "userscripts", "data"}
EXCLUDE_FILES = {".DS_Store", "create_shortcut.vbs", "prefs.json"}

def get_current_version():
    try:
        with open("config.py", "r", encoding="utf-8") as f:
            match = re.search(r'^VERSION\s*=\s*[\'"]([^\'"]+)[\'"]', f.read(), re.MULTILINE)
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass
    return "0.0.0"

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_list = []

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file in EXCLUDE_FILES or file.endswith(".pyc"):
                continue

            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, base_dir)

            rel_path = rel_path.replace(os.sep, "/")
            file_list.append(rel_path)

    file_list.sort()

    version = get_current_version()

    manifest_data = {
        "version": version,
        "files": file_list
    }

    manifest_path = os.path.join(base_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"[s] make_manifest: generated manifest.json for v{version}")
    print(f"[i] make_manifest: included {len(file_list)} files.")

if __name__ == "__main__":
    main()
