# ATC v0.8 Test & Evidence Report

Test scope: local Python environment on 2026-10-14 (Hong Kong time). Tests use synthetic inputs and local files. No LLM endpoint was accessed; no real paid or writable external operation was performed.

## 1. Semantic intent benchmark

- Hand-authored cases: **51**. Gold labels include Cantonese, English, code-switching, authorization requests, negation, priority rankings, ambiguous requests and prompt-injection-like quotations.
- Deterministic v0.7 rule baseline: **42/51** exact-case passes (**82.35%**).
- Nine failures: `report-no-send`, `report-send`, `modify-deny`, `modify-approval`, `no-delete`, `job-no-send`, `research-with-quote`, `cost-first-english`, `english-modify`.
- Failing checks: six task-kind mismatches, two permission mismatches, one priority mismatch (several tags overlap; one case may fail one or more checks). Inspect JSON for exact per-case checks rather than trusting this short description.
- **Live LLM evaluations executed: 0**. Missing API credentials; any claimed GPT/Claude accuracy would be fabricated.
- A separate evaluation-only JSON response schema was added to test task-kind/priority/permissions directly. No outputs from this schema can authorize real tools.
- Regression score here is not a statistically representative model benchmark: one curator labelled expected answers, the test set is small, and no independent human rater double-checked all labels.

See `outputs/BASELINE_RULES_EVAL.json` for complete test outputs and per-tag breakdown. No LLM predictions have been invented.

## 2. Compiler

- Tested: consistent contract hash, notes hash, zero open questions, content freeze exact match, scope / permissions, zero spend, catalog path and hash checks, IR strict semantics, original policy declarations retained, and denied capability escalation.
- Compiled IR: `outputs/CURATED_IR.json`.
- `priority`, `decide`, `verify`, `deliverables` are preserved as metadata; the host is explicitly **not** an engine for these semantics.
- A local synthetic content-freeze record is present only to provide a reproducible fixture; it is not genuine human authorization.

## 3. Curated read-only host

- Allowed: listed SHA256-pinned UTF-8 synthetic file read; local document listing.
- Denied: unknown tool (`deploy`), unknown document, altered digest, symlink traversal, oversized file, incorrect root, forged/wrong Ed25519 grant, expired grant, unexpected IR digest.
- Host requires operator-signed time-limited grant, pins corpus root and IR digest, checks grant expiry for each operation.
- `outputs/HOST_DEMO_TRACE.json` confirms synthetic A read, `deploy` denial, cached same-id replay and hash-chain audit check.
- Operator private keys generated for test were held outside the release directory and **not packaged**.
- Security remains conditional on actual process/key isolation, not delivered by the single-process demo.

## 4. Automated test suites

- ATC v0.8 + inherited v0.7 unittest suite: **92** tests, passing (includes **52** new v0.8 tests and **40** inherited tests).
- Historical v0.5 `pytest` suite: **89 passed, 31 subtests passed**.
- Historical v0.4 independent unittest suite: **40 passed**.
- These suites are listed separately because they overlap in historical behavior; do not sum them as independent security guarantees.

## 5. Remaining gaps

1. No real model-run comparison, costs or observed model latency.
2. No independent policy enforcement service, OS sandbox, identity provider, revocation or global nonce ledger.
3. No external public repository/web read connector; only local curated fixture corpus.
4. No runtime implementation of general `DECIDE`, `VERIFY`, human sign-off or end-to-end task completion.
5. No third-party security review, penetration testing, production load testing or formally verified semantics.
