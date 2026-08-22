---
name: outpost-work
description: Dispatch durable coding, research, and exploration tasks to Pi sessions inside remote Outpost VMs. Use when the user wants work started remotely so it continues after the local Pi session or laptop disconnects.
compatibility: Requires the outpost CLI, SSH access to the configured Outpost server, and Bash.
---

# Outpost Work

Outpost manages persistent Firecracker VMs on a remote server. The local Pi is a dispatcher: understand and confirm the plan, prepare an Outpost, start Pi in detached tmux, then forget the task. Do not monitor the remote Pi or wait for completion.

New Outposts are isolated. They need development tools plus explicit copies of Pi, Git, and GitHub authentication before remote work can use them. The bundled bootstrap script performs that repetitive setup without printing credentials.

Run `outpost help` whenever command discovery is needed or the user asks what Outpost supports.

## Rules

- Preserve the user's requested work. Do not introduce or remove requirements such as testing, committing, pushing, or opening pull requests.
- Always run remote Pi inside detached tmux.
- Never work directly on `main` or `master` unless the user explicitly requests it.
- Never print credentials or use shell tracing during credential provisioning.
- Treat local repository context as a hint, not a constraint. A task may involve a different repository, multiple repositories, or no repository.
- Do not monitor, attach to, clean up, stop, or delete the Outpost after launch.

## Plan

Before making changes or launching remote Pi:

1. Interpret the user's task.
2. Run `outpost list` to understand available Outposts.
3. If the current directory is a Git repository, inspect its remote URL, current branch, and working-tree state for possible context.
4. Determine the Outpost, tmux session name, repositories, clone paths, base branches, working branches, working directory, and exact prompt for remote Pi.
5. If work would otherwise happen on `main` or `master`, propose a task-specific branch such as `outpost/<task-slug>`.
6. If local changes are uncommitted or unavailable remotely and matter to the task, explain that in the plan and determine how they will be made available.

Present a confirmation in this form, adapting it for zero, one, or many repositories:

```text
Outpost: <name> (<existing or new>)
tmux session: <name>
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

1. Create the confirmed Outpost if needed, or start it if stopped.
2. Run the bootstrap helper:

```bash
~/.pi/agent/skills/outpost-work/scripts/bootstrap <outpost>
```

The helper idempotently installs Git, GitHub CLI, tmux, and mise; installs the latest Node.js through mise; and installs Pi under that Node.js version. Repositories can then select their own tool versions with mise. The helper also provisions host Pi authentication, host Git configuration, and keyring-backed GitHub authentication when missing.

3. Prepare repositories with `outpost exec` according to the confirmed plan. Clone or fetch each repository and create or checkout its confirmed working branch. This is agent reasoning; do not delegate repository selection or branch policy to the helper scripts.
4. Send the exact confirmed prompt to the launch helper on stdin:

```bash
printf '%s' "$PROMPT" | ~/.pi/agent/skills/outpost-work/scripts/launch-pi <outpost> <tmux-name> <working-directory>
```

Use a safe method such as a quoted heredoc instead of shell interpolation when the prompt contains arbitrary text.

5. Once the helper confirms tmux started, respond only:

```text
Started <tmux-name> in <outpost>.
```
