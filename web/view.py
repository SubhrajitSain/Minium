import time
import urllib.parse

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import (
    QWidget,
    QStackedWidget,
    QMenu,
    QPushButton,
    QHBoxLayout,
    QWidgetAction,
)
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from utils import load_google_icon, apply_google_icon

class CustomWebEngineView(QWebEngineView):
    def __init__(self, stack, window):
        super().__init__(stack)
        self.window = window
        self._last_active_time = time.time()
        self._is_unloaded = False
        self._snapshot_pixmap = None
        self._saved_url = None
        self._is_pinned = False

    def contextMenuEvent(self, event):
        req = self.lastContextMenuRequest()
        link_url = str(req.linkUrl().toString()) if (req and req.linkUrl().isValid()) else ""
        media_url = str(req.mediaUrl().toString()) if (req and req.mediaUrl().isValid()) else ""
        selected_text = req.selectedText().strip() if req else ""
        is_editable = req.isContentEditable() if req else False
        curr_url = self.url().toString()

        menu = QMenu(self)
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
        """)

        top_bar = QWidget(menu)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(4, 2, 4, 2)
        top_bar_layout.setSpacing(8)

        btn_back = QPushButton(top_bar)
        btn_back.setFixedSize(28, 24)
        apply_google_icon(btn_back, "arrow_back", "←", QSize(14, 14))
        btn_back.setEnabled(self.history().canGoBack())
        btn_back.clicked.connect(lambda: (menu.close(), self.back()))

        btn_fwd = QPushButton(top_bar)
        btn_fwd.setFixedSize(28, 24)
        apply_google_icon(btn_fwd, "arrow_forward", "→", QSize(14, 14))
        btn_fwd.setEnabled(self.history().canGoForward())
        btn_fwd.clicked.connect(lambda: (menu.close(), self.forward()))

        btn_reload = QPushButton(top_bar)
        btn_reload.setFixedSize(28, 24)
        apply_google_icon(btn_reload, "refresh", "⟳", QSize(14, 14))
        btn_reload.clicked.connect(lambda: (menu.close(), self.reload()))

        for b in (btn_back, btn_fwd, btn_reload):
            b.setStyleSheet("QPushButton { border: none; background: #1a1c27; border-radius: 4px; } QPushButton:hover { background: #252838; }")
            top_bar_layout.addWidget(b)

        top_act = QWidgetAction(menu)
        top_act.setDefaultWidget(top_bar)
        menu.addAction(top_act)
        menu.addSeparator()

        if link_url:
            open_link = QAction(load_google_icon("in_new"), "Open Link in New Tab", self)
            open_link.triggered.connect(lambda: self.window.add_tab(link_url))
            menu.addAction(open_link)

            copy_link = QAction(load_google_icon("copy"), "Copy Link Address", self)
            copy_link.triggered.connect(lambda: QGuiApplication.clipboard().setText(link_url))
            menu.addAction(copy_link)
            menu.addSeparator()

        if media_url:
            open_img = QAction(load_google_icon("in_new"), "Open Image in New Tab", self)
            open_img.triggered.connect(lambda: self.window.add_tab(media_url))
            menu.addAction(open_img)

            copy_img_link = QAction(load_google_icon("copy"), "Copy Image Address", self)
            copy_img_link.triggered.connect(lambda: QGuiApplication.clipboard().setText(media_url))
            menu.addAction(copy_img_link)
            menu.addSeparator()

        if selected_text:
            preview = (selected_text[:20] + "...") if len(selected_text) > 20 else selected_text
            trans_sel_act = QAction(load_google_icon("translate"), f'Translate "{preview}"', self)
            enc_text = urllib.parse.quote(selected_text)
            trans_sel_act.triggered.connect(lambda: self.window.add_tab(
                f"https://translate.google.com/?sl=auto&tl=en&text={enc_text}&op=translate"
            ))
            menu.addAction(trans_sel_act)

        if is_editable:
            undo_act = QAction(load_google_icon("undo"), "Undo", self)
            undo_act.setEnabled(self.page().action(QWebEnginePage.WebAction.Undo).isEnabled())
            undo_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Undo))
            menu.addAction(undo_act)

            redo_act = QAction(load_google_icon("redo"), "Redo", self)
            redo_act.setEnabled(self.page().action(QWebEnginePage.WebAction.Redo).isEnabled())
            redo_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Redo))
            menu.addAction(redo_act)
            menu.addSeparator()

            cut_act = QAction(load_google_icon("cut"), "Cut", self)
            cut_act.setEnabled(bool(selected_text))
            cut_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Cut))
            menu.addAction(cut_act)

            copy_act = QAction(load_google_icon("copy"), "Copy", self)
            copy_act.setEnabled(bool(selected_text))
            copy_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Copy))
            menu.addAction(copy_act)

            paste_act = QAction(load_google_icon("paste"), "Paste", self)
            paste_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Paste))
            menu.addAction(paste_act)

            delete_act = QAction(load_google_icon("delete"), "Delete", self)
            delete_act.setEnabled(bool(selected_text))
            delete_act.triggered.connect(lambda: self.page().runJavaScript("document.execCommand('delete');"))
            menu.addAction(delete_act)
        elif selected_text:
            copy_act = QAction(load_google_icon("copy"), "Copy", self)
            copy_act.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.Copy))
            menu.addAction(copy_act)

        select_all = QAction(load_google_icon("select_all"), "Select All", self)
        select_all.triggered.connect(lambda: self.triggerPageAction(QWebEnginePage.WebAction.SelectAll))
        menu.addAction(select_all)
        menu.addSeparator()

        if curr_url and not curr_url.startswith("minium://") and curr_url != "about:blank":
            trans_page_act = QAction(load_google_icon("translate"), "Translate Page", self)
            enc_url = urllib.parse.quote(curr_url)
            trans_page_act.triggered.connect(lambda: self.window.add_tab(
                f"https://translate.google.com/translate?sl=auto&tl=en&u={enc_url}"
            ))
            menu.addAction(trans_page_act)

        save_page = QAction(load_google_icon("save_as"), "Save Page As PDF...", self)
        save_page.triggered.connect(self.window.print_to_pdf)
        menu.addAction(save_page)

        def trigger_pip():
            js_code = r"""
            (function() {
                let videos = Array.from(document.querySelectorAll('video'));
                let v = videos.find(vid => !vid.paused && vid.currentTime > 0) ||
                        document.querySelector('video:hover') ||
                        videos[0];

                if (!v) return null;

                if (window.location.hostname.includes('youtube.com')) {
                    let id = new URLSearchParams(window.location.search).get('v');
                    if (!id) {
                        let m = window.location.pathname.match(/\/shorts\/([a-zA-Z0-9_-]+)/);
                        if (m) id = m[1];
                    }
                    if (id) {
                        let t = Math.floor(v.currentTime || 0);
                        return {
                            type: 'url',
                            src: 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&start=' + t
                        };
                    }
                }

                let src = v.currentSrc || v.src;
                if (src && !src.startsWith('blob:') && !src.startsWith('mediasource:')) {
                    return { type: 'url', src: src };
                }

                return {
                    type: 'html',
                    src: `<!DOCTYPE html><html><head><style>
                        * { margin:0; padding:0; overflow:hidden; background:#000; }
                        video { width:100vw; height:100vh; object-fit:contain; }
                    </style></head><body>
                    <video src="${v.currentSrc || v.src}" controls autoplay></video>
                    </body></html>`
                };
            })();
            """
            def on_media(res):
                main_win = getattr(self, "window", None)
                if res and main_win:
                    if not hasattr(main_win, "pip_window") or not main_win.pip_window:
                        from widgets.pip import FloatingPiPWindow
                        main_win.pip_window = FloatingPiPWindow()

                    if res.get('type') == 'html':
                        main_win.pip_window.load_content(res.get('src'), is_html=True)
                    else:
                        main_win.pip_window.load_content(res.get('src'), is_html=False)
                else:
                    if main_win and hasattr(main_win, "fullscreen_banner"):
                        main_win.fullscreen_banner.show_message("PiP is currently unavailable.", is_error=True)

            self.page().runJavaScript(js_code, on_media)

        pip_act = QAction(load_google_icon("in_new"), "Picture-in-Picture [BETA]", self)
        pip_act.triggered.connect(trigger_pip)
        menu.addAction(pip_act)

        view_source = QAction(load_google_icon("code"), "View Page Source", self)
        view_source.triggered.connect(self.window.view_source)
        menu.addAction(view_source)

        def inspect_element():
            main_win = getattr(self, "window", None)
            if main_win and hasattr(main_win, "devtools_pane"):
                if not main_win.devtools_pane.isVisible():
                    main_win.devtools_pane.attach_to_page(self.page())
                    total_w = main_win.width()
                    main_win.splitter.setSizes([int(total_w * 0.62), int(total_w * 0.38)])

            self.triggerPageAction(QWebEnginePage.WebAction.InspectElement)

        inspect_act = QAction(load_google_icon("inspect"), "Inspect Element", self)
        inspect_act.triggered.connect(inspect_element)
        menu.addAction(inspect_act)

        menu.exec(event.globalPos())

class WebEngineStack(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background-color: #050608;")
