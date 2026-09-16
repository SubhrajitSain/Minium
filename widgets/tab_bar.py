import time

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QAction, QPixmap, QPainter, QMouseEvent, QFont, QFontMetrics
from PySide6.QtWidgets import QTabBar, QWidget, QMenu, QSizePolicy, QApplication, QScrollArea

from utils import load_google_icon, get_google_icon_path

class BrowserTabBar(QTabBar):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setTabsClosable(True)
        self.setMovable(False)
        self.setIconSize(QSize(16, 16))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        tab_font = QFont("Google Sans Flex")
        tab_font.setPixelSize(12)
        self.setFont(tab_font)

        self._drag_index = -1
        self._drag_start_pos = None
        self._drag_offset_x = 0
        self._overlay = MovingTabOverlay(self)
        self._overlay.hide()

        close_path = get_google_icon_path("close")

        self.setStyleSheet(f"""
            QToolTip {{
                background-color: #151722;
                color: #f1f3f8;
                border: 1px solid #252838;
                border-radius: 6px;
                padding: 2px 3px;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 11.5px;
                font-weight: 500;
            }}
            QTabBar {{
                background-color: transparent;
                border: none;
                qproperty-drawBase: 0;
            }}
            QTabBar::tab {{
                background-color: #12131b;
                color: #8c8ea0;
                font-family: 'Google Sans Flex', sans-serif;
                font-size: 12px;
                padding: 3px 4px 3px 6px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                text-align: left;
            }}
            QTabBar::tab:selected {{
                background-color: #191b26;
                color: #ffffff;
                border-bottom: 2px solid #3b82f6;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #161722;
                color: #cbd5e1;
            }}
            QTabBar::close-button {{
                image: url("{close_path}");
                subcontrol-position: right;
                subcontrol-origin: padding;
                width: 16px;
                height: 16px;
                margin: 3px 3px 3px 0px;
                padding: 0px;
                border-radius: 4px;
            }}
            QTabBar::close-button:hover {{
                background-color: rgba(255, 255, 255, 0.18);
            }}
        """)

    def contextMenuEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx == -1:
            return
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
        view = self.tabData(idx)
        is_muted = view.page().isAudioMuted() if (view and hasattr(view, 'page')) else False
        mute_act = QAction(load_google_icon("volume_off" if is_muted else "volume_up"), "Unmute Tab" if is_muted else "Mute Tab", self)
        mute_act.triggered.connect(lambda: self.window.toggle_mute_tab(idx))
        menu.addAction(mute_act)

        clone_act = QAction(load_google_icon("duplicate"), "Duplicate Tab", self)
        clone_act.triggered.connect(lambda: self.window.duplicate_tab(idx))
        menu.addAction(clone_act)

        is_pinned = getattr(view, "_is_pinned", False)
        pin_act = QAction(load_google_icon("unpin" if is_pinned else "pin"), "Unpin Tab" if is_pinned else "Pin Tab", self)
        pin_act.triggered.connect(lambda: self.window.toggle_pin_tab(idx))
        menu.addAction(pin_act)

        unload_act = QAction(load_google_icon("unload"), "Unload Tab", self)
        unload_act.triggered.connect(lambda: self.window.unload_tab(idx))
        menu.addAction(unload_act)

        menu.addSeparator()

        close_others = QAction(load_google_icon("close_tabs"), "Close Other Tabs", self)
        close_others.triggered.connect(lambda: self.window.close_other_tabs(idx))
        menu.addAction(close_others)

        close_act = QAction(load_google_icon("close"), "Close This Tab", self)
        close_act.triggered.connect(lambda: self.tabCloseRequested.emit(idx))
        menu.addAction(close_act)

        menu.exec(event.globalPos())

    def wheelEvent(self, event):
        scroll_area = getattr(self.window, "tab_scroll", None)
        if not scroll_area:
            p = self.parentWidget()
            while p:
                if isinstance(p, QScrollArea):
                    scroll_area = p
                    break
                p = p.parentWidget()

        h_bar = scroll_area.horizontalScrollBar() if scroll_area else None

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

        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta != 0 and hasattr(self.window, "next_tab") and hasattr(self.window, "prev_tab"):
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
                self.window.prev_tab()
            elif acc <= -THRESHOLD:
                self._scroll_delta_acc = 0
                self.window.next_tab()
            else:
                self._scroll_delta_acc = acc

            event.accept()
            return

        super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self.tabAt(event.position().toPoint())
            if idx != -1:
                btn = self.tabButton(idx, QTabBar.ButtonPosition.RightSide)
                if btn and btn.geometry().contains(event.position().toPoint()):
                    super().mousePressEvent(event)
                    return
                self._drag_index = idx
                self._drag_start_pos = event.position().toPoint()
                self._drag_offset_x = event.position().x() - self.tabRect(idx).x()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_index != -1 and (event.buttons() & Qt.MouseButton.LeftButton):
            curr_pos = event.position().toPoint()
            if not self._overlay.isVisible():
                if (curr_pos - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                    rect = self.tabRect(self._drag_index)
                    pix = self.grab(rect)
                    self._overlay.set_pixmap(pix)
                    self._overlay.move(int(curr_pos.x() - self._drag_offset_x), rect.y())
                    self._overlay.show()
                    self._overlay.raise_()
            else:
                rect = self.tabRect(self._drag_index)
                new_x = int(curr_pos.x() - self._drag_offset_x)
                new_x = max(0, min(new_x, self.width() - self._overlay.width()))
                self._overlay.move(new_x, rect.y())

                target_idx = self.tabAt(curr_pos)
                if target_idx != -1 and target_idx != self._drag_index:
                    target_rect = self.tabRect(target_idx)
                    if (target_idx > self._drag_index and curr_pos.x() > target_rect.center().x()) or \
                       (target_idx < self._drag_index and curr_pos.x() < target_rect.center().x()):
                        old_idx = self._drag_index
                        self._drag_index = target_idx
                        self.moveTab(old_idx, target_idx)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._overlay.isVisible():
            self._overlay.hide()
        self._drag_index = -1
        self._drag_start_pos = None

        if event.button() == Qt.MouseButton.MiddleButton:
            tab_idx = self.tabAt(event.position().toPoint())
            if tab_idx != -1:
                self.tabCloseRequested.emit(tab_idx)
                return
        super().mouseReleaseEvent(event)

    def tabSizeHint(self, index: int) -> QSize:
        view = self.tabData(index)
        is_pinned = getattr(view, "_is_pinned", False) if view else False

        has_audio = False
        if view:
            btn = getattr(view, "_audio_btn", None)
            if btn and btn.isVisible():
                has_audio = True

        audio_extra = 22 if has_audio else 0

        if is_pinned:
            return QSize(56 if has_audio else 36, 28)

        text = self.tabText(index)

        font = QFont("Google Sans Flex")
        font.setPixelSize(12)
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(text) if hasattr(fm, "horizontalAdvance") else fm.width(text)

        has_icon = not self.tabIcon(index).isNull()
        chrome_w = 58 if has_icon else 36

        w = max(64, min(220, text_w + chrome_w + audio_extra))
        return QSize(w, 28)

    def sizeHint(self) -> QSize:
        if self.count() == 0:
            return QSize(0, 28)
        total_w = sum(self.tabSizeHint(i).width() for i in range(self.count())) + (self.count() * 2)
        return QSize(total_w, 28)

    def adjust_size(self):
        w = self.sizeHint().width()
        self.setFixedWidth(w)
        self.updateGeometry()
        if self.parentWidget():
            self.parentWidget().adjustSize()

    def tabInserted(self, index: int):
        super().tabInserted(index)
        self.adjust_size()

    def tabRemoved(self, index: int):
        super().tabRemoved(index)
        self.adjust_size()

class MovingTabOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._pixmap = QPixmap()

    def set_pixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.setFixedSize(pixmap.size())
        self.update()

    def paintEvent(self, event):
        if not self._pixmap.isNull():
            painter = QPainter(self)
            painter.setOpacity(0.85)
            painter.drawPixmap(0, 0, self._pixmap)
