#!/usr/bin/env python3
"""Run deterministic repository checks for loku-agentkit."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(args, *, cwd=ROOT, env=None):
    result = subprocess.run(args, cwd=str(cwd), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{result.stdout}\n{result.stderr}")


def main() -> int:
    run(["bash", "guide/scripts/validate-guide.sh"])
    run(["bash", "-n", "guide/scripts/new-task.sh", "guide/scripts/archive-task.sh", "guide/scripts/validate-guide.sh"])
    run([sys.executable, "-m", "unittest", "tests.test_deferctl", "-v"], cwd=ROOT / "skills/defer-task")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"])
    with tempfile.TemporaryDirectory(prefix="agentkit-happy-") as tmp:
        env = dict(os.environ, AGENTKIT_TASK_STORE=tmp)
        run(["bash", "guide/scripts/new-task.sh", "other", "synthetic-happy-path", "local-agent"], env=env)
        active = next((Path(tmp) / "active").iterdir())
        run(["bash", "guide/scripts/archive-task.sh", active.name, "completed"], env=env)
        if not any((Path(tmp) / "archive").rglob("ARCHIVE_RELOCATION.md")):
            raise RuntimeError("archive smoke did not produce relocation evidence")
    print("loku-agentkit verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
