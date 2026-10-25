# Loop Engineering AI - Product Requirements (MVP)
## Problem
Developers repeatedly translate requirements into code, run tests, inspect failures and manually repair defects.
## Target users
Individual developers working in small local Git repositories.
## Goal
Given a bounded task, inspect a repository, propose and apply an approved patch, run validation and report the outcome.
## In scope
Local CLI; repository inventory; task statement; deterministic demo planner; optional LLM adapter in future; bounded retries; explicit user approval; JSONL audit; Git diff; configurable test command.
## Out of scope
Autonomous deployment, unrestricted terminal access, secrets access, production systems, arbitrary repository support, guaranteed successful repairs.
## User story
As a developer, I supply a task and a local repository, review proposed changes, and receive test evidence and a diff.
## Acceptance criteria
- Refuses repositories without .git.
- Refuses dirty working trees by default.
- Rejects file changes outside the repository.
- Runs a configured allowlisted test command with timeout.
- Stops after a finite number of attempts.
- Writes a structured report containing outcome and test output.
- Never reports success unless validation exits zero.
- Never pushes, commits or deploys without separate approval.
## Success metrics
Demo task completes end to end; no out-of-scope writes; logs capture every attempt; user can inspect patch.
