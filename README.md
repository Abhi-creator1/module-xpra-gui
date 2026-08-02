# ROS2 GUI Viewer - edrys-Lite Module

Streams ROS2 GUI applications (rviz2, rqt_graph, Gazebo) from a station PC to remote students via WebRTC video, with full mouse and keyboard interactivity.

## How It Works

```
Student Browser                     Station Browser                    Docker Container
+-----------------------+           +-----------------------+          +------------------+
| module (student mode) |           | module (station mode) |          | Xvfb + xpra      |
|                       |  WebRTC   |                       |          |                  |
| <video> display      <-----------+ getDisplayMedia()     |          | rviz2 / rqt      |
|                       |  stream   | captures xpra tab     |          |                  |
| mouse/keyboard events |  Edrys    | Edrys.onMessage()     |  HTTP    | input_server.py  |
| --------------------->| messages  | relay via fetch() --->|  POST    | xdotool inject   |
+-----------------------+           +-----------------------+          +------------------+
```

1. **Video**: Station captures the xpra browser tab via `getDisplayMedia()`, streams via `Edrys.sendStream()` (WebRTC). Students receive via `Edrys.onStream()`.
2. **Input**: Students capture mouse/keyboard events, send via `Edrys.sendMessage()`. Station relays to `input_server.py` inside Docker, which injects into the X display via `xdotool`.

## Prerequisites

- Docker container running Xvfb + xpra + your ROS2 GUI apps
- `xdotool` installed in the container (`apt-get install xdotool`)
- `flask` and `flask-cors` installed in the container (`pip install flask flask-cors`)
- `input_server.py` running inside the container

## Setup

### 1. Docker Container Changes

Add to your Dockerfile:

```dockerfile
RUN apt-get update && apt-get install -y xdotool && rm -rf /var/lib/apt/lists/*
```

Copy the input server into the container and start it in your entrypoint:

```bash
python3 /path/to/input_server.py &
```

### 2. Edrys Classroom Configuration

Add this module to your classroom with these settings:

**Module URL**: `https://Abhi-creator1.github.io/module-xpra-gui/`

**Station Config** (optional):
```yaml
inputServer: "http://localhost:5001"    # Input server URL
resolution: "1280x800"                  # Must match your Xvfb resolution
streamName: "ros2-gui"                  # Stream identifier
```

### 3. Usage

**Station operator**:
1. Open xpra at `http://localhost:14500/?floating_menu=no` in a browser tab
2. Open the edrys classroom in station mode
3. Click "Share Screen" in the module
4. Select the xpra browser tab in the screen picker
5. Students can now see and interact with the GUI

**Remote student**:
1. Open the edrys classroom link
2. The video stream appears automatically when the station is sharing
3. Click on the video to focus, then use mouse and keyboard to interact

## Configuration

### Environment Variables (input_server.py)

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY` | `:100` | X display to inject input into |
| `XVFB_WIDTH` | `1280` | Xvfb framebuffer width |
| `XVFB_HEIGHT` | `800` | Xvfb framebuffer height |
| `INPUT_PORT` | `5001` | HTTP server port |

### Module Config (edrys stationConfig)

| Key | Default | Description |
|-----|---------|-------------|
| `inputServer` | `http://localhost:5001` | URL of the input injection server |
| `resolution` | `1280x800` | Xvfb resolution (WxH) |
| `streamName` | `ros2-gui` | WebRTC stream identifier |

## Input Event Protocol

Events sent from student to station via `Edrys.sendMessage('gui-input', payload)`:

```js
// Mouse (coordinates normalized to 0.0-1.0)
{ type: 'mousemove', nx: 0.5, ny: 0.3 }
{ type: 'mousedown', nx: 0.5, ny: 0.3, button: 1 }   // 1=left, 2=middle, 3=right
{ type: 'mouseup',   nx: 0.5, ny: 0.3, button: 1 }
{ type: 'scroll',    nx: 0.5, ny: 0.3, deltaY: 100 }

// Keyboard
{ type: 'keydown', key: 'a', code: 'KeyA', ctrlKey: false, shiftKey: false, altKey: false }
{ type: 'keyup',   key: 'a', code: 'KeyA', ctrlKey: false, shiftKey: false, altKey: false }
```

## Tips

- Use `?floating_menu=no` when opening xpra to hide its toolbar for better coordinate accuracy
- The module accounts for `object-fit: contain` letterboxing when normalizing coordinates
- Mousemove events are throttled to ~30fps to avoid flooding the P2P channel
- Escape and F11 keys are not captured (they pass through to the browser)

## Files

- `index.html` - The edrys module (station + student logic)
- `input_server.py` - Flask HTTP server for Docker (receives events, injects via xdotool)
- `module.json` - Module metadata
