import json
import urllib.parse
import urllib.request
from threading import Thread

from PySide6.QtCore import QObject, Signal, QTimer
from config import PHISH_CACHE, BYPASSED_PHISH_URLS, PHISHTANK_API_KEY

class PhishTankService(QObject):
    phish_found = Signal(object, str)

    def check_url_async(self, view, url_str: str):
        if url_str in BYPASSED_PHISH_URLS:
            return

        if url_str in PHISH_CACHE:
            is_phish, _ = PHISH_CACHE[url_str]
            if is_phish:
                QTimer.singleShot(0, lambda: self.phish_found.emit(view, url_str))
            return

        def worker():
            try:
                endpoint = "https://checkurl.phishtank.com/checkurl/"
                if PHISHTANK_API_KEY != "[PTAPIKEY]":
                    data = urllib.parse.urlencode({
                        "url": url_str,
                        "format": "json",
                        "app_key": PHISHTANK_API_KEY
                    }).encode("utf-8")
                else:
                    data = urllib.parse.urlencode({
                        "url": url_str,
                        "format": "json"
                    }).encode("utf-8")

                req = urllib.request.Request(
                    endpoint,
                    data=data,
                    headers={
                        "User-Agent": "phishtank/Minium 0.1",
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )

                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                    results = payload.get("results", {})
                    is_phish = bool(results.get("in_database") and results.get("valid"))

                    PHISH_CACHE[url_str] = (is_phish, results)
                    if is_phish:
                        self.phish_found.emit(view, url_str)
            except Exception as e:
                pass

        Thread(target=worker, daemon=True).start()

PHISHTANK_SERVICE = PhishTankService()
