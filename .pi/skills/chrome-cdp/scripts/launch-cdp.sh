#!/usr/bin/env bash
set -euo pipefail

PORT=9222
USER_DATA_DIR=""
SOURCE_PROFILE_DIR="${HOME}/.config/chromium"

while (($#)); do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --user-data-dir) USER_DATA_DIR="$2"; shift 2 ;;
    --source-profile-dir) SOURCE_PROFILE_DIR="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--port PORT] [--user-data-dir PATH] [--source-profile-dir PATH]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$USER_DATA_DIR" ]]; then
  USER_DATA_DIR="/tmp/pi-chromium-cdp-${PORT}"
fi

if curl -fsS --max-time 1 "http://127.0.0.1:${PORT}/json/version" >/dev/null; then
  echo "A CDP endpoint is already listening on port ${PORT}." >&2
  exit 1
fi

# Never use the user's live profile: refresh an isolated copy before every launch.
"$(dirname "$0")/copy-profile.sh" --source "$SOURCE_PROFILE_DIR" --destination "$USER_DATA_DIR" >/dev/null

CHROMIUM="$(command -v chromium || command -v chromium-browser || command -v google-chrome)"
nohup "$CHROMIUM" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins=http://localhost \
  --user-data-dir="$USER_DATA_DIR" \
  "chrome://profile-picker/" >"$USER_DATA_DIR/chromium.log" 2>&1 &

for _ in {1..10}; do
  sleep 1
  if curl -fsS --max-time 1 "http://127.0.0.1:${PORT}/json/version" >/dev/null; then
    echo "CDP ready at http://127.0.0.1:${PORT} (copied profiles: $USER_DATA_DIR)"
    exit 0
  fi
done

echo "Chromium did not expose CDP. See $USER_DATA_DIR/chromium.log" >&2
exit 1
