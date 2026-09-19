# 🌟 Minium Updates and Changelog

## v0.1.9

* Highly enhanced Minium's Adblock system from 81 to 100 on `adblock-tester.com`.

## v0.1.8

* Fixed 2 bugs due to undefined imports in `browser.py` and `address_bar.py`.

## v0.1.7

* Added Maxium mode, which makes data persist after the browser closes.
* Added a preferences system using a `prefs.json` file.
* Made the new tab more customizable: background and shortcuts.
* Added bookmarks and browsing history pages.
* Added a settings page with items from the menu moved there.
* Made a proper `requirements.txt` file for easy dependency installation.
* Added an extra password manager.
* ...and maybe some more that I missed.

## v0.1.6

* Made `get_pid_memory()` in `utils.py` compatible with Windows.
* Minium should now be cross-compatible with Linux and Windows.

## v0.1.5

* Fixed tab switching not working after opening Dev Tools.
* Fixed an edge case regarding trailing `/` during HTTPS upgrade attempts.
* Fixed an edge case related to user permissions during updates.
* Added `ESC` detection to the `Ctrl+F` find tool to close the tool.
* Fixed a bug where the PiP was kept open when the browser was closing.

## v0.1.4

* Extended Linux & Windows cross compatability.
* Added all files in `manifest.json`.
* Make a script to auto-generate the manifest for the `VERSION` in `config.py`.

## v0.1.3

* Fixed a bug where the Site Blocked page did not show up.
* Fixed a bug where the Back to safety button reloaded the same bad site.
* Fixed another bug which makes the tabs reappear when exitting fullscreen mode when tabs are hidden.
* Added `VERSION` to adblock's and phishing detector's UA.
* Made checks show `Checking for updates` and updates show `Updating` separately.

## All versions prior

Initial publish and update system setup.
