from PySide6.QtCore import Qt, QRect, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGraphicsOpacityEffect,
    QPushButton
)

from utils import apply_google_icon

class FullscreenBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.progress_value = -1
        self.is_error = False
        self._current_task_id = None
        self._dismissed_task_id = None

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 0, 10, 0)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.label = QLabel(self)
        self.label.setFixedHeight(22)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.label.setStyleSheet("""
            QLabel {
                color: #f1f3f8;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }
        """)
        self.layout.addWidget(self.label)

        self.btn_close = QPushButton(self)
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Dismiss")
        apply_google_icon(self.btn_close, "close", "✕", QSize(10, 10))
        self.btn_close.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #94a3b8;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
            }
        """)
        self.btn_close.clicked.connect(self.on_close_clicked)
        self.layout.addWidget(self.btn_close)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.finished.connect(self._on_anim_finished)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.fade_out)

    def _on_anim_finished(self):
        if self.opacity_effect.opacity() == 0.0:
            self.hide()

    def on_close_clicked(self):
        if self._current_task_id is not None:
            self._dismissed_task_id = self._current_task_id
        self.fade_out()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QColor("#2d3142"))
        painter.setBrush(QColor("#161822"))
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 18, 18)

        if self.progress_value >= 0:
            pie_rect = QRect(rect.right() - 50, rect.center().y() - 8, 16, 16)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#242633"))
            painter.drawEllipse(pie_rect)

            pie_color = QColor("#ef4444") if self.is_error else QColor("#3b82f6")
            painter.setBrush(pie_color)
            angle = int(-(self.progress_value / 100.0) * 360 * 16)
            painter.drawPie(pie_rect, 90 * 16, angle)

    def show_message(self, message: str, progress: int = -1, is_error: bool = False, task_id: str = None, auto_dismiss: bool = True):
        if task_id is not None and task_id == self._dismissed_task_id:
            return

        self.anim.stop()
        self.hide_timer.stop()

        self._current_task_id = task_id
        if task_id is None:
            self._dismissed_task_id = None

        self.progress_value = progress
        self.is_error = is_error
        self.label.setText(message)

        extra_w = 82 if progress >= 0 else 54
        target_w = self.label.fontMetrics().horizontalAdvance(message) + extra_w
        self.resize(target_w, 38)

        if self.parent():
            parent_w = self.parent().width()
            is_fs = getattr(self.window(), "_fullscreen_mode", False)
            y = 20 if is_fs else 76
            self.move((parent_w - self.width()) // 2, y)

        self.show()
        self.raise_()
        self.opacity_effect.setOpacity(1.0)
        self.update()

        if auto_dismiss and (progress < 0 or progress >= 100 or is_error):
            self.hide_timer.start(3500)

    def fade_out(self):
        self.anim.stop()
        self.anim.setDuration(220)
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()

class LoadingViewport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #050608;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Loading viewport...")
        label.setStyleSheet("""
            QLabel {
                color: #8c8ea0;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 16px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }
        """)
        layout.addWidget(label)
