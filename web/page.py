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
