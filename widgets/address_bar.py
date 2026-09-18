from PySide6.QtCore import Qt, QSize, QRect, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPalette, QAction
from PySide6.QtWidgets import QLineEdit

from utils import load_google_icon

class AddressBar(QLineEdit):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self._progress = 0
        self._loading = False
        self._is_previewing = False
        self._original_text = ""
        self.setFixedHeight(26)

        self.setPlaceholderText("Search with DuckDuckGo or enter address...")
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.PlaceholderText, QColor("#64748b"))
        self.setPalette(pal)

        self.setStyleSheet("""
            QLineEdit {
                padding: 1px 10px;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 12px;
                border: 1px solid #232532;
                border-radius: 4px;
                background-color: #14151e;
                color: #e2e8f0;
            }
            QLineEdit:focus { border: 1px solid #3b82f6; }
        """)

        # Link Preview Icon
        self._preview_action = None
        preview_icon = self._get_preview_icon()
        if not preview_icon.isNull():
            self._preview_action = self.addAction(preview_icon, QLineEdit.ActionPosition.LeadingPosition)
            self._preview_action.setVisible(False)

        # Bookmark Star Icon
        self.btn_bookmark = QAction(self._get_star_icon(False), "Bookmark this page", self)
        self.btn_bookmark.triggered.connect(self._toggle_bookmark)
        self.addAction(self.btn_bookmark, QLineEdit.ActionPosition.TrailingPosition)

        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.timeout.connect(self._reset_progress)

    def _get_preview_icon(self) -> QIcon:
        base_icon = load_google_icon("link")
        if base_icon.isNull():
            return QIcon()
        pixmap = base_icon.pixmap(QSize(13, 13))
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.GlobalColor.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QColor("#3b82f6"))
        painter.end()
        return QIcon(tinted)

    def _get_star_icon(self, filled: bool) -> QIcon:
        icon_name = "bm_y" if filled else "bm_n"
        base_icon = load_google_icon(icon_name)

        if base_icon.isNull():
            pix = QPixmap(18, 18)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setFont(QFont("Google Sans Flex", 14))
            if filled:
                painter.setPen(QColor("#f59e0b"))
                painter.drawText(QRect(0, 0, 18, 18), Qt.AlignmentFlag.AlignCenter, "★")
            else:
                painter.setPen(QColor("#64748b"))
                painter.drawText(QRect(0, 0, 18, 18), Qt.AlignmentFlag.AlignCenter, "☆")
            painter.end()
            return QIcon(pix)

        pixmap = base_icon.pixmap(QSize(15, 15))
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.GlobalColor.transparent)

        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        color = QColor("#f59e0b") if filled else QColor("#64748b")
        painter.fillRect(tinted.rect(), color)
        painter.end()
        return QIcon(tinted)

    def set_bookmark_state(self, is_bookmarked: bool):
        self.btn_bookmark.setIcon(self._get_star_icon(is_bookmarked))

    def _toggle_bookmark(self):
        if hasattr(self.window, "toggle_bookmark_current"):
            self.window.toggle_bookmark_current()

    def show_link_preview(self, url_str: str):
        if not self._is_previewing:
            self._original_text = self.text()
            self._is_previewing = True

        if self._preview_action:
            self._preview_action.setVisible(True)
            self.setText(url_str)
            self.setStyleSheet("""
                QLineEdit {
                    padding: 1px 2px 1px 2px;
                    font-family: 'Google Sans Flex', sans-serif;
                    font-size: 12px;
                    border: 1px solid #3b82f6;
                    border-radius: 4px;
                    background-color: #14151e;
                    color: #3b82f6;
                }
            """)
        else:
            self.setText(f"» {url_str}")
            self.setStyleSheet("""
                QLineEdit {
                    padding: 1px 2px;
                    font-family: 'Google Sans Flex', sans-serif;
                    font-size: 12px;
                    border: 1px solid #3b82f6;
                    border-radius: 4px;
                    background-color: #14151e;
                    color: #3b82f6;
                }
            """)

        self.setCursorPosition(0)
        self.deselect()

    def clear_link_preview(self):
        if self._is_previewing:
            self._is_previewing = False
            if self._preview_action:
                self._preview_action.setVisible(False)
            self.setText(self._original_text)
            self.setStyleSheet("""
                QLineEdit {
                    padding: 1px 10px;
                    font-family: 'Google Sans Flex', sans-serif;
                    font-size: 12px;
                    border: 1px solid #232532;
                    border-radius: 4px;
                    background-color: #14151e;
                    color: #e2e8f0;
                }
                QLineEdit:focus {
                    border: 1px solid #3b82f6;
                }
            """)
            self.setCursorPosition(0)
            self.deselect()

    def set_progress(self, progress: int):
        self._progress = progress
        self._loading = 0 < progress < 100
        self.update()

    def start_loading(self):
        self._progress = 15
        self._loading = True
        self.update()

    def finish_loading(self, ok: bool = True):
        self._progress = 100
        self.update()
        self._reset_timer.start(250)

    def _reset_progress(self):
        self._loading = False
        self._progress = 0
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._loading and self._progress > 0:
            painter = QPainter(self)
            bar_height = 2
            progress_width = int(self.width() * (self._progress / 100.0))
            painter.fillRect(0, 0, progress_width, self.height() - bar_height, QColor(59, 130, 246, 30))
            bar_rect = QRect(0, self.height() - bar_height, progress_width, bar_height)
            painter.fillRect(bar_rect, QColor("#3b82f6"))
