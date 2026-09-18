import os
import re

from PySide6.QtCore import Qt, QSize, QUrl, QTimer
from PySide6.QtGui import (
    QDesktopServices,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QIcon
)
from PySide6.QtWidgets import (
    QMenu,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QWidgetAction,
    QDialog,
    QTextBrowser,
)

from utils import load_google_icon, apply_google_icon
from config import VERSION

class SecurityPopup(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setStyleSheet("""
            QMenu {
                background-color: #151722;
                border: 1px solid #252838;
                border-radius: 8px;
                padding: 14px;
                font-family: 'Google Sans Flex', sans-serif;
            }
        """)

        self.container = QWidget(self)
        self.container.setMinimumWidth(220)
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        self.header = QHBoxLayout()
        self.title_lbl = QLabel("Security Info", self.container)
        self.title_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 13px;")
        self.score_lbl = QLabel("100%", self.container)
        self.score_lbl.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 13px;")
        self.header.addWidget(self.title_lbl)
        self.header.addStretch(1)
        self.header.addWidget(self.score_lbl)
        self.layout.addLayout(self.header)

        line = QWidget(self.container)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #252838;")
        self.layout.addWidget(line)

        self.info_box = QVBoxLayout()
        self.info_box.setSpacing(7)

        self.tls_lbl = QLabel(self.container)
        self.phish_lbl = QLabel(self.container)
        self.ads_lbl = QLabel(self.container)
        self.trackers_lbl = QLabel(self.container)
        self.perms_lbl = QLabel(self.container)

        for lbl in (self.tls_lbl, self.phish_lbl, self.ads_lbl, self.trackers_lbl, self.perms_lbl):
            lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
            self.info_box.addWidget(lbl)

        self.layout.addLayout(self.info_box)

        act = QWidgetAction(self)
        act.setDefaultWidget(self.container)
        self.addAction(act)

    def update_security(self, tls_ok: bool, phish_status: str, ads: int, trackers: int, perms_str: str, score: int):
        if score >= 90:
            score_color = "#22c55e"
        elif score >= 60:
            score_color = "#eab308"
        else:
            score_color = "#ef4444"

        self.score_lbl.setText(f"{score}%")
        self.score_lbl.setStyleSheet(f"color: {score_color}; font-weight: bold; font-size: 13px;")

        self.tls_lbl.setText(f"<b>Protocol:</b> {'Secure' if tls_ok else 'Insecure'}")
        self.tls_lbl.setStyleSheet(f"color: {'#22c55e' if tls_ok else '#ef4444'}; font-size: 12px;")

        self.phish_lbl.setText(f"<b>Phishing:</b> {phish_status}")
        self.phish_lbl.setStyleSheet(f"color: {'#ef4444' if 'Phish' in phish_status else '#94a3b8'}; font-size: 12px;")

        self.ads_lbl.setText(f"<b>Ads Blocked:</b> {ads}")
        self.trackers_lbl.setText(f"<b>Trackers Blocked:</b> {trackers}")
        self.perms_lbl.setText(f"<b>Perms:</b> {perms_str}")

class DownloadsPopup(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        self.setStyleSheet("""
            QMenu {
                background-color: #151722;
                border: 1px solid #252838;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Google Sans Flex', sans-serif;
            }
        """)

        self.container = QWidget(self)
        self.container.setMinimumWidth(280)
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)

        header_layout = QHBoxLayout()
        self.title_lbl = QLabel("Downloads", self.container)
        self.title_lbl.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch(1)

        self.btn_open_folder = QPushButton(self.container)
        self.btn_open_folder.setFixedSize(24, 24)
        self.btn_open_folder.setToolTip("Open Downloads Folder")
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background: #1a1c27;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #252838;
            }
        """)
        apply_google_icon(self.btn_open_folder, "dl_folder", "📁", QSize(14, 14))
        self.btn_open_folder.clicked.connect(self.open_downloads_folder)
        header_layout.addWidget(self.btn_open_folder)
        self.layout.addLayout(header_layout)

        line = QWidget(self.container)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #252838;")
        self.layout.addWidget(line)

        self.scroll = QScrollArea(self.container)
        self.scroll.setWidgetResizable(True)
        self.scroll.setMaximumHeight(260)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.items_container = QWidget()
        self.items_container.setStyleSheet("background: transparent;")
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.items_container)

        self.no_dl_label = QLabel("No downloads at the moment.", self.items_container)
        self.no_dl_label.setStyleSheet("color: #64748b; font-size: 12px; padding: 10px;")
        self.no_dl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.items_layout.addWidget(self.no_dl_label)

        self.layout.addWidget(self.scroll)

        self.download_items = {}

        act = QWidgetAction(self)
        act.setDefaultWidget(self.container)
        self.addAction(act)

    def add_or_update_download(self, download_id: str, name: str, source: str, progress: int, meta_str: str, cancel_callback=None):
        if download_id not in self.download_items:
            self.no_dl_label.hide()
            item = DownloadItemWidget(download_id, name, source, cancel_callback, self.items_container)
            self.download_items[download_id] = item
            self.items_layout.insertWidget(0, item)

        item = self.download_items[download_id]
        if cancel_callback and not item.cancel_callback:
            item.cancel_callback = cancel_callback
            item.btn_cancel.clicked.connect(item.on_cancel_clicked)
            item.btn_cancel.show()
        item.update_progress(progress, meta_str)

    def open_downloads_folder(self):
        self.close()
        def launch():
            downloads_path = os.path.expanduser("~/Downloads")
            if not os.path.exists(downloads_path):
                os.makedirs(downloads_path, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(downloads_path))

        QTimer.singleShot(50, launch)

class DownloadItemWidget(QWidget):
    def __init__(self, download_id: str, name: str, source: str, cancel_callback=None, parent=None):
        super().__init__(parent)
        self.download_id = download_id
        self.cancel_callback = cancel_callback
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

        self.setStyleSheet("""
            DownloadItemWidget {
                background: #1a1c27;
                border: 1px solid #252838;
                border-radius: 6px;
            }
        """)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self.name_lbl = QLabel(name, self)
        self.name_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600;")
        self.name_lbl.setWordWrap(True)
        header.addWidget(self.name_lbl, 1)

        self.btn_cancel = QPushButton(self)
        self.btn_cancel.setFixedSize(18, 18)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setToolTip("Cancel Download")
        apply_google_icon(self.btn_cancel, "close", "✕", QSize(10, 10))
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #94a3b8;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #e81123;
                color: #ffffff;
            }
        """)
        if self.cancel_callback:
            self.btn_cancel.clicked.connect(self.on_cancel_clicked)
        else:
            self.btn_cancel.hide()
        header.addWidget(self.btn_cancel, 0, Qt.AlignmentFlag.AlignTop)
        self.layout.addLayout(header)

        self.source_lbl = QLabel(source[:36] + ("..." if len(source) > 36 else ""), self)
        self.source_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        self.layout.addWidget(self.source_lbl)

        self.pbar = QProgressBar(self)
        self.pbar.setFixedHeight(5)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("""
            QProgressBar {
                background: #242633;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: #3b82f6;
                border-radius: 2px;
            }
        """)
        self.layout.addWidget(self.pbar)

        self.meta_lbl = QLabel("Starting...", self)
        self.meta_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.layout.addWidget(self.meta_lbl)

    def on_cancel_clicked(self):
        self.is_cancelled = True
        self.btn_cancel.hide()
        self.meta_lbl.setText("Cancelled")
        self.meta_lbl.setStyleSheet("color: #ef4444; font-size: 11px;")
        if self.cancel_callback:
            try:
                self.cancel_callback()
            except Exception:
                pass

    def update_progress(self, progress: int, meta_str: str):
        try:
            if progress == -1 or "cancel" in meta_str.lower() or getattr(self, "is_cancelled", False):
                self.is_cancelled = True
                self.btn_cancel.hide()
                self.meta_lbl.setText("Cancelled")
                self.meta_lbl.setStyleSheet("color: #ef4444; font-size: 11px;")
                return

            if progress >= 100:
                self.btn_cancel.hide()
                self.meta_lbl.setStyleSheet("color: #22c55e; font-size: 11px;")

            self.pbar.setValue(max(0, min(100, progress)))
            self.meta_lbl.setText(meta_str)
        except RuntimeError:
            pass

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Minium")
        self.setFixedSize(480, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #0e0f15;
                color: #f1f3f8;
                font-family: 'Google Sans Flex', sans-serif;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        logo_lbl = QLabel()
        logo_icon = load_google_icon("minium")
        if not logo_icon.isNull():
            logo_lbl.setPixmap(logo_icon.pixmap(36, 36))
        header_layout.addWidget(logo_lbl)

        title_lbl = QLabel(f"<h2>Minium v{VERSION}</h2>")
        title_lbl.setStyleSheet("color: #f1f3f8;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        desc_lbl = QLabel(
            "A minimal, privacy-first Chromium based web-browser.<br>"
            "Powered by Python, PySide6, and QtWebEngine.<br>"
            "Everything is ephemeral and destroyed once you leave or Burn."
        )
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        layout.addWidget(desc_lbl)

        credits_browser = QTextBrowser(self)
        credits_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #151722;
                border: 1px solid #252838;
                border-radius: 6px;
                color: #cbd5e1;
                font-size: 11.5px;
                padding: 8px;
            }
        """)
        credits_browser.setHtml("""
            <p><b>Core &amp; Frameworks:</b></p>
            <ul>
                <li><b>&copy; 2026 Minium by Subhrajit Sain.</b> All rights reserved.</li>
                <li><b>Core:</b> Python, PySide6, QtWebEngine (Chromium)</li>
                <li><b>Font:</b> Google Sans Flex</li>
                <li><b>Icons:</b> Google Material Design Icons</li>
                <li><b>Search:</b> DuckDuckGo</li>
            </ul>
            <p><b>Security &amp; Threat Intel:</b></p>
            <ul>
                <li><b>PhishTank</b> by Cisco Talos</li>
                <li><b>HaGeZi Multi Ultimate</b> DNS Blocklist</li>
                <li><b>HaGeZi TIF Medium</b> (Threat Intelligence Feeds)</li>
                <li><b>StevenBlack</b> Unified Hosts</li>
                <li><b>AdGuard</b> DNS Filter</li>
                <li><b>AdAway</b> Official Blocklist</li>
                <li><b>d3ward</b> Toolz Blacklist</li>
                <li><b>Peter Lowe's</b> Adservers (Yoyo)</li>
                <li><b>AnudeepND</b> Adservers Blacklist</li>
            </ul>
        """)
        layout.addWidget(credits_browser)

        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        btn_close = QPushButton("Close", self)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 18px;
                font-weight: 600;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        btn_close.clicked.connect(self.close)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

class HtmlSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#7dd3fc"))
        tag_format.setFontWeight(QFont.Weight.Bold)

        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor("#c084fc"))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#86efac"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#64748b"))
        self.comment_format.setFontItalic(True)

        doctype_format = QTextCharFormat()
        doctype_format.setForeground(QColor("#f472b6"))
        doctype_format.setFontWeight(QFont.Weight.Bold)

        entity_format = QTextCharFormat()
        entity_format.setForeground(QColor("#fbbf24"))

        self.rules = [
            (re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE), doctype_format),
            (re.compile(r"</?[a-zA-Z0-9_-]+"), tag_format),
            (re.compile(r"/?>"), tag_format),
            (re.compile(r'\b[a-zA-Z0-9_-]+(?=\=)'), attr_format),
            (re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format),
            (re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format),
            (re.compile(r"&[a-zA-Z0-9#]+;"), entity_format),
        ]

        self.comment_start = re.compile(r"<!--")
        self.comment_end = re.compile(r"-->")

    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            match = self.comment_start.search(text)
            start_index = match.start() if match else -1
        else:
            start_index = 0

        while start_index >= 0:
            end_match = self.comment_end.search(text, start_index)
            if end_match:
                comment_length = end_match.end() - start_index
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index

            self.setFormat(start_index, comment_length, self.comment_format)
            match = self.comment_start.search(text, start_index + comment_length)
            start_index = match.start() if match else -1

class WarningDialog(QDialog):
    def __init__(self, title, message, action_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        self.setFixedWidth(460)
        self.setStyleSheet("background-color: #0e0f15;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        header = QHBoxLayout()
        icon_label = QLabel(self)
        icon_label.setPixmap(load_google_icon("warning").pixmap(32, 32))
        header.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(12, 0, 0, 0)
        title_layout.setSpacing(6)

        title_label = QLabel(title, self)
        title_label.setFont(QFont("Google Sans Flex", 15, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #f1f3f8;")
        title_layout.addWidget(title_label)

        msg_label = QLabel(message, self)
        msg_label.setFont(QFont("Google Sans Flex", 10))
        msg_label.setStyleSheet("color: #94a3b8; line-height: 1.4;")
        msg_label.setWordWrap(True)
        title_layout.addWidget(msg_label)

        header.addWidget(title_widget)
        layout.addLayout(header)

        self.result = False
        btn_box = QHBoxLayout()
        btn_box.setContentsMargins(0, 0, 0, 0)
        btn_box.addStretch(1)

        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setFont(QFont("Google Sans Flex", 10, QFont.Weight.Medium))
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #94a3b8; border: none; padding: 6px 16px; }
            QPushButton:hover { background: #1a1c27; color: #ffffff; border-radius: 4px; }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        self.btn_action = QPushButton(action_text, self)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.setFont(QFont("Google Sans Flex", 10, QFont.Weight.Bold))
        self.btn_action.setStyleSheet("""
            QPushButton { background: #3b82f6; color: #ffffff; border: none; border-radius: 4px; padding: 6px 18px; }
            QPushButton:hover { background: #2563eb; }
        """)
        self.btn_action.clicked.connect(self.accept)
        btn_box.addWidget(self.btn_action)

        layout.addLayout(btn_box)

    def set_destructive(self):
        self.btn_action.setStyleSheet("""
            QPushButton { background: #ef4444; color: #ffffff; border: none; border-radius: 4px; padding: 6px 18px; }
            QPushButton:hover { background: #dc2626; }
        """)

    def accept(self):
        self.result = True
        super().accept()
