// XPRA initialization for Edrys integration
console.log("[XPRA Init] Starting initialization");

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

  // The XPRA client will initialize automatically via $(document).ready()
  // and will now read our injected config via the intercepted Utilities.getparam()
});
