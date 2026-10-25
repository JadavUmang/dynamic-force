"""Command Executor for Loop Engineering AI: Safe, bounded subprocess execution."""

import dataclasses
import os
import shlex
import subprocess
import time
import pathlib
import sys
from typing import List, Optional, Union


@dataclasses.dataclass
class ExecutionResult:
    """Outcome of a test or command execution."""
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and not self.timed_out and self.error is None

    @property
    def combined_output(self) -> str:
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        if self.error:
            parts.append(f"[Executor Error] {self.error}")
        return "\n".join(parts)


class CommandExecutor:
    """Executes validation and test commands within strict safety boundaries."""

    MAX_OUTPUT_CHARS = 65536  # Cap stdout/stderr to 64KB

    ALLOWED_ROOT_COMMANDS = {
        "python",
        "python3",
        "py",
        "pytest",
        "unittest",
        "npm",
        "npx",
        "node",
        "cargo",
        "go",
        "mvn",
        "gradle",
    }

    def __init__(self, timeout_seconds: float = 30.0, allow_arbitrary_commands: bool = False):
        self.timeout_seconds = timeout_seconds
        self.allow_arbitrary_commands = allow_arbitrary_commands

    def _parse_command(self, command: Union[str, List[str]]) -> List[str]:
        if isinstance(command, list):
            return list(command)
        return shlex.split(command, posix=True)

    def validate_command_safety(self, argv: List[str]) -> None:
        """Validates that command uses safe binaries and doesn't run dangerous shells."""
        if not argv:
            raise ValueError("Command cannot be empty.")

        root_cmd = pathlib.Path(argv[0]).stem.lower()

        # Reject direct shell invocations
        forbidden_shells = {"bash", "sh", "zsh", "cmd", "powershell", "pwsh"}
        if root_cmd in forbidden_shells:
            raise ValueError(f"Direct invocation of shell '{root_cmd}' is prohibited by safety guardrails.")

        if not self.allow_arbitrary_commands and root_cmd not in self.ALLOWED_ROOT_COMMANDS:
            # Check if it starts with current python executable
            current_py = pathlib.Path(sys.executable).stem.lower()
            if root_cmd != current_py:
                raise ValueError(
                    f"Command '{root_cmd}' is not in the allowlist ({', '.join(sorted(self.ALLOWED_ROOT_COMMANDS))})."
                )

    def run(
        self,
        command: Union[str, List[str]],
        cwd: pathlib.Path,
        timeout: Optional[float] = None,
    ) -> ExecutionResult:
        """
        Runs a command synchronously with timeout, output capping, and safety checks.
        Never invokes shell=True.
        """
        start_time = time.perf_counter()
        timeout_to_use = timeout if timeout is not None else self.timeout_seconds
        cmd_str = command if isinstance(command, str) else " ".join(command)

        try:
            argv = self._parse_command(command)
            self.validate_command_safety(argv)

            # If command calls 'python' or 'python3', substitute with current python interpreter if available
            if argv[0].lower() in ("python", "python3", "py"):
                argv[0] = sys.executable

            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            process = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_to_use,
                shell=False,
                env=env,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            stdout = process.stdout or ""
            stderr = process.stderr or ""

            # Cap output to avoid buffer overflow
            if len(stdout) > self.MAX_OUTPUT_CHARS:
                stdout = stdout[: self.MAX_OUTPUT_CHARS] + "\n...[stdout truncated]..."
            if len(stderr) > self.MAX_OUTPUT_CHARS:
                stderr = stderr[: self.MAX_OUTPUT_CHARS] + "\n...[stderr truncated]..."

            return ExecutionResult(
                command=cmd_str,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                timed_out=False,
            )

        except subprocess.TimeoutExpired as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
            stderr = (e.stderr or "") if isinstance(e.stderr, str) else ""
            return ExecutionResult(
                command=cmd_str,
                returncode=124,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                timed_out=True,
                error=f"Command timed out after {timeout_to_use} seconds.",
            )

        except FileNotFoundError as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                command=cmd_str,
                returncode=127,
                stdout="",
                stderr="",
                duration_ms=duration_ms,
                timed_out=False,
                error=f"Executable not found: {e}",
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                command=cmd_str,
                returncode=1,
                stdout="",
                stderr="",
                duration_ms=duration_ms,
                timed_out=False,
                error=str(e),
            )
