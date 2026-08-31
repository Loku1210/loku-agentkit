from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocsContractTests(unittest.TestCase):
    def test_compatibility_matrix_distinguishes_native_and_static_validation(self):
        text = (ROOT / "docs/COMPATIBILITY.md").read_text(encoding="utf-8")
        self.assertIn("macOS native", text)
        self.assertIn("Linux static/unit-tested", text)
        self.assertIn("Windows static/unit-tested", text)
        self.assertIn("Windows native", text)
        self.assertIn("not validated", text)

    def test_defer_skill_no_longer_claims_backends_are_unimplemented(self):
        text = (ROOT / "skills/defer-task/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("systemd-user", text)
        self.assertIn("windows-task-scheduler", text)
        self.assertNotIn("are not implemented", text)


if __name__ == "__main__":
    unittest.main()
