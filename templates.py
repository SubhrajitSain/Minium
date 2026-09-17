import os

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
        html, body {
            background-color: #050608;
            color: #f1f3f8;
            font-family: 'Google Sans Flex', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            user-select: none;
            overflow: hidden;
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
        .logo {
            width: 48px;
            height: 48px;
            margin-right: 6px;
            object-fit: contain;
        }
        .title {
            font-family: 'Google Sans Flex', sans-serif;
            font-size: 48px;
            font-weight: 700;
            letter-spacing: -1px;
            color: #f1f3f8;
        }
        .search-box {
            position: relative;
            width: 100%;
            display: flex;
            align-items: center;
        }
        .search-icon-wrap {
            position: absolute;
            left: 16px;
            width: 16px;
            height: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
        }
        .search-icon-wrap svg {
            width: 16px;
            height: 16px;
            fill: #64748b;
            transition: fill 0.15s ease;
        }
        .search-box input {
            font-family: 'Google Sans Flex', sans-serif;
            width: 100%;
            height: 38px;
            padding: 0 24px 0 44px;
            font-size: 13.5px;
            font-weight: 500;
            border: 1px solid #242633;
            border-radius: 19px;
            outline: none;
            background-color: #161720;
            color: #f1f3f8;
            transition: border-color 0.15s ease, background-color 0.15s ease;
        }
        .search-box input::placeholder {
            font-family: 'Google Sans Flex', sans-serif;
            color: #5d6173;
            font-weight: 400;
        }
        .search-box input:focus {
            border-color: #3b82f6;
            background-color: #191a26;
        }
        .search-box:focus-within .search-icon-wrap svg {
            fill: #3b82f6;
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
                __SEARCH_ICON_SVG__
            </div>
            <input
                type="text"
                name="q"
                placeholder="Search with DuckDuckGo or enter address..."
                autofocus
                autocomplete="off"
            />
        </form>
        <script>
            function focusSearchInput() {
                const inp = document.querySelector('input[name="q"]');
                if (inp) {
                    inp.focus();
                }
            }
            window.addEventListener('DOMContentLoaded', focusSearchInput);
            window.addEventListener('load', focusSearchInput);
            window.addEventListener('focus', focusSearchInput);
        </script>
    </div>
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

def get_new_tab_html() -> str:
    search_svg_path = os.path.join(ICON_DIR, "search.svg")
    search_svg = ""
    if os.path.exists(search_svg_path):
        try:
            with open(search_svg_path, "r", encoding="utf-8") as f:
                search_svg = f.read().strip()
        except Exception:
            pass

    b64 = get_minium_icon_b64()
    favicon_tag = f'<link rel="icon" type="image/png" href="data:image/png;base64,{b64}">' if b64 else ""
    logo_tag = f'<img class="logo" src="data:image/png;base64,{b64}" alt="Minium Logo">' if b64 else ""

    html = NEW_TAB_HTML_TEMPLATE.replace("__FONT_FACE_CSS__", get_font_face_css())
    html = html.replace("__SEARCH_ICON_SVG__", search_svg)
    html = html.replace("__FAVICON_TAG__", favicon_tag)
    html = html.replace("__LOGO_TAG__", logo_tag)
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
