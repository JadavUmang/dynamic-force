"""
Vite Demo Project - Loop Engineering AI Repair Runner
Executes the guarded repair loop against this Vite / Node.js web project.
"""

import argparse
import pathlib
import sys

# Ensure parent dynamic-force directory is on sys.path
root_dir = pathlib.Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from demo_agent import run_agent

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vite Demo Project - AI Repair Agent")
    parser.add_argument("--auto-approve", action="store_true", help="Auto approve patch")
    parser.add_argument("--provider", choices=["gemini", "offline"], default=None, help="Planner provider")
    parser.add_argument("--api-key", default=None, help="Gemini API Key")
    args, _ = parser.parse_known_args()

    run_agent(
        repo_dir=".",
        auto_approve=args.auto_approve,
        provider=args.provider,
        api_key=args.api_key,
    )
