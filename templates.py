import os
import urllib.parse

from PySide6.QtCore import QDateTime

from config import ICON_DIR
from utils import get_minium_icon_b64, get_font_face_css

NEW_TAB_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="color-scheme" content="dark">
    <title>New Tab</title>
    __FAVICON_TAG__
    <style>
        __FONT_FACE_CSS__
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html {
            width: 100%;
            height: 100%;
        }
        body {
            width: 100%;
            height: 100vh;
            margin: 0;
            padding: 0;
            background-color: #050608;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            user-select: none;
            overflow: hidden;
            background-repeat: no-repeat;
            background-position: center;
            background-size: cover;
            __BG_STYLE__
        }
        .container {
            width: 100%;
            max-width: 720px;
            min-width: 560px;
            padding: 0 20px;
            text-align: center;
            margin-top: -60px;
        }
        .title-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 28px;
        }
        .logo { width: 48px; height: 48px; margin-right: 6px; object-fit: contain; }
        .title {
            font-family: 'Google Sans Flex', sans-serif;
            font-size: 48px;
            font-weight: 700;
            letter-spacing: -1px;
            color: #f1f3f8;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.5);
        }
        .search-box { position: relative; width: 100%; display: flex; align-items: center; }
        .search-icon-wrap {
            position: absolute; left: 16px; width: 16px; height: 16px;
            display: flex; align-items: center; justify-content: center; pointer-events: none;
            z-index: 10;
        }
        .search-icon-wrap svg { width: 16px; height: 16px; fill: #64748b; transition: fill 0.15s ease; }
        .search-box input {
            font-family: 'Google Sans Flex', sans-serif; width: 100%; height: 38px;
            padding: 0 24px 0 44px; font-size: 13.5px; font-weight: 500;
            border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 19px; outline: none;
            background-color: rgba(22, 23, 32, 0.75); color: #f1f3f8; backdrop-filter: blur(8px);
            transition: 0.15s ease;
        }
        .search-box input:focus {
            border-color: #3b82f6; background-color: rgba(25, 26, 38, 0.9);
        }
        .search-box:focus-within .search-icon-wrap svg { fill: #3b82f6; }
        .shortcuts {
            display: flex;
            gap: 16px;
            justify-content: center;
            margin-top: 36px;
            flex-wrap: wrap;
            max-width: 640px;
        }
        .shortcut {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            width: 86px;
            padding: 12px 8px;
            border-radius: 12px;
            background: rgba(22, 23, 32, 0.75);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .shortcut:hover {
            background: rgba(30, 33, 48, 0.9);
            border-color: rgba(59, 130, 246, 0.5);
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
        }
        .shortcut-icon {
            width: 44px;
            height: 44px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 8px;
            overflow: hidden;
        }
        .shortcut-icon img {
            width: 24px;
            height: 24px;
            object-fit: contain;
        }
        .shortcut-fallback {
            font-size: 18px;
            font-weight: 700;
            color: #cbd5e1;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
        }
        .shortcut-title {
            color: #cbd5e1;
            font-size: 11px;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            width: 100%;
            text-align: center;
        }
        .customize-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 14px;
            background: rgba(21, 23, 34, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid #252838;
            border-radius: 20px;
            color: #94a3b8;
            text-decoration: none;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .customize-btn:hover {
            background: #1a1c27;
            border-color: #3b82f6;
            color: #f1f3f8;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .customize-btn svg {
            width: 14px;
            height: 14px;
            fill: currentColor;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="title-wrap">
            __LOGO_TAG__
            <h1 class="title">Minium</h1>
        </div>
        <form action="https://duckduckgo.com/" method="GET" class="search-box">
            <div class="search-icon-wrap">
                <svg viewBox="0 0 24 24" width="16" height="16">
                    <path fill="#64748b" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
            </div>
            <input type="text" name="q" placeholder="Search with DuckDuckGo or enter address..." autofocus autocomplete="off"/>
        </form>
        <div class="shortcuts">
            __SHORTCUTS_HTML__
        </div>
        <script>
            function focusSearchInput() {
                const inp = document.querySelector('input[name="q"]');
                if (inp) inp.focus();
            }
            window.addEventListener('DOMContentLoaded', focusSearchInput);
            window.addEventListener('load', focusSearchInput);
            window.addEventListener('focus', focusSearchInput);
        </script>
    </div>

    <a href="minium://action?do=customize_new_tab" class="customize-btn" title="Edit New Tab Page">
        <svg viewBox="0 0 24 24">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34a.9959.9959 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
        </svg>
        <span>Edit</span>
    </a>
</body>
</html>
"""

ERROR_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="color-scheme" content="dark">
    <title>Page Error</title>
    __FAVICON_TAG__
    <style>
        __FONT_FACE_CSS__
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            background-color: #050608;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            user-select: none;
            padding: 20px;
        }
        .container {
            max-width: 540px;
            width: 100%;
            text-align: center;
        }
        .icon-circle {
            margin-bottom: 16px;
        }
        h2 {
            font-family: 'Google Sans Flex', sans-serif;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #f1f3f8;
        }
        .error-msg {
            font-family: 'Google Sans Flex', sans-serif;
            font-size: 14px;
            color: #ef4444;
            line-height: 1.5;
            margin-bottom: 16px;
            background: rgba(239, 68, 68, 0.08);
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 8px 14px;
            border-radius: 6px;
            display: inline-block;
        }
        details {
            background: #161720;
            border: 1px solid #242633;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 24px;
            text-align: left;
            font-size: 13px;
        }
        summary {
            cursor: pointer;
            color: #94a3b8;
            font-weight: 600;
            outline: none;
            user-select: none;
        }
        .accordion-content {
            margin-top: 10px;
            border-top: 1px solid #242633;
            padding-top: 10px;
        }
        .detail-row {
            font-size: 12px;
            color: #94a3b8;
            margin-bottom: 6px;
            word-break: break-all;
        }
        .detail-row:last-child {
            margin-bottom: 0;
        }
        .detail-label {
            color: #64748b;
            font-weight: 600;
            margin-right: 6px;
        }
        .actions {
            display: flex;
            gap: 10px;
            justify-content: center;
        }
        button {
            font-family: 'Google Sans Flex', sans-serif;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: background 0.15s ease;
        }
        .btn-retry {
            background: #3b82f6;
            color: #ffffff;
        }
        .btn-retry:hover {
            background: #2563eb;
        }
        .btn-home {
            background: #1e202b;
            color: #cbd5e1;
        }
        .btn-home:hover {
            background: #282a3a;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon-circle">
            <svg viewBox="0 0 24 24" width="36" height="36" fill="#ef4444">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
        </div>
        <h2>Failed to Load</h2>
        <div class="error-msg">__ERROR_MSG__</div>
        <details>
            <summary>More Info</summary>
            <div class="accordion-content">
                <div class="detail-row"><span class="detail-label">URL:</span>__FAILED_URL__</div>
                <div class="detail-row"><span class="detail-label">Diagnostics:</span>__ERROR_CODE__</div>
                <div class="detail-row"><span class="detail-label">Timestamp:</span>__TIME_NOW__</div>
            </div>
        </details>
        <div class="actions">
            <button class="btn-retry" onclick="window.location.href='__FAILED_URL__'">Retry</button>
            <button class="btn-home" onclick="window.location.href='minium://safety'">Back</button>
        </div>
    </div>
</body>
</html>
"""

PHISHING_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="color-scheme" content="dark">
    <title>Phishing Site</title>
    __FAVICON_TAG__
    <style>
        __FONT_FACE_CSS__
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            background-color: #1a0505;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            user-select: none;
            padding: 20px;
        }
        .container {
            max-width: 560px;
            width: 100%;
            text-align: center;
        }
        .shield-icon {
            margin-bottom: 18px;
        }
        h2 {
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #ef4444;
        }
        p {
            font-size: 14px;
            color: #cbd5e1;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .details-box {
            background: #240a0a;
            border: 1px solid #451a1a;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 24px;
            text-align: left;
            font-size: 12px;
            color: #fca5a5;
            word-break: break-all;
        }
        .actions {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
        button {
            font-family: 'Google Sans Flex', sans-serif;
            padding: 10px 22px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: opacity 0.15s ease;
        }
        .btn-safe {
            background: #3b82f6;
            color: #ffffff;
        }
        .btn-safe:hover {
            opacity: 0.9;
        }
        .btn-ignore {
            background: #2b1111;
            color: #94a3b8;
            border: 1px solid #451a1a;
        }
        .btn-ignore:hover {
            color: #f1f3f8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="shield-icon">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="#ef4444">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 6h2v6h-2V7zm1 10.25c-.69 0-1.25-.56-1.25-1.25s.56-1.25 1.25-1.25 1.25.56 1.25 1.25-.56 1.25-1.25 1.25z"/>
            </svg>
        </div>
        <h2>Phishing Site Ahead</h2>
        <p>Minium has identified this page as a malicious phishing site designed to steal your passwords, credentials, credit cards or other details.</p>
        <div class="details-box">
            <b>Flagged URL:</b> __PHISH_URL__
        </div>
        <div class="actions">
            <button class="btn-safe" onclick="window.location.href='minium://safety'">Back to safety</button>
            <button class="btn-ignore" onclick="window.location.href='minium://proceed?target=__PHISH_URL__'">Proceed anyway</button>
        </div>
    </div>
</body>
</html>
"""

BLOCKED_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="color-scheme" content="dark">
    <title>Site Blocked</title>
    __FAVICON_TAG__
    <style>
        __FONT_FACE_CSS__
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            background-color: #120904;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            user-select: none;
            padding: 20px;
        }
        .container {
            max-width: 560px;
            width: 100%;
            text-align: center;
        }
        .shield-icon {
            margin-bottom: 18px;
        }
        h2 {
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #f59e0b;
        }
        p {
            font-size: 14px;
            color: #cbd5e1;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        .details-box {
            background: #1f1207;
            border: 1px solid #4a2d13;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 24px;
            text-align: left;
            font-size: 12px;
            color: #fcd34d;
            word-break: break-all;
        }
        .actions {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
        button {
            font-family: 'Google Sans Flex', sans-serif;
            padding: 10px 22px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: opacity 0.15s ease;
        }
        .btn-safe {
            background: #3b82f6;
            color: #ffffff;
        }
        .btn-safe:hover {
            background: #2563eb;
        }
        .btn-ignore {
            background: #23160c;
            color: #94a3b8;
            border: 1px solid #4a2d13;
        }
        .btn-ignore:hover {
            color: #f1f3f8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="shield-icon">
            <svg viewBox="0 0 24 24" width="48" height="48" fill="#f59e0b">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-1 6h2v6h-2V7zm1 10.25c-.69 0-1.25-.56-1.25-1.25s.56-1.25 1.25-1.25 1.25.56 1.25 1.25-.56 1.25-1.25 1.25z"/>
            </svg>
        </div>
        <h2>Site Blocked</h2>
        <p>Minium Adblock has blocked this site because it is listed in its ad, tracker, or security threat blocklists.</p>
        <div class="details-box">
            <b>Flagged URL:</b> __BLOCKED_URL__<br>
            <b>Diagnostic:</b> net::ERR_ACCESS_DENIED
        </div>
        <div class="actions">
            <button class="btn-safe" onclick="window.location.href='minium://safety'">Back to safety</button>
            <button class="btn-ignore" onclick="window.location.href='minium://proceed?target=__BLOCKED_URL__'">Proceed anyway</button>
        </div>
    </div>
</body>
</html>
"""

SETTINGS_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="color-scheme" content="dark">
    <title>Settings - Minium</title>
    __FAVICON_TAG__
    <style>
        __FONT_FACE_CSS__
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            background-color: #050608;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', sans-serif;
            display: flex;
            justify-content: center;
            padding: 40px 20px;
        }
        .container { max-width: 600px; width: 100%; }
        h1 { font-size: 28px; font-weight: 700; margin-bottom: 30px; display: flex; align-items: center; gap: 12px; }
        .logo { width: 48px; height: 48px; object-fit: contain; }
        .section {
            background: #151722; border: 1px solid #252838; border-radius: 8px; padding: 20px; margin-bottom: 24px;
        }
        .section h2 { font-size: 16px; font-weight: 600; color: #94a3b8; margin-bottom: 16px; border-bottom: 1px solid #252838; padding-bottom: 8px; }
        .row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #1c1e29; }
        .row:last-child { border-bottom: none; padding-bottom: 0; }
        .row-info strong { display: block; font-size: 14px; margin-bottom: 4px; }
        .row-info span { font-size: 12px; color: #64748b; margin-right: 20px; }
        .btn {
            background: #242633; color: #f1f3f8; border: 1px solid #3b4058; padding: 8px 16px; border-radius: 6px;
            cursor: pointer; font-size: 12px; font-weight: 600; text-decoration: none; transition: all 0.15s ease;
        }
        .btn:hover { background: #3b82f6; border-color: #3b82f6; color: #fff; }
        .btn-active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
        .btn-active:hover { opacity: 0.9; }
        .btn-danger { background: rgba(239, 68, 68, 0.1); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
        .btn-danger:hover { background: #ef4444; border-color: #ef4444; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>__LOGO_TAG__ Settings</h1>

        <div class="section">
            <h2>Privacy & Security</h2>
            <div class="row">
                <div class="row-info">
                    <strong>Minium Adblock</strong>
                    <span>Block ads, trackers, bad sites. Works quite well.</span>
                </div>
                <a href="minium://action?do=toggle_protect" class="btn __PROTECT_CLASS__">__PROTECT_TEXT__</a>
            </div>
            <div class="row">
                <div class="row-info">
                    <strong>Minium Maxium Mode</strong>
                    <span>__MAXIUM_DESC__</span>
                </div>
                <a href="minium://action?do=toggle_maxium" class="btn __MAXIUM_CLASS__">__MAXIUM_TEXT__</a>
            </div>
            <div class="row">
                <div class="row-info">
                    <strong>Password Manager</strong>
                    <span>__PASSWORD_DESC__</span>
                </div>
                <a href="minium://action?do=passwords" class="btn">Open</a>
            </div>
            <div class="row">
                <div class="row-info">
                    <strong>JavaScript</strong>
                    <span>Allow websites to run JS scripts.</span>
                </div>
                <a href="minium://action?do=toggle_js" class="btn __JS_CLASS__">__JS_TEXT__</a>
            </div>
        </div>

        <div class="section">
            <h2>Appearance</h2>
            <div class="row">
                <div class="row-info">
                    <strong>Dark Web Theme</strong>
                    <span>[BETA] Force websites to become dark themed.</span>
                </div>
                <a href="minium://action?do=toggle_theme" class="btn __THEME_CLASS__">__THEME_TEXT__</a>
            </div>
            <div class="row">
                <div class="row-info">
                    <strong>Bookmarks Bar</strong>
                    <span>Show a quick access bookmarks bar under the URL.</span>
                </div>
                <a href="minium://action?do=toggle_bookmarks_bar" class="btn __BM_CLASS__">__BM_TEXT__</a>
            </div>
        </div>

        <div class="section">
            <h2>Updates</h2>
            <div class="row">
                <div class="row-info">
                    <strong>Auto-Update Adblock</strong>
                    <span>Check for blocklist updates silently in the background.</span>
                </div>
                <a href="minium://action?do=toggle_adblock_update" class="btn __ADBLOCK_UPD_CLASS__">__ADBLOCK_UPD_TEXT__</a>
            </div>
            <div class="row">
                <div class="row-info">
                    <strong>Boot-time Checks</strong>
                    <span>Check for Minium core updates when the browser starts.</span>
                </div>
                <a href="minium://action?do=toggle_boot_update" class="btn __BOOT_UPD_CLASS__">__BOOT_UPD_TEXT__</a>
            </div>
        </div>

        <div class="section">
            <h2>Data</h2>
            <div class="row">
                <div class="row-info">
                    <strong>Burn All Data</strong>
                    <span>Instantly delete all data, cache and cookies.</span>
                </div>
                <a href="minium://action?do=burn_data" class="btn btn-danger">Burn</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

HISTORY_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="color-scheme" content="dark">
    <title>History - Minium</title>
    __FAVICON_TAG__
    <style>
        __FONT_FACE_CSS__
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            background-color: #050608;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', sans-serif;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }
        .container { max-width: 700px; width: 100%; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        h1 { font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 12px; }
        img {
            width: 48px;
            height: 48px;
            object-fit: contain;
        }
        .btn-clear {
            background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600;
            transition: 0.15s;
        }
        .btn-clear:hover { background: #ef4444; color: #fff; }
        .list-container {
            background: #151722; border: 1px solid #252838; border-radius: 8px; overflow: hidden;
        }
        .list-item {
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px 16px; border-bottom: 1px solid #252838; text-decoration: none; transition: background 0.1s;
        }
        .list-item:last-child { border-bottom: none; }
        .list-item:hover { background: #1a1c27; }
        .item-main { display: flex; align-items: center; gap: 12px; overflow: hidden; }
        .item-main img { width: 16px; height: 16px; opacity: 0.7; }
        .item-text { display: flex; flex-direction: column; overflow: hidden; }
        .item-title { color: #f1f3f8; font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .item-url { color: #64748b; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .item-time { color: #475569; font-size: 11px; white-space: nowrap; margin-left: 12px; }
        .empty { padding: 40px; text-align: center; color: #64748b; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>__LOGO_TAG__ History</h1>
            <a href="minium://action?do=clear_history" class="btn-clear">Clear</a>
        </div>
        <div class="list-container">
            __HISTORY_LIST__
        </div>
    </div>
</body>
</html>
"""

BOOKMARKS_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="color-scheme" content="dark">
    <title>Bookmarks - Minium</title>
    __FAVICON_TAG__
    <style>
        __FONT_FACE_CSS__
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            background-color: #050608;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', sans-serif;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }
        .container { max-width: 700px; width: 100%; }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }
        h1 { font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 12px; }
        h1 img { width: 48px; height: 48px; object-fit: contain; }
        .list-container {
            background: #151722; border: 1px solid #252838; border-radius: 8px; overflow: hidden;
        }
        .list-item {
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px 16px; border-bottom: 1px solid #252838; transition: background 0.1s;
        }
        .list-item:last-child { border-bottom: none; }
        .list-item:hover { background: #1a1c27; }
        .item-main { display: flex; align-items: center; gap: 12px; overflow: hidden; flex: 1; text-decoration: none; }
        .item-icon {
            width: 16px; height: 16px; fill: #94a3b8; flex-shrink: 0;
        }
        .item-text { display: flex; flex-direction: column; overflow: hidden; flex: 1; }
        .item-title { color: #f1f3f8; font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .item-url { color: #64748b; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        .btn-remove {
            color: #94a3b8; text-decoration: none; font-size: 12px; font-weight: bold; padding: 4px 8px; border-radius: 4px; margin-left: 12px; background: transparent;
        }
        .btn-remove:hover { background: #e81123; color: #fff; }
        .empty { padding: 40px; text-align: center; color: #64748b; font-size: 13px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>__LOGO_TAG__ Bookmarks</h1>
        </div>
        <div class="list-container">
            __BOOKMARKS_LIST__
        </div>
    </div>
</body>
</html>
"""

DEFAULT_SEARCH_SVG = """<svg viewBox="0 0 24 24" width="16" height="16" fill="#64748b"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>"""

def get_new_tab_html() -> str:
    from utils import get_prefs, get_cached_favicon_b64
    prefs = get_prefs()
    search_svg_path = os.path.join(ICON_DIR, "search.svg")
    search_svg = ""
    if os.path.exists(search_svg_path):
        try:
            with open(search_svg_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content and "<svg" in content:
                    search_svg = content
        except Exception:
            pass

    final_search_svg = search_svg if search_svg else DEFAULT_SEARCH_SVG

    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""
    logo_tag = f'<img class="logo" src="data:image/png;base64,{b64}" alt="Minium Logo">' if b64 else ""

    bg_style = ""
    if prefs.get("new_tab_bg_type") == "image" and prefs.get("new_tab_bg"):
        bg_style = f"background-image: url('file://{prefs['new_tab_bg']}'); background-size: cover; background-position: center; background-repeat: no-repeat;"
    elif prefs.get("new_tab_bg_type") == "color" and prefs.get("new_tab_bg"):
        bg_style = f"background-color: {prefs['new_tab_bg']};"

    shortcuts_html = ""
    for sc in prefs.get("new_tab_shortcuts", []):
        name = sc.get("name", "Site")
        url = sc.get("url", "#")
        fav_b64 = get_cached_favicon_b64(url, fetch_if_missing=True)
        if fav_b64:
            icon_markup = f'<img src="data:image/png;base64,{fav_b64}" alt="{name}">'
        else:
            letter = name[0].upper() if name else "?"
            icon_markup = f'<div class="shortcut-fallback">{letter}</div>'

        shortcuts_html += f"""
        <a href="{url}" class="shortcut">
            <div class="shortcut-icon">{icon_markup}</div>
            <div class="shortcut-title">{name}</div>
        </a>
        """

    html = NEW_TAB_HTML_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__BG_STYLE__", bg_style)
    html = html.replace("__SHORTCUTS_HTML__", shortcuts_html)
    html = html.replace("__SEARCH_ICON_SVG__", final_search_svg)
    html = html.replace("__FAVICON_TAG__", favicon_tag)
    html = html.replace("__LOGO_TAG__", logo_tag)
    return html

def get_settings_html(prefs) -> str:
    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""
    logo_tag = f'<img class="logo" src="data:image/png;base64,{b64}" alt="Logo">' if b64 else ""

    html = SETTINGS_HTML_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__FAVICON_TAG__", favicon_tag).replace("__LOGO_TAG__", logo_tag)

    is_protect = prefs.get("protect_me", True)
    is_js = prefs.get("js_enabled", True)
    is_dark = prefs.get("web_theme_dark", True)
    is_maxium = prefs.get("maxium_mode", False)
    is_bm = prefs.get("show_bookmarks_bar", False)
    is_ad_upd = prefs.get("auto_update_adblock", True)
    is_boot_upd = prefs.get("boot_update_checks", True)

    html = html.replace("__PROTECT_CLASS__", "btn-active" if is_protect else "").replace("__PROTECT_TEXT__", "ON" if is_protect else "OFF")
    html = html.replace("__JS_CLASS__", "btn-active" if is_js else "").replace("__JS_TEXT__", "ON" if is_js else "OFF")
    html = html.replace("__THEME_CLASS__", "btn-active" if is_dark else "").replace("__THEME_TEXT__", "ON" if is_dark else "OFF")

    max_desc = "Currently in Maxium mode." if is_maxium else "Currently in ephemeral mode."
    pwd_desc = "Manage encrypted passwords securely." if is_maxium else "Available in Maxium Mode only."

    html = html.replace("__MAXIUM_DESC__", max_desc).replace("__MAXIUM_CLASS__", "btn-active" if is_maxium else "").replace("__MAXIUM_TEXT__", "ON" if is_maxium else "OFF")
    html = html.replace("__PASSWORD_DESC__", pwd_desc)

    html = html.replace("__BM_CLASS__", "btn-active" if is_bm else "").replace("__BM_TEXT__", "ON" if is_bm else "OFF")
    html = html.replace("__ADBLOCK_UPD_CLASS__", "btn-active" if is_ad_upd else "").replace("__ADBLOCK_UPD_TEXT__", "ON" if is_ad_upd else "OFF")
    html = html.replace("__BOOT_UPD_CLASS__", "btn-active" if is_boot_upd else "").replace("__BOOT_UPD_TEXT__", "ON" if is_boot_upd else "OFF")

    return html

def get_error_html(failed_url: str, error_msg: str, error_code: str) -> str:
    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""

    html = ERROR_PAGE_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__FAVICON_TAG__", favicon_tag)
    html = html.replace("__FAILED_URL__", failed_url)
    html = html.replace("__ERROR_MSG__", error_msg)
    html = html.replace("__ERROR_CODE__", error_code)
    html = html.replace("__TIME_NOW__", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))
    return html

def get_blocked_html(failed_url: str) -> str:
    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""
    html = BLOCKED_PAGE_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__FAVICON_TAG__", favicon_tag)
    html = html.replace("__BLOCKED_URL__", failed_url)
    return html

def get_phishing_html(failed_url: str) -> str:
    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""
    html = PHISHING_PAGE_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__FAVICON_TAG__", favicon_tag)
    html = html.replace("__PHISH_URL__", failed_url)
    return html

def get_bookmarks_html(bookmarks_list: list) -> str:
    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""
    logo_tag = f'<img src="data:image/png;base64,{b64}">' if b64 else ""

    html = BOOKMARKS_HTML_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__FAVICON_TAG__", favicon_tag).replace("__LOGO_TAG__", logo_tag)

    if not bookmarks_list:
        items_html = '<div class="empty">No bookmarks saved. It feels lonely here...</div>'
    else:
        items_html = ""
        svg_icon = '<svg class="item-icon" xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M200-120v-640q0-33 23.5-56.5T280-840h400q33 0 56.5 23.5T760-760v640L480-240 200-120Zm80-122 200-86 200 86v-518H280v518Zm0-518h400-400Z"/></svg>'

        for item in bookmarks_list:
            safe_url = urllib.parse.quote(item['url'], safe='')
            remove_url = f"minium://action?do=remove_bookmark&url={safe_url}"

            icon_b64 = item.get("icon", "")
            if icon_b64:
                icon_html = f'<img class="item-icon" src="data:image/png;base64,{icon_b64}">'
            else:
                icon_html = svg_icon

            items_html += f"""
            <div class="list-item">
                <a href="{item['url']}" class="item-main">
                    {icon_html}
                    <div class="item-text">
                        <span class="item-title">{item['title']}</span>
                        <span class="item-url">{item['url']}</span>
                    </div>
                </a>
                <a href="{remove_url}" class="btn-remove" title="Remove Bookmark">✕</a>
            </div>
            """

    html = html.replace("__BOOKMARKS_LIST__", items_html)
    return html

def get_history_html(history_list: list) -> str:
    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""
    logo_tag = f'<img src="data:image/png;base64,{b64}">' if b64 else ""

    html = HISTORY_HTML_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__FAVICON_TAG__", favicon_tag).replace("__LOGO_TAG__", logo_tag)

    if not history_list:
        items_html = '<div class="empty">No history recorded yet. Tried browsing yet?</div>'
    else:
        items_html = ""
        svg_icon = '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960" width="24px" fill="#e3e3e3"><path d="M480-120q-138 0-240.5-91.5T122-440h82q14 104 92.5 172T480-200q117 0 198.5-81.5T760-480q0-117-81.5-198.5T480-760q-69 0-129 32t-101 88h110v80H120v-240h80v94q51-64 124.5-99T480-840q75 0 140.5 28.5t114 77q48.5 48.5 77 114T840-480q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T480-120Zm112-192L440-464v-216h80v184l128 128-56 56Z"/></svg>'

        for item in reversed(history_list):
            items_html += f"""
            <a href="{item['url']}" class="list-item">
                <div class="item-main">
                    {svg_icon}
                    <div class="item-text">
                        <span class="item-title">{item['title']}</span>
                        <span class="item-url">{item['url']}</span>
                    </div>
                </div>
                <span class="item-time">{item['time']}</span>
            </a>
            """

    html = html.replace("__HISTORY_LIST__", items_html)
    return html
