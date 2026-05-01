# Going online - end-to-end checklist

This is the order to follow once. After it, the public site updates automatically twice a day.

## 1. Push the project to GitHub

Single repo recommended. Both Render and GitHub Pages deploy from the same repo.

```bash
git init
git add .
git commit -m "Initial scroll climber"
gh repo create scroll-climber --public --source . --remote origin --push
```

## 2. Deploy the API on Render

Follow [reall-scroll-runner-api/DEPLOY_RENDER.md](reall-scroll-runner-api/DEPLOY_RENDER.md). Save:

- Public URL, e.g. `https://scroll-climber-api.onrender.com`
- The `EXTERNAL_PROGRESS_TOKEN` value Render generated.

Verify:

```bash
curl https://<your-app>.onrender.com/api/health
```

## 3. Update the frontend with the API URL

Edit `REALL_SCROLL_RUNNER_v1.html` and set:

```js
const PRODUCTION_API_BASE = "https://<your-app>.onrender.com/api";
```

Commit + push.

## 4. Publish the static site on GitHub Pages

Follow [DEPLOY_GITHUB_PAGES.md](DEPLOY_GITHUB_PAGES.md). Save the Pages URL.

## 5. Lock the Google Maps API key

Follow [GOOGLE_MAPS_KEY.md](GOOGLE_MAPS_KEY.md) and add the Pages URL as an HTTP referrer.

## 6. Set up the twice-daily Mac sync

Follow [automation/README.md](automation/README.md). Use the Render URL and token from step 2 in the `.env`.

## After all steps

- Public visitors load the Pages URL, browser fetches route + progress from Render API.
- Twice a day, Mac launchd job opens Scroll Mile dashboard, posts lifetime miles to Render with `X-Bridge-Token`.
- The trail HUD shows `Bridge: API ... mi` after each sync.

## What stays local-only

- `scroll-mile-bridge/bridge-snippet.js` - manual snippet for live testing in DevTools.
- `automation/.env` - local secrets (gitignored).
- Local `python3 server.py` runs on `127.0.0.1:3000` for development.
