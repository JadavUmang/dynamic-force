"""CLI entrypoint for Loop Engineering AI."""

import argparse
import os
import pathlib
import sys
import tempfile
import subprocess
from typing import Optional
from loop_ai.controller import RepairLoopController
from loop_ai.planner import LLMPlanner, DeterministicDemoPlanner
from loop_ai.executor import CommandExecutor


def run_demo(provider: Optional[str] = None, api_key: Optional[str] = None):
    """Runs a self-contained demonstration repository with failing test and automated repair."""
    print("=" * 60)
    print("🚀 Loop Engineering AI - Interactive Demonstrator")
    print("=" * 60)

    use_gemini = (provider == "gemini") or bool(api_key) or bool(os.environ.get("GEMINI_API_KEY"))
    if use_gemini:
        planner = LLMPlanner(api_key=api_key)
        print("🧠 AI Provider: Google Gemini LLM (Dynamic Multimodal Engine)")
    else:
        planner = DeterministicDemoPlanner()
        print("⚡ AI Provider: Deterministic Planner (Offline Benchmark Mode)")

    with tempfile.TemporaryDirectory(prefix="loop-demo-") as tmp:
        repo = pathlib.Path(tmp)
        print(f"📁 Initializing temporary demo repository: {repo}")

        # Create broken sample code
        calc_code = "def add(a, b):\n    # Bug: subtraction instead of addition\n    return a - b\n"
        (repo / "calculator.py").write_text(calc_code, encoding="utf-8")

        test_code = (
            "import unittest\n"
            "from calculator import add\n\n"
            "class TestCalculator(unittest.TestCase):\n"
            "    def test_addition(self):\n"
            "        self.assertEqual(add(2, 3), 5)\n"
            "        self.assertEqual(add(10, -4), 6)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n"
        )
        (repo / "test_calculator.py").write_text(test_code, encoding="utf-8")

        # Initialize git repo with same user configuration
        author_name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip() or "Umang Jadav"
        author_email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip() or "jadavumang160@gmail.com"
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "-c", f"user.name={author_name}", "-c", f"user.email={author_email}", "commit", "-m", "Initial broken calculator"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        def print_status(state, msg):
            colors = {
                "CREATED": "\033[94m",
                "INSPECTED": "\033[96m",
                "PLANNED": "\033[93m",
                "AWAITING_APPROVAL": "\033[95m",
                "APPLIED": "\033[94m",
                "VERIFYING": "\033[96m",
                "PASSED": "\033[92m",
                "RETRY": "\033[91m",
                "REJECTED": "\033[91m",
            }
            color = colors.get(state, "\033[0m")
            reset = "\033[0m"
            print(f"{color}[{state}]{reset} {msg}")

        controller = RepairLoopController(
            repo_path=repo,
            task="Fix addition calculation bug in calculator.py",
            test_command="python -m unittest discover -v",
            max_attempts=3,
            auto_approve=False,
            allow_dirty=False,
            planner=planner,
            on_status=print_status,
        )

        report = controller.run()

        print("\n" + "=" * 60)
        print(f"🏁 Final Status: {report.status}")
        print(f"Attempts: {report.attempts_used} / {report.max_attempts}")
        print("=" * 60)
        print("Git Diff:")
        print(report.diff or "No diff")
        print("=" * 60)
        print(f"Demonstration complete. Temporary repo {repo} cleaned up.")


def main():
    parser = argparse.ArgumentParser(
        prog="loop-ai",
        description="Loop Engineering AI: Guarded autonomous repair loop for software repositories.",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Path to local Git repository (default: current directory)",
    )
    parser.add_argument(
        "--task",
        type=str,
        default="Fix failing tests and repair defects",
        help="Description of the repair task to achieve",
    )
    parser.add_argument(
        "--test",
        type=str,
        default="python -m unittest discover -v",
        help="Validation test command to run (default: 'python -m unittest discover -v')",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=3,
        help="Maximum number of repair attempts (default: 3)",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically apply proposed patches without prompting",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow running when Git working tree has uncommitted changes",
    )
    parser.add_argument(
        "--provider",
        choices=["gemini", "offline"],
        default="gemini",
        help="Planner provider (gemini or offline, default: gemini)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Google Gemini API key (or set GEMINI_API_KEY environment variable)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Gemini model to use (default: gemini-2.5-flash)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run self-contained offline demo repository and exit",
    )

    args = parser.parse_args()

    if args.demo:
        run_demo(provider=args.provider, api_key=args.api_key)
        return

    repo_path = pathlib.Path(args.repo).resolve()

    planner = (
        LLMPlanner(api_key=args.api_key, model=args.model)
        if args.provider == "gemini"
        else DeterministicDemoPlanner()
    )

    def print_status(state, msg):
        print(f"[{state}] {msg}")

    controller = RepairLoopController(
        repo_path=repo_path,
        task=args.task,
        test_command=args.test,
        max_attempts=args.attempts,
        auto_approve=args.auto_approve,
        allow_dirty=args.allow_dirty,
        planner=planner,
        on_status=print_status,
    )

    report = controller.run()
    sys.exit(0 if report.status == "PASSED" else 1)


if __name__ == "__main__":
    main()
