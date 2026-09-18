import os
import sys
import json
import stat
import shutil
import urllib.request
import platform

from config import BASE_DIR, ICON_DIR, VERSION, RAW_REPO_URL

IS_WINDOWS = platform.system().lower() == "windows"
USER_HOME = os.path.expanduser("~")
BIN_DIR = os.path.join(USER_HOME, ".local", "bin")
DESKTOP_DIR = os.path.join(USER_HOME, ".local", "share", "applications")
LINUX_DESKTOP_FILE = os.path.join(DESKTOP_DIR, "minium.desktop")
LINUX_BIN_FILE = os.path.join(BIN_DIR, "minium")
ICON_FILE = os.path.join(ICON_DIR, "minium.png")

def _get_windows_paths():
    desktop = os.path.join(os.environ.get("USERPROFILE", USER_HOME), "Desktop")
    start_menu = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs")
    return desktop, start_menu

def install():
    print("[*] installer: preparing to install...")
    main_script = os.path.join(BASE_DIR, "minium.py")

    if IS_WINDOWS:
        print("[i] installer: detected platform: Windows")
        desktop, start_menu = _get_windows_paths()
        shortcut_desktop = os.path.join(desktop, "Minium.lnk")
        shortcut_start = os.path.join(start_menu, "Minium.lnk")

        python_exe = sys.executable.replace("python.exe", "pythonw.exe")

        vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{shortcut_desktop}")
oLink.TargetPath = "{python_exe}"
oLink.Arguments = "{main_script}"
oLink.WorkingDirectory = "{BASE_DIR}"
oLink.Save
Set oLink2 = oWS.CreateShortcut("{shortcut_start}")
oLink2.TargetPath = "{python_exe}"
oLink2.Arguments = "{main_script}"
oLink2.WorkingDirectory = "{BASE_DIR}"
oLink2.Save
"""
        vbs_path = os.path.join(BASE_DIR, "create_shortcut.vbs")
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        
        os.system(f'cscript //nologo "{vbs_path}"')
        os.remove(vbs_path)
        print(f"[i] installer: created Windows shortcuts on Desktop and Start Menu.")

    else:
        print("[i] installer: detected platform: non-Windows (Linux)")
        os.makedirs(BIN_DIR, exist_ok=True)
        os.makedirs(DESKTOP_DIR, exist_ok=True)

        wrapper_content = f"""#!/bin/sh
exec "{sys.executable}" "{main_script}" "$@"
"""
        with open(LINUX_BIN_FILE, "w", encoding="utf-8") as f:
            f.write(wrapper_content)
        os.chmod(LINUX_BIN_FILE, os.stat(LINUX_BIN_FILE).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[i] installer: created launcher: {LINUX_BIN_FILE}")

        desktop_entry = f"""[Desktop Entry]
Version={VERSION}
Type=Application
Name=Minium
GenericName=Web Browser
Comment=A minimal, privacy-first Chromium based web browser
Exec={LINUX_BIN_FILE} %U
Icon={ICON_FILE}
Terminal=false
StartupWMClass=minium
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
"""
        with open(LINUX_DESKTOP_FILE, "w", encoding="utf-8") as f:
            f.write(desktop_entry)
        print(f"[i] installer: created desktop entry: {LINUX_DESKTOP_FILE}")
        os.system(f"update-desktop-database {DESKTOP_DIR} >/dev/null 2>&1")

    print(f"[s] installer: Minium v{VERSION} successfully installed!")


def uninstall():
    print("[*] installer: preparing to uninstall...")
    if IS_WINDOWS:
        desktop, start_menu = _get_windows_paths()
        shortcut_desktop = os.path.join(desktop, "Minium.lnk")
        shortcut_start = os.path.join(start_menu, "Minium.lnk")

        for p in (shortcut_desktop, shortcut_start):
            if os.path.exists(p):
                os.remove(p)
                print(f"[i] installer: removed: {p}")
    else:
        if os.path.exists(LINUX_BIN_FILE):
            os.remove(LINUX_BIN_FILE)
            print(f"[i] installer: removed: {LINUX_BIN_FILE}")

        if os.path.exists(LINUX_DESKTOP_FILE):
            os.remove(LINUX_DESKTOP_FILE)
            print(f"[i] installer: removed: {LINUX_DESKTOP_FILE}")

        os.system(f"update-desktop-database {DESKTOP_DIR} >/dev/null 2>&1")
        
    print("[s] installer: Minium has been removed from your system.")


def check_and_apply_update(dry_run=False):
    manifest_url = f"{RAW_REPO_URL}/manifest.json"
    print(f"[*] installer: checking manifest: {manifest_url}")

    try:
        req = urllib.request.Request(manifest_url, headers={"User-Agent": f"Minium/{VERSION}", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            manifest = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[x] installer: could not check for updates: {e}")
        return False, f"Check failed: {e}"

    remote_version = manifest.get("version", "unknown")

    if remote_version == "unknown":
        print("[x] installer: failed to check version in remote manifest.")
        return False, "Failed to parse remote manifest."

    if remote_version <= VERSION:
        print(f"[s] installer: Minium is up to date (v{VERSION}).")
        return False, f"Minium is up to date (v{VERSION})."

    print(f"[i] installer: new version available: v{remote_version} (current: v{VERSION})")
    if dry_run:
        return True, f"New version v{remote_version} is available. Update from the menu."

    files_to_update = manifest.get("files", [])
    if "manifest.json" not in files_to_update:
        files_to_update.append("manifest.json")

    if not os.access(BASE_DIR, os.W_OK):
        print("[x] installer: permission denied, cannot write to browser directory.")
        return False, "Permission denied! Please exit and then run 'minium --update' with admin/root privileges."

    staging_dir = os.path.join(BASE_DIR, ".update_staging")
    os.makedirs(staging_dir, exist_ok=True)

    try:
        for rel_path in files_to_update:
            file_url = f"{RAW_REPO_URL}/{rel_path}"
            dest_staged = os.path.join(staging_dir, rel_path)
            os.makedirs(os.path.dirname(dest_staged), exist_ok=True)

            print(f"[*] installer: downloading: {rel_path}")
            req = urllib.request.Request(file_url, headers={"User-Agent": f"Minium/{VERSION}", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=15) as res, open(dest_staged, "wb") as out:
                out.write(res.read())

        for rel_path in files_to_update:
            staged_file = os.path.join(staging_dir, rel_path)
            target_file = os.path.join(BASE_DIR, rel_path)
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            os.replace(staged_file, target_file)

        shutil.rmtree(staging_dir, ignore_errors=True)
        print(f"[s] installer: successfully updated Minium to v{remote_version}!")
        return True, f"Updated to v{remote_version}! Restart Minium to apply changes."
    except Exception as e:
        shutil.rmtree(staging_dir, ignore_errors=True)
        print(f"[x] installer: update failed mid-patch: {e}")
        return False, "Update failed while modifying files. Please try again."
