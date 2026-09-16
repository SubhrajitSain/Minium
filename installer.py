import os
import sys
import json
import stat
import shutil
import urllib.request
from config import BASE_DIR, ICON_DIR, VERSION, RAW_REPO_URL

USER_HOME = os.path.expanduser("~")
BIN_DIR = os.path.join(USER_HOME, ".local", "bin")
DESKTOP_DIR = os.path.join(USER_HOME, ".local", "share", "applications")
DESKTOP_FILE = os.path.join(DESKTOP_DIR, "minium.desktop")
BIN_FILE = os.path.join(BIN_DIR, "minium")
ICON_FILE = os.path.join(ICON_DIR, "minium.png")


def install():
    print("[*] installer: preparing to install...")
    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(DESKTOP_DIR, exist_ok=True)

    main_script = os.path.join(BASE_DIR, "minium.py")
    wrapper_content = f"""#!/bin/sh
exec "{sys.executable}" "{main_script}" "$@"
"""
    with open(BIN_FILE, "w", encoding="utf-8") as f:
        f.write(wrapper_content)
    os.chmod(BIN_FILE, os.stat(BIN_FILE).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"[i] installer: created launcher: {BIN_FILE}")

    desktop_entry = f"""[Desktop Entry]
Version={VERSION}
Type=Application
Name=Minium
GenericName=Web Browser
Comment=A minimal, privacy-first Chromium based web browser
Exec={BIN_FILE} %U
Icon={ICON_FILE}
Terminal=false
StartupWMClass=minium
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
"""
    with open(DESKTOP_FILE, "w", encoding="utf-8") as f:
        f.write(desktop_entry)
    print(f"[i] installer: created desktop entry: {DESKTOP_FILE}")

    os.system(f"update-desktop-database {DESKTOP_DIR} >/dev/null 2>&1")
    print(f"[s] installer: Minium v{VERSION} successfully installed for this user!")
    print("[i] installer: you can now run 'minium' from terminal or launch it from your application menu.")


def uninstall():
    if os.path.exists(BIN_FILE):
        os.remove(BIN_FILE)
        print(f"[i] installer: removed: {BIN_FILE}")

    if os.path.exists(DESKTOP_FILE):
        os.remove(DESKTOP_FILE)
        print(f"[i] installer: removed: {DESKTOP_FILE}")

    os.system(f"update-desktop-database {DESKTOP_DIR} >/dev/null 2>&1")
    print("[s] installer: Minium has been uninstalled from your user environment.")


def check_and_apply_update(dry_run=False):
    manifest_url = f"{RAW_REPO_URL}/manifest.json"
    print(f"[*] installer: checking for updates from: {manifest_url}")

    try:
        req = urllib.request.Request(manifest_url, headers={"User-Agent": f"Minium/{VERSION}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[x] installer: could not check updates: {e}")
        return False, f"Check failed: {e}"

    remote_version = manifest.get("version", "unknown")

    if remote_version == "unknown":
        print("[x] installer: failed to check version in remote manifest.")
        return False, "Failed to check version in remote manifest."

    if remote_version <= VERSION:
        print(f"[s] installer: Minium is up to date (v{VERSION}).")
        return False, f"Minium is up to date (v{VERSION})."

    print(f"[i] installer: new version available: v{remote_version} (current: v{VERSION})")
    if dry_run:
        return True, f"New version v{remote_version} is available (current: {VERSION}). Update from the menu."

    files_to_update = manifest.get("files", [])
    staging_dir = os.path.join(BASE_DIR, ".update_staging")
    os.makedirs(staging_dir, exist_ok=True)

    try:
        for rel_path in files_to_update:
            file_url = f"{RAW_REPO_URL}/{rel_path}"
            dest_staged = os.path.join(staging_dir, rel_path)
            os.makedirs(os.path.dirname(dest_staged), exist_ok=True)

            print(f"[*] installer: downloading: {rel_path}")
            req = urllib.request.Request(file_url, headers={"User-Agent": f"Minium/{VERSION}"})
            with urllib.request.urlopen(req, timeout=15) as res, open(dest_staged, "wb") as out:
                out.write(res.read())

        for rel_path in files_to_update:
            staged_file = os.path.join(staging_dir, rel_path)
            target_file = os.path.join(BASE_DIR, rel_path)
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            os.replace(staged_file, target_file)

        shutil.rmtree(staging_dir, ignore_errors=True)
        print(f"[s] installer: successfully updated Minium to v{remote_version}!")
        return True, f"Updated Minium to v{remote_version}! Restart to apply changes."
    except Exception as e:
        shutil.rmtree(staging_dir, ignore_errors=True)
        print(f"[x] installer: update failed mid-patch: {e}")
        return False, "Update failed while modifying files, Minium may be corrupted."
