import os
from PySide6.QtCore import Qt, QSize, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QLineEdit,
    QFileDialog, QColorDialog, QWidget, QFrame
)
from utils import get_cached_favicon_b64, apply_google_icon

class ShortcutDialog(QDialog):
    def __init__(self, title="Add Shortcut", name="", url="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(380, 210)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0c12;
                color: #f1f3f8;
                font-family: 'Google Sans Flex', sans-serif;
            }
            QLabel {
                color: #94a3b8;
                font-size: 12px;
                border: none;
                background: transparent;
            }
            QLineEdit {
                background-color: #141622;
                color: #f1f3f8;
                border: 1px solid #252838;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton {
                background-color: #1e202c;
                color: #f1f3f8;
                border: 1px solid #282a3a;
                padding: 7px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2a2d3e;
                border-color: #3b82f6;
            }
            QPushButton#primary {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                font-weight: 600;
            }
            QPushButton#primary:hover {
                background-color: #2563eb;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Shortcut Name:"))
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("e.g. YouTube")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Shortcut URL (http(s)://...):"))
        self.url_input = QLineEdit(url)
        self.url_input.setPlaceholderText("e.g. https://youtube.com")
        layout.addWidget(self.url_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save", objectName="primary")
        btn_save.clicked.connect(self.on_save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def on_save(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        if not name or not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.result_data = (name, url)
        self.accept()


class NewTabCustomizerDialog(QDialog):
    def __init__(self, browser_window, parent=None):
        super().__init__(parent or browser_window)
        self.window = browser_window
        self.setWindowTitle("Edit New Tab")
        self.resize(520, 480)

        self.setStyleSheet("""
            QDialog {
                background-color: #0b0c12;
                color: #f1f3f8;
                font-family: 'Google Sans Flex', sans-serif;
            }
            QLabel {
                color: #94a3b8;
                font-size: 12px;
                border: none;
                background: transparent;
            }
            QLabel#heading {
                color: #f1f3f8;
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#subheading {
                color: #64748b;
                font-size: 12px;
                margin-bottom: 4px;
            }
            QFrame#card {
                background-color: #12141c;
                border: 1px solid #202330;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #1c1f2b;
                color: #e2e8f0;
                border: 1px solid #282c3d;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #252a3a;
                border-color: #3b82f6;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #181b26;
            }
            QPushButton#primary {
                background-color: #3b82f6;
                color: #ffffff;
                border: 1px solid #3b82f6;
                font-weight: 600;
            }
            QPushButton#primary:hover {
                background-color: #2563eb;
                border-color: #2563eb;
            }
            QPushButton#danger {
                background-color: rgba(239, 68, 68, 0.12);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }
            QPushButton#danger:hover {
                background-color: #ef4444;
                color: #ffffff;
                border-color: #ef4444;
            }
            QListWidget {
                background-color: #0d0e15;
                border: 1px solid #1c1f2b;
                border-radius: 6px;
                outline: none;
                padding: 2px;
            }
            QListWidget::item {
                border: none;
                background: transparent;
            }
            QListWidget::item:hover {
                background-color: #161822;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        h_lbl = QLabel("Edit New Tab", objectName="heading")
        sub_lbl = QLabel("Personalize background appearance and manage quick shortcuts on the New Tab page.", objectName="subheading")
        layout.addWidget(h_lbl)
        layout.addWidget(sub_lbl)

        bg_card = QFrame(objectName="card")
        bg_layout = QVBoxLayout(bg_card)
        bg_layout.setContentsMargins(14, 12, 14, 12)
        bg_layout.setSpacing(10)

        bg_header = QHBoxLayout()
        bg_title = QLabel("<b>Background</b>")
        bg_title.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        bg_header.addWidget(bg_title)

        self.bg_status_lbl = QLabel()
        self.bg_status_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        bg_header.addStretch(1)
        bg_header.addWidget(self.bg_status_lbl)
        bg_layout.addLayout(bg_header)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        color_presets = [
            ("#20242e", "Old Slate"),
            ("#361010", "Fresh Magma"),
            ("#0d1527", "Midnight Blue"),
            ("#140f24", "Distant Nebula"),
            ("#0a1813", "Wild Forest"),
            ("#1c1410", "Morning Espresso")
        ]
        for hex_code, name in color_presets:
            dot = QPushButton()
            dot.setFixedSize(24, 24)
            dot.setToolTip(f"{name} ({hex_code})")
            dot.setCursor(Qt.CursorShape.PointingHandCursor)
            dot.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: 2px solid #32374a;
                    border-radius: 12px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    border: 2px solid #3b82f6;
                }}
            """)
            dot.clicked.connect(lambda _, c=hex_code: self.set_color_bg(c))
            controls_row.addWidget(dot)

        controls_row.addSpacing(6)

        btn_color = QPushButton("Color...")
        btn_color.clicked.connect(self.choose_custom_color)
        controls_row.addWidget(btn_color)

        btn_image = QPushButton("Image...")
        btn_image.clicked.connect(self.choose_custom_image)
        controls_row.addWidget(btn_image)

        btn_remove_bg = QPushButton("Remove")
        btn_remove_bg.clicked.connect(self.clear_background)
        controls_row.addWidget(btn_remove_bg)

        bg_layout.addLayout(controls_row)
        layout.addWidget(bg_card)

        sc_card = QFrame(objectName="card")
        sc_layout = QVBoxLayout(sc_card)
        sc_layout.setContentsMargins(14, 12, 14, 12)
        sc_layout.setSpacing(10)

        sc_header = QHBoxLayout()
        sc_title = QLabel("<b>Shortcuts</b>")
        sc_title.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        sc_header.addWidget(sc_title)
        sc_header.addStretch(1)

        btn_add_sc = QPushButton("Add", objectName="primary")
        btn_add_sc.setToolTip("Add Shortcut")
        btn_add_sc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_sc.clicked.connect(self.add_shortcut)
        sc_header.addWidget(btn_add_sc)
        sc_layout.addLayout(sc_header)

        self.list_widget = QListWidget()
        self.list_widget.setFixedHeight(150)
        sc_layout.addWidget(self.list_widget)
        layout.addWidget(sc_card)

        bottom_bar = QHBoxLayout()
        btn_reset_all = QPushButton("Reset", objectName="danger")
        btn_reset_all.clicked.connect(self.reset_all_new_tab)
        bottom_bar.addWidget(btn_reset_all)

        bottom_bar.addStretch(1)

        btn_close = QPushButton("Done", objectName="primary")
        btn_close.setFixedWidth(80)
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)
        layout.addLayout(bottom_bar)

        self.update_status_label()
        self.refresh_shortcuts_list()

    def update_status_label(self):
        bg_type = self.window.prefs.get("new_tab_bg_type", "none")
        val = self.window.prefs.get("new_tab_bg", "")
        if bg_type == "image" and val:
            name = os.path.basename(val)
            self.bg_status_lbl.setText(f"Active: Image ({name})")
        elif bg_type == "color" and val:
            self.bg_status_lbl.setText(f"Active: Color ({val})")
        else:
            self.bg_status_lbl.setText("Active: Default settings")

    def set_color_bg(self, color_hex):
        self.window.prefs["new_tab_bg_type"] = "color"
        self.window.prefs["new_tab_bg"] = color_hex
        self.window.save_prefs()
        self.update_status_label()
        self.reload_new_tabs()

    def choose_custom_color(self):
        col = QColorDialog.getColor(parent=self)
        if col.isValid():
            self.set_color_bg(col.name())

    def choose_custom_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.webp *.gif)")
        if path:
            self.window.prefs["new_tab_bg_type"] = "image"
            self.window.prefs["new_tab_bg"] = path
            self.window.save_prefs()
            self.update_status_label()
            self.reload_new_tabs()

    def clear_background(self):
        self.window.prefs["new_tab_bg_type"] = "none"
        self.window.prefs["new_tab_bg"] = ""
        self.window.save_prefs()
        self.update_status_label()
        self.reload_new_tabs()

    def refresh_shortcuts_list(self):
        self.list_widget.clear()
        shortcuts = self.window.prefs.get("new_tab_shortcuts", [])
        for i, sc in enumerate(shortcuts):
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 40))

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(10, 4, 10, 4)
            item_layout.setSpacing(10)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(20, 20)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fav_b64 = get_cached_favicon_b64(sc.get("url", ""), fetch_if_missing=True)
            if fav_b64:
                pix = QPixmap()
                pix.loadFromData(QByteArray.fromBase64(fav_b64.encode("utf-8")), "PNG")
                icon_lbl.setPixmap(pix.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                apply_google_icon(icon_lbl, "globe", "🌐", QSize(16, 16))
            item_layout.addWidget(icon_lbl)

            text_lbl = QLabel(f"<b>{sc.get('name', 'Site')}</b> <span style='color:#64748b;'>({sc.get('url', '')})</span>")
            item_layout.addWidget(text_lbl, 1)

            btn_edit = QPushButton("Edit")
            btn_edit.setFixedSize(56, 26)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, idx=i: self.edit_shortcut(idx))
            item_layout.addWidget(btn_edit)

            btn_del = QPushButton(objectName="danger")
            btn_del.setFixedSize(26, 26)
            btn_del.setToolTip("Delete Shortcut")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_google_icon(btn_del, "delete", "X", QSize(12, 12))
            btn_del.clicked.connect(lambda _, idx=i: self.delete_shortcut(idx))
            item_layout.addWidget(btn_del)

            self.list_widget.setItemWidget(item, item_widget)

    def add_shortcut(self):
        dlg = ShortcutDialog("Add Shortcut", parent=self)
        if dlg.exec():
            name, url = dlg.result_data
            scs = self.window.prefs.get("new_tab_shortcuts", [])
            scs.append({"name": name, "url": url})
            self.window.prefs["new_tab_shortcuts"] = scs
            self.window.save_prefs()
            self.refresh_shortcuts_list()
            self.reload_new_tabs()

    def edit_shortcut(self, idx):
        scs = self.window.prefs.get("new_tab_shortcuts", [])
        if idx < 0 or idx >= len(scs):
            return
        target = scs[idx]
        dlg = ShortcutDialog("Edit Shortcut", name=target.get("name", ""), url=target.get("url", ""), parent=self)
        if dlg.exec():
            name, url = dlg.result_data
            scs[idx] = {"name": name, "url": url}
            self.window.prefs["new_tab_shortcuts"] = scs
            self.window.save_prefs()
            self.refresh_shortcuts_list()
            self.reload_new_tabs()

    def delete_shortcut(self, idx):
        scs = self.window.prefs.get("new_tab_shortcuts", [])
        if 0 <= idx < len(scs):
            del scs[idx]
            self.window.prefs["new_tab_shortcuts"] = scs
            self.window.save_prefs()
            self.refresh_shortcuts_list()
            self.reload_new_tabs()

    def reset_all_new_tab(self):
        reply = QMessageBox.question(
            self,
            "Reset New Tab Page",
            "Are you sure you want to reset the New Tab page to its defaults?\nThis will clear your custom background and shortcuts.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.window.prefs["new_tab_bg_type"] = "none"
            self.window.prefs["new_tab_bg"] = ""
            self.window.prefs["new_tab_shortcuts"] = []
            self.window.save_prefs()
            self.update_status_label()
            self.refresh_shortcuts_list()
            self.reload_new_tabs()

    def reload_new_tabs(self):
        for i in range(self.window.tab_bar.count()):
            v = self.window.tab_bar.tabData(i)
            if v and v.url().toString().startswith("minium://newtab"):
                v.reload()
