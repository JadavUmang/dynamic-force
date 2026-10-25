"""Repository Inventory: Discovers project files and extracts context for task planning."""

import pathlib
from typing import Dict, List, Set


class RepositoryInventory:
    """Scans and models repository context for planner consumption."""

    IGNORE_DIRS: Set[str] = {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }

    SOURCE_EXTENSIONS: Set[str] = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".json",
        ".md",
        ".go",
        ".rs",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".sql",
        ".sh",
    }

    MAX_FILE_BYTES = 50 * 1024  # 50 KB context cap per file

    def __init__(self, repo_root: pathlib.Path):
        self.repo_root = repo_root.resolve()

    def discover_files(self) -> List[pathlib.Path]:
        """Returns list of relevant relative file paths in repository."""
        collected: List[pathlib.Path] = []
        for path in self.repo_root.rglob("*"):
            if not path.is_file():
                continue
            # Check ignored directories in path parts
            rel = path.relative_to(self.repo_root)
            if any(part in self.IGNORE_DIRS for part in rel.parts):
                continue
            if path.suffix.lower() in self.SOURCE_EXTENSIONS:
                collected.append(rel)
        return sorted(collected)

    def get_file_summaries(self) -> Dict[str, Dict[str, any]]:
        """Gathers metadata (size, lines, extension) for discovered files."""
        summaries = {}
        for rel_path in self.discover_files():
            full_path = self.repo_root / rel_path
            try:
                stat = full_path.stat()
                summaries[str(rel_path).replace("\\", "/")] = {
                    "size": stat.st_size,
                    "extension": rel_path.suffix.lower(),
                }
            except OSError:
                continue
        return summaries

    def read_context_files(self, max_total_chars: int = 100000) -> Dict[str, str]:
        """Reads text content of source files up to total token/character budget."""
        contents: Dict[str, str] = {}
        total_chars = 0

        for rel_path in self.discover_files():
            full_path = self.repo_root / rel_path
            normalized_name = str(rel_path).replace("\\", "/")

            if full_path.stat().st_size > self.MAX_FILE_BYTES:
                continue

            try:
                text = full_path.read_text(encoding="utf-8")
                if total_chars + len(text) > max_total_chars:
                    # Truncate if nearing budget
                    remaining = max_total_chars - total_chars
                    if remaining > 200:
                        contents[normalized_name] = text[:remaining] + "\n...[truncated]..."
                    break
                contents[normalized_name] = text
                total_chars += len(text)
            except (UnicodeDecodeError, OSError):
                continue

        return contents
