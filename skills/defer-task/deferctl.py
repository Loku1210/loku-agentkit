#!/usr/bin/env python3
"""Restart-aware deferred task manager for the macOS defer-task skill."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


STATE_ENV = "LOKU_DEFER_STATE_DIR"
REGISTRY_NAME = "defer-tasks.json"
TASK_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
DELAY_RE = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


class DeferError(RuntimeError):
    """Base exception for user-facing deferctl failures."""


class TaskExistsError(DeferError):
    pass


class TaskNotFoundError(DeferError):
    pass


class InvalidTaskStateError(DeferError):
    pass


class BackendUnavailableError(DeferError):
    pass


class BackendError(DeferError):
    pass


def parse_delay(value: str) -> int:
    """Parse an ordered h/m/s delay and return a positive second count."""
    match = DELAY_RE.fullmatch(value or "")
    if not match or not any(part is not None for part in match.groups()):
        raise ValueError("delay must look like 2h30m, 90m, or 30s")
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ValueError("delay must be greater than zero")
    return total


def build_launchd_plist(
    task_id: str,
    runner_path: Path,
    fire_time: datetime,
    start_interval: Optional[int] = None,
) -> str:
    """Build a launchd property list for one deferred runner."""
    payload: Dict[str, Any] = {
        "Label": "loku.defer.{}".format(task_id),
        "ProgramArguments": ["/bin/sh", str(runner_path)],
        "RunAtLoad": False,
        "ProcessType": "Background",
    }
    if start_interval is not None:
        payload["StartInterval"] = int(start_interval)
    else:
        local_time = fire_time.astimezone()
        payload["StartCalendarInterval"] = {
            "Month": local_time.month,
            "Day": local_time.day,
            "Hour": local_time.hour,
            "Minute": local_time.minute,
        }
    return plistlib.dumps(payload, fmt=plistlib.FMT_XML, sort_keys=False).decode("utf-8")


def default_state_dir() -> Path:
    configured = os.environ.get(STATE_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "state" / "loku-defer"


def default_launch_agents_dir() -> Path:
    return Path.home() / "Library" / "LaunchAgents"


class LaunchdBackend:
    name = "launchd"
    restart_safe = True

    def __init__(self, launchctl: Optional[str] = None) -> None:
        self.launchctl = launchctl or shutil.which("launchctl")

    def available(self) -> bool:
        return sys.platform == "darwin" and bool(self.launchctl)

    def schedule(self, task: Dict[str, Any], plist_path: Path) -> Dict[str, Any]:
        if not self.available():
            raise BackendUnavailableError("launchctl is unavailable")
        result = subprocess.run(
            [str(self.launchctl), "load", str(plist_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise BackendError("launchctl load failed: {}".format(detail or result.returncode))
        return {"backend": self.name, "restart_safe": self.restart_safe}

    def cancel(self, task: Dict[str, Any]) -> None:
        if not self.available():
            return
        plist_path = task.get("plist_path")
        if plist_path:
            subprocess.run(
                [str(self.launchctl), "unload", str(plist_path)],
                capture_output=True,
                text=True,
            )

    def is_active(self, task: Dict[str, Any]) -> bool:
        if not self.available():
            return False
        label = "loku.defer.{}".format(task["id"])
        result = subprocess.run(
            [str(self.launchctl), "list", label],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0


class AtBackend:
    name = "at"
    restart_safe = True

    def __init__(self, at_command: Optional[str] = None, atrm_command: Optional[str] = None) -> None:
        self.at_command = at_command or shutil.which("at")
        self.atrm_command = atrm_command or shutil.which("atrm")

    def available(self) -> bool:
        return bool(self.at_command and self.atrm_command)

    def schedule(self, task: Dict[str, Any], plist_path: Path) -> Dict[str, Any]:
        if not self.available():
            raise BackendUnavailableError("at/atrm are unavailable")
        fire_time = datetime.fromisoformat(task["fire_time"]).astimezone()
        at_time = fire_time.strftime("%Y%m%d%H%M.%S")
        command = "/bin/sh {}\n".format(shlex.quote(task["runner_path"]))
        result = subprocess.run(
            [str(self.at_command), "-t", at_time],
            input=command,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise BackendError("at scheduling failed: {}".format(detail or result.returncode))
        match = re.search(r"\bjob\s+(\d+)\b", "{}\n{}".format(result.stdout, result.stderr))
        if not match:
            raise BackendError("at did not report a job id")
        return {
            "backend": self.name,
            "backend_job_id": match.group(1),
            "restart_safe": self.restart_safe,
        }

    def cancel(self, task: Dict[str, Any]) -> None:
        job_id = task.get("backend_job_id")
        if self.available() and job_id:
            subprocess.run(
                [str(self.atrm_command), str(job_id)],
                capture_output=True,
                text=True,
            )

    def is_active(self, task: Dict[str, Any]) -> bool:
        job_id = task.get("backend_job_id")
        atq = shutil.which("atq")
        if not (job_id and atq):
            return False
        result = subprocess.run([atq], capture_output=True, text=True)
        if result.returncode != 0:
            return False
        return any(line.split() and line.split()[0] == str(job_id) for line in result.stdout.splitlines())


class SystemdBackend:
    """Restart-safe Linux user timer created with systemd-run."""

    name = "systemd-user"
    restart_safe = True

    def __init__(
        self,
        systemd_run: Optional[str] = None,
        systemctl: Optional[str] = None,
        platform: Optional[str] = None,
        command_runner: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.systemd_run = systemd_run or shutil.which("systemd-run")
        self.systemctl = systemctl or shutil.which("systemctl")
        self.platform = platform or sys.platform
        self.command_runner = command_runner or subprocess.run

    def available(self) -> bool:
        return self.platform.startswith("linux") and bool(self.systemd_run and self.systemctl)

    @staticmethod
    def unit_name(task: Dict[str, Any]) -> str:
        return "loku-defer-{}".format(task["id"])

    def schedule(self, task: Dict[str, Any], plist_path: Path) -> Dict[str, Any]:
        if not self.available():
            raise BackendUnavailableError("systemd user scheduling is unavailable")
        unit = self.unit_name(task)
        result = self.command_runner(
            [
                str(self.systemd_run),
                "--user",
                "--unit",
                unit,
                "--on-calendar",
                task["fire_time"],
                "/bin/sh",
                task["runner_path"],
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise BackendError("systemd-run failed: {}".format(detail or result.returncode))
        return {
            "backend": self.name,
            "backend_unit": unit,
            "restart_safe": self.restart_safe,
        }

    def cancel(self, task: Dict[str, Any]) -> None:
        if not self.available():
            return
        unit = task.get("backend_unit") or self.unit_name(task)
        self.command_runner(
            [str(self.systemctl), "--user", "stop", str(unit)],
            capture_output=True,
            text=True,
        )

    def is_active(self, task: Dict[str, Any]) -> bool:
        if not self.available():
            return False
        unit = task.get("backend_unit") or self.unit_name(task)
        result = self.command_runner(
            [str(self.systemctl), "--user", "is-active", str(unit)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and result.stdout.strip() in {"active", "activating"}


class SchtasksBackend:
    """Windows Task Scheduler adapter; native execution requires a Windows host."""

    name = "windows-task-scheduler"
    restart_safe = True

    def __init__(
        self,
        schtasks: Optional[str] = None,
        platform: Optional[str] = None,
        command_runner: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.schtasks = schtasks or shutil.which("schtasks")
        self.platform = platform or sys.platform
        self.command_runner = command_runner or subprocess.run

    def available(self) -> bool:
        return self.platform == "win32" and bool(self.schtasks)

    @staticmethod
    def task_name(task: Dict[str, Any]) -> str:
        return "LokuDefer\\{}".format(task["id"])

    def schedule(self, task: Dict[str, Any], plist_path: Path) -> Dict[str, Any]:
        if not self.available():
            raise BackendUnavailableError("Windows Task Scheduler is unavailable")
        fire_time = datetime.fromisoformat(task["fire_time"]).astimezone()
        task_name = self.task_name(task)
        result = self.command_runner(
            [
                str(self.schtasks),
                "/Create",
                "/F",
                "/SC",
                "ONCE",
                "/TN",
                task_name,
                "/TR",
                task["runner_path"],
                "/SD",
                fire_time.strftime("%m/%d/%Y"),
                "/ST",
                fire_time.strftime("%H:%M"),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise BackendError("schtasks create failed: {}".format(detail or result.returncode))
        return {
            "backend": self.name,
            "backend_task_name": task_name,
            "restart_safe": self.restart_safe,
        }

    def cancel(self, task: Dict[str, Any]) -> None:
        if not self.available():
            return
        task_name = task.get("backend_task_name") or self.task_name(task)
        self.command_runner(
            [str(self.schtasks), "/Delete", "/F", "/TN", str(task_name)],
            capture_output=True,
            text=True,
        )

    def is_active(self, task: Dict[str, Any]) -> bool:
        if not self.available():
            return False
        task_name = task.get("backend_task_name") or self.task_name(task)
        result = self.command_runner(
            [str(self.schtasks), "/Query", "/TN", str(task_name)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0


class SleepOsaBackend:
    name = "osascript-sleep"
    restart_safe = False

    def __init__(self, osascript: Optional[str] = None) -> None:
        self.osascript = osascript or shutil.which("osascript")

    def available(self) -> bool:
        return sys.platform == "darwin" and bool(self.osascript)

    @staticmethod
    def _apple_string(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def schedule(self, task: Dict[str, Any], plist_path: Path) -> Dict[str, Any]:
        if not self.available():
            raise BackendUnavailableError("osascript is unavailable")
        runner = self._apple_string(task["runner_path"])
        apple_script = (
            'tell application "Terminal" to do script "/bin/sh " & quoted form of "{}"'
        ).format(runner)
        shell = 'sleep "$1"; exec "$2" -e "$3"'
        process = subprocess.Popen(
            [
                "/bin/sh",
                "-c",
                shell,
                "defer-sleep",
                str(task["delay_seconds"]),
                str(self.osascript),
                apple_script,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {
            "backend": self.name,
            "backend_pid": process.pid,
            "restart_safe": self.restart_safe,
        }

    def cancel(self, task: Dict[str, Any]) -> None:
        pid = task.get("backend_pid")
        if not pid:
            return
        try:
            os.kill(int(pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

    def is_active(self, task: Dict[str, Any]) -> bool:
        pid = task.get("backend_pid")
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
        except (ProcessLookupError, PermissionError):
            return False
        return True


class AutoBackend:
    """Select restart-aware scheduler backends for the current platform."""

    name = "auto"
    restart_safe = False

    def __init__(
        self,
        candidates: Optional[Iterable[Any]] = None,
        platform: Optional[str] = None,
    ) -> None:
        self.platform = platform or sys.platform
        if candidates is not None:
            selected = list(candidates)
        elif self.platform == "darwin":
            selected = [LaunchdBackend(), AtBackend(), SleepOsaBackend()]
        elif self.platform.startswith("linux"):
            selected = [SystemdBackend(platform=self.platform), AtBackend()]
        elif self.platform == "win32":
            selected = [SchtasksBackend(platform=self.platform)]
        else:
            selected = []
        self.candidates = selected

    def schedule(self, task: Dict[str, Any], plist_path: Path) -> Dict[str, Any]:
        failures = []
        for backend in self.candidates:
            if hasattr(backend, "available") and not backend.available():
                failures.append("{} unavailable".format(backend.name))
                continue
            try:
                return backend.schedule(task, plist_path)
            except (BackendUnavailableError, BackendError) as exc:
                failures.append("{}: {}".format(backend.name, exc))
        detail = "; ".join(failures) or "no backend is defined for {}".format(self.platform)
        raise BackendUnavailableError("no scheduling backend succeeded ({})".format(detail))

    def _matching(self, task: Dict[str, Any]) -> Optional[Any]:
        name = task.get("backend")
        return next((backend for backend in self.candidates if backend.name == name), None)

    def cancel(self, task: Dict[str, Any]) -> None:
        backend = self._matching(task)
        if backend is not None:
            backend.cancel(task)

    def is_active(self, task: Dict[str, Any]) -> bool:
        backend = self._matching(task)
        return bool(backend and backend.is_active(task))


class DeferManager:
    def __init__(
        self,
        state_dir: Optional[Path] = None,
        launch_agents_dir: Optional[Path] = None,
        backend: Optional[Any] = None,
        now: Optional[Callable[[], datetime]] = None,
        sleeper: Optional[Callable[[float], None]] = None,
        id_factory: Optional[Callable[[], str]] = None,
        platform: Optional[str] = None,
    ) -> None:
        self.state_dir = Path(state_dir or default_state_dir()).expanduser().resolve()
        self.launch_agents_dir = Path(
            launch_agents_dir or default_launch_agents_dir()
        ).expanduser().resolve()
        self.registry_path = self.state_dir / REGISTRY_NAME
        self.runners_dir = self.state_dir / "runners"
        self.platform = platform or sys.platform
        self.backend = backend or AutoBackend(platform=self.platform)
        self.now = now or (lambda: datetime.now().astimezone())
        self.sleeper = sleeper or time.sleep
        self.id_factory = id_factory or (lambda: uuid.uuid4().hex[:12])

    def _ensure_dirs(self) -> None:
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.runners_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.launch_agents_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

    def _load_registry(self) -> Dict[str, Any]:
        if not self.registry_path.exists():
            return {"version": 1, "tasks": []}
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise DeferError("cannot read registry: {}".format(exc))
        if data.get("version") != 1 or not isinstance(data.get("tasks"), list):
            raise DeferError("unsupported or malformed registry")
        return data

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        self._ensure_dirs()
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(self.state_dir),
            prefix=".defer-tasks-",
            delete=False,
        )
        temp_path = Path(handle.name)
        try:
            with handle:
                json.dump(registry, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(str(temp_path), 0o600)
            os.replace(str(temp_path), str(self.registry_path))
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def _runner_path(self, task_id: str) -> Path:
        suffix = ".cmd" if self.platform == "win32" else ".sh"
        return self.runners_dir / "{}{}".format(task_id, suffix)

    def _plist_path(self, task_id: str) -> Path:
        return self.launch_agents_dir / "loku.defer.{}.plist".format(task_id)

    def _validate_id(self, task_id: str) -> None:
        if not TASK_ID_RE.fullmatch(task_id):
            raise DeferError("generated task id is unsafe")

    def _find(self, registry: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        for task in registry["tasks"]:
            if task.get("id") == task_id:
                return task
        raise TaskNotFoundError("task not found: {}".format(task_id))

    def _write_runner(self, task_id: str) -> Path:
        runner_path = self._runner_path(task_id)
        script_path = Path(__file__).resolve()
        argv = [
            sys.executable,
            str(script_path),
            "_run",
            task_id,
            "--state-dir",
            str(self.state_dir),
            "--launch-agents-dir",
            str(self.launch_agents_dir),
        ]
        if self.platform == "win32":
            content = "@echo off\r\n{}\r\n".format(subprocess.list2cmdline(argv))
        else:
            content = "#!/bin/sh\nexec {}\n".format(" ".join(shlex.quote(item) for item in argv))
        runner_path.write_text(content, encoding="utf-8")
        runner_path.chmod(0o700)
        return runner_path

    def _write_plist(self, task: Dict[str, Any]) -> Path:
        plist_path = self._plist_path(task["id"])
        fire_time = datetime.fromisoformat(task["fire_time"])
        start_interval = task["delay_seconds"] if task["delay_seconds"] < 60 else None
        plist_path.write_text(
            build_launchd_plist(
                task_id=task["id"],
                runner_path=Path(task["runner_path"]),
                fire_time=fire_time,
                start_interval=start_interval,
            ),
            encoding="utf-8",
        )
        plist_path.chmod(0o600)
        return plist_path

    def _decorate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(task)
        active = False
        if task.get("status") == "scheduled":
            active = bool(self.backend.is_active(task))
            if not active and self.now() > datetime.fromisoformat(task["fire_time"]):
                result["status"] = "missed"
        result["backend_active"] = active
        return result

    def schedule(
        self,
        delay: str,
        cwd: Path,
        command: str,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        delay_seconds = parse_delay(delay)
        cwd_path = Path(cwd).expanduser().resolve()
        if not cwd_path.is_dir():
            raise DeferError("working directory does not exist: {}".format(cwd_path))
        if not command or not command.strip():
            raise DeferError("command must not be empty")
        task_id = str(self.id_factory())
        self._validate_id(task_id)
        registry = self._load_registry()
        if any(task.get("id") == task_id for task in registry["tasks"]):
            raise TaskExistsError("task id already exists: {}".format(task_id))

        self._ensure_dirs()
        created_at = self.now()
        fire_time = created_at + timedelta(seconds=delay_seconds)
        runner_path = self._runner_path(task_id)
        plist_path = self._plist_path(task_id)
        task: Dict[str, Any] = {
            "id": task_id,
            "label": label or task_id,
            "created_at": created_at.isoformat(),
            "fire_time": fire_time.isoformat(),
            "delay_seconds": delay_seconds,
            "cwd": str(cwd_path),
            "cmd": command,
            "status": "scheduled",
            "backend": "pending",
            "restart_safe": False,
            "runner_path": str(runner_path),
            "plist_path": str(plist_path),
        }
        backend_scheduled = False
        try:
            self._write_runner(task_id)
            self._write_plist(task)
            task.update(self.backend.schedule(task, plist_path))
            backend_scheduled = True
            registry["tasks"].append(task)
            self._save_registry(registry)
        except Exception:
            if backend_scheduled:
                try:
                    self.backend.cancel(self._with_owned_artifact_paths(task))
                except Exception:
                    pass
            runner_path.unlink(missing_ok=True)
            plist_path.unlink(missing_ok=True)
            raise
        return self._decorate(task)

    def list_tasks(self) -> List[Dict[str, Any]]:
        registry = self._load_registry()
        return [self._decorate(task) for task in registry["tasks"]]

    def status(self, task_id: str) -> Dict[str, Any]:
        registry = self._load_registry()
        return self._decorate(self._find(registry, task_id))

    def _remove_owned_artifacts(self, task_id: str) -> None:
        self._validate_id(task_id)
        self._runner_path(task_id).unlink(missing_ok=True)
        self._plist_path(task_id).unlink(missing_ok=True)

    def _with_owned_artifact_paths(self, task: Dict[str, Any]) -> Dict[str, Any]:
        safe_task = dict(task)
        safe_task["runner_path"] = str(self._runner_path(task["id"]))
        safe_task["plist_path"] = str(self._plist_path(task["id"]))
        return safe_task

    def cancel(self, task_id: str) -> Dict[str, Any]:
        registry = self._load_registry()
        task = self._find(registry, task_id)
        if task.get("status") == "fired":
            raise InvalidTaskStateError("a fired task cannot be canceled")
        if task.get("status") != "canceled":
            self.backend.cancel(self._with_owned_artifact_paths(task))
            self._remove_owned_artifacts(task_id)
            task["status"] = "canceled"
            task["canceled_at"] = self.now().isoformat()
            self._save_registry(registry)
        return self._decorate(task)

    def run_task(self, task_id: str) -> int:
        registry = self._load_registry()
        task = self._find(registry, task_id)
        if task.get("status") != "scheduled":
            return 0
        remaining = (datetime.fromisoformat(task["fire_time"]) - self.now()).total_seconds()
        if remaining > 0:
            self.sleeper(remaining)
            registry = self._load_registry()
            task = self._find(registry, task_id)
            if task.get("status") != "scheduled":
                return 0
        task["status"] = "fired"
        task["fired_at"] = self.now().isoformat()
        self._save_registry(registry)
        exit_code = 1
        try:
            result = subprocess.run(task["cmd"], shell=True, cwd=task["cwd"])
            exit_code = result.returncode
            return exit_code
        finally:
            latest = self._load_registry()
            stored = self._find(latest, task_id)
            stored["exit_code"] = exit_code
            stored["finished_at"] = self.now().isoformat()
            self._save_registry(latest)
            self.backend.cancel(self._with_owned_artifact_paths(stored))
            self._remove_owned_artifacts(task_id)


def _print_list(tasks: List[Dict[str, Any]]) -> None:
    columns = ("id", "label", "fire_time", "cwd", "status", "backend_active")
    print("\t".join(columns))
    for task in tasks:
        print("\t".join(str(task.get(column, "")) for column in columns))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deferctl.py")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    schedule_parser = subparsers.add_parser("schedule", help="schedule a deferred command")
    schedule_parser.add_argument("--delay", required=True)
    schedule_parser.add_argument("--cwd", required=True, type=Path)
    schedule_parser.add_argument("--cmd", required=True)
    schedule_parser.add_argument("--label")

    subparsers.add_parser("list", help="list all registered tasks")
    cancel_parser = subparsers.add_parser("cancel", help="cancel a task")
    cancel_parser.add_argument("id")
    status_parser = subparsers.add_parser("status", help="show one task")
    status_parser.add_argument("id")

    run_parser = subparsers.add_parser("_run", help=argparse.SUPPRESS)
    run_parser.add_argument("id")
    run_parser.add_argument("--state-dir", required=True, type=Path)
    run_parser.add_argument("--launch-agents-dir", required=True, type=Path)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.subcommand == "_run":
            manager = DeferManager(
                state_dir=args.state_dir,
                launch_agents_dir=args.launch_agents_dir,
            )
            return manager.run_task(args.id)

        manager = DeferManager()
        if args.subcommand == "schedule":
            task = manager.schedule(args.delay, args.cwd, args.cmd, args.label)
            print(json.dumps(task, indent=2, sort_keys=True))
        elif args.subcommand == "list":
            _print_list(manager.list_tasks())
        elif args.subcommand == "cancel":
            print(json.dumps(manager.cancel(args.id), indent=2, sort_keys=True))
        elif args.subcommand == "status":
            print(json.dumps(manager.status(args.id), indent=2, sort_keys=True))
        return 0
    except (DeferError, ValueError) as exc:
        print("deferctl: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
