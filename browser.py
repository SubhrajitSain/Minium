import os
import gc
import re
import time
import urllib.parse
from threading import Thread

from PySide6.QtCore import Qt, QSize, QUrl, QTimer, QEvent, QPoint, QObject, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QIcon, QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QToolButton,
    QFileDialog,
    QDialog,
    QPlainTextEdit,
    QTabBar,
    QSizePolicy,
    QLabel,
    QMenu,
    QSplitter
)
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineLoadingInfo,
    QWebEngineDownloadRequest,
    QWebEnginePage,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from config import (
    WINDOWS,
    BYPASSED_DOMAINS,
    BYPASSED_PHISH_URLS,
    PHISH_CACHE,
    ICON_DIR,
)
from utils import load_google_icon, apply_google_icon, apply_os_icon, get_pid_memory
from templates import get_error_html, get_blocked_html, get_phishing_html
from security.adblock import AdBlockInterceptor, ADBLOCK_SERVICE
from security.phishtank import PHISHTANK_SERVICE
from web.scripts import get_all_user_scripts
from web.scheme import MiniumSchemeHandler
from web.page import BrowserPage
from web.view import CustomWebEngineView, WebEngineStack
from widgets.devtools import DevToolsPane
from widgets.frame import TitleBarWidget, ResizeGripsManager, WindowBorderOverlay, TabScrollArea, ReservedDragZone
from widgets.tab_bar import BrowserTabBar
from widgets.address_bar import AddressBar
from widgets.search_bar import InPageSearchBar
from widgets.overlays import FullscreenBanner, LoadingViewport
from widgets.popups import (
    SecurityPopup,
    DownloadsPopup,
    AboutDialog,
    HtmlSyntaxHighlighter,
)
import installer

class UpdateService(QObject):
    finished = Signal(bool, str)

UPDATE_SERVICE = UpdateService()

class MiniumBrowser(QMainWindow):
    def __init__(self, headless=False, start_url=None, shared_profile=None):
        super().__init__()
        self.headless = headless
        self.start_url = start_url
        self.closed_tabs_history = []
        self.web_theme_dark = True

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.resize(800, 600)
        self.setMinimumSize(400, 300)

        self.container = QWidget(self)
        self.container.setObjectName("window_container")
        self.container.setMouseTracking(True)
        self.setCentralWidget(self.container)
        self.border_overlay = WindowBorderOverlay(self.container)

        self._pre_fullscreen_maximized = False
        self._fullscreen_mode = False
        self.fullscreen_banner = FullscreenBanner(self.container)
        self.fullscreen_banner.hide()

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        if shared_profile is not None:
            self.profile = shared_profile
        else:
            self.profile = QWebEngineProfile()
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)

        if hasattr(self.profile, "setColorScheme"):
            self.profile.setColorScheme(QWebEngineProfile.ColorScheme.Dark)

        self.adblock_interceptor = AdBlockInterceptor(self)
        self.profile.setUrlRequestInterceptor(self.adblock_interceptor)
        self.profile.downloadRequested.connect(self.on_download_requested)

        self.scheme_handler = MiniumSchemeHandler(self.profile)
        self.profile.installUrlSchemeHandler(b"minium", self.scheme_handler)

        real_ua = self.profile.httpUserAgent()
        clean_ua = re.sub(r'QtWebEngine/\S+\s*', '', real_ua)
        self.profile.setHttpUserAgent(clean_ua)
        self.profile.setHttpAcceptLanguage("en-US,en;q=0.9")

        for script in get_all_user_scripts():
            self.profile.scripts().insert(script)

        self.tab_bar = BrowserTabBar(self)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)

        self.protect_me_enabled = True
        PHISHTANK_SERVICE.phish_found.connect(self.on_phish_detected)
        ADBLOCK_SERVICE.updated.connect(self.fullscreen_banner.show_message)
        UPDATE_SERVICE.finished.connect(self.on_update_finished)

        self.stack = WebEngineStack()
        self.stack.setContentsMargins(1, 0, 1, 1)

        self.window_controls = self.create_window_controls()

        self.setup_header()

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.container)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #1a1c27;
                width: 2px;
            }
        """)
        self.splitter.addWidget(self.stack)

        self.devtools_pane = DevToolsPane(self.profile, self.splitter)
        self.devtools_pane.hide()
        self.splitter.addWidget(self.devtools_pane)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, True)

        self.main_layout.addWidget(self.splitter, 1)

        self.search_pill = InPageSearchBar(self, self.container)

        self.setup_shortcuts()

        self._reveal_timer = QTimer(self)
        self._reveal_timer.setSingleShot(True)
        self._reveal_timer.timeout.connect(self.reveal_viewport)

        first_view = self.add_tab(self.start_url)

        self.loading_screen = LoadingViewport(self.stack)
        self.stack.addWidget(self.loading_screen)
        self.stack.setCurrentWidget(self.loading_screen)

        first_view.loadStarted.connect(self.reveal_viewport)
        first_view.loadFinished.connect(self.reveal_viewport)
        self._reveal_timer.start(250)

        self.update_frame_styling()

        self.resize_grips = ResizeGripsManager(self, self.container)

        self.tab_idle_timer = QTimer(self)
        self.tab_idle_timer.setInterval(60000)
        self.tab_idle_timer.timeout.connect(self.check_idle_tabs)
        self.tab_idle_timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_window_mask()
        if hasattr(self, "resize_grips"):
            self.resize_grips.update_geometry()

    def update_window_mask(self):
        is_fs = self.isMaximized() or self.isFullScreen() or getattr(self, "_fullscreen_mode", False)
        self.clearMask()
        self.container.clearMask()
        if is_fs:
            if hasattr(self, "border_overlay"):
                self.border_overlay.hide()
        else:
            if hasattr(self, "border_overlay"):
                self.border_overlay.setGeometry(self.container.rect())
                self.border_overlay.show()
                self.border_overlay.raise_()

    def update_views_mask(self):
        if hasattr(self, "stack") and hasattr(self.stack, "update_mask"):
            self.stack.update_mask()
        if hasattr(self, "tab_bar"):
            for i in range(self.tab_bar.count()):
                v = self.tab_bar.tabData(i)
                if v and hasattr(v, "update_mask"):
                    v.update_mask()

    def update_frame_styling(self):
        self.tab_strip_widget.setObjectName("title_bar")
        is_max = self.isMaximized() or self.isFullScreen() or getattr(self, "_fullscreen_mode", False)

        tooltip_style = """
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
        """

        if is_max:
            self.container.setStyleSheet(f"""
                {tooltip_style}
                #window_container {{
                    background-color: #050608;
                    border-radius: 0px;
                }}
            """)
            self.tab_strip_widget.setStyleSheet("""
                #title_bar {
                    background-color: #0b0c12;
                    border-bottom: 1px solid #1c1e29;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                }
            """)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.stack.setContentsMargins(0, 0, 0, 0)
        else:
            self.container.setStyleSheet(f"""
                {tooltip_style}
                #window_container {{
                    background-color: #050608;
                    border-radius: 6px;
                }}
            """)
            self.tab_strip_widget.setStyleSheet("""
                #title_bar {
                    background-color: #0b0c12;
                    border-bottom: 1px solid #1c1e29;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                }
            """)
            self.main_layout.setContentsMargins(1, 1, 1, 1)
            self.stack.setContentsMargins(1, 0, 1, 1)

        self.update_window_mask()
        if hasattr(self, "resize_grips"):
            self.resize_grips.update_geometry()

    def changeEvent(self, event: QEvent):
        if event.type() == QEvent.Type.WindowStateChange:
            self.update_frame_styling()
        super().changeEvent(event)

    def on_phish_detected(self, view, url_str: str):
        print("[!] browser: phishing site detected:", url_str)
        if not self.protect_me_enabled or url_str in BYPASSED_PHISH_URLS:
            print("[!] browser: ignoring phishing site.")
            return

        def handle_danger():
            try:
                if view and (view.url().toString() == url_str or url_str in view.url().toString()):
                    view.stop()
                    view.setHtml(get_phishing_html(url_str), QUrl("minium://phishing"))
            except RuntimeError:
                pass

        QTimer.singleShot(0, handle_danger)

    def on_update_finished(self, success: bool, msg: str):
        is_err = not success and ("fail" in msg.lower() or "error" in msg.lower() or "corrupt" in msg.lower())
        self.fullscreen_banner.show_message(msg, is_error=is_err, auto_dismiss=True)

    def update_shield_status(self):
        cv = self.current_view()
        if not cv:
            return

        url = cv.url()
        url_str = url.toString()
        scheme = url.scheme()

        is_internal = url_str.startswith("minium://") or not url_str or url_str == "about:blank"
        if is_internal:
            icon_name = "sec_good"
            fallback = "🛡"
        else:
            tls_ok = (scheme == "https")
            is_phish = bool(url_str in PHISH_CACHE and PHISH_CACHE[url_str][0])

            score = 100
            if not tls_ok:
                score -= 35
            if is_phish:
                score -= 65

            if score == 100:
                icon_name = "sec_good"
                fallback = "🛡"
            elif score >= 70:
                icon_name = "sec_warn"
                fallback = "⚠️"
            else:
                icon_name = "sec_crit"
                fallback = "🚨"

        apply_google_icon(self.shield_btn, icon_name, fallback, QSize(16, 16))

    def show_security_popup(self):
        cv = self.current_view()
        if not cv:
            return

        url = cv.url()
        url_str = url.toString()
        scheme = url.scheme()
        host = url.host().lower()

        if url_str.startswith("minium://") or not url_str or url_str == "about:blank":
            self.security_popup.update_security(
                tls_ok=True,
                phish_status="N/A",
                ads=0,
                trackers=0,
                perms_str="N/A",
                score=100
            )
        else:
            tls_ok = (scheme == "https")
            is_phish = bool(url_str in PHISH_CACHE and PHISH_CACHE[url_str][0])
            phish_status = "Phish detected" if is_phish else "Clean"

            stats = self.adblock_interceptor.stats.get(host, {"ads": 0, "trackers": 0})
            ads_count = stats["ads"]
            trackers_count = stats["trackers"]

            js_enabled = cv.settings().testAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled)
            perms_str = f"JS: {'Allowed' if js_enabled else 'Blocked'}"

            score = 100
            if not tls_ok:
                score -= 35
            if is_phish:
                score -= 65

            self.security_popup.update_security(
                tls_ok=tls_ok,
                phish_status=phish_status,
                ads=ads_count,
                trackers=trackers_count,
                perms_str=perms_str,
                score=max(0, score)
            )

        btn_global = self.shield_btn.mapToGlobal(QPoint(0, self.shield_btn.height() + 4))
        popup_x = btn_global.x() - (self.security_popup.sizeHint().width() - self.shield_btn.width())
        self.security_popup.popup(QPoint(max(10, popup_x), btn_global.y()))

    def show_downloads_popup(self):
        btn_global = self.dl_btn.mapToGlobal(QPoint(0, self.dl_btn.height() + 4))
        popup_x = btn_global.x() - (self.downloads_popup.sizeHint().width() - self.dl_btn.width())
        self.downloads_popup.popup(QPoint(max(10, popup_x), btn_global.y()))

    def on_fullscreen_requested(self, request: QWebEngineFullScreenRequest):
        request.accept()
        if request.toggleOn():
            self.enter_fullscreen()
        else:
            self.exit_fullscreen()

    def toggle_fullscreen(self):
        if self._fullscreen_mode:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):
        if self._fullscreen_mode:
            return
        self._fullscreen_mode = True
        self._pre_fullscreen_maximized = self.isMaximized()

        self.tab_strip_widget.hide()
        self.navbar_widget.hide()

        if self.isMaximized():
            self.showNormal()

        self.showFullScreen()
        self.update_frame_styling()

        cv = self.current_view()
        domain = "Minium"
        if cv:
            qurl = cv.url()
            if qurl.host():
                domain = qurl.host()
            elif cv.title() and cv.title() != "New Tab":
                domain = cv.title()
        if domain == "newtab":
            domain = "New Tab"

        QTimer.singleShot(150, lambda: self.fullscreen_banner.show_message(f"{domain} is now fullscreen, press F11 to exit."))

    def exit_fullscreen(self):
        if not self._fullscreen_mode:
            return
        self._fullscreen_mode = False
        self.fullscreen_banner.hide()

        self.showNormal()
        if self._pre_fullscreen_maximized:
            self.showMaximized()

        self.tab_strip_widget.show()
        if not self.headless:
            self.navbar_widget.show()

        self.update_frame_styling()

        cv = self.current_view()
        domain = "Minium"
        if cv:
            qurl = cv.url()
            if qurl.host():
                domain = qurl.host()
            elif cv.title() and cv.title() != "New Tab":
                domain = cv.title()
        if domain == "newtab":
            domain = "New Tab"
        QTimer.singleShot(150, lambda: self.fullscreen_banner.show_message(f"{domain} is no longer fullscreen."))

    def reveal_viewport(self, *args):
        try:
            if not self.isVisible():
                return
        except RuntimeError:
            return

        if hasattr(self, 'loading_screen') and self.loading_screen:
            self.stack.removeWidget(self.loading_screen)
            self.loading_screen.deleteLater()
            self.loading_screen = None
            idx = self.tab_bar.currentIndex()
            target_view = self.tab_bar.tabData(idx)
            if target_view:
                self.stack.setCurrentWidget(target_view)
            cv = self.current_view()
            if cv:
                self.on_url_changed(cv, cv.url())

    def setup_shortcuts(self):
        print("[*] browser: setting up keyboard shortcuts...")

        self.fs_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F11), self)
        self.fs_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fs_shortcut.activated.connect(self.toggle_fullscreen)
        self.fs_shortcut_alt = QShortcut(QKeySequence("Ctrl+F11"), self)
        self.fs_shortcut_alt.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.fs_shortcut_alt.activated.connect(self.toggle_fullscreen)

        act_next_tab = QAction(self)
        act_next_tab.setShortcut(QKeySequence("Ctrl+Tab"))
        act_next_tab.triggered.connect(self.next_tab)
        self.addAction(act_next_tab)

        act_prev_tab = QAction(self)
        act_prev_tab.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        act_prev_tab.triggered.connect(self.prev_tab)
        self.addAction(act_prev_tab)

        act_focus_url = QAction(self)
        act_focus_url.setShortcuts([QKeySequence("Ctrl+L"), QKeySequence("Alt+D")])
        act_focus_url.triggered.connect(self.focus_address_bar)
        self.addAction(act_focus_url)

        act_reload = QAction(self)
        act_reload.setShortcuts([QKeySequence("Ctrl+R"), QKeySequence("F5")])
        act_reload.triggered.connect(lambda: self.current_view() and self.current_view().reload())
        self.addAction(act_reload)

        act_hard_reload = QAction(self)
        act_hard_reload.setShortcuts([QKeySequence("Ctrl+Shift+R"), QKeySequence("Ctrl+F5")])
        act_hard_reload.triggered.connect(self.hard_reload)
        self.addAction(act_hard_reload)

        for i in range(1, 10):
            act_num = QAction(self)
            act_num.setShortcut(QKeySequence(f"Ctrl+{i}"))
            act_num.triggered.connect(lambda _, n=i: self.jump_to_tab(n))
            self.addAction(act_num)

        self.devtools_window = None

        def toggle_devtools():
            cv = self.current_view()
            if not cv:
                return
            if self.devtools_pane.isVisible():
                self.devtools_pane.close_pane()
            else:
                self.devtools_pane.attach_to_page(cv.page())
                total_w = self.width()
                self.splitter.setSizes([int(total_w * 0.62), int(total_w * 0.38)])

        act_devtools = QAction(self)
        act_devtools.setShortcuts(["F12", "Ctrl+Shift+I"])
        act_devtools.triggered.connect(toggle_devtools)
        self.addAction(act_devtools)

        def trigger_current_pip():
            cv = self.current_view()
            if not cv:
                self.fullscreen_banner.show_message("PiP is currently unavailable.", is_error=True)
                return

            js_code = """
            (function() {
                if (!document.pictureInPictureEnabled) return false;
                let v = Array.from(document.querySelectorAll('video')).find(v => !v.paused) ||
                        document.querySelector('video');
                if (!v || !v.requestPictureInPicture) return false;
                try {
                    v.removeAttribute('disablePictureInPicture');
                    if (document.pictureInPictureElement) {
                        document.exitPictureInPicture();
                        return true;
                    } else {
                        let p = v.requestPictureInPicture();
                        if (p && p.catch) p.catch(() => {});
                        return true;
                    }
                } catch(e) {
                    return false;
                }
            })();
            """
            def on_pip_result(success):
                if not success:
                    self.fullscreen_banner.show_message("PiP is currently unavailable.", is_error=True)

            cv.page().runJavaScript(js_code, on_pip_result)

        act_pip = QAction(self)
        act_pip.setShortcut(QKeySequence("Alt+P"))
        act_pip.triggered.connect(trigger_current_pip)
        self.addAction(act_pip)

    def next_tab(self):
        count = self.tab_bar.count()
        if count > 1:
            self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() + 1) % count)

    def prev_tab(self):
        count = self.tab_bar.count()
        if count > 1:
            self.tab_bar.setCurrentIndex((self.tab_bar.currentIndex() - 1 + count) % count)

    def jump_to_tab(self, n: int):
        count = self.tab_bar.count()
        if count == 0:
            return
        if n == 9:
            self.tab_bar.setCurrentIndex(count - 1)
        elif n <= count:
            self.tab_bar.setCurrentIndex(n - 1)

    def focus_address_bar(self):
        if not self.headless:
            self.url_bar.setFocus()
            self.url_bar.selectAll()

    def hard_reload(self):
        cv = self.current_view()
        if cv:
            cv.triggerPageAction(QWebEnginePage.WebAction.ReloadAndBypassCache)

    def open_new_window(self):
        win = MiniumBrowser(headless=self.headless, shared_profile=self.profile)
        WINDOWS.append(win)
        win.show()

    def open_fresh_window(self):
        win = MiniumBrowser(headless=self.headless, shared_profile=None)
        WINDOWS.append(win)
        win.show()

    def reopen_closed_tab(self):
        if self.closed_tabs_history:
            url = self.closed_tabs_history.pop()
            self.add_tab(url)
        else:
            self.fullscreen_banner.show_message("Cannot reopen last closed tab as there is no history.")

    def create_window_controls(self) -> QWidget:
        print("[*] browser: creating window controls...")

        controls = QWidget()
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_min = QPushButton()
        self.btn_max = QPushButton()
        self.btn_close = QPushButton()

        for btn in (self.btn_min, self.btn_max, self.btn_close):
            btn.setFixedSize(38, 32)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        base_btn_qss = """
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
            }
            QPushButton:hover {
                background: #1e202c;
                color: #ffffff;
            }
            QToolTip {
                background-color: #151722;
                background: #151722;
                color: #f1f3f8;
                border: 1px solid #252838;
                border-radius: 6px;
                padding: 2px 3px;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 11.5px;
                font-weight: 500;
            }
        """
        self.btn_min.setStyleSheet(base_btn_qss)
        self.btn_max.setStyleSheet(base_btn_qss)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
            }
            QPushButton:hover {
                background: #e81123;
                color: #ffffff;
            }
        """)

        apply_os_icon(self.btn_min, ["window-minimize", "window-minimize-symbolic"], "—")
        apply_os_icon(self.btn_max, ["window-maximize", "window-maximize-symbolic"], "□")
        apply_os_icon(self.btn_close, ["window-close", "window-close-symbolic"], "✕")

        self.btn_min.clicked.connect(self.showMinimized)

        def toggle_max():
            if self.isMaximized():
                self.showNormal()
                apply_os_icon(self.btn_max, ["window-maximize", "window-maximize-symbolic"], "□")
            else:
                self.showMaximized()
                apply_os_icon(self.btn_max, ["window-restore", "window-restore-symbolic"], "🗗")

        self.btn_max.clicked.connect(toggle_max)
        self.btn_close.clicked.connect(self.close)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
        return controls

    def setup_header(self):
        print("[*] browser: setting up header...")

        self.tab_strip_widget = TitleBarWidget(self)
        self.tab_strip_widget.setFixedHeight(36)
        self.tab_strip_layout = QHBoxLayout(self.tab_strip_widget)
        self.tab_strip_layout.setContentsMargins(4, 3, 0, 0)
        self.tab_strip_layout.setSpacing(4)
        self.tab_strip_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.tab_container = QWidget()
        self.tab_container.setStyleSheet("background: transparent;")
        self.tab_container_layout = QHBoxLayout(self.tab_container)
        self.tab_container_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_container_layout.setSpacing(2)
        self.tab_container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.tab_container_layout.addWidget(self.tab_bar, 0, Qt.AlignmentFlag.AlignLeft)

        self.add_tab_btn = QPushButton()
        self.add_tab_btn.setFixedSize(24, 24)
        self.add_tab_btn.setToolTip("New Tab (Ctrl+T)")
        self.add_tab_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8c8ea0;
                border-radius: 4px;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background: #1a1c27;
                color: #ffffff;
            }
            QToolTip {
                background-color: #151722;
                background: #151722;
                color: #f1f3f8;
                border: 1px solid #252838;
                border-radius: 6px;
                padding: 2px 3px;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 11.5px;
                font-weight: 500;
            }
        """)
        apply_google_icon(self.add_tab_btn, "add", "+", QSize(13, 13))
        self.add_tab_btn.clicked.connect(lambda: self.add_tab())
        self.tab_container_layout.addWidget(self.add_tab_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.tab_scroll = TabScrollArea(self.tab_strip_widget)
        self.tab_scroll.setWidget(self.tab_container)
        self.tab_strip_layout.addWidget(self.tab_scroll, 1)

        self.headless_favicon_label = QLabel()
        self.headless_favicon_label.setFixedSize(24, 16)
        self.headless_favicon_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.headless_favicon_label.setScaledContents(False)
        self.headless_favicon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.headless_favicon_label.setPixmap(load_google_icon("globe").pixmap(16, 16))
        self.tab_strip_layout.addWidget(self.headless_favicon_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.headless_title_label = QLabel("Minium")
        self.headless_title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.headless_title_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 12px;
                font-weight: 500;
                padding-left: 4px;
            }
        """)
        self.tab_strip_layout.addWidget(self.headless_title_label, 0, Qt.AlignmentFlag.AlignLeft)

        if self.headless:
            self.tab_scroll.hide()
            self.headless_favicon_label.show()
            self.headless_title_label.show()
        else:
            self.headless_favicon_label.hide()
            self.headless_title_label.hide()

        self.title_drag_zone = ReservedDragZone(self, self.tab_strip_widget)
        self.tab_strip_layout.addWidget(self.title_drag_zone, 0, Qt.AlignmentFlag.AlignVCenter)
        self.tab_strip_layout.addWidget(self.window_controls, 0)
        self.main_layout.addWidget(self.tab_strip_widget, 0)

        self.navbar_widget = QWidget()
        self.navbar_widget.setFixedHeight(34)
        self.navbar_widget.setCursor(Qt.CursorShape.ArrowCursor)
        self.navbar_widget.setStyleSheet("background-color: #0f1016; border: none;")
        self.navbar_layout = QHBoxLayout(self.navbar_widget)
        self.navbar_layout.setContentsMargins(6, 4, 6, 4)
        self.navbar_layout.setSpacing(6)

        self.nav_btns_widget = QWidget()
        self.nav_btns_layout = QHBoxLayout(self.nav_btns_widget)
        self.nav_btns_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_btns_layout.setSpacing(1)

        self.back_btn = QPushButton()
        self.back_btn.setFixedSize(28, 26)
        self.back_btn.setToolTip("Back (Alt+Left)")
        self.style_nav_btn(self.back_btn)
        apply_google_icon(self.back_btn, "arrow_back", "←", QSize(14, 14))
        self.back_btn.clicked.connect(lambda: self.current_view() and self.current_view().back())
        self.nav_btns_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton()
        self.forward_btn.setFixedSize(28, 26)
        self.forward_btn.setToolTip("Forward (Alt+Right)")
        self.style_nav_btn(self.forward_btn)
        apply_google_icon(self.forward_btn, "arrow_forward", "→", QSize(14, 14))
        self.forward_btn.clicked.connect(lambda: self.current_view() and self.current_view().forward())
        self.nav_btns_layout.addWidget(self.forward_btn)

        self.reload_btn = QPushButton()
        self.reload_btn.setFixedSize(28, 26)
        self.reload_btn.setToolTip("Reload (Ctrl+R / F5)")
        self.style_nav_btn(self.reload_btn)
        apply_google_icon(self.reload_btn, "refresh", "⟳", QSize(14, 14))
        self.reload_btn.clicked.connect(lambda: self.current_view() and self.current_view().reload())
        self.nav_btns_layout.addWidget(self.reload_btn)

        self.navbar_layout.addWidget(self.nav_btns_widget)

        self.url_bar = AddressBar()
        self.url_bar.returnPressed.connect(lambda: self.navigate_to(self.url_bar.text()))
        self.navbar_layout.addWidget(self.url_bar)

        self.nav_drag_zone = TitleBarWidget(self)
        self.nav_drag_zone.setFixedHeight(26)
        self.nav_drag_zone.setFixedWidth(78)
        self.nav_drag_zone.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.nav_drag_zone.setStyleSheet("background: transparent;")
        self.nav_drag_zone.hide()
        self.navbar_layout.addWidget(self.nav_drag_zone, 0)

        self.shield_btn = QPushButton()
        self.shield_btn.setFixedSize(28, 26)
        self.shield_btn.setToolTip("Security Information")
        self.style_nav_btn(self.shield_btn)
        apply_google_icon(self.shield_btn, "sec_good", "🛡", QSize(16, 16))
        self.shield_btn.clicked.connect(self.show_security_popup)
        self.navbar_layout.addWidget(self.shield_btn)

        self.security_popup = SecurityPopup(self)

        self.dl_btn = QPushButton()
        self.dl_btn.setFixedSize(28, 26)
        self.dl_btn.setToolTip("Downloads List")
        self.style_nav_btn(self.dl_btn)
        apply_google_icon(self.dl_btn, "dl", "↓", QSize(15, 15))
        self.dl_btn.clicked.connect(self.show_downloads_popup)
        self.navbar_layout.addWidget(self.dl_btn)

        self.downloads_popup = DownloadsPopup(self)

        self.hamburger_btn = QToolButton()
        apply_google_icon(self.hamburger_btn, "menu", "☰", QSize(15, 15))
        self.hamburger_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.hamburger_btn.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 4px 6px;
                color: #e2e8f0;
            }
            QToolButton::menu-indicator { image: none; }
            QToolButton:hover {
                background-color: #1a1c27;
                border-radius: 4px;
            }
        """)

        self.setup_menu()
        self.navbar_layout.addWidget(self.hamburger_btn)

        if not self.headless:
            self.main_layout.addWidget(self.navbar_widget, 0)
        else:
            self.navbar_widget.hide()

    def style_nav_btn(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-family: 'Google Sans Flex', sans-serif;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1a1c27;
                color: #ffffff;
            }
            QToolTip {
                background-color: #151722;
                background: #151722;
                color: #f1f3f8;
                border: 1px solid #252838;
                border-radius: 6px;
                padding: 2px 3px;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 11.5px;
                font-weight: 500;
            }
        """)

    def setup_menu(self):
        print("[*] browser: setting up hamburger menu...")
        menu = QMenu(self.hamburger_btn)
        menu.setStyleSheet("""
            QMenu {
                background-color: #151722;
                border: 1px solid #252838;
                border-radius: 6px;
                padding: 4px;
                font-family: 'Google Sans Flex', sans-serif;
            }
            QMenu::item {
                padding: 6px 18px 6px 6px;
                border-radius: 4px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QMenu::icon {
                padding-left: 8px;
                margin-right: 6px;
            }
            QMenu::separator {
                height: 1px;
                background-color: #252838;
                margin: 4px 6px;
            }
        """)

        new_tab_act = QAction(load_google_icon("add"), "New Tab", self)
        new_tab_act.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_act.triggered.connect(lambda: self.add_tab())
        menu.addAction(new_tab_act)

        new_win_act = QAction(load_google_icon("ad"), "New Window", self)
        new_win_act.setShortcut(QKeySequence("Ctrl+N"))
        new_win_act.triggered.connect(self.open_new_window)
        menu.addAction(new_win_act)

        fresh_win_act = QAction(load_google_icon("ad"), "New Burnt Window", self)
        fresh_win_act.setShortcut(QKeySequence("Ctrl+Shift+N"))
        fresh_win_act.triggered.connect(self.open_fresh_window)
        menu.addAction(fresh_win_act)

        reopen_tab_act = QAction(load_google_icon("refresh"), "Reopen Closed Tab", self)
        reopen_tab_act.setShortcut(QKeySequence("Ctrl+Shift+T"))
        reopen_tab_act.triggered.connect(self.reopen_closed_tab)
        menu.addAction(reopen_tab_act)

        close_tab_act = QAction(load_google_icon("close"), "Close Tab", self)
        close_tab_act.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_act.triggered.connect(lambda: self.close_tab(self.tab_bar.currentIndex()))
        menu.addAction(close_tab_act)

        self.toggle_tabs_act = QAction(load_google_icon("tabs"), "Toggle Tabs", self)
        self.toggle_tabs_act.setCheckable(True)
        self.toggle_tabs_act.setChecked(True)
        self.toggle_tabs_act.triggered.connect(self.toggle_tabs)
        menu.addAction(self.toggle_tabs_act)

        menu.addSeparator()

        def do_zoom(delta=None, reset=False):
            cv = self.current_view()
            if not cv:
                return

            if reset:
                cv.setZoomFactor(1.0)
            else:
                current = cv.zoomFactor()
                current_pct = round(current * 100)
                new_pct = max(30, min(500, current_pct + round(delta * 100)))
                cv.setZoomFactor(new_pct / 100)

            pct = round(cv.zoomFactor() * 100)
            self.fullscreen_banner.show_message(f"Zoom: {pct}%")

        zoom_in_act = QAction(load_google_icon("zoom_in"), "Zoom In", self)
        zoom_in_act.setShortcuts([QKeySequence("Ctrl++"), QKeySequence("Ctrl+=")])
        zoom_in_act.triggered.connect(lambda: do_zoom(delta=0.1))
        menu.addAction(zoom_in_act)

        zoom_out_act = QAction(load_google_icon("zoom_out"), "Zoom Out", self)
        zoom_out_act.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_act.triggered.connect(lambda: do_zoom(delta=-0.1))
        menu.addAction(zoom_out_act)

        zoom_reset_act = QAction(load_google_icon("restart_alt"), "Reset Zoom", self)
        zoom_reset_act.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_act.triggered.connect(lambda: do_zoom(reset=True))
        menu.addAction(zoom_reset_act)

        menu.addSeparator()

        find_act = QAction(load_google_icon("search"), "Find in Page...", self)
        find_act.setShortcut(QKeySequence("Ctrl+F"))
        find_act.triggered.connect(lambda: self.search_pill.show_search())
        menu.addAction(find_act)

        def toggle_web_theme():
            self.web_theme_dark = not getattr(self, "web_theme_dark", True)

            if hasattr(Qt, "ColorScheme") and hasattr(QGuiApplication.styleHints(), "setColorScheme"):
                scheme = Qt.ColorScheme.Dark if self.web_theme_dark else Qt.ColorScheme.Light
                QGuiApplication.styleHints().setColorScheme(scheme)

            color_str = 'dark' if self.web_theme_dark else 'light'
            js_code = f"""
            (function() {{
                let meta = document.querySelector('meta[name="color-scheme"]');
                if (!meta) {{
                    meta = document.createElement('meta');
                    meta.name = 'color-scheme';
                    document.head.appendChild(meta);
                }}
                meta.content = '{color_str}';
                document.documentElement.style.setProperty('color-scheme', '{color_str}', 'important');
            }})();
            """

            for i in range(self.tab_bar.count()):
                v = self.tab_bar.tabData(i)
                if v and not getattr(v, "_is_unloaded", False):
                    v.page().runJavaScript(js_code)
                    if hasattr(QWebEngineSettings.WebAttribute, "ForceDarkMode"):
                        v.settings().setAttribute(
                            QWebEngineSettings.WebAttribute.ForceDarkMode,
                            self.web_theme_dark
                        )

            theme_name = "Dark" if self.web_theme_dark else "Light"
            self.fullscreen_banner.show_message(f"Web Content Theme: {theme_name}")

        theme_act = QAction(load_google_icon("theme"), "Toggle Web Theme [BETA]", self)
        theme_act.triggered.connect(toggle_web_theme)
        menu.addAction(theme_act)

        source_act = QAction(load_google_icon("code"), "View Page Source", self)
        source_act.triggered.connect(self.view_source)
        menu.addAction(source_act)

        pdf_act = QAction(load_google_icon("print"), "Print to PDF...", self)
        pdf_act.triggered.connect(self.print_to_pdf)
        menu.addAction(pdf_act)

        def translate_current_page():
            cv = self.current_view()
            if cv:
                u = cv.url().toString()
                if u and not u.startswith("minium://") and u != "about:blank":
                    self.add_tab(f"https://translate.google.com/translate?sl=auto&tl=en&u={urllib.parse.quote(u)}")

        translate_act = QAction(load_google_icon("translate"), "Translate Page", self)
        translate_act.triggered.connect(translate_current_page)
        menu.addAction(translate_act)

        menu.addSeparator()

        protect_act = QAction(load_google_icon("security"), "Toggle Protection", self)
        protect_act.setCheckable(True)
        protect_act.setChecked(True)

        def toggle_protect(enabled):
            self.protect_me_enabled = enabled
            self.adblock_interceptor.enabled = enabled
            status = "now protected" if enabled else "no longer protected"
            self.fullscreen_banner.show_message(f"You are {status} from ads, trackers and malicious sites.")

        protect_act.toggled.connect(toggle_protect)
        menu.addAction(protect_act)

        js_act = QAction(load_google_icon("js"), "Toggle JavaScript", self)
        js_act.setCheckable(True)
        js_act.setChecked(True)

        def toggle_js(enabled):
            cv = self.current_view()
            if cv:
                cv.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, enabled)
                cv.reload()
            status = "enabled" if enabled else "disabled"
            self.fullscreen_banner.show_message(f"JavaScript is now {status}.")

        js_act.toggled.connect(toggle_js)
        menu.addAction(js_act)

        burn_act = QAction(load_google_icon("local_fire_department"), "Burn All Data", self)
        burn_act.triggered.connect(self.burn_data)
        menu.addAction(burn_act)

        menu.addSeparator()

        def trigger_ui_update_dry():
            trigger_ui_update(True)

        def trigger_ui_update(dry=False):
            self.fullscreen_banner.show_message("Updating Minium, please wait...", auto_dismiss=False)

            def worker():
                try:
                    success, msg = installer.check_and_apply_update(dry)
                except Exception as e:
                    success, msg = False, f"Update failed: {e}"

                UPDATE_SERVICE.finished.emit(success, msg)

            Thread(target=worker, daemon=True).start()

        update_act = QAction(load_google_icon("check"), "Check For Updates", self)
        update_act.triggered.connect(trigger_ui_update_dry)
        menu.addAction(update_act)

        update_act = QAction(load_google_icon("update"), "Update Minium", self)
        update_act.triggered.connect(trigger_ui_update)
        menu.addAction(update_act)

        about_act = QAction(load_google_icon("info"), "About Minium", self)
        about_act.triggered.connect(lambda: AboutDialog(self).exec())
        menu.addAction(about_act)

        exit_act = QAction(load_google_icon("exit"), "Exit Minium", self)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        exit_act.triggered.connect(self.close)
        menu.addAction(exit_act)

        for act in (new_tab_act, new_win_act, fresh_win_act, reopen_tab_act,
                    close_tab_act, zoom_in_act, zoom_out_act, zoom_reset_act,
                    find_act, exit_act):
            self.addAction(act)

        self.hamburger_btn.setMenu(menu)

    def toggle_tabs(self, visible: bool):
        if visible:
            self.navbar_layout.removeWidget(self.window_controls)
            self.tab_strip_layout.addWidget(self.window_controls, 0)
            self.nav_drag_zone.hide()
            self.tab_strip_widget.setVisible(True)
            self.fullscreen_banner.show_message("Tabs are now visible.")
        else:
            self.tab_strip_widget.setVisible(False)
            self.tab_strip_layout.removeWidget(self.window_controls)
            self.nav_drag_zone.show()
            self.navbar_layout.addWidget(self.window_controls, 0)
            self.fullscreen_banner.show_message("Tabs are now hidden.")

    def current_view(self) -> QWebEngineView:
        widget = self.stack.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def find_tab_for_view(self, view) -> int:
        try:
            for i in range(self.tab_bar.count()):
                if self.tab_bar.tabData(i) is view:
                    return i
        except Exception:
            pass
        return -1

    def on_download_requested(self, download: QWebEngineDownloadRequest):
        print("[*] browser: starting download...")
        name = download.suggestedFileName()
        if not name:
            name = os.path.basename(download.url().path()) or "download"

        download.accept()

        start_time = time.time()
        source_url = download.url().host() or "Unkown Host"
        download_id = str(download.id()) if hasattr(download, 'id') else f"{name}_{time.time()}"

        if not hasattr(self, "_active_downloads"):
            self._active_downloads = {}
        self._active_downloads[download_id] = download
        cancel_cb = lambda d=download: d.cancel()
        self.downloads_popup.add_or_update_download(download_id, name, source_url, 0, "Starting...", cancel_cb)
        self.fullscreen_banner.show_message(f"Downloading {name}...", 0, task_id=download_id)

        def on_received_bytes():
            if getattr(self, "_is_closing", False):
                return
            if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
                return
            try:
                current_name = download.suggestedFileName() or name
                received = download.receivedBytes()
                total = download.totalBytes()
                pct = int((received / total * 100)) if total > 0 else 0

                elapsed = max(0.1, time.time() - start_time)
                speed = received / elapsed
                speed_str = f"{speed / (1024*1024):.1f} MB/s" if speed >= 1024*1024 else f"{speed / 1024:.0f} KB/s"

                if total > 0 and speed > 0:
                    eta_secs = max(0, int((total - received) / speed))
                    eta_str = f"{eta_secs}s left" if eta_secs < 60 else f"{eta_secs // 60}m {eta_secs % 60}s left"
                    eta_full = f"{pct}% · {speed_str} · {eta_str}"
                else:
                    mb_received = received / (1024 * 1024)
                    eta_full = f"{mb_received:.1f} MB · {speed_str}"

                self.downloads_popup.add_or_update_download(download_id, current_name, source_url, pct, eta_full)
                self.fullscreen_banner.show_message(f"Downloading {current_name}...", pct, task_id=download_id)
            except (RuntimeError, AttributeError):
                pass

        def on_state_changed(state):
            if getattr(self, "_is_closing", False):
                return
            try:
                current_name = download.suggestedFileName() or name
                if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                    print("[s] browser: a download has completed sucessfully.")
                    self.downloads_popup.add_or_update_download(download_id, current_name, source_url, 100, "Complete")
                    self.fullscreen_banner.show_message(f"Downloaded {current_name}.", 100, task_id=download_id)
                    self._active_downloads.pop(download_id, None)
                elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
                    print("[!] browser: a download is being cancelled.")
                    self.downloads_popup.add_or_update_download(download_id, current_name, source_url, -1, "Cancelled")
                    pct = int((download.receivedBytes() / max(1, download.totalBytes())) * 100) if download.totalBytes() > 0 else 100
                    self.fullscreen_banner.show_message(
                        f"Cancelled downloading {current_name}.",
                        progress=100,
                        is_error=True,
                        task_id=None
                    )
                    self._active_downloads.pop(download_id, None)
            except (RuntimeError, AttributeError):
                pass

        download.receivedBytesChanged.connect(on_received_bytes)
        download.stateChanged.connect(on_state_changed)

    def on_link_hovered(self, url_str: str):
        if url_str and not self.headless:
            self.url_bar.show_link_preview(url_str)
        elif not self.headless:
            self.url_bar.clear_link_preview()

    def add_tab(self, url=None):
        view = CustomWebEngineView(self.stack, self)
        page = BrowserPage(self.profile, view)
        view.setPage(page)
        view.setStyleSheet("background-color: #0d0e12;")

        index = self.tab_bar.addTab("New Tab")
        self.tab_bar.setTabData(index, view)
        self.stack.addWidget(view)

        app_icon_path = os.path.join(ICON_DIR, "minium.png")
        is_internal = not url or str(url).startswith("minium://")
        if is_internal and os.path.exists(app_icon_path):
            self.tab_bar.setTabIcon(index, QIcon(app_icon_path))
        else:
            self.tab_bar.setTabIcon(index, load_google_icon("globe"))

        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(view)
        self.tab_bar.adjust_size()

        view.titleChanged.connect(lambda title, v=view: self.on_title_changed(v, title))
        view.urlChanged.connect(lambda q, v=view: self.on_url_changed(v, q))
        view.iconChanged.connect(lambda icon, v=view: self.on_icon_changed(v, icon))
        view.loadStarted.connect(lambda v=view: self.on_load_started(v))
        view.loadProgress.connect(lambda p, v=view: self.on_load_progress(v, p))
        view.loadFinished.connect(lambda ok, v=view: self.on_load_finished(v, ok))

        page.loadingChanged.connect(lambda info, v=view: self.on_loading_changed(v, info))
        page.recentlyAudibleChanged.connect(lambda audible, v=view: self.on_audio_changed(v))
        page.linkHovered.connect(self.on_link_hovered)

        page_settings = page.settings()
        page_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        page_settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        page_settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        page_settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        page.fullScreenRequested.connect(lambda req: self.on_fullscreen_requested(req))

        setattr(view, "_audio_btn", None)

        if url:
            self.navigate_to(url, view)
        else:
            self.load_new_tab_page(view)

        return view

    def toggle_view_mute(self, view):
        muted = not view.page().isAudioMuted()
        view.page().setAudioMuted(muted)
        self.on_audio_changed(view)

    def toggle_mute_tab(self, idx):
        view = self.tab_bar.tabData(idx)
        if view:
            self.toggle_view_mute(view)

    def duplicate_tab(self, idx):
        view = self.tab_bar.tabData(idx)
        if view:
            u = view.url().toString()
            self.add_tab(u if u and u != "about:blank" else "minium://newtab")

    def toggle_pin_tab(self, idx):
        view = self.tab_bar.tabData(idx)
        if view:
            view._is_pinned = not getattr(view, "_is_pinned", False)
            if view._is_pinned:
                self.tab_bar.setTabText(idx, "")
                btn = self.tab_bar.tabButton(idx, QTabBar.ButtonPosition.RightSide)
                if btn:
                    btn.hide()
            else:
                self.tab_bar.setTabText(idx, view.title() or "New Tab")
                btn = self.tab_bar.tabButton(idx, QTabBar.ButtonPosition.RightSide)
                if btn:
                    btn.show()
            self.tab_bar.adjust_size()

    def unload_tab(self, idx):
        view = self.tab_bar.tabData(idx)
        if not view or view == self.current_view() or getattr(view, "_is_unloaded", False):
            self.fullscreen_banner.show_message("You cannot unload the currently active tab.")
            return

        pix = view.grab()
        view._snapshot_pixmap = pix
        view._saved_url = view.url()
        view._is_unloaded = True

        placeholder = QLabel(self.stack)
        placeholder.setPixmap(pix)
        placeholder.setScaledContents(True)

        self.stack.removeWidget(view)
        self.stack.addWidget(placeholder)
        setattr(view, "_placeholder", placeholder)

        view.load(QUrl("about:blank"))
        self.fullscreen_banner.show_message(f"Unloaded tab: {view.title()[:24]}, reopen tab to load again.")
        QTimer.singleShot(150, gc.collect)

    def restore_tab(self, view):
        if not getattr(view, "_is_unloaded", False):
            return
        view._is_unloaded = False
        if hasattr(view, "_placeholder"):
            self.stack.removeWidget(view._placeholder)
            view._placeholder.deleteLater()
            delattr(view, "_placeholder")

        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)
        if getattr(view, "_saved_url", None):
            view.load(view._saved_url)

    def close_other_tabs(self, keep_idx):
        keep_view = self.tab_bar.tabData(keep_idx)
        for i in reversed(range(self.tab_bar.count())):
            if self.tab_bar.tabData(i) != keep_view:
                self.close_tab(i)

    def check_idle_tabs(self):
        now = time.time()
        curr = self.current_view()
        for i in range(self.tab_bar.count()):
            try:
                v = self.tab_bar.tabData(i)
                if v and v != curr and not getattr(v, "_is_unloaded", False):
                    if now - getattr(v, "_last_active_time", now) > 600:
                        self.unload_tab(i)
            except (RuntimeError, AttributeError):
                continue

    def on_audio_changed(self, view):
        if not view:
            return
        page = view.page()
        if not page:
            return

        audible = page.recentlyAudible()
        muted = page.isAudioMuted()

        idx = self.find_tab_for_view(view)
        if idx == -1:
            return

        btn = getattr(view, "_audio_btn", None)

        if audible or muted:
            if not btn:
                btn = QPushButton(self.tab_bar)
                btn.setFixedSize(16, 16)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        background: transparent;
                        border-radius: 4px;
                        padding: 0px;
                        margin: 0px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.18);
                    }
                """)
                btn.clicked.connect(lambda _, v=view: self.toggle_view_mute(v))
                setattr(view, "_audio_btn", btn)

            apply_google_icon(btn, "volume_off" if muted else "volume_up", fallback_text="🔇" if muted else "🔊", size=QSize(13, 13))
            self.tab_bar.setTabButton(idx, QTabBar.ButtonPosition.LeftSide, btn)
            btn.show()
        else:
            if btn:
                self.tab_bar.setTabButton(idx, QTabBar.ButtonPosition.LeftSide, None)
                btn.hide()
                btn.deleteLater()
                setattr(view, "_audio_btn", None)

        self.tab_bar.adjust_size()

    def load_new_tab_page(self, view):
        view.load(QUrl("minium://newtab"))
        self.update_tab_tooltip(view)
        view.setFocus()

    def close_tab(self, index):
        count = self.tab_bar.count()
        if count > 1:
            w = self.tab_bar.tabData(index)
            if isinstance(w, QWebEngineView):
                try:
                    url_str = w.url().toString()
                    if url_str and not url_str.startswith("minium://") and url_str != "about:blank":
                        self.closed_tabs_history.append(url_str)
                except Exception:
                    pass

            self.tab_bar.blockSignals(True)
            self.tab_bar.setTabData(index, None)
            self.tab_bar.removeTab(index)
            self.tab_bar.blockSignals(False)

            if w:
                btn = getattr(w, "_audio_btn", None)
                if btn:
                    btn.deleteLater()
                    setattr(w, "_audio_btn", None)

                self.stack.removeWidget(w)
                try:
                    w.disconnect()
                except Exception:
                    pass

                page = w.page()
                if page:
                    try:
                        page.disconnect()
                    except Exception:
                        pass

                w.stop()
                if page:
                    page.deleteLater()
                w.deleteLater()
                QTimer.singleShot(100, gc.collect)

            new_index = self.tab_bar.currentIndex()
            target_view = self.tab_bar.tabData(new_index)
            if target_view:
                self.stack.setCurrentWidget(target_view)
            self.on_tab_changed(new_index)
            self.tab_bar.adjust_size()
        else:
            self.close()

    def on_tab_changed(self, index):
        if hasattr(self, "devtools_pane") and self.devtools_pane.isVisible() and cv:
            self.devtools_pane.attach_to_page(cv.page())
        if hasattr(self, "tab_scroll") and self.tab_scroll:
            rect = self.tab_bar.tabRect(index)
            self.tab_scroll.ensureVisible(rect.center().x(), rect.center().y(), 60, 0)
        target_view = self.tab_bar.tabData(index)
        if target_view:
            if getattr(target_view, "_is_unloaded", False):
                self.restore_tab(target_view)
            target_view._last_active_time = time.time()
            self.stack.setCurrentWidget(target_view)
            if hasattr(target_view, "update_mask"):
                target_view.update_mask()

        cv = self.current_view()
        if cv:
            self.on_url_changed(cv, cv.url())
            self.on_title_changed(cv, cv.title())

            if cv.url().toString().startswith("minium://newtab"):
                cv.setFocus()
                cv.page().runJavaScript("(()=>{ const inp = document.querySelector('input[name=\"q\"]'); if (inp) inp.focus(); })();")

            icon = cv.icon()
            url_str = cv.url().toString()
            if not icon.isNull():
                target_icon = icon
            elif url_str.startswith("minium://"):
                app_icon_path = os.path.join(ICON_DIR, "minium.png")
                target_icon = QIcon(app_icon_path) if os.path.exists(app_icon_path) else load_google_icon("globe")
            else:
                target_icon = load_google_icon("globe")

            self.headless_favicon_label.setPixmap(target_icon.pixmap(16, 16))

    def on_tab_moved(self, from_idx, to_idx):
        target_view = self.tab_bar.tabData(to_idx)
        if target_view:
            self.stack.setCurrentWidget(target_view)

    def on_icon_changed(self, view, icon: QIcon):
        url_str = view.url().toString()
        if not icon.isNull():
            target_icon = icon
        elif url_str.startswith("minium://"):
            app_icon_path = os.path.join(ICON_DIR, "minium.png")
            target_icon = QIcon(app_icon_path) if os.path.exists(app_icon_path) else load_google_icon("globe")
        else:
            target_icon = load_google_icon("globe")

        idx = self.find_tab_for_view(view)
        if idx != -1:
            self.tab_bar.setTabIcon(idx, target_icon)
            self.tab_bar.adjust_size()

        if view == self.current_view():
            self.headless_favicon_label.setPixmap(target_icon.pixmap(16, 16))

    def update_tab_tooltip(self, view):
        try:
            idx = self.find_tab_for_view(view)
            if idx == -1:
                return
            title = view.title() or "New Tab"
            url = view.url().toString()
            pid = view.page().renderProcessPid() if view.page() else 0
            mem = get_pid_memory(pid)

            tip_lines = [title]
            if url and not url.startswith("minium://") and url != "about:blank":
                tip_lines.append(f"URL: {url}")
            if mem:
                tip_lines.append(f"RAM: {mem}")

            self.tab_bar.setTabToolTip(idx, "\n".join(tip_lines))
        except (RuntimeError, AttributeError):
            pass

    def on_title_changed(self, view, title):
        idx = self.find_tab_for_view(view)
        if idx != -1:
            if not getattr(view, "_is_pinned", False):
                short_title = title if len(title) <= 20 else f"{title[:18]}..."
                self.tab_bar.setTabText(idx, short_title or "New Tab")
            else:
                self.tab_bar.setTabText(idx, "")
            self.tab_bar.adjust_size()

        if view == self.current_view():
            display_title = title if title and title != "New Tab" else "Minium"
            self.headless_title_label.setText(display_title)
            if not title or title.strip() == "" or title == "New Tab":
                self.setWindowTitle("Minium")
            else:
                self.setWindowTitle(f"{title} | Minium")

        self.update_tab_tooltip(view)

    def on_url_changed(self, view, q: QUrl):
        if view == self.current_view() and not self.headless:
            u = q.toString()
            if not u or u == "minium://newtab" or u == "about:blank":
                self.url_bar.clear()
                self.url_bar.setPlaceholderText("Search with DuckDuckGo or enter address...")
            else:
                self.url_bar.setText(u)
            self.update_shield_status()
        self.update_tab_tooltip(view)

    def on_load_started(self, view):
        if view == self.current_view() and not self.headless:
            self.url_bar.start_loading()

    def on_load_progress(self, view, progress):
        if view == self.current_view() and not self.headless:
            self.url_bar.set_progress(progress)

    def on_load_finished(self, view, ok):
        if view == self.current_view() and not self.headless:
            self.url_bar.finish_loading(ok)
            self.update_shield_status()
            if view.url().toString().startswith("minium://newtab"):
                view.setFocus()
                view.page().runJavaScript("(()=>{ const inp = document.querySelector('input[name=\"q\"]'); if (inp) inp.focus(); })();")
        self.update_tab_tooltip(view)

    def on_loading_changed(self, view, info: QWebEngineLoadingInfo):
        if info.status() == QWebEngineLoadingInfo.LoadStatus.LoadFailedStatus:
            err_url = info.url().toString()
            err_str = info.errorString()
            err_code = info.errorCode()

            if not err_url or err_url.startswith("minium://") or err_url == "about:blank":
                return

            if err_url in HTTPS_UPGRADE_ATTEMPTS:
                HTTPS_UPGRADE_ATTEMPTS.discard(err_url)
                fallback_url = QUrl(err_url)
                fallback_url.setScheme("http")
                HTTP_FALLBACK_URLS.add(fallback_url.host().lower())
                view.setUrl(fallback_url)
                return

            if err_code > 0:
                return
            if hasattr(QWebEngineLoadingInfo, "ErrorDomain") and info.errorDomain() == QWebEngineLoadingInfo.ErrorDomain.HttpStatusCodeDomain:
                return

            if view.url().toString().startswith("minium://phishing"):
                return

            is_phish = bool(err_url in PHISH_CACHE and PHISH_CACHE[err_url][0])
            if is_phish and err_url not in BYPASSED_PHISH_URLS:
                view.setHtml(get_phishing_html(err_url), QUrl("minium://phishing"))
                self.update_tab_tooltip(view)
                return

            if err_code == -10 or "ERR_ACCESS_DENIED" in err_str:
                print("[!] browser: Minium blocked a page from being loaded.")
                view.setHtml(get_blocked_html(err_url), QUrl("minium://blocked"))
            else:
                error_html = get_error_html(
                    failed_url=err_url,
                    error_msg=err_str or "An unknown error occured.",
                    error_code=f"{err_str} (code: {err_code})"
                )
                view.setHtml(error_html, QUrl("minium://error"))
            self.update_tab_tooltip(view)

    def navigate_to(self, text: str, view=None):
        if view is None:
            view = self.current_view()
        if not view:
            return

        text = text.strip()
        if not text:
            return
        if text == "minium://newtab":
            self.load_new_tab_page(view)
        elif text.startswith("http://") or text.startswith("https://") or text.startswith("about:"):
            view.setUrl(QUrl(text))
        elif "." in text and " " not in text:
            view.setUrl(QUrl(f"https://{text}"))
        else:
            query = QUrl.toPercentEncoding(text).data().decode()
            view.setUrl(QUrl(f"https://duckduckgo.com/?q={query}"))

    def view_source(self):
        cv = self.current_view()
        if cv:
            def render(html):
                try:
                    if not self.isVisible(): return
                except RuntimeError:
                    return

                dlg = QDialog(self)
                dlg.setWindowTitle(f"Source: {cv.title() or cv.url().toString()}")
                dlg.resize(900, 650)
                dlg.setStyleSheet("background-color: #0d0e12;")

                layout = QVBoxLayout(dlg)
                layout.setContentsMargins(12, 12, 12, 12)
                layout.setSpacing(8)

                text_edit = QPlainTextEdit(dlg)
                text_edit.setReadOnly(True)

                mono_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
                mono_font.setPointSize(10.5)
                text_edit.setFont(mono_font)

                text_edit.setStyleSheet("""
                    QPlainTextEdit {
                        background-color: #12131b;
                        color: #e2e8f0;
                        border: 1px solid #232532;
                        border-radius: 8px;
                        padding: 10px;
                        selection-background-color: #2563eb;
                        selection-color: #ffffff;
                    }
                """)

                highlighter = HtmlSyntaxHighlighter(text_edit.document())
                text_edit._highlighter = highlighter

                text_edit.setPlainText(html)
                layout.addWidget(text_edit)
                dlg.exec()

            cv.page().toHtml(render)

    def print_to_pdf(self):
        cv = self.current_view()
        if cv:
            path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "minium-export.pdf", "PDF Files (*.pdf)")
            if path:
                cv.page().printToPdf(path)

    def burn_data(self):
        self.profile.clearHttpCache()
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearAllVisitedLinks()
        self.closed_tabs_history.clear()
        BYPASSED_DOMAINS.clear()
        BYPASSED_PHISH_URLS.clear()
        while self.tab_bar.count() > 1:
            self.close_tab(1)
        cv = self.current_view()
        if cv:
            cv.history().clear()
            self.load_new_tab_page(cv)
        self.fullscreen_banner.show_message("Burnt up all browsing data.")
        QTimer.singleShot(200, gc.collect)

    def closeEvent(self, event):
        print("[*] browser: closing browser...")
        self._is_closing = True

        if hasattr(self, "_active_downloads"):
            for d in list(self._active_downloads.values()):
                try:
                    d.receivedBytesChanged.disconnect()
                    d.stateChanged.disconnect()
                    d.cancel()
                except Exception:
                    pass
            self._active_downloads.clear()

        if hasattr(self, "tab_idle_timer"):
            self.tab_idle_timer.stop()
        if hasattr(self, "_reveal_timer"):
            self._reveal_timer.stop()
        if hasattr(self, "fullscreen_banner"):
            self.fullscreen_banner.close()
        if hasattr(self, "downloads_popup"):
            self.downloads_popup.close()
        if hasattr(self, "security_popup"):
            self.security_popup.close()
        if hasattr(self, "search_pill"):
            self.search_pill.close()

        if self in WINDOWS:
            WINDOWS.remove(self)

        for i in range(self.tab_bar.count()):
            try:
                w = self.tab_bar.tabData(i)
                self.tab_bar.setTabData(i, None)
                if w:
                    try:
                        w.disconnect()
                    except Exception:
                        pass
                    p = w.page()
                    if p:
                        try:
                            p.disconnect()
                        except Exception:
                            pass
                        p.deleteLater()
                    w.deleteLater()
            except Exception:
                pass

        while self.stack.count() > 0:
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

        QTimer.singleShot(50, gc.collect)
        event.accept()
        print("[s] browser: closing finished.")
