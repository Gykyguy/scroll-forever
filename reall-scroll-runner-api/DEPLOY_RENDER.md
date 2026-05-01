# Deploy the Scroll Climber API on Render

This folder is ready to deploy as a Render Web Service.

## One-time setup

1. Push the project to a GitHub repository.
2. Sign in to https://render.com with that GitHub account.
3. Click **New +** -> **Web Service** -> connect the repo.
4. Configure:
   - **Root Directory**: `WEB projects/scroll_climber/reall-scroll-runner-api`
   - **Runtime**: Python 3
   - **Build Command**: leave blank
   - **Start Command**: `python server.py`
   - **Instance Type**: Free is fine to start.
5. Add an environment variable:
   - `EXTERNAL_PROGRESS_TOKEN` -> click **Generate** (Render will create a random secret), or paste your own long random string.
6. Click **Create Web Service**.

Render will build and give you a public URL like:

```
https://scroll-climber-api.onrender.com
```

## Verify

```
curl https://<your-app>.onrender.com/api/health
curl https://<your-app>.onrender.com/api/marathon-route | head -c 200
```

You should get `{"ok": true}` and a GeoJSON snippet.

## Notes

- `EXTERNAL_PROGRESS_TOKEN` is required as the `X-Bridge-Token` header for any `POST /api/external-progress` request. If the env var is empty, auth is disabled (matches local dev behavior).
- Render's free tier sleeps idle services; the first request after sleep is slow.
- The included `render.yaml` lets Render auto-detect settings via the **Blueprint** flow if you prefer that path.
