import os
import json
import base64
import time
import urllib.request
import urllib.parse
import platform
import subprocess

from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import QIcon

from config import BASE_DIR, ICON_DIR, FONTS_DIR, PREFS_FILE, PREFS_FILE, HISTORY_FILE, BOOKMARKS_FILE, GLOBAL_HISTORY, GLOBAL_BOOKMARKS, FAVICONS_DIR

def get_pid_memory(pid: int) -> str:
    if pid <= 0:
        return ""

    if platform.system().lower() == "windows":
        try:
            out = subprocess.check_output(
                ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode('utf-8', errors='ignore')

            parts = out.strip().split('","')
            if len(parts) >= 5:
                mem_str = parts[4].replace(' K"', '').replace(',', '')
                kb = int(mem_str)
                if kb >= 1024:
                    return f"{kb / 1024:.1f} MB"
                return f"{kb} KB"
        except Exception:
            pass
    else:
        try:
            with open(f"/proc/{pid}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            kb = int(parts[1])
                            if kb >= 1024:
                                return f"{kb / 1024:.1f} MB"
                            return f"{kb} KB"
        except Exception:
            pass

    return ""

def get_minium_icon_b64() -> str:
    path = os.path.join(ICON_DIR, "minium.png")
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            pass
    return ""

def get_font_face_css() -> str:
    path = os.path.join(FONTS_DIR, "gsans_flex.ttf")
    url = QUrl.fromLocalFile(path).toString() if os.path.exists(path) else ""

    return f"""
    @font-face {{
        font-family: 'Google Sans Flex';
        src: local('Google Sans Flex'), url('{url}') format('truetype');
    }}
    """

def load_google_icon(name: str) -> QIcon:
    for ext in (".svg", ".png"):
        path = os.path.join(ICON_DIR, f"{name}{ext}")
        if os.path.exists(path):
            return QIcon(path)
    return QIcon()

def get_google_icon_path(name: str) -> str:
    for ext in (".svg", ".png"):
        path = os.path.join(ICON_DIR, f"{name}{ext}")
        if os.path.exists(path):
            return path.replace("\\", "/")
    return ""

def apply_google_icon(widget, icon_name: str, fallback_text: str = "", size: QSize = QSize(15, 15)):
    icon = load_google_icon(icon_name)
    if hasattr(widget, "setIcon"):
        if not icon.isNull():
            widget.setIcon(icon)
            widget.setIconSize(size)
            widget.setText("")
        else:
            widget.setText(fallback_text)
    elif hasattr(widget, "setPixmap"):
        if not icon.isNull():
            widget.setPixmap(icon.pixmap(size))
        else:
            widget.setText(fallback_text)

def apply_os_icon(btn, theme_names: list, fallback_text: str = "", size: QSize = QSize(12, 12)):
    for name in theme_names:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            btn.setIcon(icon)
            btn.setIconSize(size)
            btn.setText("")
            return
    btn.setText(fallback_text)

def get_prefs():
    defaults = {
        "maxium_mode": False,
        "protect_me": True,
        "js_enabled": True,
        "web_theme_dark": True,
        "show_bookmarks_bar": False,
        "auto_update_adblock": True,
        "boot_update_checks": True,
        "new_tab_bg_type": "none",
        "new_tab_bg": "",
        "new_tab_shortcuts": []
    }

    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                user_prefs = json.load(f)
                defaults.update(user_prefs)
        except Exception:
            pass
    return defaults

def save_prefs(prefs):
    try:
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
    except Exception as e:
        print(f"[!] utils: failed to save prefs: {e}")

def load_persistent_data():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                GLOBAL_HISTORY.extend(json.load(f))
        except Exception:
            pass
    if os.path.exists(BOOKMARKS_FILE):
        try:
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                GLOBAL_BOOKMARKS.extend(json.load(f))
        except Exception:
            pass

def save_history(maxium_mode: bool):
    if maxium_mode:
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(GLOBAL_HISTORY, f, indent=2)
        except Exception:
            pass

def save_bookmarks(maxium_mode: bool):
    if maxium_mode:
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(GLOBAL_BOOKMARKS, f, indent=2)
        except Exception:
            pass

def ensure_favicon_dir():
    os.makedirs(FAVICONS_DIR, exist_ok=True)

def get_favicon_cache_path(url: str) -> str:
    ensure_favicon_dir()
    try:
        host = urllib.parse.urlparse(url).netloc.lower() or url.lower()
    except Exception:
        host = "unknown"
    safe_host = "".join(c for c in host if c.isalnum() or c in (".", "-", "_")) or "unknown"
    return os.path.join(FAVICONS_DIR, f"{safe_host}.png")

def is_favicon_cache_valid(file_path: str) -> bool:
    SEVEN_DAYS = 7 * 24 * 3600
    if os.path.exists(file_path):
        try:
            return (time.time() - os.path.getmtime(file_path)) < SEVEN_DAYS
        except Exception:
            return False
    return False

def cache_favicon_bytes(url: str, data: bytes):
    if not data:
        return
    cache_path = get_favicon_cache_path(url)
    try:
        with open(cache_path, "wb") as f:
            f.write(data)
    except Exception:
        pass

def get_cached_favicon_b64(url: str, fetch_if_missing: bool = True) -> str:
    cache_path = get_favicon_cache_path(url)
    if is_favicon_cache_valid(cache_path):
        try:
            with open(cache_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            pass

    if fetch_if_missing:
        try:
            host = urllib.parse.urlparse(url).netloc.lower() or url.lower()
            if host:
                fetch_url = f"https://www.google.com/s2/favicons?domain={host}&sz=64"
                req = urllib.request.Request(fetch_url, headers={"User-Agent": "Mozilla/5.0 Minium"})
                with urllib.request.urlopen(req, timeout=2.0) as res:
                    data = res.read()
                    if data:
                        cache_favicon_bytes(url, data)
                        return base64.b64encode(data).decode("utf-8")
        except Exception:
            pass

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            pass

    return ""
