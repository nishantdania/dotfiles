#!/usr/bin/env bash
set -euo pipefail

SOURCE="${HOME}/.config/chromium"
DESTINATION="/tmp/pi-chromium-profiles"

while (($#)); do
  case "$1" in
    --source) SOURCE="$2"; shift 2 ;;
    --destination) DESTINATION="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--source CHROMIUM_PROFILE_DIR] [--destination PATH]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -d "$SOURCE" ]]; then
  echo "Source profile directory does not exist: $SOURCE" >&2
  exit 1
fi

mkdir -p "$DESTINATION"
rsync -a --delete \
  --exclude='SingletonCookie' \
  --exclude='SingletonLock' \
  --exclude='SingletonSocket' \
  --exclude='LOCK' \
  "$SOURCE/" "$DESTINATION/"

echo "Copied Chromium profiles to: $DESTINATION"
echo "Launch with: $(dirname "$0")/launch-cdp.sh --user-data-dir $DESTINATION"
