import urllib

from PySide6.QtCore import QUrl, QTimer, QUrlQuery
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from config import BYPASSED_DOMAINS, BYPASSED_PHISH_URLS, PHISH_CACHE, HTTPS_UPGRADE_ATTEMPTS, HTTP_FALLBACK_URLS, ADBLOCK_DOMAINS
from security.phishtank import PHISHTANK_SERVICE
from templates import get_phishing_html

class BrowserPage(QWebEnginePage):
    def __init__(self, profile, window):
        super().__init__(profile, window)
        self.window = window

    def get_view(self):
        if isinstance(self.window, QWebEngineView):
            return self.window
        parent = self.parent()
        if isinstance(parent, QWebEngineView):
            return parent
        return None

    def get_main_window(self):
        view = self.get_view()
        if view and hasattr(view, "window"):
            return view.window
        return None

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:
        url_str = url.toString()
        main_win = self.get_main_window()
        target_view = self.get_view()

        if url_str.startswith("minium://safety"):
            if main_win and hasattr(main_win, "navigate_back"):
                QTimer.singleShot(0, lambda: main_win.navigate_back(target_view))
            elif target_view and main_win:
                QTimer.singleShot(0, lambda: main_win.load_new_tab_page(target_view))
            return False

        if url_str.startswith("minium://action"):
            parsed = urllib.parse.urlparse(url_str)
            qs = urllib.parse.parse_qs(parsed.query)
            action = qs.get("do", [""])[0]

            if main_win:
                if action == "toggle_protect":
                    main_win.protect_me_enabled = not main_win.protect_me_enabled
                    main_win.adblock_interceptor.enabled = main_win.protect_me_enabled
                    main_win.prefs["protect_me"] = main_win.protect_me_enabled
                    main_win.save_prefs()
                elif action == "toggle_maxium":
                    main_win.toggle_maxium_mode()
                elif action == "passwords":
                    main_win.open_password_manager()
                elif action == "toggle_js":
                    main_win.toggle_js()
                    main_win.prefs["js_enabled"] = main_win.js_enabled
                    main_win.save_prefs()
                elif action == "toggle_theme":
                    main_win.toggle_web_theme()
                    main_win.prefs["web_theme_dark"] = main_win.web_theme_dark
                    main_win.save_prefs()
                elif action == "toggle_bookmarks_bar":
                    main_win.toggle_bookmarks_bar()
                elif action == "toggle_adblock_update":
                    current = main_win.prefs.get("auto_update_adblock", True)
                    main_win.prefs["auto_update_adblock"] = not current
                    main_win.save_prefs()
                elif action == "toggle_boot_update":
                    current = main_win.prefs.get("boot_update_checks", True)
                    main_win.prefs["boot_update_checks"] = not current
                    main_win.save_prefs()
                elif action == "pick_bg":
                    main_win.pick_new_tab_background()
                elif action == "add_shortcut":
                    main_win.add_new_tab_shortcut()
                elif action == "burn_data":
                    main_win.burn_data_with_warning()
                elif action == "clear_history":
                    from config import GLOBAL_HISTORY
                    from utils import save_history
                    GLOBAL_HISTORY.clear()
                    save_history(main_win.maxium_mode)
                elif action == "remove_bookmark":
                    from config import GLOBAL_BOOKMARKS
                    from utils import save_bookmarks
                    b_url = qs.get("url", [""])[0]
                    GLOBAL_BOOKMARKS[:] = [b for b in GLOBAL_BOOKMARKS if b.get("url") != b_url]
                    save_bookmarks(main_win.maxium_mode)
                    main_win.update_bookmark_icon()
                    if hasattr(main_win, "refresh_bookmarks_bar"):
                        main_win.refresh_bookmarks_bar()
                elif action == "customize_new_tab":
                    if main_win and hasattr(main_win, "open_new_tab_customizer"):
                        QTimer.singleShot(0, main_win.open_new_tab_customizer)

                if target_view and action not in ("burn_data", "toggle_maxium"):
                    QTimer.singleShot(0, target_view.reload)
            return False

        if url_str.startswith("minium://proceed?target="):
            target = url_str.split("target=", 1)[1]
            target_host = QUrl(target).host().lower()
            BYPASSED_DOMAINS.add(target_host)
            BYPASSED_PHISH_URLS.add(target)
            BYPASSED_PHISH_URLS.add(target.rstrip('/'))
            BYPASSED_PHISH_URLS.add(target.rstrip('/') + '/')
            if target_view and main_win:
                QTimer.singleShot(0, lambda: main_win.navigate_to(target, target_view))
            return False

        if is_main_frame and url.scheme() == "http":
            host = url.host().lower()
            if host not in HTTP_FALLBACK_URLS \
                and not url_str.startswith("http://localhost") \
                and not url_str.startswith("http://127.0.0.1") \
                and not url_str.startswith("http://192.168."):
                https_url = QUrl(url)
                https_url.setScheme("https")
                HTTPS_UPGRADE_ATTEMPTS.add(https_url.toString())
                if target_view and main_win:
                    QTimer.singleShot(0, lambda: target_view.setUrl(https_url))
                return False

        if self.url().scheme() == "minium" and url.scheme() in ("http", "https"):
            if target_view and main_win:
                query = QUrlQuery(url).queryItemValue("q").replace("+", " ") if url.hasQuery() else ""
                dest = query if query else url.toString()
                QTimer.singleShot(0, lambda: main_win.navigate_to(dest, target_view))
            return False

        if url.scheme() in ("minium", "about", "data", "devtools"):
            return True

        if is_main_frame and url.scheme() in ("http", "https"):
            protect_enabled = getattr(main_win, "protect_me_enabled", True) if main_win else True
            if protect_enabled:
                if url_str in PHISH_CACHE and PHISH_CACHE[url_str][0] and url_str not in BYPASSED_PHISH_URLS:
                    if target_view:
                        print("[!] page: detected a phishing site.")
                        QTimer.singleShot(0, lambda: target_view.setHtml(get_phishing_html(url_str), QUrl("minium://phishing")))
                    return False

                if target_view and url_str not in BYPASSED_PHISH_URLS:
                    PHISHTANK_SERVICE.check_url_async(target_view, url_str)

        return True
