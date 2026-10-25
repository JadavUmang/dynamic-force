"""
Loop Engineering AI Demonstrator
Runs a guarded repair loop against a real Git repository so all changes
reflect directly in the file and live editor without directly committing.
"""

import argparse
import os
import pathlib
import sys
from loop_ai.controller import RepairLoopController
from loop_ai.planner import LLMPlanner, DeterministicDemoPlanner
from loop_ai.cli import run_demo


def run_agent(repo_dir: str = None, auto_approve: bool = False, provider: str = None, api_key: str = None):
    if repo_dir is None:
        repo_dir = "." if pathlib.Path("calculator.py").exists() else "./demo_project"
    repo_path = pathlib.Path(repo_dir).resolve()

    if not (repo_path / ".git").exists() and not (pathlib.Path(".git").exists()):
        run_demo(provider=provider, api_key=api_key)
        return

    # Use test_calculator.py if present in target directory
    if (repo_path / "test_calculator.py").exists():
        test_command = "python -m unittest test_calculator.py -v"
    else:
        test_command = "python -m unittest discover -v"

    print("=" * 60)
    print("🚀 Loop Engineering AI - Repository Repair Engine")
    print("=" * 60)
    print(f"📁 Target Repository: {repo_path}")
    print(f"📄 Target File to Repair: {repo_path / 'calculator.py'}")
    print(f"🧪 Test Command: {test_command}")

    use_gemini = (provider == "gemini") or bool(api_key) or bool(os.environ.get("GEMINI_API_KEY"))
    if use_gemini:
        planner = LLMPlanner(api_key=api_key)
        print("🧠 AI Engine: Google Gemini LLM (Dynamic Multimodal Engine)")
    else:
        planner = DeterministicDemoPlanner()
        print("⚡ AI Engine: Deterministic Rule Planner (Offline Benchmark Mode)")

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
        repo_path=repo_path,
        task="Fix addition calculation bug in calculator.py",
        test_command=test_command,
        max_attempts=3,
        auto_approve=auto_approve,
        allow_dirty=True,
        planner=planner,
        on_status=print_status,
    )

    report = controller.run()
    print("=" * 60)
    print(f"🏁 Final Status: {report.status}")
    print(f"Audit Trail Written: {repo_path / 'loop-audit.jsonl'}")
    print(f"Full Report: {repo_path / 'loop-report.md'}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loop Engineering AI Demonstrator")
    parser.add_argument("--repo", default=None, help="Target repository (default: current workspace if calculator.py exists)")
    parser.add_argument("--auto-approve", action="store_true", help="Auto approve patch")
    parser.add_argument("--provider", choices=["gemini", "offline"], default=None, help="Planner provider")
    parser.add_argument("--api-key", default=None, help="Gemini API Key")
    parser.add_argument("--temp", action="store_true", help="Run in temporary throwaway directory")
    args, _ = parser.parse_known_args()

    if args.temp:
        run_demo(provider=args.provider, api_key=args.api_key)
    else:
        run_agent(repo_dir=args.repo, auto_approve=args.auto_approve, provider=args.provider, api_key=args.api_key)
