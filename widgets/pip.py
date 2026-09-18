from PySide6.QtCore import Qt, QPoint, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView

class FloatingPiPWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.resize(480, 270)
        self.setMinimumSize(240, 135)
        self.setStyleSheet("background-color: #000000; border: none;")
        self.setMouseTracking(True)
        self._drag_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view = QWebEngineView(self)
        self.view.setStyleSheet("background: #000000; border: none;")
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.view)

        self.btn_close = QPushButton("✕", self)
        self.btn_close.setFixedSize(26, 26)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: rgba(0, 0, 0, 0.65);
                color: #ffffff;
                border-radius: 13px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e81123;
            }
        """)
        self.btn_close.clicked.connect(self.close)
        self.btn_close.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.btn_close.move(self.width() - self.btn_close.width() - 8, 8)
        self.btn_close.raise_()

    def enterEvent(self, event):
        self.btn_close.show()
        self.btn_close.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_close.hide()
        super().leaveEvent(event)

    def load_content(self, url_str, is_html=False):
        if is_html:
            self.view.setHtml(url_str)
        else:
            self.view.setUrl(QUrl(url_str))
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
from PySide6.QtCore import Qt, QPoint, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView

class FloatingPiPWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.resize(480, 270)
        self.setMinimumSize(240, 135)
        self.setStyleSheet("background-color: #000000; border: none;")
        self.setMouseTracking(True)
        self._drag_pos = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view = QWebEngineView(self)
        self.view.setStyleSheet("background: #000000; border: none;")
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.view)

        self.btn_close = QPushButton("✕", self)
        self.btn_close.setFixedSize(26, 26)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: rgba(0, 0, 0, 0.65);
                color: #ffffff;
                border-radius: 13px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e81123;
            }
        """)
        self.btn_close.clicked.connect(self.close)
        self.btn_close.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.btn_close.move(self.width() - self.btn_close.width() - 8, 8)
        self.btn_close.raise_()

    def enterEvent(self, event):
        self.btn_close.show()
        self.btn_close.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_close.hide()
        super().leaveEvent(event)

    def load_content(self, url_str, is_html=False):
        if is_html:
            self.view.setHtml(url_str)
        else:
            self.view.setUrl(QUrl(url_str))
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
