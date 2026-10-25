"""Patch Applier: Handles safe validation, application, diff generation, and rollback."""

import difflib
import pathlib
import subprocess
from typing import Dict, List, Optional
from loop_ai.schema import FileChange, PatchProposal
from loop_ai.guard import RepositoryGuard, RepositoryGuardError


class PatchApplicationError(Exception):
    """Raised when a patch proposal fails validation or application."""
    pass


class PatchApplier:
    """Safely applies patches with rollback support and git diff generation."""

    def __init__(self, repo_root: pathlib.Path):
        self.repo_root = repo_root.resolve()
        self._backups: Dict[pathlib.Path, str] = {}

    def validate_patch(self, proposal: PatchProposal) -> None:
        """Verifies that each change in proposal is valid and can be applied unambiguously."""
        RepositoryGuard.validate_patch_changes(self.repo_root, proposal.changes)

        for change in proposal.changes:
            target = self.repo_root / change.path
            content = target.read_text(encoding="utf-8")

            if change.old not in content:
                raise PatchApplicationError(
                    f"Target file '{change.path}' does not contain expected original text:\n{change.old!r}"
                )

            count = content.count(change.old)
            if count > 1:
                raise PatchApplicationError(
                    f"Ambiguous replacement in '{change.path}': original text appears {count} times.\n{change.old!r}"
                )

    def preview_diff(self, proposal: PatchProposal) -> str:
        """Generates unified diff preview without modifying filesystem."""
        diff_lines: List[str] = []

        for change in proposal.changes:
            target = self.repo_root / change.path
            norm_path = change.path.replace("\\", "/")
            if not target.exists():
                old_lines = []
            else:
                old_lines = target.read_text(encoding="utf-8").splitlines(keepends=True)

            # Apply change in memory
            content = "".join(old_lines)
            new_content = content.replace(change.old, change.new, 1)
            new_lines = new_content.splitlines(keepends=True)

            chunk = difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{norm_path}",
                tofile=f"b/{norm_path}",
            )
            diff_lines.extend(chunk)

        return "".join(diff_lines)

    def apply(self, proposal: PatchProposal) -> None:
        """Backs up files and applies changes to disk."""
        self.validate_patch(proposal)
        self._backups.clear()

        # Step 1: Backup all target files
        for change in proposal.changes:
            target = self.repo_root / change.path
            self._backups[target] = target.read_text(encoding="utf-8")

        # Step 2: Write modifications
        try:
            for change in proposal.changes:
                target = self.repo_root / change.path
                orig = self._backups[target]
                updated = orig.replace(change.old, change.new, 1)
                target.write_text(updated, encoding="utf-8")
        except Exception as e:
            # Atomic rollback on any write failure
            self.rollback()
            raise PatchApplicationError(f"Failed to write patch files: {e}") from e

    def rollback(self) -> None:
        """Restores all modified files to pre-patch state."""
        for target, original_text in self._backups.items():
            try:
                target.write_text(original_text, encoding="utf-8")
            except OSError as err:
                print(f"Warning: Failed to rollback file {target}: {err}")
        self._backups.clear()

    def get_git_diff(self, paths: Optional[List[str]] = None) -> str:
        """Retrieves actual git diff from repository."""
        cmd = ["git", "diff", "--no-color"]
        if paths:
            cmd.extend(["--"] + paths)

        try:
            res = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0:
                return res.stdout
        except Exception:
            pass

        return ""

    def commit_repair(
        self,
        summary: str,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
    ) -> Optional[str]:
        """Creates an actual Git commit reflecting the validated repair."""
        try:
            author_name = (
                author_name
                or subprocess.run(["git", "config", "user.name"], cwd=self.repo_root, capture_output=True, text=True).stdout.strip()
                or "Umang Jadav"
            )
            author_email = (
                author_email
                or subprocess.run(["git", "config", "user.email"], cwd=self.repo_root, capture_output=True, text=True).stdout.strip()
                or "jadavumang160@gmail.com"
            )

            # Stage all changes
            subprocess.run(["git", "add", "."], cwd=self.repo_root, capture_output=True, check=True)
            msg = f"fix(repair): {summary}\n\nAutomated code repair verified by Loop Engineering AI."
            commit_res = subprocess.run(
                ["git", "-c", f"user.name={author_name}", "-c", f"user.email={author_email}", "commit", "-m", msg],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if commit_res.returncode == 0:
                commit_info = subprocess.run(
                    ["git", "log", "-1", "--oneline"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                return commit_info
        except Exception:
            pass
        return None

    def push_repair(self) -> Optional[str]:
        """Pushes the repair commit to remote GitHub repository if origin is configured."""
        try:
            remotes = subprocess.run(["git", "remote"], cwd=self.repo_root, capture_output=True, text=True).stdout
            if "origin" in remotes:
                res = subprocess.run(
                    ["git", "push", "origin", "HEAD"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if res.returncode == 0:
                    remote_url = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    return remote_url
        except Exception:
            pass
        return None
