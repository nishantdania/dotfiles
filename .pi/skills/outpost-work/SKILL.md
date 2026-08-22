---
name: outpost-work
description: Dispatch durable coding, research, and exploration tasks to Pi sessions inside remote Outpost VMs. Use when the user wants work started remotely so it continues after the local Pi session or laptop disconnects.
compatibility: Requires the outpost CLI, SSH access to the configured Outpost server, and Bash.
---

# Outpost Work

Outpost manages persistent Firecracker VMs on a remote server. The local Pi is a dispatcher: understand and confirm the plan, prepare an Outpost, start Pi in detached tmux, then return without proactively waiting for completion. This is a default launch behavior, not a restriction on later requests.

New Outposts are isolated. They need development tools plus explicit copies of Pi, Git, and GitHub authentication before remote work can use them. The bundled bootstrap script performs that repetitive setup without printing credentials.

Run `outpost help` whenever command discovery is needed or the user asks what Outpost supports.

## Rules

- Preserve the user's requested work. Do not introduce or remove requirements such as testing, committing, pushing, or opening pull requests.
- Always run remote Pi inside detached tmux.
- Never work directly on `main` or `master` unless the user explicitly requests it.
- Never print credentials or use shell tracing during credential provisioning.
- Treat local repository context as a hint, not a constraint. A task may involve a different repository, multiple repositories, or no repository.
- Outpost lifecycle and access commands accept either an ID or name. Prefer the confirmed Outpost name in `start`, `stop`, `delete`, `ssh`, `exec`, and `copy` commands instead of looking up a UUID.
- The guest user is `root` and its home is `/root`. Never assume `/home/pi` or a `pi` Unix user exists. For work without a repository, default to `/root`. For repositories, default to `/root/<repository-name>` unless the user requests another path.
- After launch, do not proactively monitor, attach, clean up, stop, or delete anything. If the user explicitly asks to check output, inspect status, attach, stop, delete, or otherwise interact with the launched work, comply normally. Never refuse a follow-up because the initial workflow is fire-and-forget.
- Use the CLI's configured default host unless the user specifies another host. Do not read `~/.config/outpost/config.json` to discover it: omit `--host` and let Outpost resolve the default. Read client configuration only when the user explicitly asks to inspect or change it.
- For a new Outpost, use 2 vCPU, 4 GiB RAM, and 8 GiB disk unless the user specifies different resources. In CLI commands, write these sizes as `--memory 4G --disk 8G`; Outpost accepts `M`, `MB`, `G`, or `GB`, not `MiB` or `GiB`.
- Unless the user specifies otherwise, launch `gpt-5.6-terra` with `medium` reasoning.
- When the user asks for Sol, launch `gpt-5.6-sol` with `high` reasoning by default. Use `medium` reasoning instead when the user explicitly asks for Sol medium.

## Simple operations

For informational or direct management requests such as “any Outposts?”, listing, status, stopping, or checking output, perform the requested CLI operation directly. Do not enter the dispatch planning flow, inspect client configuration, bootstrap, or ask for launch confirmation. Use `outpost list` for the default host and add `--host <name>` only when the user explicitly names another host.

## Plan

Before creating an Outpost or launching remote Pi:

1. Interpret the user's task.
2. Run `outpost list` for the default host. If the user explicitly selected another host, run `outpost --host <name> list`.
3. If the current directory is a Git repository, inspect its remote URL, current branch, and working-tree state for possible context.
4. Determine the host, Outpost, CPU, RAM, disk, tmux session name, model, reasoning level, repositories, clone paths, base branches, working branches, working directory, and exact prompt for remote Pi.
5. If work would otherwise happen on `main` or `master`, propose a task-specific branch such as `outpost/<task-slug>`.
6. If local changes are uncommitted or unavailable remotely and matter to the task, explain that in the plan and determine how they will be made available.

Present a confirmation in this form, adapting it for zero, one, or many repositories:

```text
Host: <default or explicitly selected name>
Outpost: <name> (<existing or new>)
Resources: <vCPU>, <RAM>, <disk>
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

Do not create the Outpost, prepare repositories, bootstrap the VM, or launch Pi until the user confirms. If the user changes the plan, show the revised confirmation.

## Dispatch

After confirmation:

1. Create the confirmed Outpost if needed, or start it if stopped. For the default host, omit the host flag: `outpost create <name> --cpus <count> --memory <size> --disk <size>`. Only for an explicitly selected host use `outpost --host <host> create ...`. Convert display units to CLI units: for the default resources, the exact flags are `--cpus 2 --memory 4G --disk 8G`. Never pass `MiB` or `GiB` suffixes.
2. Run the bootstrap helper:

```bash
~/.pi/agent/skills/outpost-work/scripts/bootstrap <default|explicit-host> <outpost>
```

The helper idempotently installs Git, GitHub CLI, tmux, and mise; installs the latest Node.js through mise; and installs Pi under that Node.js version. Repositories can then select their own tool versions with mise. The helper also provisions host Pi authentication, host Git configuration, and keyring-backed GitHub authentication when missing.

3. Prepare repositories with `outpost exec` on the default host or `outpost --host <host> exec` on an explicitly selected host, according to the confirmed plan. Clone or fetch each repository and create or checkout its confirmed working branch. This is agent reasoning; do not delegate repository selection or branch policy to the helper scripts.
4. Before launch, verify that the exact confirmed working directory exists inside the guest. For a repository task, it must be the prepared clone path. For a task without a repository, use `/root` or explicitly create the confirmed directory. Do not invent a different path after confirmation.
5. Send the exact confirmed prompt to the launch helper on stdin:

```bash
printf '%s' "$PROMPT" | ~/.pi/agent/skills/outpost-work/scripts/launch-pi <default|explicit-host> <outpost> <tmux-name> <working-directory> <model> <reasoning>
```

Use a safe method such as a quoted heredoc instead of shell interpolation when the prompt contains arbitrary text.

6. Once the helper confirms tmux started, respond only:

```text
Started <tmux-name> in <outpost>.
```

On later turns, follow the user's request normally. For example, when asked what remote Pi said, inspect it with `outpost exec <outpost> 'tmux capture-pane -pt <tmux-name> -S -50'` for the default host, adding `--host <host>` only for an explicitly selected host and report the output.
