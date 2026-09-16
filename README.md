<div align="center">

# 🌐 Minium [BETA]

**A minimal, privacy-first Chromium-based web browser built with Python, PySide6, and QtWebEngine.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/Minium_Loves-Qt6-green?logo=qt&logoColor=white)](https://www.qt.io/)

</div>

---

> [!IMPORTANT]
> Minium is a privacy oriented browser. No user data is saved after closing, everything remains in RAM.  
> Please make sure you save your important work before quitting the browser. Minium shall not be held responsible for data loss.
> Also as a side note, you should update Minium frequently through `Menu > Update Minium`.  

> [!WARNING]
> Minium was designed to be run on Linux, it most probably won't work correctly on Windows.

To report problems or ask questions, please use GitHub Issues on this repository.  
And for contributions, use GitHub Pull Requests.
All third-party resources such as the font, icons and blocklists used retain the copyrights and licenses of their respective owners.

---

## ✨ Features

* 🛡️ **Privacy & Security First:** Built-in multi-source ad blocker (HaGeZi Ultimate & TIF Medium, AdGuard, StevenBlack, etc.) and real-time Phishing protection via Cisco Talos PhishTank.
* ⚡ **Ephemeral & Lightweight:** Your session is never saved to disk. Includes a **"Burn All Data"** option (`Menu > Burn All Data`) to wipe cache, history, and active sessions instantly.
* 🪟 **Modern UI:** Rounded window borders, drag zones, hide-able tabs, toast messages, `-l` or `--less` mode and more.
* 🔍 **Power-User Ergonomics:** In-page find utility, audio indicators, tab pinning, tab unloading (to save RAM), and a Minium Dev Tools side pane (`F12` or `Ctrl+Shift+I`).
* 🎥 **Picture-in-Picture [BETA]:** Floating video player compatible with (atleast) standard HTML5 `<video>` tags.
* 🔄 **Installer & Updater:** Rootless user-space setup (`--install`, `--uninstall`, `--update`) with automatic GitHub raw patching.

---

## 🛠️ System Prerequisites

Ensure your system has Python 3.10+ and the Qt6 system dependencies installed.

### On Fedora / RHEL / CentOS

```bash
sudo dnf install python3 python3-pip qt6-qtwebengine-devtools
pip install PySide6
```

### On Ubuntu / Debian / Mint

```bash
sudo apt update
sudo apt install python3 python3-pip qt6-webengine-dev-tools
pip install PySide6
```

---

## 📥 Installation

1. Clone or download the Minium repository to your local machine:

   ```bash
   git clone https://github.com/SubhrajitSain/Minium.git
   cd Minium
   ```

2. Install Python dependencies (PySide6):

   ```bash
   pip install --user PySide6
   ```

3. Run the built-in installer script to register Minium to your user environment (creates the binary launcher at `~/.local/bin/minium`, creates the XDG desktop entry, and registers MIME protocols):

   ```bash
   python3 minium.py --install
   ```

You can now launch **Minium** directly from your desktop application launcher or type `minium` in your terminal!

---

## 🚀 Running Minium Manually (Development Mode)

If you prefer running it directly from the source directory without installing it to your PATH:

```bash
python3 minium.py
```

### Command-Line Arguments

* Run in minimal viewport-only mode (hiding tabs/nav bars):

  ```bash
  python3 minium.py --less
  ```

* Open a starting URL immediately:

  ```bash
  python3 minium.py https://example.com
  ```

* Check for updates and update manually via CLI:

  ```bash
  python3 minium.py --update
  ```

---

## 🗑️ Uninstallation

To completely remove Minium, its desktop launchers, and environment links from your user space, run:

```bash
python3 minium.py --uninstall
```

...or...

```bash
minium --uninstall
```

To remove all data, simply remove the Minium source folder that you downloaded.

---

## ⌨️ Keyboard Shortcuts & Controls

| Shortcut | Action |
| :--- | :--- |
| <kbd>Ctrl</kbd> + <kbd>T</kbd> | Open New Tab |
| <kbd>Ctrl</kbd> + <kbd>W</kbd> | Close Current Tab |
| <kbd>Ctrl</kbd> + <kbd>N</kbd> | Open New Window (Same Session) |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>N</kbd> | Open New Burnt Window (New Session) |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>T</kbd> | Reopen Last Closed Tab |
| <kbd>Ctrl</kbd> + <kbd>Tab</kbd> / <kbd>Ctrl</kbd> + <kbd>PgDn</kbd> | Switch to Next Tab |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Tab</kbd> | Switch to Previous Tab |
| <kbd>Ctrl</kbd> + <kbd>1</kbd> to <kbd>9</kbd> | Jump to Tab 1–9 |
| <kbd>Ctrl</kbd> + <kbd>L</kbd> or <kbd>Alt</kbd> + <kbd>D</kbd> | Focus Address Bar |
| <kbd>Ctrl</kbd> + <kbd>F</kbd> | Find In Page |
| <kbd>F12</kbd> or <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>I</kbd> | Toggle Developer Tools Pane |
| <kbd>Alt</kbd> + <kbd>P</kbd> | Open Video in Picture-in-Picture |
| <kbd>F11</kbd> | Toggle Fullscreen Mode |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> or <kbd>F5</kbd> | Reload Page |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>R</kbd> | Hard Reload (Bypass Cache) |
| <kbd>Ctrl</kbd> + <kbd>+</kbd> (or <kbd>=</kbd>) / <kbd>-</kbd> / <kbd>0</kbd> | Zoom In / Out / Reset |
| <kbd>Ctrl</kbd> + <kbd>Q</kbd> | Exit Browser |

---

## 🔌 Extras

### 🧩 UserScripts & UserCSS (.user.js / .user.css)

Drop any custom `.user.js` (Greasemonkey-style scripts) or `.user.css` file into the `./userscripts/` directory. Minium automatically detects, loads, and injects them into web pages on startup.

---

## ❤️ Thank You

Resources used in the making:

* **Google Sans Flex** font for the entire app.
* **Google Material Icons** as icons for buttons and actions.
* **DuckDuckGo** as the search engine.
* **Python**, **PySide6** + **Qt** for the heavy lifting.
* **Phishtank** by Cisco Talos for phishting threat protection.
* **HaGeZi** for the Ultimate DNS Blocklist and TIF Medium.
* **StevenBlack** for Unified Hosts blocklist.
* **AdGuard**'s DNS Filter.
* **AdAway**'s official blocklist.
* **d3ward** for the Toolz Blacklist.
* **Peter Lowe**'s Adservers (Yoyo).
* **AnudeepND** for the Adservers Blacklist.

---

*&copy; 2026 Minium by Subhrajit Sain. All rights reserved.*  
*Minium is licensed under the MIT License.*
