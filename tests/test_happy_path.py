from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HappyPathContractTests(unittest.TestCase):
    def test_expected_task_is_complete_and_placeholder_free(self):
        text = (ROOT / "examples/happy-path/EXPECTED_TASK.md").read_text(encoding="utf-8")
        self.assertNotIn("[PROJECT", text)
        self.assertIn("Allowed writes", text)
        self.assertIn("Acceptance anchors", text)
        self.assertIn("Stop conditions", text)

    def test_readme_points_to_executable_happy_path_and_verifier(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("examples/happy-path/EXPECTED_TASK.md", text)
        self.assertIn("python3 verify.py", text)


if __name__ == "__main__":
    unittest.main()
