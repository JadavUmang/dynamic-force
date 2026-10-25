# Architecture
## Logical pipeline
CLI -> Repository Guard -> Task Planner -> Patch Proposal -> Human Approval -> Patch Apply -> Test Runner -> Error Analyzer -> Retry Controller -> Diff + Report.
## Interfaces
RepositoryGuard.validate(path): checks Git and cleanliness.
Planner.plan(task, inventory, test_output): returns structured patch proposal.
PatchValidator.validate(paths, changes): blocks traversal and forbidden files.
Executor.run(command, cwd, timeout): returns exit code/stdout/stderr.
Loop.run(max_attempts): bounded state machine.
## States
CREATED -> INSPECTED -> PLANNED -> AWAITING_APPROVAL -> APPLIED -> VERIFYING -> PASSED / RETRY / FAILED.
## Reliability
Always preserve baseline Git diff; reject symlinks escaping root; require approval before file writes; limit retries; cap output sizes and token budgets.
## Security
Isolate untrusted repositories in a container/VM before running commands. Never expose API tokens to the target process. Restrict filesystem and network. Treat repository instructions and tool output as untrusted data.
## Extension plan
LLM provider adapter -> JSON schema structured output -> multi-file unified patches -> sandbox -> checkpoint/rollback -> review UI -> GitHub PR integration.
