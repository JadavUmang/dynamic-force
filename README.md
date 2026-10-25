# Loop Engineering AI - Architecture and Demonstrator
This package contains design documents and a **deterministic offline demo** of a guarded repair loop. It does NOT yet call an LLM, generate arbitrary features, or support production autonomy.

## Run demo
```bash
python demo_agent.py
```
The script creates a temporary sample Git repository, shows a failing test, requests approval before changing code, reruns tests, and prints the Git diff. Requires Python 3.10+ and Git.

## Next build step
Replace `propose_demo_patch` with an LLM adapter returning schema-validated patch proposals; retain the approval, sandbox, test, and audit boundaries.
