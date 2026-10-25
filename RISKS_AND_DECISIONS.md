# Risks and Architecture Decisions
- A green test suite is not a correctness proof; tests may be incomplete.
- Arbitrary shell commands are dangerous; allowlist commands and isolate execution.
- Autonomous modifications can destroy work; require clean Git state and backups.
- LLM hallucinations can introduce vulnerabilities; require code review and security checks.
- Retry loops can waste tokens; impose hard attempt, time and cost limits.
- Multi-agent systems add coordination complexity; begin with one orchestrator.
- Two hours permits a narrow demonstrator, not a production autonomous engineer.
