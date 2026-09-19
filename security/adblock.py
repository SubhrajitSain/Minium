import os
import re
import time
import urllib.request
from threading import Thread, Lock

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
    WINDOWS,
    VERSION
)

EASYLIST_PATTERNS = []
EASYLIST_EXCEPTIONS = []
EASYLIST_LOCK = Lock()


def matches_domain_option(first_party: str, domain_opt: str) -> bool:
    if not domain_opt or not first_party:
        return True
    domains = domain_opt.split("|")
    for d in domains:
        if d.startswith("~"):
            target = d[1:].lower()
            if first_party == target or first_party.endswith("." + target):
                return False
        else:
            target = d.lower()
            if first_party == target or first_party.endswith("." + target):
                return True
    if all(d.startswith("~") for d in domains):
        return True
    return False


def parse_easylist_line(line: str):
    line = line.strip()
    if not line or line.startswith(("!", "[", "#")):
        return None, None

    if "##" in line or "#@#" in line or "#?#" in line:
        return None, None

    is_exception = False
    if line.startswith("@@"):
        is_exception = True
        line = line[2:]

    options = {}
    if "$" in line:
        line, opt_str = line.split("$", 1)
        for opt in opt_str.split(","):
            opt = opt.strip()
            if opt == "third-party":
                options["third_party"] = True
            elif opt in ("~third-party", "first-party"):
                options["third_party"] = False
            elif opt.startswith("domain="):
                options["domain"] = opt[7:]

    line = line.strip()
    if not line:
        return None, None

    if line.startswith("||") and line.endswith("^") and "/" not in line and "*" not in line:
        domain = line[2:-1].strip().lower()
        if domain and not options and not is_exception:
            return "domain", domain

    parts = line.split()
    if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
        d = parts[1].strip().lower()
        if "." in d and d not in ("localhost", "local", "broadcasthost") and not is_exception:
            return "domain", d

    if len(parts) == 1 and not is_exception and not options:
        if not any(c in line for c in ("*", "^", "|", "/", ":", "?", "=")):
            d = line.lower()
            if "." in d and d not in ("localhost", "local", "broadcasthost"):
                return "domain", d

    pattern = line
    has_domain_anchor = pattern.startswith("||")
    has_start_anchor = pattern.startswith("|") and not has_domain_anchor

    if has_domain_anchor:
        pattern = pattern[2:]
    elif has_start_anchor:
        pattern = pattern[1:]

    has_end_anchor = pattern.endswith("|")
    if has_end_anchor:
        pattern = pattern[:-1]

    escaped = re.escape(pattern)
    escaped = escaped.replace(r"\*", ".*").replace(r"\^", r"(?:[^a-zA-Z0-9_\.-]|$)")

    if has_domain_anchor:
        escaped = r"^https?://(?:[a-zA-Z0-9\-]+\.)*" + escaped
    elif has_start_anchor:
        escaped = r"^" + escaped

    if has_end_anchor:
        escaped = escaped + r"$"

    try:
        compiled = re.compile(escaped, re.IGNORECASE)
        rule_type = "exception" if is_exception else "pattern"
        return rule_type, (compiled, options)
    except re.error:
        return None, None


def load_rules_from_lines(lines):
    print("[*] adblock: getting rules from lines...")
    domains = set()
    patterns = []
    exceptions = []

    for line in lines:
        rtype, data = parse_easylist_line(line)
        if rtype == "domain":
            domains.add(data)
        elif rtype == "pattern":
            patterns.append(data)
        elif rtype == "exception":
            exceptions.append(data)

    return domains, patterns, exceptions


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.stats = {}
        self.lock = Lock()

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if not self.enabled:
            return

        scheme = info.requestUrl().scheme()
        if scheme in (
            "devtools", "minium", "chrome", "chrome-error",
            "chrome-extension", "data", "file", "blob", "qrc", "javascript"
        ):
            return

        req_url = info.requestUrl().toString()
        if req_url in PHISH_CACHE and PHISH_CACHE[req_url][0]:
            info.block(True)
            return

        host = info.requestUrl().host().lower()
        if host.startswith("www."):
            host = host[4:]

        path = info.requestUrl().path().lower()
        first_party = info.firstPartyUrl().host().lower()
        if first_party.startswith("www."):
            first_party = first_party[4:]

        if host in BYPASSED_DOMAINS or first_party in BYPASSED_DOMAINS:
            return

        if "cloudflare" in host or "/cdn-cgi/" in path or "turnstile" in path:
            return

        with self.lock:
            if first_party and first_party not in self.stats:
                self.stats[first_party] = {"ads": 0, "trackers": 0}

        is_third_party = False
        if host and first_party:
            is_third_party = (host != first_party and not host.endswith("." + first_party))

        with EASYLIST_LOCK:
            exceptions = list(EASYLIST_EXCEPTIONS)
            patterns = list(EASYLIST_PATTERNS)

        for compiled, options in exceptions:
            if options.get("third_party") is True and not is_third_party:
                continue
            if options.get("third_party") is False and is_third_party:
                continue
            if not matches_domain_option(first_party, options.get("domain", "")):
                continue
            if compiled.search(req_url):
                return

        is_tracker = False
        is_ad = False

        blocked_keywords = [
            "/pagead.js", "/pagead2.js", "/ads.js", "/ad.js", "/show_ads.js",
            "/prebid.js", "google-analytics.com/analytics.js", "/gtag/js",
            "doubleclick.net", "adsystem.", "adserver.", "/tracker.js",
            "/pixel.js", "popunder.js", "popup.js"
        ]

        url_str_lower = req_url.lower()
        for kw in blocked_keywords:
            if kw in url_str_lower:
                if "analytics" in kw or "tracker" in kw or "pixel" in kw:
                    is_tracker = True
                else:
                    is_ad = True
                break

        if is_tracker or is_ad:
            with self.lock:
                if first_party:
                    if is_tracker:
                        self.stats[first_party]["trackers"] += 1
                    else:
                        self.stats[first_party]["ads"] += 1
            info.block(True)
            return

        if not host:
            return

        parts = host.split(".")
        if len(parts) > 1:
            for i in range(len(parts) - 1):
                sub = ".".join(parts[i:])
                if sub in ADBLOCK_DOMAINS:
                    with self.lock:
                        if first_party:
                            if "analytics" in sub or "tracker" in sub or "telemetry" in sub or "pixel" in sub:
                                self.stats[first_party]["trackers"] += 1
                            else:
                                self.stats[first_party]["ads"] += 1
                    info.block(True)
                    return

        for compiled, options in patterns:
            if options.get("third_party") is True and not is_third_party:
                continue
            if options.get("third_party") is False and is_third_party:
                continue
            if not matches_domain_option(first_party, options.get("domain", "")):
                continue
            if compiled.search(req_url):
                with self.lock:
                    if first_party:
                        self.stats[first_party]["ads"] += 1
                info.block(True)
                return


class AdBlockService(QObject):
    updated = Signal(str)
    update_finished = Signal()
    is_connected = False


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

    if on_complete_callback:
        if ADBLOCK_SERVICE.is_connected:
            try:
                ADBLOCK_SERVICE.update_finished.disconnect()
            except Exception:
                pass
        ADBLOCK_SERVICE.update_finished.connect(on_complete_callback)
        ADBLOCK_SERVICE.is_connected = True

    def background_task():
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

                    print("[*] adblock: loading rules, this may take some time...")
                    f.seek(0)
                    cached_lines = [
                        line.strip() for line in f
                        if line.strip() and not line.startswith("[ Minium Adblock Cache ]")
                    ]
                    print("[i] adblock: parsed cached lines.")

                    if cached_lines:
                        c_domains, c_patterns, c_exceptions = load_rules_from_lines(cached_lines)
                        ADBLOCK_DOMAINS.clear()
                        ADBLOCK_DOMAINS.update(c_domains)
                        with EASYLIST_LOCK:
                            EASYLIST_PATTERNS.clear()
                            EASYLIST_PATTERNS.extend(c_patterns)
                            EASYLIST_EXCEPTIONS.clear()
                            EASYLIST_EXCEPTIONS.extend(c_exceptions)
            except Exception:
                print("[!] adblock: exception occurred during reading cache, will update.")
                needs_update = True

        if not needs_update and ADBLOCK_DOMAINS:
            print("[*] adblock: cache restored, update not required, calling callback in 1s...")
            if on_complete_callback:
                time.sleep(1)
                ADBLOCK_SERVICE.update_finished.emit()
            return

        print("[*] adblock: starting update procedure...")
        sources = [
            "https://raw.githubusercontent.com/d3ward/toolz/master/src/d3host.txt",
            "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/ultimate.txt",
            "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/tif.medium.txt",
            "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
            "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
            "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=nohtml&showintro=0&mimetype=plaintext",
            "https://raw.githubusercontent.com/AnudeepND/blacklist/master/adservers.txt",
            "https://adaway.org/hosts.txt",
            "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/easylist.txt",
            "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/easyprivacy.txt",
            "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/easycookie.txt",
            "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/fanboyannoyance.txt",
            "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/antiadblock.txt"
        ]

        new_domains = set()
        new_patterns = []
        new_exceptions = []
        raw_lines_to_cache = []

        for s in sources:
            print("[*] adblock: downloading:", s)
            try:
                req = urllib.request.Request(s, headers={'User-Agent': f'Mozilla/5.0 Minium/{VERSION}'})
                with urllib.request.urlopen(req, timeout=15) as res:
                    lines = res.read().decode('utf-8', errors='ignore').splitlines()
                    for line in lines:
                        rtype, data = parse_easylist_line(line)
                        if rtype == "domain":
                            new_domains.add(data)
                            raw_lines_to_cache.append(data)
                        elif rtype == "pattern":
                            new_patterns.append(data)
                            raw_lines_to_cache.append(line.strip())
                        elif rtype == "exception":
                            new_exceptions.append(data)
                            raw_lines_to_cache.append(line.strip())
            except Exception as e:
                print(f"[!] adblock: exception during download ({s}): {e}")
                continue

        total_rules = len(new_domains) + len(new_patterns)
        if total_rules > 10000:
            print(f"[*] adblock: saving {len(new_domains)} domains and {len(new_patterns)} EasyList patterns to cache...")

            ADBLOCK_DOMAINS.clear()
            ADBLOCK_DOMAINS.update(new_domains)
            with EASYLIST_LOCK:
                EASYLIST_PATTERNS.clear()
                EASYLIST_PATTERNS.extend(new_patterns)
                EASYLIST_EXCEPTIONS.clear()
                EASYLIST_EXCEPTIONS.extend(new_exceptions)

            try:
                now = int(time.time())
                readable = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                with open(ADBLOCK_CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(f"[ Minium Adblock Cache ] Last-Updated: {now} | {readable}\n")
                    f.write("\n".join(raw_lines_to_cache))

                ADBLOCK_SERVICE.updated.emit(f"Minium Adblock blocklists updated, {total_rules:,} total rules.")

                if on_complete_callback:
                    print("[s] adblock: update completed, calling callback in 4.5 s.")
                    if WINDOWS:
                        time.sleep(4.5)
                        ADBLOCK_SERVICE.update_finished.emit()
            except Exception:
                print("[!] adblock: exception while saving to disk, possible corruption.")
                pass

    Thread(target=background_task, daemon=True).start()
