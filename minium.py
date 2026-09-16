import sys
import os
import argparse
from threading import Thread

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QFontDatabase, QFont, QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEngineUrlScheme

from config import ICON_DIR, FONTS_DIR, WINDOWS, VERSION
from security.adblock import start_adblock_fetch
from browser import MiniumBrowser, UPDATE_SERVICE
from installer import check_and_apply_update

def main():
    print(
         "\n"
         "   ██▄  ▄██ ▄▄ ▄▄  ▄▄ ▄▄ ▄▄ ▄▄ ▄▄   ▄▄ \n"
         "   ██ ▀▀ ██ ██ ███▄██ ██ ██ ██ ██▀▄▀██ \n"
        f"   ██    ██ ██ ██ ▀██ ██ ▀███▀ ██   ██ v{VERSION}\n"
         "    The Minimal Chromium Web Browser.  \n"
    )

    print("(c) 2026 Minium by Subhrajit Sain. All rights reserved.")
    print("Thanks to the authors of the deps and resources used.\n")

    print("[*] main: setting up flags and scheme...")
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--log-level=3"
    os.environ["GTK_THEME"] = "Adwaita:dark"
    scheme = QWebEngineUrlScheme(b"minium")
    scheme.setFlags(
        QWebEngineUrlScheme.Flag.LocalScheme |
        QWebEngineUrlScheme.Flag.LocalAccessAllowed |
        QWebEngineUrlScheme.Flag.SecureScheme
    )
    QWebEngineUrlScheme.registerScheme(scheme)
    if not os.environ.get("QTWEBENGINE_RESOURCES_PATH"):
        for p in ("/usr/share/qt6/resources", "/usr/lib64/qt6/resources", "/usr/lib/qt6/resources"):
            if os.path.exists(p):
                os.environ["QTWEBENGINE_RESOURCES_PATH"] = p
                break

    print("[*] main: setting up argument parser...")
    parser = argparse.ArgumentParser(description=f"Minium v{VERSION} - Minimal Chromium Browser")
    parser.add_argument("-l", "--less", action="store_true", help="Run in viewport-only mode")
    parser.add_argument("-i", "--install", action="store_true", help="Install Minium for current user")
    parser.add_argument("-u", "--uninstall", action="store_true", help="Uninstall Minium from current user")
    parser.add_argument("-U", "--update", action="store_true", help="Update Minium from remote repository")
    parser.add_argument("url", nargs="?", default=None, help="Starting URL")

    print("[*] main: parsing arguments...")
    args, qt_args = parser.parse_known_args()

    if args.install:
        print("[*] main: installation requested, sending to installer...")
        import installer
        installer.install()
        sys.exit(0)

    if args.uninstall:
        print("[*] main: uninstallation requested, sending to installer...")
        import installer
        installer.uninstall()
        sys.exit(0)

    if args.update:
        print("[*] main: update requested, sending to installer...")
        import installer
        installer.check_and_apply_update()
        sys.exit(0)

    print("[*] main: setting up app and app style...")
    app = QApplication([sys.argv[0]] + qt_args)
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor("#151722"))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor("#f1f3f8"))
    app.setPalette(pal)
    if hasattr(Qt, "ColorScheme") and hasattr(QGuiApplication.styleHints(), "setColorScheme"):
        QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    app.setStyleSheet("""
        QToolTip {
            background-color: #151722;
            color: #f1f3f8;
            border: 1px solid #252838;
            border-radius: 6px;
            padding: 2px 3px;
            font-family: 'Google Sans Flex', sans-serif;
            font-size: 11.5px;
            font-weight: 500;
        }
    """)

    print("[*] main: setting up app icon...")
    app_icon_path = os.path.join(ICON_DIR, "minium.png")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))

    print("[*] main: setting up app font...")
    font_path = os.path.join(FONTS_DIR, "gsans_flex.ttf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)

    app.setFont(QFont("Google Sans Flex", 10))

    print("[*] main: starting browser...")
    browser = MiniumBrowser(headless=args.less, start_url=args.url)
    WINDOWS.append(browser)
    browser.show()

    def boot_update_check(browser=None):
        print("[*] main: starting boot update checks...")
        from config import WINDOWS
        from browser import UPDATE_SERVICE
        import installer
        target = browser or (WINDOWS[0] if WINDOWS else None)
        if not target or getattr(target, "_is_closing", False):
            return
        target.fullscreen_banner.show_message("Checking for any new updates...", auto_dismiss=False)
        def worker():
            try:
                success, msg = installer.check_and_apply_update(dry_run=True)
            except Exception as e:
                success, msg = False, f"Check failed: {e}"
            UPDATE_SERVICE.finished.emit(success, msg)
        Thread(target=worker, daemon=True).start()

    QTimer.singleShot(2000, lambda: start_adblock_fetch(on_complete_callback=boot_update_check))

    print("[*] main: executing app...")
    ret = app.exec()

    print("[*] main: finishing up...")
    WINDOWS.clear()
    del browser

    print("[s] main: quitting Minium, bye!")
    sys.exit(ret)


if __name__ == "__main__":
    main()
