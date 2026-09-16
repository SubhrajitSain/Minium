from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtWebEngineCore import QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob

from templates import get_new_tab_html

class MiniumSchemeHandler(QWebEngineUrlSchemeHandler):
    def requestStarted(self, job: QWebEngineUrlRequestJob):
        url = job.requestUrl().toString()
        if "newtab" in url:
            html = get_new_tab_html().encode("utf-8")
            buf = QBuffer(job)
            buf.setData(QByteArray(html))
            buf.open(QIODevice.OpenModeFlag.ReadOnly)
            job.reply(b"text/html", buf)
        else:
            job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
