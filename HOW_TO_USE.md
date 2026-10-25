# Loop Engineering AI - Complete User Guide

This guide explains how to set up credentials, understand the AI decision pipeline, and run autonomous repairs on any repository.

---

## 🔑 1. Setting Up Credentials (.env)

Loop Engineering AI uses Google Gemini LLM for open-ended, dynamic repairs across any codebase and language.

### Step 1: Create your `.env` file
A template file `.env.example` is provided in the repository root. Copy it or edit `.env`:

```ini
# .env
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
GEMINI_MODEL=gemini-2.5-flash
```

> [!NOTE]
> - You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
> - `.env` is automatically ignored by Git (via `.gitignore`) and blocked from AI modification by `RepositoryGuard`.
> - If no key is set, the system automatically falls back to offline benchmark mode so tests and demos always work.

---

## 🧠 2. How the Decision Engine Works (End-to-End)

```text
 ┌────────────────┐       ┌────────────────────┐       ┌──────────────────────┐
 │  Failing Test  │ ────► │ Command Executor   │ ────► │ Raw Captured Logs    │
 │ (pytest, npm)  │       │ (bounded sandbox)  │       │ (stdout/stderr/exit) │
 └────────────────┘       └────────────────────┘       └──────────┬───────────┘
                                                                  │
 ┌────────────────┐                                               ▼
 │ All Repository │ ─────────────────────────────────────► [ Gemini LLM ]
 │ Source Files   │                                               │
 └────────────────┘                                               │
                                                                  ▼
 ┌────────────────────────────────────────────────────────────────────────────────┐
 │ 🔍 STAGE 1: LLM ERROR LOG ANALYSIS & DIAGNOSIS                                │
 │ • Failed Component: Identifies the exact file and function that crashed       │
 │ • Error Type: Parses assertion or exception (e.g. AssertionError, TypeError)   │
 │ • Root Cause: Diagnoses why the code deviated from expected behavior          │
 └────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌────────────────────────────────────────────────────────────────────────────────┐
 │ 🤖 STAGE 2: CODING AI AGENT - PATCH PROPOSAL                                   │
 │ • Minimal Unified Diff: Generates exact verbatim replacement                   │
 │ • Human-in-the-Loop Gate: Solicits approval [y/N] (or auto-approves)           │
 └────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
 ┌────────────────────────────────────────────────────────────────────────────────┐
 │ 📊 STAGE 3: CODING AI AGENT - CHANGE & RESOLUTION SUMMARY                      │
 │ • Atomic Verification: Re-runs test suite against patched files                │
 │ • Outcome: Marks PASSED or rolls back cleanly if validation fails              │
 │ • Generates final Markdown report: loop-report.md                              │
 └────────────────────────────────────────────────────────────────────────────────┘
```

### Where Does Test Data Come From?
- Test data is **dynamically captured** by running your configured `--test` command.
- The executor captures exit code, standard output, standard error, execution time, and complete stack traces.
- Nothing is mock or static — the AI sees the exact runtime error your tests generated.

### On What Basis Does the AI Make Decisions?
1. **Dynamic Test Traceback**: Identifies failing assertions, line numbers, and error messages.
2. **Context Scanner**: Reads source files across the project (`.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, etc.).
3. **User Task**: The high-level intent specified via `--task`.
4. **Retry History**: Prior failed attempts and error messages are remembered so the AI never repeats a failed fix.

---

## 🚀 3. How to Run the Tool

### Option A: Run on ANY Project (Python, JS, Go, Rust, Java, etc.)
Point the tool to any local Git repository:

```bash
python -m loop_ai --repo "C:\path\to\your-project" --task "Fix calculation error" --test "pytest tests/ -v" --provider gemini
```

#### Node.js / TypeScript Example:
```bash
python -m loop_ai --repo "C:\projects\my-node-app" --task "Fix checkout calculation" --test "npm test" --provider gemini
```

#### Auto-Approve (Autonomous CI/CD Mode):
```bash
python -m loop_ai --repo "C:\path\to\your-project" --task "Fix bug" --test "pytest" --auto-approve
```

---

### Option B: Run the Windows 1-Click Demo Project

A ready-to-present sample repository `demo_project` is included in this repository:

1. **See the Error**: Double-click `demo_project\run_tests.bat` (shows failing test).
2. **Run Interactive Repair**: Double-click `repair_demo_project.bat` (shows 3-stage LLM diagnosis and diff, press `y` to apply).
3. **Run Auto Repair**: Double-click `repair_demo_project_auto.bat` (runs autonomously without prompt).
4. **Reset Bug**: Double-click `reset_demo_project.bat` (restores broken state for another presentation).

---

### Option C: Run Acceptance Tests (7/7 Scenarios)
Verify security boundaries, path traversal prevention, and atomic rollback:
```bash
.\run_tests.bat
```
*(Or `python -m unittest discover -s tests -v`)*

---

## ⚙️ CLI Flags Reference

| Flag | Default | Description |
| :--- | :--- | :--- |
| `--repo` | `.` | Target local Git repository root path |
| `--task` | `"Fix failing tests"` | Description of repair goal |
| `--test` | `"python -m unittest discover -v"` | Validation test command |
| `--attempts` | `3` | Maximum retry attempts |
| `--auto-approve` | `false` | Automatically apply patches without prompting |
| `--allow-dirty` | `false` | Permit running on uncommitted working trees |
| `--provider` | `gemini` | Planner provider (`gemini` or `offline`) |
| `--api-key` | `None` | Google Gemini API key (or set in `.env`) |
| `--model` | `gemini-2.5-flash` | Gemini model name |
| `--demo` | `false` | Launch temporary interactive demo repository |
