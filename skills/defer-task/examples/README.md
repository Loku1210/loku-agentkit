# deferctl examples

Schedule one command for 90 minutes from now:

```bash
python3 <SKILL_DIR>/deferctl.py schedule --delay 90m --cwd <PROJECT_ROOT> --cmd 'python3 scripts/check_results.py' --label results-check
```

List all registered tasks and their current backend state:

```bash
python3 <SKILL_DIR>/deferctl.py list
```

Cancel one task by the ID returned from `schedule` or `list`:

```bash
python3 <SKILL_DIR>/deferctl.py cancel <TASK_ID>
```
