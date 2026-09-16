from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript

from utils import apply_google_icon

class DevToolsPane(QWidget):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self.setStyleSheet("""
            QWidget#devtools_pane {
                background-color: #0b0c12;
                border-left: 1px solid #1f2230;
            }
        """)
        self.setObjectName("devtools_pane")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top Header
        header = QWidget(self)
        header.setFixedHeight(28)
        header.setStyleSheet("background-color: #12131b; border-bottom: 1px solid #1f2230;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(10, 0, 6, 0)
        h_layout.setSpacing(6)

        title = QLabel("Minium Dev Tools", header)
        title.setStyleSheet("color: #94a3b8; font-size: 11.5px; font-weight: 600;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)

        # btn_close = QPushButton(header)
        # btn_close.setFixedSize(20, 20)
        # btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        # apply_google_icon(btn_close, "close", "✕", QSize(11, 11))
        # btn_close.setStyleSheet("""
        #     QPushButton { border: none; background: transparent; color: #94a3b8; border-radius: 3px; }
        #     QPushButton:hover { background: #e81123; color: #ffffff; }
        # """)
        # btn_close.clicked.connect(self.close_pane)
        # h_layout.addWidget(btn_close)

        layout.addWidget(header)

        self.view = QWebEngineView(self)
        self.view.setStyleSheet("background-color: #0b0c12;")

        dev_page = QWebEnginePage(profile, self.view)

        # Chromium DevTools loads its JS modules asynchronously AFTER loadFinished fires.
        # We poll until DevTools' internal Common.Settings module is initialized, then force the theme update.

        def force_devtools_dark(ok=True):
            if not ok:
                return

            script = r'''
                (() => {
                    let attempts = 0;
                    const maxAttempts = 100;

                    function applyDarkTheme() {
                        attempts++;
                        let appliedViaApi = false;

                        try {
                            // 1. DevTools Internal API: Fixes desync by triggering a UI update.
                            if (window.Common && Common.Settings && Common.Settings.Settings && Common.Settings.Settings.instance) {
                                const settings = Common.Settings.Settings.instance();
                                let theme = null;
                                try { theme = settings.moduleSetting("uiTheme"); } catch(e) {}
                                if (!theme) {
                                    try { theme = settings.createSetting("uiTheme", "dark"); } catch(e) {}
                                }

                                if (theme) {
                                    // Toggling forces DevTools ThemeSupport to catch up and apply dark stylesheets
                                    if (theme.get() === "dark") {
                                        theme.set("light");
                                    }
                                    theme.set("dark");
                                    appliedViaApi = true;
                                }
                            }
                        } catch (e) {
                            console.warn("Could not set DevTools theme via API:", e);
                        }

                        // 2. Local storage sync
                        try {
                            window.localStorage.setItem('uiTheme', '"dark"');
                            let prefsRaw = window.localStorage.getItem('preferences');
                            let prefs = prefsRaw ? JSON.parse(prefsRaw) : {};
                            if (prefs.uiTheme !== '"dark"') {
                                prefs.uiTheme = '"dark"';
                                window.localStorage.setItem('preferences', JSON.stringify(prefs));
                            }
                        } catch (e) {}

                        // 3. Fallback direct DOM manipulation
                        try {
                            document.documentElement.classList.remove('-theme-with-light-background', 'theme-default');
                            document.documentElement.classList.add('-theme-with-dark-background', 'theme-dark');
                            if (document.body) {
                                document.body.classList.remove('-theme-with-light-background', 'theme-default');
                                document.body.classList.add('-theme-with-dark-background', 'theme-dark');
                            }
                        } catch (e) {}

                        // If API was not ready yet, retry every 50ms up to 5 seconds
                        if (!appliedViaApi && attempts < maxAttempts) {
                            setTimeout(applyDarkTheme, 50);
                        }
                    }

                    applyDarkTheme();
                })();
            '''

            dev_page.runJavaScript(script)

        self._force_devtools_dark = force_devtools_dark
        dev_page.loadFinished.connect(force_devtools_dark)

        self.view.setPage(dev_page)
        layout.addWidget(self.view)

        # Wire up the INTERNAL 'X' button inside the DevTools HTML UI
        dev_page.windowCloseRequested.connect(self.close_pane)

        self._current_page = None

    def attach_to_page(self, page):
        if not page:
            return
        self._current_page = page
        page.setDevToolsPage(self.view.page())
        self.show()
        if hasattr(self, '_force_devtools_dark'):
            self._force_devtools_dark(True)

    def close_pane(self):
        if self._current_page:
            try:
                self._current_page.setDevToolsPage(None)
            except Exception:
                pass
            self._current_page = None
        self.hide()
