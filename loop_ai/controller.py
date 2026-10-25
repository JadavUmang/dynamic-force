"""Repair Loop Controller: Orchestrates the bounded state machine and JSONL audit logging."""

import datetime
import json
import pathlib
import sys
from typing import List, Optional, Callable
from loop_ai.schema import AuditEntry, PatchProposal, RepairReport
from loop_ai.guard import RepositoryGuard, RepositoryGuardError
from loop_ai.inventory import RepositoryInventory
from loop_ai.executor import CommandExecutor, ExecutionResult
from loop_ai.patcher import PatchApplier, PatchApplicationError
from loop_ai.planner import BasePlanner, DeterministicDemoPlanner, LLMPlanner


class RepairLoopController:
    """
    Main state machine orchestrating repository validation, baseline testing,
    bounded repair attempts, human approvals, and audit trails.
    """

    def __init__(
        self,
        repo_path: pathlib.Path,
        task: str,
        test_command: str,
        max_attempts: int = 3,
        auto_approve: bool = False,
        allow_dirty: bool = False,
        planner: Optional[BasePlanner] = None,
        executor: Optional[CommandExecutor] = None,
        on_status: Optional[Callable[[str, str], None]] = None,
    ):
        self.repo_path = repo_path.resolve()
        self.task = task
        self.test_command = test_command
        self.max_attempts = max_attempts
        self.auto_approve = auto_approve
        self.allow_dirty = allow_dirty
        self.planner = planner or LLMPlanner()
        self.executor = executor or CommandExecutor(timeout_seconds=30.0)
        self.patcher = PatchApplier(self.repo_path)
        self.inventory = RepositoryInventory(self.repo_path)
        self.on_status = on_status or (lambda state, msg: None)

        self.audit_trail: List[AuditEntry] = []
        self.audit_file = self.repo_path / "loop-audit.jsonl"
        self.report_json_file = self.repo_path / "loop-report.json"
        self.report_md_file = self.repo_path / "loop-report.md"

    def _log_audit(self, entry: AuditEntry) -> None:
        """Appends audit entry to memory and disk in JSONL format."""
        self.audit_trail.append(entry)
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(entry.to_json_line() + "\n")
        except OSError:
            pass

    def run(self) -> RepairReport:
        """Executes the full repair loop state machine."""
        now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()

        # State 1: CREATED
        self.on_status("CREATED", f"Initializing repair loop on {self.repo_path}")
        self._log_audit(AuditEntry(timestamp=now(), attempt=0, state="CREATED"))

        # Guardrails check
        try:
            RepositoryGuard.validate_repo_root(self.repo_path)
            RepositoryGuard.check_clean_working_tree(self.repo_path, allow_dirty=self.allow_dirty)
        except RepositoryGuardError as e:
            self._log_audit(AuditEntry(timestamp=now(), attempt=0, state="GUARD_REJECTED", error=str(e)))
            report = RepairReport(
                timestamp=now(),
                task=self.task,
                repo_path=str(self.repo_path),
                status="GUARD_REJECTED",
                attempts_used=0,
                max_attempts=self.max_attempts,
                baseline_exit=-1,
                validation_exit=None,
                diff="",
                test_output=str(e),
                audit_trail=[a.__dict__ for a in self.audit_trail],
            )
            self._write_reports(report)
            return report

        # State 2: INSPECTED (Baseline test run)
        self.on_status("INSPECTED", f"Running baseline test: {self.test_command}")
        baseline_res = self.executor.run(self.test_command, cwd=self.repo_path)
        self._log_audit(
            AuditEntry(
                timestamp=now(),
                attempt=0,
                state="INSPECTED",
                baseline_exit=baseline_res.returncode,
                test_output=baseline_res.combined_output,
            )
        )

        if baseline_res.returncode == 0:
            self.on_status("PASSED", "Baseline test already passes. No repair needed.")
            report = RepairReport(
                timestamp=now(),
                task=self.task,
                repo_path=str(self.repo_path),
                status="PASSED",
                attempts_used=0,
                max_attempts=self.max_attempts,
                baseline_exit=0,
                validation_exit=0,
                diff="",
                test_output=baseline_res.combined_output,
                audit_trail=[a.__dict__ for a in self.audit_trail],
            )
            self._write_reports(report)
            return report

        # State 3: Bounded Loop
        last_test_output = baseline_res.combined_output
        final_validation_exit: Optional[int] = None
        final_status = "FAILED"
        final_diff = ""
        attempt = 1

        while attempt <= self.max_attempts:
            self.on_status("PLANNED", f"Formulating repair patch (attempt {attempt}/{self.max_attempts})...")

            try:
                proposal: PatchProposal = self.planner.plan(
                    task=self.task,
                    inventory=self.inventory,
                    test_output=last_test_output,
                    attempt=attempt,
                )
            except Exception as e:
                self._log_audit(
                    AuditEntry(
                        timestamp=now(),
                        attempt=attempt,
                        state="PLANNING_ERROR",
                        error=str(e),
                    )
                )
                self.on_status("PLANNING_ERROR", f"Planner failed: {e}")
                attempt += 1
                continue

            # Preview Diff & Approval
            diff_preview = self.patcher.preview_diff(proposal)
            self.on_status(
                "AWAITING_APPROVAL",
                f"Patch formulated: {proposal.summary}",
            )

            # Stage 1: LLM Error Log Analysis Display
            if proposal.error_summary:
                print("\n" + "=" * 60)
                print("🔍 [STAGE 1] LLM ERROR LOG ANALYSIS & DIAGNOSIS")
                print("=" * 60)
                print(proposal.error_summary.strip())
                print("=" * 60)

            # Stage 2: Coding AI Agent Patch Display
            print("\n" + "=" * 60)
            print(f"🤖 [STAGE 2] CODING AI AGENT - PROPOSED CHANGES (Attempt {attempt}/{self.max_attempts})")
            print("=" * 60)
            print(f"Summary: {proposal.summary}")
            print("-" * 60)
            print(diff_preview.strip() if diff_preview else "No diff")
            print("=" * 60)

            # Solicit Human Approval
            approved = self.auto_approve
            if not approved:
                sys.stdout.flush()
                try:
                    user_in = input("\n👉 Apply this patch to disk now? [Y/n]: ").strip().lower()
                    approved = user_in in ("y", "yes", "")
                except (EOFError, KeyboardInterrupt):
                    approved = True
            else:
                print("[Auto-Approve Enabled: Automatically applying patch to disk...]")

            if not approved:
                self.on_status("REJECTED", "Patch rejected by user. Rolling back and terminating.")
                self.patcher.rollback()
                self._log_audit(
                    AuditEntry(
                        timestamp=now(),
                        attempt=attempt,
                        state="REJECTED",
                        patch_summary=proposal.summary,
                        error_summary=proposal.error_summary,
                        diff=diff_preview,
                    )
                )
                final_status = "REJECTED"
                break

            # State 4: APPLIED
            try:
                self.patcher.apply(proposal)
                self.on_status("APPLIED", f"Applied patch for {proposal.summary}")
            except (PatchApplicationError, RepositoryGuardError) as e:
                self.on_status("APPLY_ERROR", f"Failed applying patch: {e}")
                self._log_audit(
                    AuditEntry(
                        timestamp=now(),
                        attempt=attempt,
                        state="APPLY_ERROR",
                        error=str(e),
                    )
                )
                attempt += 1
                continue

            # State 5: VERIFYING
            self.on_status("VERIFYING", f"Running validation test: {self.test_command}")
            test_res = self.executor.run(self.test_command, cwd=self.repo_path)
            last_test_output = test_res.combined_output
            final_validation_exit = test_res.returncode
            current_diff = self.patcher.get_git_diff() or diff_preview

            if test_res.returncode == 0:
                self.on_status("PASSED", "Validation tests PASSED! Repair verified.")
                final_status = "PASSED"
                final_diff = current_diff

                # Commit changes to Git & Push to GitHub if remote exists
                commit_info = self.patcher.commit_repair(summary=proposal.summary)
                pushed_url = self.patcher.push_repair()

                # Stage 3: Coding AI Agent Resolution & Change Summary
                mod_files = ", ".join(c.path for c in proposal.changes) or "repository files"
                print("\n" + "=" * 60)
                print("📊 [STAGE 3] CODING AI AGENT - RESOLUTION & CHANGE SUMMARY")
                print("=" * 60)
                print(f"• Outcome: ✅ PASSED (Repair Verified)")
                print(f"• Files Modified: {mod_files}")
                print(f"• Change Summary: {proposal.summary}")
                if commit_info:
                    print(f"• Git Commit Created: {commit_info}")
                    print("• Commit Author: Umang Jadav <jadavumang160@gmail.com>")
                if pushed_url:
                    print(f"• GitHub Synchronized: Pushed live to {pushed_url}")
                print(f"• Validation Tests: 100% Passing (exit code 0)")
                print(f"• Comprehensive Report: loop-report.md")
                print("=" * 60 + "\n")

                self._log_audit(
                    AuditEntry(
                        timestamp=now(),
                        attempt=attempt,
                        state="PASSED",
                        patch_summary=proposal.summary,
                        error_summary=proposal.error_summary,
                        diff=current_diff,
                        validation_exit=0,
                        test_output=test_res.combined_output,
                    )
                )
                break
            else:
                self.on_status("RETRY", f"Tests failed with exit code {test_res.returncode}. Reverting for next attempt.")
                # Revert to ensure clean baseline for next attempt
                self.patcher.rollback()
                self._log_audit(
                    AuditEntry(
                        timestamp=now(),
                        attempt=attempt,
                        state="RETRY",
                        patch_summary=proposal.summary,
                        error_summary=proposal.error_summary,
                        validation_exit=test_res.returncode,
                        test_output=test_res.combined_output,
                    )
                )
                attempt += 1

        report = RepairReport(
            timestamp=now(),
            task=self.task,
            repo_path=str(self.repo_path),
            status=final_status,
            attempts_used=min(attempt, self.max_attempts),
            max_attempts=self.max_attempts,
            baseline_exit=baseline_res.returncode,
            validation_exit=final_validation_exit,
            diff=final_diff,
            test_output=last_test_output,
            error_summary=proposal.error_summary if 'proposal' in locals() else "",
            audit_trail=[a.__dict__ for a in self.audit_trail],
        )
        self._write_reports(report)
        return report

    def _write_reports(self, report: RepairReport) -> None:
        """Saves loop-report.json and loop-report.md."""
        try:
            self.report_json_file.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
            self.report_md_file.write_text(report.to_markdown(), encoding="utf-8")
        except OSError as e:
            print(f"Warning: Could not write report file: {e}")
