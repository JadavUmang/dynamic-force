"""Test suite validating all 7 scenarios specified in TEST_PLAN.md."""

import json
import pathlib
import subprocess
import tempfile
import unittest
from loop_ai.controller import RepairLoopController
from loop_ai.guard import RepositoryGuard, RepositoryGuardError
from loop_ai.executor import CommandExecutor
from loop_ai.patcher import PatchApplier, PatchApplicationError
from loop_ai.planner import DeterministicDemoPlanner, BasePlanner
from loop_ai.schema import FileChange, PatchProposal, RepairReport


def create_sample_repo(tmp_path: pathlib.Path, broken: bool = True) -> pathlib.Path:
    """Helper to initialize a sample Git repository."""
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    calc_body = "def add(a, b):\n    return a - b\n" if broken else "def add(a, b):\n    return a + b\n"
    (repo / "calculator.py").write_text(calc_body, encoding="utf-8")

    test_code = (
        "import unittest\n"
        "from calculator import add\n"
        "class TestAdd(unittest.TestCase):\n"
        "    def test_add(self):\n"
        "        self.assertEqual(add(2, 3), 5)\n"
        "if __name__ == '__main__': unittest.main()\n"
    )
    (repo / "test_calculator.py").write_text(test_code, encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Tester", "-c", "user.email=test@test.local", "commit", "-m", "init"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return repo


class TestLoopEngineeringAI(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_1_baseline_failing_test_detected(self):
        """1. Baseline failing test is detected."""
        repo = create_sample_repo(self.tmp, broken=True)
        executor = CommandExecutor()
        result = executor.run("python -m unittest discover -v", cwd=repo)
        self.assertNotEqual(result.returncode, 0, "Baseline should fail on broken repo")
        self.assertIn("AssertionError", result.combined_output)

    def test_2_approved_change_fixes_sample_function(self):
        """2. Approved change fixes sample function."""
        repo = create_sample_repo(self.tmp, broken=True)
        controller = RepairLoopController(
            repo_path=repo,
            task="Fix addition",
            test_command="python -m unittest discover -v",
            max_attempts=1,
            auto_approve=True,
            planner=DeterministicDemoPlanner(),
        )
        report = controller.run()
        self.assertEqual(report.status, "PASSED")
        # Verify file on disk is fixed
        fixed_code = (repo / "calculator.py").read_text(encoding="utf-8")
        self.assertIn("return a + b", fixed_code)

    def test_3_validation_succeeds_and_report_says_passed(self):
        """3. Validation succeeds and report says PASSED."""
        repo = create_sample_repo(self.tmp, broken=True)
        controller = RepairLoopController(
            repo_path=repo,
            task="Fix addition",
            test_command="python -m unittest discover -v",
            max_attempts=2,
            auto_approve=True,
            planner=DeterministicDemoPlanner(),
        )
        report = controller.run()
        self.assertEqual(report.status, "PASSED")
        self.assertEqual(report.validation_exit, 0)
        self.assertTrue((repo / "loop-report.json").exists())
        self.assertTrue((repo / "loop-report.md").exists())
        self.assertTrue((repo / "loop-audit.jsonl").exists())

    def test_4_rejected_approval_leaves_files_unchanged(self):
        """4. Rejected approval leaves files unchanged."""
        repo = create_sample_repo(self.tmp, broken=True)
        original_code = (repo / "calculator.py").read_text(encoding="utf-8")

        controller = RepairLoopController(
            repo_path=repo,
            task="Fix addition",
            test_command="python -m unittest discover -v",
            max_attempts=1,
            auto_approve=False,  # Rejection simulated via monkeypatch or default
            planner=DeterministicDemoPlanner(),
        )
        # Monkeypatch input to reject
        import builtins
        orig_input = builtins.input
        try:
            builtins.input = lambda prompt: "n"
            report = controller.run()
        finally:
            builtins.input = orig_input

        self.assertEqual(report.status, "REJECTED")
        current_code = (repo / "calculator.py").read_text(encoding="utf-8")
        self.assertEqual(current_code, original_code, "Files should be completely unchanged upon rejection")

    def test_5_incorrect_patch_exhausts_attempts_and_reports_failed(self):
        """5. Incorrect patch exhausts attempts and reports FAILED."""
        repo = create_sample_repo(self.tmp, broken=True)

        class BadPlanner(BasePlanner):
            def plan(self, task, inventory, test_output, attempt=1):
                return PatchProposal(
                    summary="Apply bogus patch that does not fix test",
                    changes=[FileChange(path="calculator.py", old="return a - b", new="return a * b")],
                )

        controller = RepairLoopController(
            repo_path=repo,
            task="Fix addition",
            test_command="python -m unittest discover -v",
            max_attempts=2,
            auto_approve=True,
            planner=BadPlanner(),
        )
        report = controller.run()
        self.assertEqual(report.status, "FAILED")
        self.assertEqual(report.attempts_used, 2)
        self.assertNotEqual(report.validation_exit, 0)

    def test_6_path_traversal_patch_is_rejected(self):
        """6. Path traversal patch is rejected."""
        repo = create_sample_repo(self.tmp, broken=True)
        guard = RepositoryGuard()

        with self.assertRaises(RepositoryGuardError):
            guard.validate_path(repo, "../outside.py")

        with self.assertRaises(RepositoryGuardError):
            guard.validate_path(repo, "../../etc/passwd")

        with self.assertRaises(RepositoryGuardError):
            guard.validate_path(repo, ".git/config")

    def test_7_timeout_and_missing_executable_recorded_as_failures(self):
        """7. Timeout and missing executable are recorded as failures."""
        repo = create_sample_repo(self.tmp, broken=True)
        executor = CommandExecutor(timeout_seconds=0.5, allow_arbitrary_commands=True)

        # Missing executable test
        res_missing = executor.run(["non_existent_executable_12345"], cwd=repo)
        self.assertEqual(res_missing.returncode, 127)
        self.assertFalse(res_missing.passed)
        self.assertIn("Executable not found", res_missing.error)

        # Timeout test
        sleep_cmd = "python -c \"import time; time.sleep(2)\""
        res_timeout = executor.run(sleep_cmd, cwd=repo, timeout=0.2)
        self.assertTrue(res_timeout.timed_out)
        self.assertEqual(res_timeout.returncode, 124)
        self.assertIn("timed out", res_timeout.error)


if __name__ == "__main__":
    unittest.main()
