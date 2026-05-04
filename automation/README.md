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
#   MIRROR_SCROLL_MILE_FROM_CHROME=1  (recommended on macOS)
#       Copies Scroll Mile storage from your real Chrome "Default" profile into
#       USER_DATA_DIR before each run. Chrome must be **fully quit** first, or the
#       script exits with an error. Playwright cannot open ~/Library/.../Google/Chrome
#       directly (Chrome blocks automation on that path).

# 4. Smoke test
./run_sync.sh

# 5. Install launchd job (copy scripts out of Downloads)
#    macOS often blocks launchd from running scripts under ~/Downloads ("Operation not permitted").
#    Keep a copy under Application Support and point the plist at that path.
SUPPORT="$HOME/Library/Application Support/scroll-mile-sync"
mkdir -p "$SUPPORT" logs
cp -f run_sync.sh sync_scroll_mile.py .env "$SUPPORT/"
chmod +x "$SUPPORT/run_sync.sh"
cp com.guykowen.scrollmile.sync.plist "$HOME/Library/LaunchAgents/"
launchctl load "$HOME/Library/LaunchAgents/com.guykowen.scrollmile.sync.plist"
# When you change .env or sync_scroll_mile.py, copy those files into "$SUPPORT" again.
```

The job runs at **09:00 and 21:00** local time, and **once at login** (`RunAtLoad`) so your Mac pushes fresh miles soon after you open it — not only when those clock times hit.

Your trail distance on the website is stored on the **Render API server** (persisted to disk there after each sync). Closing the Mac does not erase it; only a Render redeploy or cleared disk would reset it unless miles are re-synced.

To change the schedule times, edit
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
