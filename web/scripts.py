import os
import glob
from config import BASE_DIR
from PySide6.QtWebEngineCore import QWebEngineScript

USERSCRIPTS_DIR = os.path.join(BASE_DIR, "userscripts")

dark_scrollbar_script = QWebEngineScript()
dark_scrollbar_script.setName("DarkScrollbars")
dark_scrollbar_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
dark_scrollbar_script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
dark_scrollbar_script.setRunsOnSubFrames(True)
dark_scrollbar_script.setSourceCode("""
    (function() {
        if (document.getElementById('minium-dark-scrollbars')) return;
        const css = `
            * {
                scrollbar-color: #262938 #0b0c12 !important;
            }
            ::-webkit-scrollbar {
                width: 10px !important;
                height: 10px !important;
                background: #0b0c12 !important;
            }
            ::-webkit-scrollbar-track {
                background: #0b0c12 !important;
            }
            ::-webkit-scrollbar-thumb {
                background-color: #262938 !important;
                border-radius: 5px !important;
                border: 2px solid #0b0c12 !important;
            }
            ::-webkit-scrollbar-thumb:hover {
                background-color: #3b4058 !important;
            }
            ::-webkit-scrollbar-corner {
                background: #0b0c12 !important;
            }
        `;
        const style = document.createElement('style');
        style.id = 'minium-dark-scrollbars';
        style.textContent = css;
        (document.head || document.documentElement).appendChild(style);
    })();
""")

cosmetic_script = QWebEngineScript()
cosmetic_script.setName("CosmeticAdblock")
cosmetic_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
cosmetic_script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
cosmetic_script.setRunsOnSubFrames(True)
cosmetic_script.setSourceCode("""
    (function() {
        if (document.getElementById('minium-cosmetic-adblock')) return;
        const css = `
            .adbox, .adsbox, .banner_ads, .textads,
            .advertisement, .ad-container, .ad-banner,
            ins.adsbygoogle, [id^="google_ads_iframe"],
            [class*="sponsored-post"], [data-ad-client],
            .trc_rbox_div, .outbrain_widget {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                width: 0 !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }
        `;
        const style = document.createElement('style');
        style.id = 'minium-cosmetic-adblock';
        style.textContent = css;
        (document.head || document.documentElement).appendChild(style);
    })();
""")

stealth_script = QWebEngineScript()
stealth_script.setName("StealthPatch")
stealth_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
stealth_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
stealth_script.setRunsOnSubFrames(True)
stealth_script.setSourceCode("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    try { delete navigator.__proto__.webdriver; } catch(e) {}
    if (!window.chrome) {
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    }
""")

def get_userscripts():
    scripts = []
    os.makedirs(USERSCRIPTS_DIR, exist_ok=True)

    for file_path in glob.glob(os.path.join(USERSCRIPTS_DIR, "*.user.js")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            s = QWebEngineScript()
            s.setName(os.path.basename(file_path))
            s.setSourceCode(code)
            s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
            s.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            s.setRunsOnSubFrames(True)
            scripts.append(s)
            print(f"[+] scripts: loaded UserScript: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[!] scripts: error loading {file_path}: {e}")

    for file_path in glob.glob(os.path.join(USERSCRIPTS_DIR, "*.user.css")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                css = f.read().replace("`", "\\`").replace("\\", "\\\\")
            s = QWebEngineScript()
            s.setName(os.path.basename(file_path))
            s.setSourceCode(f"""
                (function() {{
                    const style = document.createElement('style');
                    style.id = 'minium-usercss-{os.path.basename(file_path)}';
                    style.textContent = `{css}`;
                    (document.head || document.documentElement).appendChild(style);
                }})();
            """)
            s.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
            s.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
            s.setRunsOnSubFrames(True)
            scripts.append(s)
            print(f"[+] scripts: loaded UserCSS: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[!] scripts: error loading {file_path}: {e}")

    return scripts

def get_all_user_scripts():
    base_scripts = [dark_scrollbar_script, cosmetic_script, stealth_script]
    return base_scripts + get_userscripts()
