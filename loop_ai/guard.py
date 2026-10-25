"""Repository Guard for Loop Engineering AI: Enforces security and integrity boundaries."""

import os
import pathlib
import subprocess
from typing import List, Tuple
from loop_ai.schema import FileChange


class RepositoryGuardError(Exception):
    """Raised when repository integrity or security boundaries are violated."""
    pass


class RepositoryGuard:
    """Guards repositories from invalid states, dangerous file writes, and path traversals."""

    FORBIDDEN_DIR_NAMES = {
        ".git",
        ".svn",
        ".hg",
        ".ssh",
        ".aws",
        ".gnupg",
    }

    FORBIDDEN_FILE_PATTERNS = {
        ".env",
        ".env.local",
        ".env.production",
        ".gitattributes",
        ".gitignore",
        "id_rsa",
        "id_ed25519",
    }

    FORBIDDEN_EXTENSIONS = {
        ".pem",
        ".key",
        ".crt",
        ".pfx",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
    }

    MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB max for patchable source files

    @classmethod
    def validate_repo_root(cls, repo_path: pathlib.Path) -> None:
        """Validates that repo exists and has a .git directory."""
        if not repo_path.exists():
            raise RepositoryGuardError(f"Target repository path does not exist: {repo_path}")
        if not repo_path.is_dir():
            raise RepositoryGuardError(f"Target repository path is not a directory: {repo_path}")

        git_dir = repo_path / ".git"
        if not git_dir.exists():
            raise RepositoryGuardError(
                f"Repository guard failed: '{repo_path}' is not a Git repository (missing .git)."
            )

    AGENT_OUTPUT_FILES = {
        "loop-audit.jsonl",
        "loop-report.json",
        "loop-report.md",
    }

    @classmethod
    def check_clean_working_tree(cls, repo_path: pathlib.Path, allow_dirty: bool = False) -> None:
        """Ensures repository has no uncommitted changes unless allow_dirty is explicitly True."""
        if allow_dirty:
            return

        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode != 0:
                raise RepositoryGuardError(f"Failed to inspect git status: {res.stderr}")
            
            raw_lines = res.stdout.strip().splitlines()
            dirty_lines = []
            for line in raw_lines:
                # git status --porcelain formats as XY path
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    rel_name = pathlib.Path(parts[1]).name.lower()
                    if rel_name in cls.AGENT_OUTPUT_FILES:
                        continue
                dirty_lines.append(line)

            if dirty_lines:
                raise RepositoryGuardError(
                    "Repository guard rejected: Working tree has uncommitted modifications.\n"
                    f"{chr(10).join(dirty_lines)}\n"
                    "Please commit or stash changes before running, or pass --allow-dirty."
                )
        except subprocess.TimeoutExpired:
            raise RepositoryGuardError("Git status command timed out.")

    @classmethod
    def validate_path(cls, repo_root: pathlib.Path, relative_path: str) -> pathlib.Path:
        """
        Validates that a path is relative, stays strictly within the repository root,
        and does not target forbidden or sensitive files.
        """
        # Reject absolute paths or Windows drive letters
        if os.path.isabs(relative_path) or (len(relative_path) > 1 and relative_path[1] == ":"):
            raise RepositoryGuardError(f"Security violation: Absolute paths are forbidden: '{relative_path}'")

        # Resolve path against repo root
        resolved_root = repo_root.resolve()
        target_path = (repo_root / relative_path).resolve()

        # Check for path traversal (must start with repo_root)
        try:
            target_path.relative_to(resolved_root)
        except ValueError:
            raise RepositoryGuardError(
                f"Security violation: Path traversal detected outside repo root: '{relative_path}'"
            )

        # Inspect each path part
        rel_parts = pathlib.Path(relative_path).parts
        for part in rel_parts:
            if part == "..":
                raise RepositoryGuardError(f"Security violation: '..' traversal detected: '{relative_path}'")
            if part.lower() in cls.FORBIDDEN_DIR_NAMES:
                raise RepositoryGuardError(
                    f"Security violation: Modification of forbidden directory '{part}' rejected."
                )

        # Check forbidden filename patterns
        filename = target_path.name.lower()
        if filename in cls.FORBIDDEN_FILE_PATTERNS or any(filename.startswith(p) for p in cls.FORBIDDEN_FILE_PATTERNS):
            raise RepositoryGuardError(
                f"Security violation: Access to sensitive file pattern '{target_path.name}' blocked."
            )

        # Check forbidden extensions
        ext = target_path.suffix.lower()
        if ext in cls.FORBIDDEN_EXTENSIONS:
            raise RepositoryGuardError(
                f"Security violation: File extension '{ext}' is prohibited."
            )

        # Check symlink escapes
        if target_path.is_symlink():
            link_target = target_path.readlink()
            if not link_target.is_absolute():
                link_target = (target_path.parent / link_target).resolve()
            try:
                link_target.relative_to(resolved_root)
            except ValueError:
                raise RepositoryGuardError(
                    f"Security violation: Symlink '{relative_path}' points outside repository."
                )

        return target_path

    @classmethod
    def validate_patch_changes(cls, repo_root: pathlib.Path, changes: List[FileChange]) -> List[Tuple[pathlib.Path, FileChange]]:
        """Validates all file changes in a patch proposal before application."""
        if not changes:
            raise RepositoryGuardError("Patch proposal contains no changes.")

        validated: List[Tuple[pathlib.Path, FileChange]] = []
        for change in changes:
            if not change.path.strip():
                raise RepositoryGuardError("Empty file path in patch change.")

            target_path = cls.validate_path(repo_root, change.path)

            if not target_path.exists():
                raise RepositoryGuardError(f"Target file does not exist: {change.path}")

            if target_path.stat().st_size > cls.MAX_FILE_SIZE_BYTES:
                raise RepositoryGuardError(
                    f"Target file {change.path} exceeds max editable size ({cls.MAX_FILE_SIZE_BYTES} bytes)."
                )

            # Check if file is binary
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    f.read(1024)
            except UnicodeDecodeError:
                raise RepositoryGuardError(f"Target file {change.path} appears to be binary. Modification blocked.")

            validated.append((target_path, change))

        return validated
