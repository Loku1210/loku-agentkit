# Runtime compatibility

| Component | macOS | Linux | Windows |
|---|---|---|---|
| Guide, coop, handoff, overnight | Markdown/shell review required | Markdown/shell review required | Markdown usable; shell helpers require a POSIX layer |
| defer-task | **macOS native:** launchd exercised; `at` and osascript fallbacks tested | **Linux static/unit-tested:** systemd-user and `at` command adapters; native host not validated | **Windows static/unit-tested:** Task Scheduler adapter and `.cmd` runner; **Windows native not validated** |

“Static/unit-tested” means exact command construction, state transitions, cancellation,
and status parsing are covered without mutating a host scheduler. It is not a native-host
runtime claim. Unsupported or unavailable schedulers return an actionable error instead
of silently reporting restart safety.

Run `python3 verify.py` for repository checks. A real scheduler smoke changes external
host state and should be performed only with an authorized short-lived test task that is
immediately canceled and inspected.
