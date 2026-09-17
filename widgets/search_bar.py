from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout
from PySide6.QtWebEngineCore import QWebEnginePage

from utils import apply_google_icon

class InPageSearchBar(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setFixedHeight(38)
        self.setObjectName("search_pill")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.setStyleSheet("""
            QWidget#search_pill {
                background-color: #151722;
                border: 1px solid #252838;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.search_input = QLineEdit(self)
        self.search_input.setFixedHeight(26)
        self.search_input.setPlaceholderText("Find in page...")

        pal = self.search_input.palette()
        pal.setColor(QPalette.ColorRole.PlaceholderText, QColor("#64748b"))
        self.search_input.setPalette(pal)

        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 1px 10px;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 12px;
                border: 1px solid #232532;
                border-radius: 4px;
                background-color: #14151e;
                color: #e2e8f0;
                min-width: 180px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        self.search_input.textChanged.connect(self.search_text)
        self.search_input.returnPressed.connect(self.find_next)
        layout.addWidget(self.search_input)

        self.btn_prev = QPushButton(self)
        self.btn_prev.setFixedSize(24, 24)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_google_icon(self.btn_prev, "arrow_back", "↑", QSize(13, 13))
        self.btn_prev.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #94a3b8;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1e202c;
                color: #ffffff;
            }
        """)
        self.btn_prev.clicked.connect(self.find_prev)
        layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton(self)
        self.btn_next.setFixedSize(24, 24)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_google_icon(self.btn_next, "arrow_forward", "↓", QSize(13, 13))
        self.btn_next.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #94a3b8;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1e202c;
                color: #ffffff;
            }
        """)
        self.btn_next.clicked.connect(self.find_next)
        layout.addWidget(self.btn_next)

        self.btn_close = QPushButton(self)
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_google_icon(self.btn_close, "close", "✕", QSize(13, 13))
        self.btn_close.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #94a3b8;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #e81123;
                color: #ffffff;
            }
        """)
        self.btn_close.clicked.connect(self.hide_search)
        layout.addWidget(self.btn_close)

        self.hide()

    def show_search(self):
        cv = self.window.current_view()
        if cv:
            self.adjustSize()
            self.move(self.parent().width() - self.width() - 20, 76)
            self.show()
            self.raise_()
            self.search_input.setFocus()
            self.search_input.selectAll()

    def hide_search(self):
        cv = self.window.current_view()
        if cv:
            cv.findText("")
        self.hide()

    def search_text(self, text):
        cv = self.window.current_view()
        if cv:
            cv.findText(text)

    def find_next(self):
        cv = self.window.current_view()
        if cv:
            cv.findText(self.search_input.text())

    def find_prev(self):
        cv = self.window.current_view()
        if cv:
            cv.findText(self.search_input.text(), QWebEnginePage.FindFlag.FindBackward)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide_search()
            event.accept()
        else:
            super().keyPressEvent(event)
