# Google Maps key restrictions before going public

The current `REALL_SCROLL_RUNNER_v1.html` loads Maps with a hardcoded API key. Once the page is on GitHub Pages, lock the key down so nobody can reuse it elsewhere and run up your billing.

## In Google Cloud Console

1. Go to **APIs & Services -> Credentials**.
2. Pick the API key used by `REALL_SCROLL_RUNNER_v1.html`.
3. Under **Application restrictions**, choose **HTTP referrers (web sites)** and add:
   - `https://<your-github-username>.github.io/*`
   - `https://<your-github-username>.github.io/<repo-name>/*` (if Pages is project-scoped)
   - `http://localhost/*` and `http://127.0.0.1/*` (for local dev)
   - `file:///*` (only if you also open the HTML directly from disk)
4. Under **API restrictions**, restrict to only:
   - Maps JavaScript API
   - Street View Static API (if Street View thumbnails are needed)
5. Save.

## Billing & quotas

- In Google Cloud, set a **budget alert** so a misuse spike notifies you.
- Optionally set per-day **quota limits** for the Maps APIs.

## Note about committing the key

The key is visible in the HTML to any visitor; that is normal for client-side Maps usage. The referrer + API restrictions above are what actually keep it safe.
