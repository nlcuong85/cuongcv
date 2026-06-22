from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE_SOP = Path(__file__).resolve().parents[1] / "SOP.py"


class SopCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        shutil.copy2(SOURCE_SOP, self.repo / "SOP.py")
        (self.repo / "AGENTS.md").write_text("# Contract\n", encoding="utf-8")
        (self.repo / "README.md").write_text("# Fixture\n", encoding="utf-8")
        app_system = self.repo / "application-system"
        app_system.mkdir()
        (app_system / "AGENTS.md").write_text("# Application contract\n", encoding="utf-8")
        governance = self.repo / "governance"
        governance.mkdir()
        (governance / "SOP_RESEARCH.md").write_text("# Rationale\n", encoding="utf-8")
        self.run_sop("init")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_sop(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.repo / "SOP.py"), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=check,
        )

    def state(self) -> dict:
        return json.loads((self.repo / "governance" / ".sop" / "state.json").read_text(encoding="utf-8"))

    def test_task_completion_requires_evidence(self) -> None:
        result = self.run_sop("done", "T-0001", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--evidence", result.stderr)

    def test_goal_change_starts_fresh_session(self) -> None:
        self.run_sop("session", "--goal", "first", "--task-id", "T-0001")
        first_id = self.state()["work_session"]["id"]
        self.run_sop("session", "--goal", "second", "--task-id", "T-0001")
        second = self.state()["work_session"]
        self.assertNotEqual(first_id, second["id"])
        self.assertEqual(second["goal"], "second")

    def test_run_rejects_cwd_outside_repository(self) -> None:
        result = self.run_sop("run", "--cwd", str(self.repo.parent), "--", sys.executable, "-V", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must stay inside", result.stderr)

    def test_strict_preflight_detects_drift(self) -> None:
        self.run_sop("snapshot", "--hashes")
        (self.repo / "changed.txt").write_text("drift\n", encoding="utf-8")
        result = self.run_sop("preflight", "--strict", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("filesystem change", result.stdout)

    def test_concurrent_mutations_do_not_lose_updates(self) -> None:
        processes = []
        for index in range(12):
            processes.append(
                subprocess.Popen(
                    [sys.executable, str(self.repo / "SOP.py"), "add-task", f"Concurrent {index}", "--id", f"C-{index:02d}"],
                    cwd=self.repo,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, msg=stdout + stderr)
        ids = {task["id"] for task in self.state()["tasks"]}
        self.assertTrue({f"C-{index:02d}" for index in range(12)}.issubset(ids))


if __name__ == "__main__":
    unittest.main()
