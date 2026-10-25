# Technical Design
## Proposed stack
Python 3.12+, standard library CLI, Git subprocess, JSONL logs; future provider adapter for OpenAI/Claude/Gemini.
## CLI contract
loop-ai --repo ./demo --task "Fix addition" --test "python -m unittest discover -v" --attempts 3
## Patch schema
{ "summary": "...", "changes": [{"path":"calculator.py", "old":"return a - b", "new":"return a + b"}], "tests": ["python -m unittest discover -v"] }
## Guardrails
Only approved command presets; no shell=True; reject absolute and parent traversal paths; reject binary files; limit patch size; require human approval.
## Failure policy
If tests fail, collect bounded stderr and request new patch; stop at max attempts; never silently declare success.
## Production gaps
Need container isolation, secure credential boundaries, dependency pinning, stronger patch parser, rollback, and adversarial testing before running on real projects.
