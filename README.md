# Loop Engineering AI (Dynamic Force)

**Guarded Autonomous Repair Loop for Software Repositories (MVP)**

[![Tests](https://img.shields.io/badge/tests-7%2F7%20passing-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

Loop Engineering AI is an autonomous, self-healing code repair engine. It inspects local Git repositories, detects failing tests, formulates schema-constrained patch proposals (via deterministic planners or Google Gemini LLM), requests human review, and validates repairs within a bounded state machine.

---

## 🏛 System Architecture

```text
       ┌───────────────────┐
       │     CLI / UI      │
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │ Repository Guard  │ ◄── Enforces .git, clean tree, blocks ../ & secrets
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │  Task Planner     │ ◄── Gemini LLM or Deterministic Offline Planner
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │  Human Approval   │ ◄── Interactive diff review ([y/N] or --auto-approve)
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │  Patch Applier    │ ◄── Atomic apply with checkpoint & rollback
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │ Command Executor  │ ◄── Safe subprocess execution (bounded time & output)
       └─────────┬─────────┘
                 │
       ┌─────────▼─────────┐
       │ Retry Controller  │ ◄── Bounded attempts, audit JSONL, report generation
       └───────────────────┘
```

---

## 🚀 Quick Start

### 1. Run the Interactive Demonstrator
Runs an isolated, end-to-end repair demonstration in a temporary Git repository:
```bash
python demo_agent.py
```
Or via the module:
```bash
python -m loop_ai --demo
```

### 2. Run on Any Local Repository
```bash
python -m loop_ai --repo ./path-to-repo --task "Fix calculation error" --test "python -m unittest discover -v" --attempts 3
```

### CLI Arguments
| Flag | Default | Description |
| :--- | :--- | :--- |
| `--repo` | `.` | Target local Git repository root |
| `--task` | `"Fix failing tests"` | Description of repair goal |
| `--test` | `"python -m unittest discover -v"` | Validation test command |
| `--attempts` | `3` | Maximum retry attempts |
| `--auto-approve` | `false` | Automatically apply patches without prompting |
| `--allow-dirty` | `false` | Permit running on uncommitted working trees |
| `--provider` | `gemini` | Planner provider (`gemini` or `offline`) |
| `--demo` | `false` | Launch temporary interactive demo repository |

---

## 🛡 Guardrails & Security

- **Repository Integrity**: Rejects directories lacking `.git`.
- **Clean State**: Refuses dirty trees by default to prevent destructive modifications.
- **Path Traversal Blocker**: Statically prevents path traversal (`../`, absolute paths, symlinks pointing outside root).
- **Sensitive File Shield**: Blocks modifications to `.git`, `.env*`, `.ssh`, `.aws`, `.pem`, `.key`, and binary files.
- **Process Boundaries**: Does not invoke `shell=True`. Commands are executed with configurable timeouts and output memory caps.
- **Non-Destructive Rollback**: Failed validation or user rejections instantly revert files back to their baseline state.
- **Comprehensive Audit Trail**: Streams every state transition and diff to `loop-audit.jsonl` and writes a final summary to `loop-report.json` and `loop-report.md`.

---

## 🧪 Running Tests

The test suite validates all 7 acceptance criteria defined in [TEST_PLAN.md](file:///e:/hacktoberfest/TEST_PLAN.md):
```bash
python -m unittest discover -s tests -v
```

All 7 test scenarios pass:
1. Baseline failing test detected.
2. Approved change fixes sample function.
3. Validation succeeds and report says PASSED.
4. Rejected approval leaves files unchanged.
5. Incorrect patch exhausts attempts and reports FAILED.
6. Path traversal patch is rejected.
7. Timeout and missing executable recorded as failures.

---

## 📂 Project Structure

```text
├── loop_ai/
│   ├── __init__.py         # Package exports
│   ├── __main__.py         # python -m loop_ai entrypoint
│   ├── cli.py              # Argument parsing and demo runner
│   ├── controller.py       # Main state machine and audit logger
│   ├── executor.py         # Subprocess runner with timeout & output caps
│   ├── guard.py            # Security boundary enforcement
│   ├── inventory.py        # Context scanner and file reader
│   ├── patcher.py          # Unified diff preview, apply, and rollback
│   ├── planner.py          # LLM (Gemini) and deterministic planners
│   └── schema.py           # Dataclasses and JSON serialization
├── tests/
│   └── test_loop.py        # 7 acceptance tests
├── demo_agent.py           # Quick runnable demo
├── ARCHITECTURE.md         # Logical system architecture
├── IMPLEMENTATION_PLAN.md  # Engineering milestones
├── PRD.md                  # Product requirements document
├── RISKS_AND_DECISIONS.md  # Architectural decision records
├── TECHNICAL_DESIGN.md     # Technical specification & contracts
├── TEST_PLAN.md            # Acceptance test plan
└── setup.py                # Setuptools packaging
```
