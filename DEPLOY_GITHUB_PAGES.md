# Publish the Scroll Climber frontend on GitHub Pages

## Files Pages needs to serve

From `WEB projects/scroll_climber/`:

- `REALL_SCROLL_RUNNER_v1.html`
- `sideview_everest_trans.png`
- `sideview_everest.png` (only if you reference it)
- `trail_everest.png`, `trail_everest.svg` (if referenced)
- `sideimage_with_path.svg` (if referenced)

(`reall-scroll-runner-api/` and `scroll-mile-bridge/` are NOT served on Pages; they belong to the Render service and your local Mac.)

## Recommended layout

Make `REALL_SCROLL_RUNNER_v1.html` the entry point or rename it to `index.html` so the URL is clean:

```
https://<user>.github.io/<repo>/
```

## Steps

1. Push the project to a GitHub repo (public is fine; the API is the part that needs locking down, not the static page).
2. In the repo, go to **Settings -> Pages**.
3. **Build and deployment**:
   - **Source**: Deploy from a branch
   - **Branch**: `main` (or your default), **Folder**: choose either:
     - `/ (root)` -> rename `REALL_SCROLL_RUNNER_v1.html` to `index.html` first, OR
     - `/docs` -> move/copy the static files there.
4. Save. Pages will give you a URL within ~1 minute.

## After Pages is live

- In `REALL_SCROLL_RUNNER_v1.html`, replace `PRODUCTION_API_BASE` with your Render URL:
  ```
  const PRODUCTION_API_BASE = "https://<your-app>.onrender.com/api";
  ```
- Lock the Google Maps key per `GOOGLE_MAPS_KEY.md` and add the new Pages URL to allowed referrers.

## Sanity check

Open the Pages URL in an incognito window. The trail should load (because the page detects it is not localhost and uses the Render API). The HUD should show `Bridge: stale` until the launchd job runs and pushes lifetime miles.
