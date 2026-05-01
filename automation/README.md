# Scroll Mile twice-daily sync (launchd)

Scheduled job that opens the Scroll Mile dashboard via Playwright + a persistent
Chrome profile, reads `#lifetimeMiles`, and POSTs it to the Render API.

## One-time setup

```bash
cd "/Users/guykowen/Downloads/WEB projects/scroll_climber/automation"

# 1. Install Playwright + Chromium
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium

# 2. Create a dedicated Chrome profile that has Scroll Mile installed
#    Run Chromium once with the profile dir, install Scroll Mile, sign in if needed.
mkdir -p "$HOME/Library/Application Support/ScrollMileSyncProfile"
"$(python3 -m playwright path chromium 2>/dev/null || true)"  # may not exist; use the chromium binary Playwright installed.
# Easier: just open Chrome normally and copy-install the extension into the profile,
# then point USER_DATA_DIR at the profile path.

# 3. Configure secrets
cp .env.example .env
# edit .env and set:
#   BRIDGE_URL                = https://<your-render-app>.onrender.com/api/external-progress
#   EXTERNAL_PROGRESS_TOKEN   = same value you set on Render
#   USER_DATA_DIR             = absolute path to the profile dir from step 2

# 4. Smoke test
./run_sync.sh

# 5. Install launchd job
mkdir -p logs
cp com.guykowen.scrollmile.sync.plist "$HOME/Library/LaunchAgents/"
launchctl load "$HOME/Library/LaunchAgents/com.guykowen.scrollmile.sync.plist"
```

The job runs at 09:00 and 21:00 local time. To change the times, edit
`StartCalendarInterval` in the plist and reload it:

```bash
launchctl unload "$HOME/Library/LaunchAgents/com.guykowen.scrollmile.sync.plist"
launchctl load   "$HOME/Library/LaunchAgents/com.guykowen.scrollmile.sync.plist"
```

## Logs

- `automation/logs/sync.out.log`
- `automation/logs/sync.err.log`

## Notes

- Mac must be awake at scheduled times. If asleep, launchd runs the missed job on next wake.
- Visible browser window pops briefly each run by default; set `HEADLESS=1` in `.env` to hide it (extension support in headless can be flaky; only switch if it works for you).
- If Scroll Mile updates the dashboard structure, adjust `#lifetimeMiles` selector in `sync_scroll_mile.py`.
