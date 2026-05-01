# Scroll Mile Bridge

This folder contains a robust bridge script that reads miles from the Scroll Mile dashboard tab and posts them to:

- `http://127.0.0.1:3000/api/external-progress`

Your trail app already reads from that endpoint.

The bridge reads **lifetime miles** from the dashboard element:

`<div id="lifetimeMiles">Lifetime: … mi</div>`

Older broad DOM / network scraping is disabled so other stats cannot override this value.

## Why this is a script (not an extension)

Chrome does not allow one extension to auto-inject content scripts into another extension page (`chrome-extension://...`), which is exactly where Scroll Mile runs.

So the reliable approach is to run this script in the Scroll Mile dashboard tab.

## One-time setup each browser session

1. Start the local API server:

```bash
python3 "/Users/guykowen/Downloads/WEB projects/scroll_climber/reall-scroll-runner-api/server.py"
```

2. Open Scroll Mile dashboard:

- `chrome-extension://kdeibhcngffpofgiaglnbhfpiocffihh/dashboard.html`

3. Open DevTools Console on that tab.

4. Open `bridge-snippet.js`, copy everything, paste into console, press Enter.

5. Keep that dashboard tab open while using the trail app.

## Verify it is live

In your trail app HUD:

- `Bridge: API ... mi` means updates are arriving.
- `Bridge: stale ...` means sender stopped or tab is closed/suspended.

## Optional quick API check

```bash
curl "http://127.0.0.1:3000/api/external-progress"
```

`updatedAt` should keep changing while you scroll in Scroll Mile.
