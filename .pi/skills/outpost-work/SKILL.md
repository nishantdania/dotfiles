---
name: outpost-work
description: Dispatch durable coding, research, and exploration work to persistent Outpost VMs. Use when the user wants remote work that continues after the local Pi session or laptop disconnects.
compatibility: Requires Bash, jq, and a locally installed, configured outpost CLI.
---

# Outpost Work

Outpost manages persistent VMs. The local Pi dispatches confirmed work to an Outpost, starts remote Pi in detached tmux, and returns without waiting. This fire-and-forget launch behavior does not restrict normal inspection or lifecycle requests later.

Before using this skill, verify local `outpost` and `jq` are installed and that `outpost` is configured. The standard installer-managed `outpost` wrapper loads `~/.config/outpost/server.env` automatically, so exported environment variables are not required. The bootstrap helper structurally parses `outpost --output json inspect` with `jq` and accepts only `running` or `stopped`; it starts only `stopped` Outposts. Use Outpost's JSON output for listings: `outpost --output json list`.

Run `outpost --help` when command discovery is needed or the user asks what Outpost supports.

## Rules

- Preserve the user's requested work. Do not add or remove testing, commits, pushes, or pull requests.
- Always run remote Pi in detached tmux.
- Never work directly on `main` or `master` unless the user explicitly requests it.
- Never print credentials, put secrets in command arguments, or use shell tracing during credential provisioning.
- Use authenticated HTTPS or SSH GitHub URLs. Normalize `http://github.com/` URLs to `https://github.com/`; never clone credentials over plain HTTP.
- Treat local repository context as a hint, not a constraint. A task may involve different, multiple, or no repositories.
- Use Outpost names in `outpost create`, `outpost start`, `outpost stop`, `outpost delete`, `outpost ssh`, `outpost exec`, and `outpost copy`; do not look up or rely on IDs.
- The guest user and home are `root` and `/root`. For work without a repository, default to `/root`; for repositories, default to `/root/<repository-name>` unless requested otherwise.
- After launch, do not proactively monitor, attach, stop, or delete the Outpost. On later turns, inspect, attach, stop, delete, or otherwise interact with it when asked.
- For a new Outpost, default to 2 CPU, 4G memory, and 8G disk. Use `--cpus 2 --memory 4G --disk 8G`.
- Unless specified otherwise, launch `gpt-5.6-terra` with `medium` reasoning. For Sol, default to `gpt-5.6-sol` with `high` reasoning, or `medium` when explicitly requested.

## Simple operations

For listing, status, output inspection, or lifecycle requests, perform the requested Outpost operation directly. Do not enter dispatch planning, bootstrap, or ask for launch confirmation. Use `outpost --output json list` for listings. Use `outpost stop <name>`, `outpost delete <name>`, `outpost ssh <name>`, `outpost exec <name> -- <program> [args...]`, and `outpost copy <source> <destination>` as appropriate.

## Plan

Before creating an Outpost or launching remote Pi:

1. Interpret the task and run `outpost --output json list`.
2. If the current directory is a Git repository, inspect its remote URL, branch, and working-tree state for context.
3. Determine the Outpost name, whether it exists, CPU, memory, disk, tmux session, model, reasoning, repositories, clone paths, base branches, work branches, working directory, and exact remote prompt.
4. If work would otherwise happen on `main` or `master`, propose a task-specific branch such as `outpost/<task-slug>`.
5. If relevant local changes are uncommitted or unavailable remotely, explain how they will be made available.

Present this confirmation, adapting repository entries as needed:

```text
Outpost: <name> (<existing or new>)
Resources: <CPU>, <memory>, <disk>
tmux session: <name>
Model: <model>
Reasoning: <level>
Working directory: <path>

Repositories:
- <URL>
  Base: <branch>
  Work branch: <branch>
  Path: <path>

Remote Pi prompt:
<exact complete prompt>

Start this work?
```

Do not create or start an Outpost, prepare repositories, bootstrap it, or launch Pi until the user confirms. Show a revised confirmation if the plan changes.

## Dispatch

After confirmation:

1. Create a new Outpost with `outpost create <name> --cpus 2 --memory 4G --disk 8G`, or start an existing stopped Outpost with `outpost start <name>`.
2. Run the bootstrap helper:

   ```bash
   ~/.pi/agent/skills/outpost-work/scripts/bootstrap <outpost>
   ```

   It idempotently installs Git, GitHub CLI, tmux, ncurses terminfo tools, xz, libatomic, mise, the latest Node.js, and Pi. It also installs the local Ghostty (`xterm-ghostty`) terminfo entry when available, so tmux can be attached from Ghostty. It explicitly copies local Pi authentication and Git configuration to `/root` with secure modes, and pipes local GitHub authentication to the guest without logging it.
3. Prepare repositories with `outpost exec <name> -- ...` according to the confirmed plan. Clone or fetch each repository and create or check out its confirmed working branch. Repository and branch policy remains dispatcher reasoning, not helper behavior.
4. Verify the exact confirmed working directory exists with `outpost exec <name> -- test -d <path>`. For repository work it must be the prepared clone; otherwise use `/root` or create the confirmed directory explicitly.
5. Send the exact confirmed prompt to the launch helper on stdin:

   ```bash
   printf '%s' "$PROMPT" | ~/.pi/agent/skills/outpost-work/scripts/launch-pi <outpost> <tmux-name> <working-directory> <model> <reasoning>
   ```

   Use a quoted heredoc rather than interpolation for arbitrary prompts.
6. Once the helper confirms tmux started, respond only:

   ```text
   Started <tmux-name> in <outpost>.
   ```

Later, inspect output normally on request, for example:

```bash
outpost exec <outpost> -- tmux capture-pane -pt <tmux-name> -S -50
```
