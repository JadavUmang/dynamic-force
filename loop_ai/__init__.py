"""Loop Engineering AI (Dynamic Force) - Autonomous Engineer Guarded Repair Loop MVP."""

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
