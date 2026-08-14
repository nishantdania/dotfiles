---
name: subagents
description: Spawn and manage parallel Pi subagents in visible tmux windows. Use when delegating work to one or more separate Pi sessions that the user can monitor or interact with.
compatibility: Requires tmux, bash, and pi on PATH.
---

# Subagents

Use one detached tmux session for this main Pi conversation and one window per subagent. Do not use panes or background `pi -p` processes.

The helper is `scripts/subagent-tmux` (resolve that path relative to this skill directory).

## Spawn

Choose and retain one short tmux session name for this conversation. It **must start with `pi-subagents`**, such as `pi-subagents-auth`. Choose a distinct short window name and give the subagent a complete, self-contained task:

```bash
scripts/subagent-tmux spawn pi-subagents-auth research 'Investigate the auth flow and report concrete findings; do not modify files.'
```

It creates the tmux session when needed, otherwise adds a window. Each window runs an interactive Pi session in the current working directory.

## Monitor and interact

```bash
scripts/subagent-tmux list pi-subagents-auth
scripts/subagent-tmux capture pi-subagents-auth research
scripts/subagent-tmux send pi-subagents-auth research 'Also check token refresh handling.'
scripts/subagent-tmux attach pi-subagents-auth
```

Report the tmux session and window names after spawning. Do not attach to, kill, or reuse a subagent window unless requested.
