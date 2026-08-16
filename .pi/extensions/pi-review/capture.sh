#!/usr/bin/env bash
# Invoked by wl-paste --watch. Forwards text to the already-warm GTK daemon.
set -euo pipefail

review_socket="${PI_REVIEW_SOCKET:?}"
title_tag="${PI_REVIEW_TITLE_TAG:?}"
focused_title="$(hyprctl activewindow -j 2>/dev/null | jq -r 'select(.class == "com.mitchellh.ghostty") | .title // empty')"
# Ghostty is a single-instance process, so every window has the same PID.
# The session-specific OSC title is the reliable per-window identity.
[[ "$focused_title" == *"$title_tag"* ]] || exit 0

# Ignore image-only clipboard changes (for example screenshots pasted into Pi).
if ! wl-paste --list-types 2>/dev/null | grep -q '^text/'; then
  exit 0
fi

selected="$(cat)"
[[ -n "$selected" ]] || exit 0

printf '%s' "$selected" | socat - "UNIX-CONNECT:$review_socket" >/dev/null 2>&1 || true
