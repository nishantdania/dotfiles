---
name: ark-work
description: Dispatch durable coding, research, and exploration work to persistent Ark VMs. Use when the user wants remote work that continues after the local Pi session or laptop disconnects.
compatibility: Requires Bash, jq, and a locally installed, configured ark CLI.
---

# Ark Work

Ark manages persistent VMs. The local Pi dispatches confirmed work to an Ark, starts remote Pi in detached tmux, and returns without waiting. This fire-and-forget launch behavior does not restrict normal inspection or lifecycle requests later.

Before using this skill, verify local `ark` and `jq` are installed and that `ark` is configured. The standard installer-managed `ark` wrapper loads `~/.config/ark/server.env` automatically; manually exported Ark variables also remain supported. The bootstrap helper structurally parses `ark --output json inspect` with `jq` and accepts only `running` or `stopped`; it starts only `stopped` Arks. Use Ark's JSON output for listings: `ark --output json list`.

Run `ark --help` when command discovery is needed or the user asks what Ark supports.

## Rules

- Preserve the user's requested work. Do not add or remove testing, commits, pushes, or pull requests.
- Always run remote Pi in detached tmux.
- Never work directly on `main` or `master` unless the user explicitly requests it.
- Never print credentials, put secrets in command arguments, or use shell tracing during credential provisioning.
- Use authenticated HTTPS or SSH GitHub URLs. Normalize `http://github.com/` URLs to `https://github.com/`; never clone credentials over plain HTTP.
- Treat local repository context as a hint, not a constraint. A task may involve different, multiple, or no repositories.
- Use Ark names in `ark create`, `ark start`, `ark stop`, `ark delete`, `ark ssh`, `ark exec`, and `ark copy`; do not look up or rely on IDs.
- The guest user and home are `root` and `/root`. For work without a repository, default to `/root`; for repositories, default to `/root/<repository-name>` unless requested otherwise.
- After launch, do not proactively monitor, attach, stop, or delete the Ark. On later turns, inspect, attach, stop, delete, or otherwise interact with it when asked.
- For a new Ark, default to 2 CPU, 4G memory, and 8G disk. Use `--cpus 2 --memory 4G --disk 8G`.
- Unless specified otherwise, launch `gpt-5.6-terra` with `medium` reasoning. For Sol, default to `gpt-5.6-sol` with `high` reasoning, or `medium` when explicitly requested.

## Simple operations

For listing, status, output inspection, or lifecycle requests, perform the requested Ark operation directly. Do not enter dispatch planning, bootstrap, or ask for launch confirmation. Use `ark --output json list` for listings. Use `ark stop <name>`, `ark delete <name>`, `ark ssh <name>`, `ark exec <name> -- <program> [args...]`, and `ark copy <source> <destination>` as appropriate.

## Plan

Before creating an Ark or launching remote Pi:

1. Interpret the task and run `ark --output json list`.
2. If the current directory is a Git repository, inspect its remote URL, branch, and working-tree state for context.
3. Determine the Ark name, whether it exists, CPU, memory, disk, tmux session, model, reasoning, repositories, clone paths, base branches, work branches, working directory, and exact remote prompt.
4. If work would otherwise happen on `main` or `master`, propose a task-specific branch such as `ark/<task-slug>`.
5. If relevant local changes are uncommitted or unavailable remotely, explain how they will be made available.

Present this confirmation, adapting repository entries as needed:

```text
Ark: <name> (<existing or new>)
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

Do not create or start an Ark, prepare repositories, bootstrap it, or launch Pi until the user confirms. Show a revised confirmation if the plan changes.

## Dispatch

After confirmation:

1. Create a new Ark with `ark create <name> --cpus 2 --memory 4G --disk 8G`, or start an existing stopped Ark with `ark start <name>`.
2. Run the bootstrap helper:

   ```bash
   ~/.pi/agent/skills/ark-work/scripts/bootstrap <ark>
   ```

   It idempotently installs Git, GitHub CLI, tmux, xz, libatomic, mise, the latest Node.js, and Pi. It explicitly copies local Pi authentication and Git configuration to `/root` with secure modes, and pipes local GitHub authentication to the guest without logging it.
3. Prepare repositories with `ark exec <name> -- ...` according to the confirmed plan. Clone or fetch each repository and create or check out its confirmed working branch. Repository and branch policy remains dispatcher reasoning, not helper behavior.
4. Verify the exact confirmed working directory exists with `ark exec <name> -- test -d <path>`. For repository work it must be the prepared clone; otherwise use `/root` or create the confirmed directory explicitly.
5. Send the exact confirmed prompt to the launch helper on stdin:

   ```bash
   printf '%s' "$PROMPT" | ~/.pi/agent/skills/ark-work/scripts/launch-pi <ark> <tmux-name> <working-directory> <model> <reasoning>
   ```

   Use a quoted heredoc rather than interpolation for arbitrary prompts.
6. Once the helper confirms tmux started, respond only:

   ```text
   Started <tmux-name> in <ark>.
   ```

Later, inspect output normally on request, for example:

```bash
ark exec <ark> -- tmux capture-pane -pt <tmux-name> -S -50
```
