#!/usr/bin/env python3
"""
Downloads the XPRA server's own bundled HTML5 client files.
Run this from Windows PowerShell (with your conda base env) or WSL,
as long as it can reach the Jetson's IP.

Usage:
    python fetch_client.py

This guarantees the client version matches the Jetson's XPRA server exactly,
avoiding protocol/framing mismatches that occur when mixing a client pulled
from a different source (e.g. GitHub master) with an older/newer server.
"""

import os
import urllib.request
import urllib.error

SERVER = "http://192.168.137.108:14500"
OUTPUT_DIR = "client"

FILES = """clipboard.html
connect.html
crypto.html
css/client.css
css/connect.css
css/icon.css
css/menu-skin.css
css/menu.css
css/simple-keyboard.css
css/simple-keyboard.css.map
css/slick.css
css/spinner.css
default-settings.txt
digest.html
favicon.ico
favicon.png
icons/authentication.png
icons/close.png
icons/default_cursor.png
icons/empty.png
icons/eye-slash.png
icons/eye.png
icons/fullscreen.png
icons/materialicons-regular.ttf
icons/materialicons-regular.woff
icons/materialicons-regular.woff2
icons/maximize.png
icons/minimize.png
icons/noicon.png
icons/unfullscreen.png
icons/xpra-logo.png
index.html
js/Client.js
js/Constants.js
js/DecodeWorker.js
js/ImageDecoder.js
js/Keycodes.js
js/MediaSourceUtil.js
js/Menu.js
js/MenuCustom.js
js/Notifications.js
js/OffscreenDecodeWorker.js
js/OffscreenDecodeWorkerHelper.js
js/Protocol.js
js/RgbHelpers.js
js/Utilities.js
js/VideoDecoder.js
js/WebTransport.js
js/Window.js
js/lib/FileSaver.js
js/lib/StreamSaver.js
js/lib/aurora/aac.js
js/lib/aurora/aurora-xpra.js
js/lib/aurora/aurora.js
js/lib/aurora/flac.js
js/lib/aurora/mp3.js
js/lib/brotli_decode.js
js/lib/detect-zoom.js
js/lib/hmac.js
js/lib/jquery-transform-draggable.js
js/lib/jquery-ui.js
js/lib/jquery.ba-throttle-debounce.js
js/lib/jquery.js
js/lib/jsmpeg.js
js/lib/lz4.js
js/lib/rencode.js
js/lib/simple-keyboard.js
js/lib/slick.js
js/lib/web-streams-ponyfill.es6.js
mitm.html
sw.js""".splitlines()

def main():
    ok, failed = 0, []
    for rel_path in FILES:
        rel_path = rel_path.strip()
        if not rel_path:
            continue
        url = f"{SERVER}/{rel_path}"
        dest = os.path.join(OUTPUT_DIR, rel_path)
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"OK   {rel_path}")
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"MISS {rel_path} (HTTP {e.code}) -- server may not have this file, skipping")
            failed.append(rel_path)
        except Exception as e:
            print(f"FAIL {rel_path}: {e}")
            failed.append(rel_path)

    print(f"\nDone. {ok} downloaded, {len(failed)} failed/missing.")
    if failed:
        print("Failed/missing files (may be OK if this server version doesn't include them):")
        for f in failed:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
