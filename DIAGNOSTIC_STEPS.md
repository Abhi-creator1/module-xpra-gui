# XPRA Module Diagnostic Steps

## Changes Made
Added enhanced console logging to help diagnose the connection issue.

## Step-by-Step Diagnostic Process

### 1. Push Changes and Deploy
```bash
git add index.html
git commit -m "add diagnostic logging for connection troubleshooting"
git push
```
Wait for GitHub Actions to complete deployment (~1-2 minutes).

### 2. Test Through Edrys with DevTools Open

1. Open Chrome DevTools (F12)
2. Go to the **Console** tab
3. Load your Edrys classroom with the module
4. Look for log messages prefixed with `[XPRA Wrapper]`

**Expected output:**
```
[XPRA Wrapper] XPRA module loaded. config: {server: "192.168.137.108:14500"}
[XPRA Wrapper] Raw config value: 192.168.137.108:14500
[XPRA Wrapper] Cleaned value: 192.168.137.108:14500
[XPRA Wrapper] Parsed host: 192.168.137.108 port: 14500
[XPRA Wrapper] Final iframe URL: client/index.html?server=192.168.137.108&port=14500&ssl=false&path=/&...
[XPRA Wrapper] Full URL would be: https://abhi-creator1.github.io/module-xpra-gui/client/index.html?...
[XPRA Wrapper] Iframe loaded successfully: ...
```

**Check for:**
- ✅ Port value is clean (no trailing slash): `port: 14500` ✓
- ✅ Final URL looks correct
- ❌ Any errors about blocked requests, CORS, or permissions

### 3. Monitor Jetson Server Log (CRITICAL)

**On your Jetson (via SSH or direct access):**
```bash
tail -f /home/appuser/.run/xpra/:100.log
```

**While the module is "stuck on Connecting":**
- **If you see new log entries** → Connection IS reaching the server, but failing at protocol level
- **If you see NO new entries** → Connection is NOT reaching the server (blocked by browser)

### 4. Check Local Network Access Permission

**In Chrome, navigate to:**
```
chrome://settings/content/localNetworkAccess
```

**Verify:**
- [ ] `edrys-labs.github.io` is in the "Allowed to access your local network" list
- [ ] Try removing and re-adding the permission
- [ ] Test again after refresh

### 5. Inspect the Actual Iframe in DevTools

**In Chrome DevTools:**
1. Switch to **Elements** tab
2. Find the `<iframe id="viewer">` element
3. Check its `src` attribute value
4. Right-click the iframe → "View frame source" to see what's actually loaded

**Verify:**
- Port number has no trailing characters
- All query parameters look correct
- The iframe loaded `client/index.html` successfully

### 6. Check Network Tab for Blocked Requests

**In Chrome DevTools:**
1. Switch to **Network** tab
2. Enable "Preserve log"
3. Reload the Edrys page
4. Look for:
   - Any requests to `192.168.137.108:14500` (HTTP or WS)
   - Status codes (especially 403, 404, or ERR_* errors)
   - Filter by "WS" to see WebSocket connections

**Look for:**
- `ws://192.168.137.108:14500/` connection attempt
- If blocked: error message will indicate why (CORS, LNA, etc.)

## Likely Issues & Solutions

### Issue A: Connection Not Reaching Server (No Jetson Log Entries)

**Possible causes:**
1. **LNA permission not delegated properly**
   - The iframe's `allow="local-network-access"` might not be effective when the module is embedded by Edrys
   - Edrys loads your module by injecting HTML directly (not via iframe wrapper)

   **Solution:** Check if Edrys needs to set permissions policy on its side

2. **Multiple origin chain blocking LNA**
   - edrys-labs.github.io → abhi-creator1.github.io → client/index.html → ws://192.168.137.108
   - Each hop might need explicit permission delegation

   **Solution:** May need to contact Edrys team about permission delegation

3. **WebSocket blocked by CSP or CORS**
   - Check Console for CSP violation errors

   **Solution:** May need to add CSP headers (but can't control this on GitHub Pages)

### Issue B: Connection Reaching Server But Failing (Jetson Log Shows Attempts)

**Check the Jetson log for:**
- Handshake failures
- Protocol errors
- Authentication issues

**Possible solutions:**
- Re-run `fetch_client.py` to ensure version match
- Check XPRA server settings
- Verify firewall/Docker network settings

### Issue C: Iframe Not Loading At All

**Check for:**
- CORS errors in console
- X-Frame-Options blocking
- CSP violations

**Solution:** Verify GitHub Pages deployment is active and accessible

## Alternative Approaches to Consider

If LNA permission delegation is fundamentally blocked:

1. **Run Edrys locally** (on same network as Jetson) to bypass LNA restrictions
2. **Set up a public proxy/tunnel** to the XPRA server (ngrok, CloudFlare Tunnel, etc.)
3. **Use XPRA's built-in SSL/TLS** with a public domain (more complex setup)
4. **Host the module on the same origin as the XPRA server** (e.g., serve from Jetson)

## Quick Test: Direct GitHub Pages Access

**To isolate Edrys from the equation:**

1. Open directly in Chrome: `https://abhi-creator1.github.io/module-xpra-gui/`
2. Open DevTools Console
3. Manually trigger the connection by entering in Console:
   ```javascript
   Edrys = {
     module: { config: { server: "192.168.137.108:14500" } },
     onReady: (cb) => cb(),
     onUpdate: () => {}
   };
   // Then reload the page
   ```
4. Check if it connects (monitor Jetson log)

If this works, the issue is with Edrys embedding specifically.
If this doesn't work, the issue is with LNA permission or the module itself.
