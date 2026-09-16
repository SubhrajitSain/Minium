import os
import base64

from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import QIcon

from config import BASE_DIR, ICON_DIR, FONTS_DIR

def get_pid_memory(pid: int) -> str:
    if pid <= 0:
        return ""
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

def apply_google_icon(btn, icon_name: str, fallback_text: str = "", size: QSize = QSize(15, 15)):
    icon = load_google_icon(icon_name)
    if not icon.isNull():
        btn.setIcon(icon)
        btn.setIconSize(size)
        btn.setText("")
    else:
        btn.setText(fallback_text)

def apply_os_icon(btn, theme_names: list, fallback_text: str = "", size: QSize = QSize(12, 12)):
    for name in theme_names:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            btn.setIcon(icon)
            btn.setIconSize(size)
            btn.setText("")
            return
    btn.setText(fallback_text)
