(() => {
  const BRIDGE_URL = "http://127.0.0.1:3000/api/external-progress";
  const STATE = {
    lastSentMiles: null,
    lastDetectedMiles: null,
    installedAt: Date.now(),
    sends: 0
  };

  function toNumber(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }

  function extractMilesFromText(text) {
    if (!text) return null;
    const normalized = String(text).replace(/,/g, "");
    const labeled = normalized.match(/(\d+(?:\.\d+)?)\s*(mi|mile|miles)\b/i);
    if (labeled) return toNumber(labeled[1]);
    const decimal = normalized.match(/\b(\d+\.\d{2,})\b/);
    if (decimal) return toNumber(decimal[1]);
    return null;
  }

  /** Authoritative stat from Scroll Mile dashboard: "Lifetime: 0.06 mi" */
  function readLifetimeMiles() {
    const el = document.getElementById("lifetimeMiles");
    if (!el) return null;
    return extractMilesFromText(el.textContent || "");
  }

  function searchMilesInDom() {
    const lifetime = readLifetimeMiles();
    if (lifetime !== null) return lifetime;

    const candidates = [
      "[data-testid*='mile' i]",
      "[class*='mile' i]",
      "[id*='mile' i]",
      "main",
      "body"
    ];
    for (const selector of candidates) {
      const nodes = document.querySelectorAll(selector);
      for (const node of nodes) {
        const miles = extractMilesFromText(node.textContent || "");
        if (miles !== null) return miles;
      }
    }
    return extractMilesFromText(document.body?.innerText || "");
  }

  function maybeSendMiles(miles, source) {
    if (!Number.isFinite(miles) || miles < 0) return;
    STATE.lastDetectedMiles = miles;
    if (STATE.lastSentMiles !== null && Math.abs(STATE.lastSentMiles - miles) < 0.000001) return;
    STATE.lastSentMiles = miles;
    fetch(BRIDGE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        miles,
        source,
        clientTs: Date.now()
      })
    })
      .then((res) => res.json())
      .then((data) => {
        STATE.sends += 1;
        console.log("[ScrollBridge] sent", { miles, source, server: data });
      })
      .catch((err) => {
        console.error("[ScrollBridge] POST failed", err);
      });
  }

  function scanDomAndSend() {
    const miles = searchMilesInDom();
    if (miles !== null) {
      const source = readLifetimeMiles() === miles ? "lifetimeMiles" : "dashboard-dom";
      maybeSendMiles(miles, source);
    }
  }

  if (window.__scrollMilesBridgeInstalled) {
    console.log("[ScrollBridge] already installed");
    return;
  }
  window.__scrollMilesBridgeInstalled = true;

  scanDomAndSend();
  window.__scrollMilesBridgeTimer = setInterval(scanDomAndSend, 1000);

  console.log("[ScrollBridge] installed", {
    bridgeUrl: BRIDGE_URL,
    installedAt: new Date(STATE.installedAt).toISOString()
  });
})();
