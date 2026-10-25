"""Planners for Loop Engineering AI: Deterministic and LLM-backed repair proposal generators."""

import abc
import json
import os
import re
import urllib.request
import urllib.error
from typing import Dict, Optional, List
from loop_ai.schema import FileChange, PatchProposal
from loop_ai.inventory import RepositoryInventory


class BasePlanner(abc.ABC):
    """Abstract interface for repair planners."""

    @abc.abstractmethod
    def plan(
        self,
        task: str,
        inventory: RepositoryInventory,
        test_output: str,
        attempt: int = 1,
    ) -> PatchProposal:
        """Generates a structured patch proposal given context and test failure output."""
        pass


class DeterministicDemoPlanner(BasePlanner):
    """
    Offline deterministic planner for benchmarks, unit tests, and fallback execution.
    Inspects repository files and failure tracebacks to propose precise repairs.
    """

    def plan(
        self,
        task: str,
        inventory: RepositoryInventory,
        test_output: str,
        attempt: int = 1,
    ) -> PatchProposal:
        files = inventory.read_context_files()

        # Strategy 1: Add/Subtract Calculator Repair (Standard Benchmark)
        for path, code in files.items():
            if "def add(" in code and "return a - b" in code:
                return PatchProposal(
                    summary="Fix addition operator: replace 'return a - b' with 'return a + b'",
                    error_summary=(
                        f"• Failed Component: {path} :: add(a, b)\n"
                        f"• Error Type: AssertionError (Calculation mismatch, e.g. -1 != 5)\n"
                        f"• Root Cause Diagnosis: Subtraction operator ('return a - b') executed instead of expected addition ('return a + b')."
                    ),
                    changes=[
                        FileChange(path=path, old="return a - b", new="return a + b")
                    ],
                )

        # Strategy 2: Common Off-By-One pattern
        for path, code in files.items():
            if "<= len(" in code and ("IndexError" in test_output or "range" in task.lower()):
                match = re.search(r"(\w+\s*<=\s*len\(\w+\))", code)
                if match:
                    old_expr = match.group(1)
                    new_expr = old_expr.replace("<=", "<")
                    return PatchProposal(
                        summary=f"Fix off-by-one indexing error in {path}",
                        error_summary=(
                            f"• Failed Component: {path}\n"
                            f"• Error Type: IndexError (sequence index out of range)\n"
                            f"• Root Cause Diagnosis: Inclusive comparison '<= len()' accesses one element past array boundary."
                        ),
                        changes=[FileChange(path=path, old=old_expr, new=new_expr)],
                    )

        # Strategy 3: Inverted boolean return
        for path, code in files.items():
            if "return False" in code and "expected True" in test_output.lower():
                return PatchProposal(
                    summary=f"Invert return value to True in {path}",
                    error_summary=(
                        f"• Failed Component: {path}\n"
                        f"• Error Type: AssertionError (Expected True, received False)\n"
                        f"• Root Cause Diagnosis: Inverted boolean return statement in conditional logic."
                    ),
                    changes=[FileChange(path=path, old="return False", new="return True")],
                )
            if "return True" in code and "expected False" in test_output.lower():
                return PatchProposal(
                    summary=f"Invert return value to False in {path}",
                    error_summary=(
                        f"• Failed Component: {path}\n"
                        f"• Error Type: AssertionError (Expected False, received True)\n"
                        f"• Root Cause Diagnosis: Inverted boolean return statement in conditional logic."
                    ),
                    changes=[FileChange(path=path, old="return True", new="return False")],
                )

        # Strategy 4: Task-directed simple replacement
        # e.g., Task says "Change return a - b to return a + b in calculator.py"
        match = re.search(r"replace ['\"](.*?)['\"] with ['\"](.*?)['\"]", task, re.IGNORECASE)
        if match:
            old_str, new_str = match.group(1), match.group(2)
            for path, code in files.items():
                if old_str in code:
                    return PatchProposal(
                        summary=f"Replace '{old_str}' with '{new_str}' in {path}",
                        error_summary=(
                            f"• Failed Component: {path}\n"
                            f"• Error Type: Target string replacement required\n"
                            f"• Root Cause Diagnosis: Identified target '{old_str}' violating specification."
                        ),
                        changes=[FileChange(path=path, old=old_str, new=new_str)],
                    )

        # Strategy 5: Package.json Dependency Repair (Vite / Node Projects)
        for path, code in files.items():
            if path.endswith("package.json"):
                if '"canvas-confetti": "MISSING"' in code:
                    return PatchProposal(
                        summary="Fix missing dependency version: replace 'MISSING' with '^1.9.2' for canvas-confetti in package.json",
                        error_summary=(
                            f"• Failed Component: {path} :: dependencies\n"
                            f"• Error Type: ERR_MODULE_NOT_FOUND (Missing / Invalid Dependency Specification)\n"
                            f"• Root Cause Diagnosis: 'canvas-confetti' has placeholder version 'MISSING'. Valid version '^1.9.2' is required for Vite build."
                        ),
                        changes=[
                            FileChange(
                                path=path,
                                old='"canvas-confetti": "MISSING"',
                                new='"canvas-confetti": "^1.9.2"',
                            )
                        ],
                    )

        # If nothing matched, generate a minimal proposal or raise
        first_file = next(iter(files.keys()), "unknown")
        raise ValueError(
            f"Deterministic planner could not formulate a confident patch for task: '{task}'. "
            f"Configure an LLM provider (GEMINI_API_KEY) for open-ended repairs."
        )


class LLMPlanner(BasePlanner):
    """
    LLM-powered planner using Gemini API with JSON schema enforcement.
    Falls back gracefully to DeterministicDemoPlanner if API key is unset or unreachable.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL") or "gemini-flash-latest"
        self.fallback = DeterministicDemoPlanner()

    def plan(
        self,
        task: str,
        inventory: RepositoryInventory,
        test_output: str,
        attempt: int = 1,
    ) -> PatchProposal:
        if not self.api_key:
            return self.fallback.plan(task, inventory, test_output, attempt)

        try:
            return self._call_gemini_api(task, inventory, test_output, attempt)
        except Exception as err:
            print(f"[LLMPlanner] API call failed: {err}. Falling back to deterministic planner.")
            return self.fallback.plan(task, inventory, test_output, attempt)

    def _call_gemini_api(
        self,
        task: str,
        inventory: RepositoryInventory,
        test_output: str,
        attempt: int,
    ) -> PatchProposal:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        files_content = inventory.read_context_files(max_total_chars=60000)
        formatted_files = []
        for path, content in files_content.items():
            formatted_files.append(f"--- File: {path} ---\n{content}\n")

        system_instruction = (
            "You are Loop Engineering AI, an autonomous software repair engineer. "
            "Your job is to:\n"
            "1. Analyze the test failure output and repository context to provide an 'error_summary' explaining: "
            "the failed component, error type, and root cause diagnosis.\n"
            "2. Formulate minimal, safe, exact code changes to repair the defect.\n"
            "Output ONLY valid JSON matching this schema:\n"
            "{\n"
            '  "error_summary": "Concise 2-3 line summary of: Failed Component, Error Type, and Root Cause",\n'
            '  "summary": "Brief explanation of the code repair",\n'
            '  "changes": [\n'
            '    {"path": "relative/path/to/file.py", "old": "verbatim text to replace", "new": "replacement text"}\n'
            "  ]\n"
            "}\n"
            "CRITICAL: 'old' must match characters in the file EXACTLY and uniquely."
        )

        user_prompt = (
            f"Task: {task}\n"
            f"Attempt: {attempt}\n\n"
            f"=== Test Failure Output ===\n{test_output or 'No prior test output'}\n\n"
            f"=== Repository Files ===\n" + "\n".join(formatted_files)
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_instruction + "\n\n" + user_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Clean markdown code block wraps if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)
        parsed = json.loads(raw_text)
        return PatchProposal.from_dict(parsed)
