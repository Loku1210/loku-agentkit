---
name: defer-task
description: Use when a user explicitly asks to schedule, list, inspect, or cancel a delayed local agent task on macOS.
---

# defer-task

> **macOS MVP.** Restart-safe scheduling uses a per-task launchd LaunchAgent. Windows Task Scheduler and Linux systemd backends remain roadmap items.

Schedule a user-approved shell command for later execution without expanding its authority. Standard permission prompts still apply when the command runs.

## Command-line manager

Use the stdlib-only `deferctl.py` beside this file:

```bash
python3 <SKILL_DIR>/deferctl.py schedule \
  --delay 2h30m \
  --cwd <PROJECT_ROOT> \
  --cmd '<SHELL_COMMAND>' \
  --label '<LABEL>'

python3 <SKILL_DIR>/deferctl.py list
python3 <SKILL_DIR>/deferctl.py status <TASK_ID>
python3 <SKILL_DIR>/deferctl.py cancel <TASK_ID>
```

The state root is `<STATE_DIR>`. It defaults to `~/.local/state/loku-defer` and can be overridden with `LOKU_DEFER_STATE_DIR`. The registry is `<STATE_DIR>/defer-tasks.json`; generated runners are under `<STATE_DIR>/runners/`. launchd plists use the tool-owned name `~/Library/LaunchAgents/loku.defer.<TASK_ID>.plist`.

`list` reports `id`, `label`, `fire_time`, `cwd`, `status`, and whether the selected backend is still active. Status values are:

- `scheduled`: registered and not yet run or canceled;
- `fired`: the runner started, with completion details retained in the registry;
- `canceled`: canceled by `deferctl cancel`;
- `missed`: the deadline passed while the registered backend is no longer active. This is computed during inspection and does not rewrite the stored task.

## Scheduling flow

1. Confirm the host is macOS and `<PROJECT_ROOT>` is an existing, user-authorized directory.
2. Require a non-empty command and a positive delay such as `30s`, `90m`, or `2h30m`.
3. Freeze the exact command, working directory, label, and scheduled time in the confirmation.
4. Run `deferctl.py schedule`. Do not manually create a timer or interpolate the command into AppleScript.
5. Report the task ID, local fire time, backend, `restart_safe` value, target directory, registry path, runner path, and plist path.

## Backend behavior

`deferctl.py` attempts backends in this order:

1. **launchd:** creates `loku.defer.<TASK_ID>.plist` and calls `launchctl load`. Delays of at least one minute use `StartCalendarInterval`; sub-minute delays use `StartInterval`. The runner unloads and removes its one-shot scheduling artifacts after firing. This is the macOS restart-safe backend.
2. **at:** used when launchd is unavailable or rejects the job. Persistence depends on the host's enabled `at` service.
3. **osascript + sleep:** opens the runner in Terminal after an in-process sleep. The task is explicitly recorded with `restart_safe: false` and is lost if the timer process or Mac restarts.

Tests inject a fake backend and must never load a real LaunchAgent. A real smoke test requires explicit user authorization and must be canceled and cleaned up afterward.

## Safety contract

- Scheduling and cancellation may modify only `<STATE_DIR>/defer-tasks.json`, `<STATE_DIR>/runners/<TASK_ID>.sh`, and `loku.defer.<TASK_ID>.plist` in the configured LaunchAgents directory.
- Artifact deletion derives paths from a validated task ID; it does not trust arbitrary paths stored in the registry.
- The delayed shell command may act only within the authority already granted by the user. Credentials, publication, destructive operations, or broader writes require `NEEDS_USER_AUTH`.
- `cancel` unloads the matching launchd job when present, removes only that task's runner and plist, and retains the registry record as `canceled` for auditability.
- Never add flags that bypass the delayed runtime's permission system.

## Confirmation contract

```text
Task ID: <TASK_ID>
Scheduled time: <LOCAL_TIMESTAMP>
Task: <EXACT_SHELL_COMMAND>
Working directory: <PROJECT_ROOT>
Backend: <launchd|at|osascript-sleep>
Restart-safe: <true|false>
State: <STATE_DIR>/defer-tasks.json
Runner: <STATE_DIR>/runners/<TASK_ID>.sh
LaunchAgent: <LAUNCH_AGENTS_DIR>/loku.defer.<TASK_ID>.plist
Permission behavior: standard interactive permissions
```

## Limitations and roadmap

- launchd tasks survive logout/restart as LaunchAgents, but the Mac must be powered on for execution; calendar jobs normally run when the machine next wakes.
- The osascript fallback requires macOS Automation permission and the Mac to stay awake.
- The requested agent or shell CLI must already be installed and authenticated.
- Windows Task Scheduler and Linux systemd/at-native backends are not implemented as supported platform backends in this MVP.
