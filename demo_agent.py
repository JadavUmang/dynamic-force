import argparse
from loop_ai.cli import run_demo

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Loop Engineering AI Demonstrator")
    parser.add_argument("--provider", choices=["gemini", "offline"], default=None, help="Planner provider (gemini or offline)")
    parser.add_argument("--api-key", default=None, help="Google Gemini API Key")
    args, _ = parser.parse_known_args()
    run_demo(provider=args.provider, api_key=args.api_key)
