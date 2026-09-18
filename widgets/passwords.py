import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QLineEdit, QListWidget, QInputDialog, QMessageBox, QWidget)

from config import PASSWORDS_FILE

class PasswordManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Minium Passwords")
        self.resize(550, 450)
        self.setStyleSheet("""
            QDialog { background-color: #050608; color: #f1f3f8; font-family: 'Google Sans Flex', sans-serif; }
            QLineEdit { background: #14151e; color: #fff; padding: 10px; border: 1px solid #252838; border-radius: 6px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #3b82f6; }
            QPushButton { background: #242633; color: #f1f3f8; border: 1px solid #3b4058; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 12px; }
            QPushButton:hover { background: #3b82f6; border-color: #3b82f6; color: #ffffff; }
            QPushButton#danger { background: rgba(239, 68, 68, 0.1); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
            QPushButton#danger:hover { background: #ef4444; color: #ffffff; border-color: #ef4444; }
            QPushButton#primary { background: #3b82f6; color: #ffffff; border: none; }
            QPushButton#primary:hover { background: #2563eb; }
            QListWidget { background: #12131b; color: #cbd5e1; border: 1px solid #252838; border-radius: 6px; padding: 4px; font-size: 13px; outline: none; }
            QListWidget::item { padding: 8px; border-radius: 4px; border-bottom: 1px solid transparent; }
            QListWidget::item:hover { background-color: #1a1c27; }
            QListWidget::item:selected { background-color: #3b82f6; color: #ffffff; }
            QLabel#title { font-size: 20px; font-weight: 700; color: #f1f3f8; }
            QLabel#subtitle { font-size: 12px; color: #94a3b8; margin-bottom: 10px; }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)

        self.lbl_title = QLabel("Password Manager", objectName="title")
        self.layout.addWidget(self.lbl_title)
        self.lbl_subtitle = QLabel("Unlock your vault (or create one) to manage saved credentials.", objectName="subtitle")
        self.layout.addWidget(self.lbl_subtitle)

        self.auth_container = QWidget()
        auth_layout = QVBoxLayout(self.auth_container)
        auth_layout.setContentsMargins(0, 20, 0, 0)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("Enter Master Password")
        self.pwd_input.returnPressed.connect(self.unlock_vault)
        auth_layout.addWidget(self.pwd_input)

        self.btn_unlock = QPushButton("Continue", objectName="primary")
        self.btn_unlock.setFixedHeight(36)
        self.btn_unlock.clicked.connect(self.unlock_vault)
        auth_layout.addWidget(self.btn_unlock)

        self.layout.addWidget(self.auth_container)

        self.vault_container = QWidget()
        vault_layout = QVBoxLayout(self.vault_container)
        vault_layout.setContentsMargins(0, 0, 0, 0)
        vault_layout.setSpacing(12)

        self.list_widget = QListWidget()
        vault_layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add New", objectName="primary")
        self.btn_add.clicked.connect(self.add_entry)

        self.btn_change_pwd = QPushButton("Change Password")
        self.btn_change_pwd.clicked.connect(self.change_master_password)

        self.btn_copy_user = QPushButton("Copy User")
        self.btn_copy_user.clicked.connect(self.copy_username)

        self.btn_copy_pass = QPushButton("Copy Pass")
        self.btn_copy_pass.clicked.connect(self.copy_password)

        self.btn_delete = QPushButton("Delete", objectName="danger")
        self.btn_delete.clicked.connect(self.delete_entry)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_change_pwd)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_copy_user)
        btn_layout.addWidget(self.btn_copy_pass)
        btn_layout.addWidget(self.btn_delete)

        vault_layout.addLayout(btn_layout)

        self.layout.addWidget(self.vault_container)
        self.vault_container.hide()
        self.layout.addStretch(1)

        self.master_key = None
        self.vault_data = []

    def _derive_key(self, pwd: str, salt: bytes):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        return kdf.derive(pwd.encode())

    def unlock_vault(self):
        pwd = self.pwd_input.text()
        if not pwd: return

        if os.path.exists(PASSWORDS_FILE):
            try:
                with open(PASSWORDS_FILE, "r") as f:
                    data = json.load(f)
                salt = base64.b64decode(data['salt'])
                nonce = base64.b64decode(data['nonce'])
                ct = base64.b64decode(data['ciphertext'])

                key = self._derive_key(pwd, salt)
                aesgcm = AESGCM(key)
                pt = aesgcm.decrypt(nonce, ct, None)

                self.vault_data = json.loads(pt.decode())
                self.master_key = key
                self.show_vault()
            except Exception:
                QMessageBox.critical(self, "Error", "Invalid Master Password or corrupted vault detected.")
        else:
            salt = os.urandom(16)
            self.master_key = self._derive_key(pwd, salt)
            self.vault_data = []
            self.save_vault(salt)
            self.show_vault()

    def show_vault(self):
        self.auth_container.hide()
        self.lbl_subtitle.setText("Your passwords are encrypted securely, no need to worry.")
        self.vault_container.show()
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        for entry in self.vault_data:
            self.list_widget.addItem(f"{entry['site']}  •  {entry['username']}")

    def add_entry(self):
        site, ok1 = QInputDialog.getText(self, "Add Entry", "Site Name:")
        if ok1 and site:
            usr, ok2 = QInputDialog.getText(self, "Add Entry", "Username:")
            if ok2 and usr:
                pwd, ok3 = QInputDialog.getText(self, "Add Entry", "Password:", QLineEdit.EchoMode.Password)
                if ok3 and pwd:
                    self.vault_data.append({"site": site, "username": usr, "password": pwd})
                    self.save_vault()
                    self.refresh_list()

    def copy_username(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            QGuiApplication.clipboard().setText(self.vault_data[row]['username'])
            QMessageBox.information(self, "Copied", "Username copied to clipboard.")

    def copy_password(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            QGuiApplication.clipboard().setText(self.vault_data[row]['password'])
            QMessageBox.information(self, "Copied", "Password copied to clipboard.")

    def delete_entry(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            reply = QMessageBox.question(self, "Delete", "Are you sure you want to delete this credential?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                del self.vault_data[row]
                self.save_vault()
                self.refresh_list()

    def change_master_password(self):
        new_pwd, ok1 = QInputDialog.getText(self, "Change Password", "Enter new Master Password:", QLineEdit.EchoMode.Password)
        if ok1 and new_pwd:
            confirm_pwd, ok2 = QInputDialog.getText(self, "Confirm Password", "Re-enter Master Password:", QLineEdit.EchoMode.Password)
            if ok2 and confirm_pwd:
                if new_pwd == confirm_pwd:
                    new_salt = os.urandom(16)
                    self.master_key = self._derive_key(new_pwd, new_salt)
                    self.save_vault(new_salt)
                    QMessageBox.information(self, "Success", "Master Password changed successfully.\nYour vault has been re-encrypted and restored successfully.")
                else:
                    QMessageBox.warning(self, "Error", "The two passwords you entered do not match.")

    def save_vault(self, salt=None):
        if not self.master_key: return
        try:
            if not salt:
                with open(PASSWORDS_FILE, "r") as f:
                    salt = base64.b64decode(json.load(f)['salt'])

            aesgcm = AESGCM(self.master_key)
            nonce = os.urandom(12)
            pt = json.dumps(self.vault_data).encode()
            ct = aesgcm.encrypt(nonce, pt, None)

            with open(PASSWORDS_FILE, "w") as f:
                json.dump({
                    "salt": base64.b64encode(salt).decode(),
                    "nonce": base64.b64encode(nonce).decode(),
                    "ciphertext": base64.b64encode(ct).decode()
                }, f)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save the password vault:\n{str(e)}")
