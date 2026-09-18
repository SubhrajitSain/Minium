from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtWebEngineCore import QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob

from templates import get_new_tab_html, get_settings_html, get_history_html, get_bookmarks_html
from config import GLOBAL_HISTORY, GLOBAL_BOOKMARKS

class MiniumSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, profile, browser, parent=None):
        super().__init__(parent)
        self.browser = browser

    def requestStarted(self, job: QWebEngineUrlRequestJob):
        url = job.requestUrl().toString()
        html = ""

        if "newtab" in url:
            html = get_new_tab_html()
        elif "settings" in url:
            html = get_settings_html(self.browser.prefs)
        elif "history" in url:
            html = get_history_html(GLOBAL_HISTORY)
        elif "bookmarks" in url:
            html = get_bookmarks_html(GLOBAL_BOOKMARKS)
        else:
            job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
            return

        buf = QBuffer(job)
        buf.setData(QByteArray(html.encode("utf-8")))
        buf.open(QIODevice.OpenModeFlag.ReadOnly)
        job.reply(b"text/html", buf)
