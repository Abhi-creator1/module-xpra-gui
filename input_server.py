#!/usr/bin/env python3
"""
input_server.py - HTTP input injection server for edrys-Lite ROS2 GUI module.

Runs inside the Docker container alongside xpra. Receives normalized
mouse/keyboard events from the station's browser module and injects them
into the Xvfb display via xdotool.

Usage:
    python3 input_server.py

Environment variables:
    DISPLAY       X display to inject into (default: :100)
    XVFB_WIDTH    Virtual framebuffer width in pixels (default: 1280)
    XVFB_HEIGHT   Virtual framebuffer height in pixels (default: 800)
    INPUT_PORT    Port to listen on (default: 5001)

Requirements:
    - flask, flask-cors (pip)
    - xdotool (apt-get install xdotool)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import logging

app = Flask(__name__)
CORS(app)


@app.after_request
def add_private_network_access_headers(response):
    """Handle Chrome Private Network Access (PNA) preflight requirements.
    HTTPS pages fetching http://localhost need this header in the response."""
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Private-Network'] = 'true'
    response.headers['Access-Control-Allow-Private-Network'] = 'true'
    return response

# ---- Configuration from environment ----
DISPLAY = os.environ.get('DISPLAY', ':100')
WIDTH = int(os.environ.get('XVFB_WIDTH', '1280'))
HEIGHT = int(os.environ.get('XVFB_HEIGHT', '800'))
PORT = int(os.environ.get('INPUT_PORT', '5001'))

# Environment passed to xdotool so it targets the correct display
XDO_ENV = {**os.environ, 'DISPLAY': DISPLAY}

# ---- JavaScript key name -> xdotool key name mapping ----
JS_TO_XDO_KEY = {
    # Navigation
    'Enter': 'Return',
    'Backspace': 'BackSpace',
    'Tab': 'Tab',
    'Escape': 'Escape',
    'Delete': 'Delete',
    'Insert': 'Insert',
    'Home': 'Home',
    'End': 'End',
    'PageUp': 'Prior',
    'PageDown': 'Next',

    # Arrow keys
    'ArrowUp': 'Up',
    'ArrowDown': 'Down',
    'ArrowLeft': 'Left',
    'ArrowRight': 'Right',

    # Modifiers
    'Control': 'Control_L',
    'Shift': 'Shift_L',
    'Alt': 'Alt_L',
    'Meta': 'Super_L',
    'CapsLock': 'Caps_Lock',
    'NumLock': 'Num_Lock',
    'ScrollLock': 'Scroll_Lock',

    # Function keys
    'F1': 'F1', 'F2': 'F2', 'F3': 'F3', 'F4': 'F4',
    'F5': 'F5', 'F6': 'F6', 'F7': 'F7', 'F8': 'F8',
    'F9': 'F9', 'F10': 'F10', 'F11': 'F11', 'F12': 'F12',

    # Whitespace
    ' ': 'space',

    # Misc
    'ContextMenu': 'Menu',
    'PrintScreen': 'Print',
    'Pause': 'Pause',
}


def xdotool(*args):
    """Run an xdotool command targeting the configured DISPLAY."""
    cmd = ['xdotool'] + list(args)
    try:
        subprocess.run(cmd, env=XDO_ENV, timeout=2, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        logging.warning('xdotool timed out: %s', ' '.join(cmd))
    except Exception as e:
        logging.warning('xdotool error: %s', e)


def map_key(js_key):
    """Map a JavaScript key name to the corresponding xdotool key name."""
    if js_key in JS_TO_XDO_KEY:
        return JS_TO_XDO_KEY[js_key]
    # Single printable characters are used as-is by xdotool
    if len(js_key) == 1:
        return js_key
    # Fallback: pass through and hope xdotool recognises it
    return js_key


def clamp_coords(nx, ny):
    """Convert normalized [0,1] coordinates to pixel coordinates."""
    x = max(0, min(WIDTH - 1, int(nx * WIDTH)))
    y = max(0, min(HEIGHT - 1, int(ny * HEIGHT)))
    return str(x), str(y)


@app.route('/input', methods=['POST'])
def handle_input():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'no JSON body'}), 400

    event_type = data.get('type', '')

    # ---- Mouse events ----
    if event_type == 'mousemove':
        x, y = clamp_coords(data.get('nx', 0), data.get('ny', 0))
        xdotool('mousemove', x, y)

    elif event_type == 'mousedown':
        x, y = clamp_coords(data.get('nx', 0), data.get('ny', 0))
        btn = str(data.get('button', 1))
        xdotool('mousemove', x, y)
        xdotool('mousedown', btn)

    elif event_type == 'mouseup':
        x, y = clamp_coords(data.get('nx', 0), data.get('ny', 0))
        btn = str(data.get('button', 1))
        xdotool('mousemove', x, y)
        xdotool('mouseup', btn)

    elif event_type == 'dblclick':
        x, y = clamp_coords(data.get('nx', 0), data.get('ny', 0))
        btn = str(data.get('button', 1))
        xdotool('mousemove', x, y, 'click', '--repeat', '2', btn)

    elif event_type == 'scroll':
        x, y = clamp_coords(data.get('nx', 0), data.get('ny', 0))
        delta_y = data.get('deltaY', 0)
        # Most browsers send deltaY in multiples of ~100; normalize
        clicks = max(1, abs(int(delta_y / 100))) if delta_y != 0 else 0
        if clicks == 0:
            return jsonify({'ok': True})
        # xdotool: button 4 = scroll up, button 5 = scroll down
        scroll_btn = '5' if delta_y > 0 else '4'
        xdotool('mousemove', x, y)
        xdotool('click', '--repeat', str(clicks), scroll_btn)

    # ---- Keyboard events ----
    elif event_type == 'keydown':
        key = map_key(data.get('key', ''))
        if key:
            xdotool('keydown', key)

    elif event_type == 'keyup':
        key = map_key(data.get('key', ''))
        if key:
            xdotool('keyup', key)

    else:
        return jsonify({'error': f'unknown event type: {event_type}'}), 400

    return jsonify({'ok': True})


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint -- also reports current config."""
    return jsonify({
        'status': 'ok',
        'display': DISPLAY,
        'resolution': f'{WIDTH}x{HEIGHT}',
        'port': PORT
    })


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [input_server] %(levelname)s: %(message)s'
    )
    logging.info('Starting input server on port %d (DISPLAY=%s, %dx%d)',
                 PORT, DISPLAY, WIDTH, HEIGHT)
    app.run(host='0.0.0.0', port=PORT)
