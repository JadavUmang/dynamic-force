"""Data models and schemas for Loop Engineering AI."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json
import datetime


@dataclass
class FileChange:
    """Represents a discrete replacement change inside a file."""
    path: str
    old: str
    new: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PatchProposal:
    """Represents a proposed patch with summary, changes, and tests."""
    summary: str
    changes: List[FileChange]
    tests: List[str] = field(default_factory=list)
    error_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "changes": [c.to_dict() for c in self.changes],
            "tests": self.tests,
            "error_summary": self.error_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatchProposal":
        changes = [
            FileChange(
                path=c.get("path", ""),
                old=c.get("old", ""),
                new=c.get("new", ""),
            )
            for c in data.get("changes", [])
        ]
        return cls(
            summary=data.get("summary", "Unspecified patch"),
            changes=changes,
            tests=data.get("tests", []),
            error_summary=data.get("error_summary", ""),
        )


@dataclass
class AuditEntry:
    """Structured entry written to loop-audit.jsonl at each state transition."""
    timestamp: str
    attempt: int
    state: str
    patch_summary: Optional[str] = None
    error_summary: Optional[str] = None
    diff: Optional[str] = None
    baseline_exit: Optional[int] = None
    validation_exit: Optional[int] = None
    test_output: Optional[str] = None
    error: Optional[str] = None

    def to_json_line(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class RepairReport:
    """Final structured report output for loop-report.json."""
    timestamp: str
    task: str
    repo_path: str
    status: str  # PASSED | FAILED | REJECTED | ERROR
    attempts_used: int
    max_attempts: int
    baseline_exit: int
    validation_exit: Optional[int]
    diff: str
    test_output: str
    error_summary: str = ""
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        status_badge = "✅ PASSED" if self.status == "PASSED" else f"❌ {self.status}"
        md = [
            f"# Loop Engineering AI Repair Report",
            f"**Timestamp**: `{self.timestamp}`  ",
            f"**Task**: {self.task}  ",
            f"**Status**: {status_badge}  ",
            f"**Attempts Used**: {self.attempts_used} / {self.max_attempts}  ",
            f"**Baseline Test Exit Code**: `{self.baseline_exit}`  ",
            f"**Final Validation Exit Code**: `{self.validation_exit}`  ",
        ]
        if self.error_summary:
            md.extend([
                f"\n## 🔍 LLM Error Log Summary & Diagnosis",
                f"{self.error_summary.strip()}",
            ])
        md.extend([
            f"\n## 🛠️ Code Changes & Patches Applied",
            f"```diff\n{self.diff.strip() or 'No diff'}\n```",
            f"\n## 📊 Test Verification Output",
            f"```text\n{self.test_output.strip() or 'No test output'}\n```",
            f"\n## 📋 Audit Trail Summary\n",
            "| Attempt | State | Outcome | Summary |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for a in self.audit_trail:
            md.append(
                f"| {a.get('attempt', '-')} | `{a.get('state', '-')}` | "
                f"exit {a.get('validation_exit', '-')} | {a.get('patch_summary', a.get('error', '-'))} |"
            )
        return "\n".join(md)

