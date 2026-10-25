import sys

# Ensure UTF-8 console output across all platforms (particularly Windows cp1252)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from loop_ai.env import load_dotenv

# Automatically load environment variables from .env
load_dotenv()

__version__ = "0.1.0"
__author__ = "Loop Engineering AI Team"

from loop_ai.guard import RepositoryGuard
from loop_ai.executor import CommandExecutor, ExecutionResult
from loop_ai.schema import FileChange, PatchProposal, AuditEntry, RepairReport
from loop_ai.patcher import PatchApplier
from loop_ai.planner import BasePlanner, DeterministicDemoPlanner, LLMPlanner
from loop_ai.controller import RepairLoopController

__all__ = [
    "RepositoryGuard",
    "CommandExecutor",
    "ExecutionResult",
    "FileChange",
    "PatchProposal",
    "AuditEntry",
    "RepairReport",
    "PatchApplier",
    "BasePlanner",
    "DeterministicDemoPlanner",
    "LLMPlanner",
    "RepairLoopController",
]
