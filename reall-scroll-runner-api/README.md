# REALL Scroll Runner API

Local API for marathon route + progress rendering.

## Run

```bash
python3 server.py
```

API base URL:

- `http://127.0.0.1:3000/api`

## Endpoints

- `GET /api/health`
- `GET /api/marathon-route`
- `GET /api/progress?distanceMeters=12345`

## Frontend

`REALL_SCROLL_RUNNER_v1.html` is configured to call this API.
