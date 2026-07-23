// Config interceptor for XPRA client
// Intercepts Utilities.getparam() to inject Edrys config instead of URL params

(function() {
  console.log("[Config Interceptor] Initializing XPRA config override");

  // This will be populated by init-xpra.js after Edrys.onReady()
  window.EDRYS_XPRA_CONFIG = window.EDRYS_XPRA_CONFIG || {};

  // Wait for Utilities to be defined, then override getparam
  function overrideGetparam() {
    if (typeof Utilities === 'undefined') {
      console.log("[Config Interceptor] Utilities not yet loaded, retrying...");
      setTimeout(overrideGetparam, 50);
      return;
    }

    console.log("[Config Interceptor] Overriding Utilities.getparam()");

    // Store original function
    const originalGetparam = Utilities.getparam;

    // Override with our interceptor
    Utilities.getparam = function(prop) {
      // Check if we have Edrys config for this property
      if (window.EDRYS_XPRA_CONFIG.hasOwnProperty(prop)) {
        const value = window.EDRYS_XPRA_CONFIG[prop];
        console.log(`[Config Interceptor] Intercepted getparam("${prop}") -> "${value}"`);
        return value;
      }

      // Fall back to original implementation for other params
      return originalGetparam.call(this, prop);
    };

    console.log("[Config Interceptor] Override complete");
  }

  // Start override attempt
  overrideGetparam();
})();
