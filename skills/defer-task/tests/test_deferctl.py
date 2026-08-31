import json
import os
import plistlib
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import deferctl


class FakeBackend:
    name = "fake-launchd"
    restart_safe = True

    def __init__(self):
        self.loaded = set()
        self.scheduled_plists = []

    def schedule(self, task, plist_path):
        self.loaded.add(task["id"])
        self.scheduled_plists.append(Path(plist_path))
        return {"backend": self.name, "restart_safe": self.restart_safe}

    def cancel(self, task):
        self.loaded.discard(task["id"])

    def is_active(self, task):
        return task["id"] in self.loaded


class DelayParsingTests(unittest.TestCase):
    def test_supported_delays_convert_to_seconds(self):
        cases = {
            "2h30m": 9_000,
            "90m": 5_400,
            "30s": 30,
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(deferctl.parse_delay(value), expected)

    def test_invalid_or_zero_delay_is_rejected(self):
        for value in ("", "0s", "1m30", "30s2m", "abc"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    deferctl.parse_delay(value)


class LaunchdPlistTests(unittest.TestCase):
    def test_calendar_plist_contains_label_program_and_local_fire_time(self):
        fire_time = datetime(2026, 9, 2, 14, 37, 42, tzinfo=ZoneInfo("Asia/Shanghai"))
        xml_text = deferctl.build_launchd_plist(
            task_id="abc123",
            runner_path=Path("/tmp/state/runners/abc123.sh"),
            fire_time=fire_time,
            start_interval=None,
        )

        mapping = plistlib.loads(xml_text.encode("utf-8"))
        self.assertEqual(mapping["Label"], "loku.defer.abc123")
        self.assertEqual(
            mapping["ProgramArguments"],
            ["/bin/sh", "/tmp/state/runners/abc123.sh"],
        )
        self.assertEqual(
            mapping["StartCalendarInterval"],
            {"Month": 9, "Day": 2, "Hour": 14, "Minute": 37},
        )
        self.assertFalse(mapping["RunAtLoad"])

    def test_subminute_plist_uses_start_interval(self):
        fire_time = datetime(2026, 9, 2, 14, 37, 42, tzinfo=ZoneInfo("Asia/Shanghai"))
        xml_text = deferctl.build_launchd_plist(
            task_id="short",
            runner_path=Path("/tmp/state/runners/short.sh"),
            fire_time=fire_time,
            start_interval=30,
        )

        mapping = plistlib.loads(xml_text.encode("utf-8"))
        self.assertEqual(mapping["StartInterval"], 30)
        self.assertNotIn("StartCalendarInterval", mapping)


class CrossPlatformBackendTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.task = {
            "id": "task001",
            "fire_time": "2026-09-02T14:37:00+08:00",
            "runner_path": "/tmp/state/runners/task001.sh",
        }

    def fake_run(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return type("Result", (), {"returncode": 0, "stdout": "Ready", "stderr": ""})()

    def test_systemd_schedule_uses_user_timer_and_exact_runner(self):
        backend = deferctl.SystemdBackend(
            systemd_run="/usr/bin/systemd-run",
            systemctl="/usr/bin/systemctl",
            platform="linux",
            command_runner=self.fake_run,
        )

        result = backend.schedule(self.task, Path("/unused"))

        self.assertEqual(result["backend"], "systemd-user")
        self.assertTrue(result["restart_safe"])
        self.assertEqual(result["backend_unit"], "loku-defer-task001")
        self.assertEqual(
            self.calls[0][0],
            [
                "/usr/bin/systemd-run",
                "--user",
                "--unit",
                "loku-defer-task001",
                "--on-calendar",
                "2026-09-02T14:37:00+08:00",
                "/bin/sh",
                "/tmp/state/runners/task001.sh",
            ],
        )

    def test_schtasks_schedule_quotes_windows_runner_without_shell(self):
        task = dict(self.task, runner_path=r"C:\State Dir\runners\task001.cmd")
        backend = deferctl.SchtasksBackend(
            schtasks=r"C:\Windows\System32\schtasks.exe",
            platform="win32",
            command_runner=self.fake_run,
        )

        result = backend.schedule(task, Path("C:/unused"))

        self.assertEqual(result["backend"], "windows-task-scheduler")
        args = self.calls[0][0]
        self.assertEqual(args[:4], [r"C:\Windows\System32\schtasks.exe", "/Create", "/F", "/SC"])
        self.assertIn("ONCE", args)
        self.assertIn(r"C:\State Dir\runners\task001.cmd", args)
        self.assertNotIn("shell", self.calls[0][1])

    def test_auto_backend_selects_only_current_platform_candidates(self):
        linux = deferctl.AutoBackend(platform="linux")
        windows = deferctl.AutoBackend(platform="win32")

        self.assertEqual([item.name for item in linux.candidates], ["systemd-user", "at"])
        self.assertEqual([item.name for item in windows.candidates], ["windows-task-scheduler"])

    def test_windows_manager_writes_cmd_runner_for_task_scheduler(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cwd = root / "project"
            cwd.mkdir()
            backend = FakeBackend()
            manager = deferctl.DeferManager(
                state_dir=root / "state",
                launch_agents_dir=root / "scheduler",
                backend=backend,
                platform="win32",
                id_factory=lambda: "windows-task",
            )

            task = manager.schedule("30s", cwd, "echo done")

            runner = Path(task["runner_path"])
            self.assertEqual(runner.suffix, ".cmd")
            self.assertTrue(runner.read_text(encoding="utf-8").startswith("@echo off"))


class ManagerStateMachineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_dir = self.root / "state"
        self.launch_agents_dir = self.root / "LaunchAgents"
        self.backend = FakeBackend()
        self.now = datetime(2026, 8, 31, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.ids = iter(("task001", "task002"))
        self.cwd = self.root / "project"
        self.cwd.mkdir()
        self.manager = deferctl.DeferManager(
            state_dir=self.state_dir,
            launch_agents_dir=self.launch_agents_dir,
            backend=self.backend,
            now=lambda: self.now,
            id_factory=lambda: next(self.ids),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_schedule_list_cancel_persists_state_and_removes_artifacts(self):
        task = self.manager.schedule(
            delay="90m",
            cwd=self.cwd,
            command="printf done",
            label="analysis",
        )

        self.assertEqual(task["status"], "scheduled")
        self.assertEqual(task["fire_time"], "2026-08-31T11:30:00+08:00")
        self.assertTrue(Path(task["runner_path"]).is_file())
        self.assertTrue(os.access(task["runner_path"], os.X_OK))
        self.assertTrue(Path(task["plist_path"]).is_file())
        self.assertEqual(self.manager.list_tasks(), [task])
        registry = json.loads((self.state_dir / "defer-tasks.json").read_text())
        self.assertEqual(registry["tasks"][0]["id"], "task001")

        canceled = self.manager.cancel("task001")

        self.assertEqual(canceled["status"], "canceled")
        self.assertFalse(Path(task["runner_path"]).exists())
        self.assertFalse(Path(task["plist_path"]).exists())
        listed = self.manager.list_tasks()
        self.assertEqual(listed[0]["status"], "canceled")
        self.assertEqual([item for item in listed if item["status"] == "scheduled"], [])
        self.assertFalse(listed[0]["backend_active"])

    def test_status_reports_whether_backend_is_still_active(self):
        self.manager.schedule(delay="30s", cwd=self.cwd, command="true")
        self.assertTrue(self.manager.status("task001")["backend_active"])

        self.backend.loaded.clear()

        self.assertFalse(self.manager.status("task001")["backend_active"])

    def test_inactive_overdue_task_is_reported_missed_without_rewriting_registry(self):
        self.manager.schedule(delay="30s", cwd=self.cwd, command="true")
        self.backend.loaded.clear()
        self.now = datetime(2026, 8, 31, 10, 1, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

        task = self.manager.status("task001")

        self.assertEqual(task["status"], "missed")
        registry = json.loads((self.state_dir / "defer-tasks.json").read_text())
        self.assertEqual(registry["tasks"][0]["status"], "scheduled")

    def test_run_marks_task_fired_executes_once_and_cleans_scheduler_files(self):
        marker = self.cwd / "ran.txt"
        task = self.manager.schedule(
            delay="30s",
            cwd=self.cwd,
            command="printf once > ran.txt",
        )
        self.now += timedelta(seconds=31)

        self.assertEqual(self.manager.run_task("task001"), 0)
        self.assertEqual(self.manager.run_task("task001"), 0)

        self.assertEqual(marker.read_text(), "once")
        fired = self.manager.status("task001")
        self.assertEqual(fired["status"], "fired")
        self.assertEqual(fired["exit_code"], 0)
        self.assertFalse(Path(task["runner_path"]).exists())
        self.assertFalse(Path(task["plist_path"]).exists())

    def test_early_launchd_wakeup_waits_until_exact_fire_time(self):
        sleeps = []

        def fake_sleep(seconds):
            sleeps.append(seconds)
            self.now = self.now.replace(hour=11, minute=30)

        manager = deferctl.DeferManager(
            state_dir=self.state_dir,
            launch_agents_dir=self.launch_agents_dir,
            backend=self.backend,
            now=lambda: self.now,
            sleeper=fake_sleep,
            id_factory=lambda: "minute-guard",
        )
        manager.schedule(delay="90m", cwd=self.cwd, command="true")

        self.assertEqual(manager.run_task("minute-guard"), 0)

        self.assertEqual(sleeps, [5_400])

    def test_cancel_is_idempotent(self):
        self.manager.schedule(delay="30s", cwd=self.cwd, command="true")
        first = self.manager.cancel("task001")
        second = self.manager.cancel("task001")
        self.assertEqual(first["canceled_at"], second["canceled_at"])

    def test_duplicate_generated_id_is_rejected_without_overwriting(self):
        manager = deferctl.DeferManager(
            state_dir=self.state_dir,
            launch_agents_dir=self.launch_agents_dir,
            backend=self.backend,
            now=lambda: self.now,
            id_factory=lambda: "same-id",
        )
        first = manager.schedule(delay="30s", cwd=self.cwd, command="echo first")

        with self.assertRaises(deferctl.TaskExistsError):
            manager.schedule(delay="30s", cwd=self.cwd, command="echo second")

        self.assertEqual(manager.list_tasks()[0]["cmd"], "echo first")
        self.assertEqual(manager.list_tasks()[0]["id"], first["id"])

    def test_registry_failure_rolls_back_loaded_backend_and_artifacts(self):
        class FailingSaveManager(deferctl.DeferManager):
            def _save_registry(self, registry):
                raise OSError("disk full")

        manager = FailingSaveManager(
            state_dir=self.state_dir,
            launch_agents_dir=self.launch_agents_dir,
            backend=self.backend,
            now=lambda: self.now,
            id_factory=lambda: "rollback-id",
        )

        with self.assertRaises(OSError):
            manager.schedule(delay="30s", cwd=self.cwd, command="true")

        self.assertNotIn("rollback-id", self.backend.loaded)
        self.assertFalse((self.state_dir / "runners" / "rollback-id.sh").exists())
        self.assertFalse((self.launch_agents_dir / "loku.defer.rollback-id.plist").exists())

    def test_missing_id_is_rejected_for_status_and_cancel(self):
        with self.assertRaises(deferctl.TaskNotFoundError):
            self.manager.status("missing")
        with self.assertRaises(deferctl.TaskNotFoundError):
            self.manager.cancel("missing")


if __name__ == "__main__":
    unittest.main()
