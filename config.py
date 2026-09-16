import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
ICON_DIR = os.path.join(BASE_DIR, "icons")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

WINDOWS = []

ADBLOCK_CACHE_FILE = os.path.join(CACHE_DIR, "adblock.minium")
ADBLOCK_DOMAINS = set()
PHISH_CACHE = {}
BYPASSED_PHISH_URLS = set()
BYPASSED_DOMAINS = set()
HTTPS_UPGRADE_ATTEMPTS = set()
HTTP_FALLBACK_URLS = set()

VERSION = "0.1"
GITHUB_REPO = "SubhrajitSain/Minium"
RAW_REPO_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

# set phishtank.org api key here to lower limits
PHISHTANK_API_KEY = "[PTAPIKEY]"
