// XPRA initialization for Edrys integration
console.log("[XPRA Init] Starting initialization");

// Global variables for logging (overridden after client init)
var clog = console.log.bind(console);
var cdebug = console.debug.bind(console);
var client = null;

Edrys.onReady(() => {
  console.log("[XPRA Init] Edrys ready");

  const DEFAULT_SERVER = "localhost:14500";
  const serverConfig = Edrys.module?.config?.server || DEFAULT_SERVER;
  const cleaned = serverConfig.replace(/^https?:\/\//, "").replace(/\/.*$/, "").trim();
  const [host, port] = cleaned.split(":");

  // Populate global config that will be read by config-interceptor.js
  window.EDRYS_XPRA_CONFIG = {
    'server': host || 'localhost',
    'port': port || '14500',
    'ssl': 'false',
    'path': '/'
  };

  console.log("[XPRA Init] Configured for:", host + ":" + port);
  console.log("[XPRA Init] Config injected:", window.EDRYS_XPRA_CONFIG);
  console.log("[XPRA Init] WebSocket will connect from origin:", window.location.origin);
});

// Initialize XPRA client when DOM is ready
$(document).ready(function() {
  console.log("[XPRA Init] DOM ready, initializing client");

  // Create convenience wrappers for Utilities functions
  window.getparam = function(prop) {
    return Utilities.getparam(prop);
  };
  window.getboolparam = function(prop, defaultValue) {
    return Utilities.getboolparam(prop, defaultValue);
  };

  // Initialize the client
  try {
    client = init_client();
    if (client) {
      console.log("[XPRA Init] Client initialized, connecting...");
      client.connect();
    } else {
      console.error("[XPRA Init] Failed to initialize client");
    }
  } catch (e) {
    console.error("[XPRA Init] Error initializing client:", e);
  }
});

// Simplified init_client function
function init_client() {
  if (typeof jQuery == 'undefined') {
    alert("jQuery is missing, cannot continue.");
    return null;
  }
  if (typeof XpraClient == 'undefined') {
    alert("XpraClient is missing, cannot continue.");
    return null;
  }

  var https = document.location.protocol == "https:";
  var server = getparam("server") || window.location.hostname;
  var port = getparam("port") || window.location.port;
  var ssl = getboolparam("ssl", https);
  var path = getparam("path") || "/";
  var sharing = getboolparam("sharing", true);
  var steal = getboolparam("steal", false);
  var reconnect = getboolparam("reconnect", true);
  var clipboard = getboolparam("clipboard", true);
  var printing = getboolparam("printing", false);
  var file_transfer = getboolparam("file_transfer", false);
  var sound = getboolparam("sound", false);

  console.log("[XPRA Init] Creating client with:", { server, port, ssl, path });

  // Progress display function
  function connection_progress(state, details, progress) {
    console.log("[XPRA Progress]", state, details, progress + "%");
    if (progress >= 100) {
      $('#progress').hide();
    } else {
      $('#progress').show();
    }
    $('#progress-label').text(state || " ");
    $('#progress-details').text(details || " ");
    $('#progress-bar').val(progress);
  }

  // Create the client
  var client = new XpraClient('screen');
  client.sharing = sharing;
  client.clipboard_enabled = clipboard;
  client.printing = printing;
  client.file_transfer = file_transfer;
  client.steal = steal;
  client.reconnect = reconnect;
  client.on_connection_progress = connection_progress;

  // Audio support (disabled by default for simplicity)
  client.audio_enabled = sound;

  // Initialize client
  client.init();
  client.host = server;
  client.port = port;
  client.ssl = ssl;
  client.path = path;

  // Redirect logging to client after initialization
  clog = function() {
    client.log.apply(client, arguments);
  };
  cdebug = function() {
    client.debug.apply(client, arguments);
  };

  console.log("[XPRA Init] Client created and configured");
  return client;
}
