import time

from PySide6.QtCore import Qt, QPoint, QRect, QRectF, QEvent, QObject
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget, QApplication, QFrame, QScrollArea

class TitleBarWidget(QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self._start_pos = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.window.isMaximized() and not self.window.isFullScreen():
                if self.window.windowHandle() and self.window.windowHandle().startSystemMove():
                    event.accept()
                    return
            self._start_pos = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        try:
            if self._start_pos and (event.buttons() & Qt.MouseButton.LeftButton):
                if self.window.isMaximized():
                    ratio = event.position().x() / max(1, self.width())
                    self.window.showNormal()
                    QApplication.processEvents()

                    new_x = int(self.window.width() * ratio)
                    new_y = int(event.position().y())
                    self._start_pos = QPoint(new_x, new_y)

                wh = self.window.windowHandle()
                if wh and wh.startSystemMove():
                    self._start_pos = None
                    event.accept()
                    return

                self.window.move(event.globalPosition().toPoint() - self._start_pos)
                event.accept()
        except RuntimeError:
            pass

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._start_pos = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.window.isMaximized():
                self.window.showNormal()
            else:
                self.window.showMaximized()
            event.accept()

class ResizeGripsManager(QObject):
    def __init__(self, window, container):
        super().__init__(window)
        self.window = window
        self.container = container
        self.edge_size = 6
        self.corner_size = 16
        self.grips = {}

        self._resizing = False
        self._active_name = None
        self._active_edge = None
        self._press_global_pos = QPoint()
        self._start_geometry = QRect()

        edges = {
            "top": (Qt.Edge.TopEdge, Qt.CursorShape.SizeVerCursor),
            "bottom": (Qt.Edge.BottomEdge, Qt.CursorShape.SizeVerCursor),
            "left": (Qt.Edge.LeftEdge, Qt.CursorShape.SizeHorCursor),
            "right": (Qt.Edge.RightEdge, Qt.CursorShape.SizeHorCursor),
            "top_left": (Qt.Edge.TopEdge | Qt.Edge.LeftEdge, Qt.CursorShape.SizeFDiagCursor),
            "top_right": (Qt.Edge.TopEdge | Qt.Edge.RightEdge, Qt.CursorShape.SizeBDiagCursor),
            "bottom_left": (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge, Qt.CursorShape.SizeBDiagCursor),
            "bottom_right": (Qt.Edge.BottomEdge | Qt.Edge.RightEdge, Qt.CursorShape.SizeFDiagCursor),
        }

        for name, (edge, cursor) in edges.items():
            grip = QWidget(self.container)
            grip.setCursor(cursor)
            grip.setStyleSheet("background: transparent;")
            grip.installEventFilter(self)
            self.grips[name] = (grip, edge)

        self.window.installEventFilter(self)
        self.update_geometry()

    def eventFilter(self, obj, event):
        if obj == self.window and event.type() == QEvent.Type.Resize:
            self.update_geometry()
            return False

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            for name, (grip, edge) in self.grips.items():
                if obj == grip:
                    if not self.window.isMaximized() and not self.window.isFullScreen():
                        wh = self.window.windowHandle()
                        if wh and wh.startSystemResize(edge):
                            return True
                        self._resizing = True
                        self._active_name = name
                        self._active_edge = edge
                        self._press_global_pos = event.globalPosition().toPoint()
                        self._start_geometry = self.window.geometry()
                        grip.grabMouse()
                    return True

        if event.type() == QEvent.Type.MouseMove and self._resizing:
            curr_pos = event.globalPosition().toPoint()
            dx = curr_pos.x() - self._press_global_pos.x()
            dy = curr_pos.y() - self._press_global_pos.y()

            min_w = self.window.minimumWidth() or 400
            min_h = self.window.minimumHeight() or 300

            x = self._start_geometry.x()
            y = self._start_geometry.y()
            w = self._start_geometry.width()
            h = self._start_geometry.height()

            if "left" in self._active_name:
                new_w = max(min_w, w - dx)
                x = x + (w - new_w)
                w = new_w
            elif "right" in self._active_name:
                w = max(min_w, w + dx)

            if "top" in self._active_name:
                new_h = max(min_h, h - dy)
                y = y + (h - new_h)
                h = new_h
            elif "bottom" in self._active_name:
                h = max(min_h, h + dy)

            self.window.setGeometry(x, y, w, h)
            return True

        if event.type() == QEvent.Type.MouseButtonRelease and self._resizing:
            self._resizing = False
            self._active_name = None
            self._active_edge = None
            if isinstance(obj, QWidget):
                obj.releaseMouse()
            return True

        return False

    def update_geometry(self):
        if not self.container:
            return

        w = self.container.width()
        h = self.container.height()
        es = self.edge_size
        cs = self.corner_size

        if self.window.isMaximized() or self.window.isFullScreen() or getattr(self.window, "_fullscreen_mode", False):
            for grip, _ in self.grips.values():
                grip.hide()
            return

        self.grips["top"][0].setGeometry(cs, 0, max(0, w - 2 * cs), es)
        self.grips["bottom"][0].setGeometry(cs, h - es, max(0, w - 2 * cs), es)
        self.grips["left"][0].setGeometry(0, cs, es, max(0, h - 2 * cs))
        self.grips["right"][0].setGeometry(w - es, cs, es, max(0, h - 2 * cs))

        self.grips["top_left"][0].setGeometry(0, 0, cs, cs)
        self.grips["top_right"][0].setGeometry(w - cs, 0, cs, cs)
        self.grips["bottom_left"][0].setGeometry(0, h - cs, cs, cs)
        self.grips["bottom_right"][0].setGeometry(w - cs, h - cs, cs, cs)

        for name in ("top", "bottom", "left", "right"):
            self.grips[name][0].show()
            self.grips[name][0].raise_()

        for name in ("top_left", "top_right", "bottom_left", "bottom_right"):
            self.grips[name][0].show()
            self.grips[name][0].raise_()

class WindowBorderOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        win = self.window()
        if win.isMaximized() or win.isFullScreen() or getattr(win, "_fullscreen_mode", False):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor("#232532"), 1.2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.drawRoundedRect(rect, 6.0, 6.0)

class ReservedDragZone(TitleBarWidget):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.setFixedSize(32, 28)
        self.setToolTip("Drag to move window")
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if self.underMouse():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#1a1c27"))
            painter.drawRoundedRect(QRectF(1, 1, self.width() - 2, self.height() - 2), 4, 4)

        dot_color = QColor("#94a3b8") if self.underMouse() else QColor("#474a5f")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)

        cx = self.width() // 2
        cy = self.height() // 2
        for dx in (-3, 3):
            for dy in (-5, 0, 5):
                painter.drawEllipse(cx + dx - 1, cy + dy - 1, 2, 2)


class TabScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFixedHeight(35)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                height: 7px;
                background: transparent;
                margin: 0px;
                border: none;
            }
            QScrollBar:horizontal:hover {
                background: rgba(255, 255, 255, 0.04);
            }
            QScrollBar::handle:horizontal {
                background: #5a627d;
                min-width: 32px;
                margin: 2px 0px;
                border-radius: 1px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #3b82f6;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #60a5fa;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                height: 0px;
                border: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """)

    def wheelEvent(self, event):
        h_bar = self.horizontalScrollBar()

        if h_bar and h_bar.maximum() > 0:
            p_delta = event.pixelDelta().y() or event.pixelDelta().x()
            if p_delta != 0:
                h_bar.setValue(h_bar.value() - p_delta * 2)
            else:
                delta = event.angleDelta().y() or event.angleDelta().x()
                if delta != 0:
                    h_bar.setValue(h_bar.value() - int(delta))
            event.accept()
            return

        win = getattr(self, "window", None) or self.window()
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta != 0 and hasattr(win, "next_tab") and hasattr(win, "prev_tab"):
            now = time.time()
            if now - getattr(self, "_last_scroll_time", 0) > 0.35:
                self._scroll_delta_acc = 0
            self._last_scroll_time = now

            acc = getattr(self, "_scroll_delta_acc", 0)
            if (acc > 0 and delta < 0) or (acc < 0 and delta > 0):
                acc = 0

            acc += delta
            THRESHOLD = 120

            if acc >= THRESHOLD:
                self._scroll_delta_acc = 0
                win.prev_tab()
            elif acc <= -THRESHOLD:
                self._scroll_delta_acc = 0
                win.next_tab()
            else:
                self._scroll_delta_acc = acc

            event.accept()
            return

        super().wheelEvent(event)
