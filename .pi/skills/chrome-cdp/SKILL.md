---
name: chrome-cdp
description: Inspect, screenshot, navigate, and debug locally running Chrome or Chromium through the Chrome DevTools Protocol (CDP). Use for requests involving browser tabs, rendered UI, browser screenshots, web-app interaction, or CDP debugging.
compatibility: Requires Python 3 and a local Chrome/Chromium instance with remote debugging enabled.
---

# Chrome CDP

Use this skill to operate a local CDP-enabled Chromium/Chrome instance.

## Safety

- Connect only to loopback CDP endpoints (`127.0.0.1` / `localhost`).
- Do not print cookies, local storage, credentials, authorization headers, or other secrets.
- Do not launch Chromium with `--ignore-certificate-errors`; let the user approve local-development certificates.
- Inspect tabs before interacting. Confirm state-changing or destructive actions unless the user explicitly requested them.
- If the user’s regular browser is open, use a fresh or copied profile; never reuse its live profile directory.

## Connection

First inspect the endpoint and available tabs:

```bash
python3 ~/.pi/agent/skills/chrome-cdp/scripts/cdp.py status
python3 ~/.pi/agent/skills/chrome-cdp/scripts/cdp.py tabs
```

The default endpoint is `127.0.0.1:9222`. Supply `--port PORT` when needed.

If no endpoint exists, launch a separate browser using a refreshed copy of the user's Chromium profiles. Do not kill their current browser or use its live profile directory. `launch-cdp.sh` copies profiles automatically and opens the profile picker. Wait for the user to select a profile before opening a web page through CDP.

```bash
~/.pi/agent/skills/chrome-cdp/scripts/launch-cdp.sh --port 9222
# After the user selects a profile:
python3 ~/.pi/agent/skills/chrome-cdp/scripts/cdp.py open 'https://example.test'
```

Use `copy-profile.sh` directly only when a manually managed copied profile is needed.

## Common workflow

Target a tab with `--url-match` (or `--tab-id`) and inspect the rendered result before and after UI changes:

```bash
CDP='python3 ~/.pi/agent/skills/chrome-cdp/scripts/cdp.py --url-match lifetimely'
$CDP screenshot --output /tmp/page.png
$CDP text
$CDP click --text 'New chat'
$CDP fill --placeholder 'Ask anything' --value 'Hi'
$CDP submit --placeholder 'Ask anything'
$CDP screenshot --output /tmp/after.png
```

Useful commands:

```bash
cdp.py tabs
cdp.py open URL
cdp.py navigate --to URL --url-match TEXT
cdp.py screenshot --output FILE --url-match TEXT
cdp.py text --url-match TEXT
cdp.py click --text TEXT|--selector CSS
cdp.py fill --placeholder TEXT|--selector CSS --value TEXT
cdp.py submit --placeholder TEXT|--selector CSS
cdp.py hover --x X --y Y
cdp.py scroll --by PIXELS [--selector CSS]
cdp.py zoom --percent 200
cdp.py zoom --reset
cdp.py eval --expression JAVASCRIPT
```

`scroll --selector` scrolls an internal scrolling container; omit it to scroll the page. Always reset temporary zoom when finished.
