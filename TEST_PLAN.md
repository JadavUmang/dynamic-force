# Test Plan
## Functional
1. Baseline failing test is detected.
2. Approved change fixes sample function.
3. Validation succeeds and report says PASSED.
4. Rejected approval leaves files unchanged.
5. Incorrect patch exhausts attempts and reports FAILED.
6. Path traversal patch is rejected.
7. Timeout and missing executable are recorded as failures.
## Security
Try symlink escape, ../ paths, secret files, malicious repository instructions, and commands containing shell metacharacters.
## Nonfunctional
Bounded output, deterministic logs, no secret leakage, timeout, maximum retries.
## Acceptance
Demonstrate a green test run and Git diff after the approved sample patch.
