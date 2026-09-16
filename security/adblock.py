import os
import time
import urllib.request
from threading import Thread

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
)

from config import (
    CACHE_DIR,
    ADBLOCK_CACHE_FILE,
    ADBLOCK_DOMAINS,
    BYPASSED_DOMAINS,
    PHISH_CACHE,
)

class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.stats = {}

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if not self.enabled:
            return

        if info.requestUrl().scheme() in (
            "devtools", "minium", "chrome", "chrome-error",
            "chrome-extension", "data", "file", "blob", "qrc", "javascript"
        ):
            return

        req_url = info.requestUrl().toString()
        if req_url in PHISH_CACHE and PHISH_CACHE[req_url][0]:
            return

        host = info.requestUrl().host().lower()
        path = info.requestUrl().path().lower()
        first_party = info.firstPartyUrl().host().lower()

        if host in BYPASSED_DOMAINS or first_party in BYPASSED_DOMAINS:
            return

        if "cloudflare" in host or "/cdn-cgi/" in path or "turnstile" in path:
            return

        first_party = info.firstPartyUrl().host().lower()
        if first_party and first_party not in self.stats:
            self.stats[first_party] = {"ads": 0, "trackers": 0}

        if path.endswith(("/pagead.js", "/ads.js", "/ad.js", "/pagead2.js", "/show_ads.js", "/prebid.js")):
            if first_party:
                self.stats[first_party]["ads"] += 1
            info.block(True)
            return

        if "/google-analytics.com/" in path or "/gtag/js" in path:
            if first_party:
                self.stats[first_party]["trackers"] += 1
            info.block(True)
            return

        if not host:
            return

        parts = host.split(".")
        for i in range(len(parts) - 1):
            sub = ".".join(parts[i:])
            if sub in ADBLOCK_DOMAINS:
                if first_party:
                    if "analytics" in sub or "tracker" in sub or "telemetry" in sub or "pixel" in sub:
                        self.stats[first_party]["trackers"] += 1
                    else:
                        self.stats[first_party]["ads"] += 1
                info.block(True)
                return

class AdBlockService(QObject):
    updated = Signal(str)

ADBLOCK_SERVICE = AdBlockService()

def parse_blocklist_line(line: str) -> str:
    line = line.strip()
    if not line or line.startswith(("#", "!", ";", "[")):
        return ""
    line = line.split("#")[0].strip()

    if line.startswith(("server=/", "local=/", "address=/")):
        parts = line.split("/")
        if len(parts) >= 2 and "." in parts[1]:
            return parts[1].strip().lower()
        return ""

    if line.startswith("/"):
        return ""

    if line.startswith("||"):
        line = line[2:].split("^")[0].split("/")[0].strip()
        return line.lower()

    parts = line.split()
    if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
        d = parts[1].strip()
    elif len(parts) == 1:
        d = parts[0].strip()
    else:
        return ""

    if "." in d and d not in ("localhost", "local", "broadcasthost"):
        return d.lower()
    return ""

def start_adblock_fetch(on_complete_callback=None):
    print("[*] adblock: starting update checks...")
    global ADBLOCK_DOMAINS

    os.makedirs(CACHE_DIR, exist_ok=True)
    needs_update = True
    SEVEN_DAYS = 7 * 24 * 3600

    if os.path.exists(ADBLOCK_CACHE_FILE):
        print("[i] adblock: found cache file.")
        try:
            with open(ADBLOCK_CACHE_FILE, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("[ Minium Adblock Cache ] Last-Updated:"):
                    ts_part = first_line.split(":", 1)[1].strip().split("|")[0].strip()
                    last_updated = float(ts_part)
                    if time.time() - last_updated < SEVEN_DAYS:
                        print("[i] adblock: cache was updated in < 7 days ago, not updating.")
                        needs_update = False

                f.seek(0)
                cached = set(
                    line.strip() for line in f
                    if line.strip() and not line.startswith("[ Minium Adblock Cache ]") and not line.startswith("#")
                )
                if cached:
                    ADBLOCK_DOMAINS = cached
        except Exception:
            print("[!] adblock: exception occured during reading cache, will update.")
            needs_update = True

    if not needs_update and ADBLOCK_DOMAINS:
        print("[*] adblock: cache restored, update not required, calling callback in 1s...")
        if on_complete_callback:
            QTimer.singleShot(1000, on_complete_callback)
        return

    def fetch():
        print("[*] adblock: starting update procedure...")
        global ADBLOCK_DOMAINS
        sources = [
            "https://raw.githubusercontent.com/d3ward/toolz/master/src/d3host.txt",
            "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/ultimate.txt",
            "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/tif.medium.txt",
            "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
            "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
            "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=nohtml&showintro=0&mimetype=plaintext",
            "https://raw.githubusercontent.com/AnudeepND/blacklist/master/adservers.txt",
            "https://adaway.org/hosts.txt"
        ]

        new_domains = set()
        for s in sources:
            print("[*] adblock: downloading:", s)
            try:
                req = urllib.request.Request(s, headers={'User-Agent': 'Mozilla/5.0 Minium/0.1'})
                with urllib.request.urlopen(req, timeout=15) as res:
                    for line in res.read().decode('utf-8', errors='ignore').splitlines():
                        dom = parse_blocklist_line(line)
                        if dom:
                            new_domains.add(dom)
            except Exception:
                print("[!] adblock: exception during download, link is down?")
                continue

        if len(new_domains) > 1000000:
            print(f"[*] adblock: saving {len(new_domains)} domains in the cache...")
            ADBLOCK_DOMAINS = new_domains
            try:
                now = int(time.time())
                readable = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                with open(ADBLOCK_CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(f"[ Minium Adblock Cache ] Last-Updated: {now} | {readable}\n")
                    f.write("\n".join(sorted(new_domains)))

                ADBLOCK_SERVICE.updated.emit(f"Minium Adblock blocklists updated, {len(new_domains):,} blocked domains.")

                if on_complete_callback:
                    print("[s] adblock: update completed, calling callback in 4.5 s.")
                    QTimer.singleShot(4500, on_complete_callback)
            except Exception:
                print("[!] adblock: exception while saving to disk, possible corruption.")
                pass

    Thread(target=fetch, daemon=True).start()
