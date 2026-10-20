# ATC v0.5 — Implemented Specification (Prototype)

## I. Contract grammar

Frontmatter is strict YAML validated with JSON Schema Draft 2020-12; required Markdown headings remain `# CONTEXT`, `# CONSTRAINTS`, `# TASK`, `# INPUT`, `# OUTPUT`. `contract_version` must be `0.5`. Schema retains the v0.4 decision modes (lexicographic, tolerance_then_secondary, weighted_score) and verification definitions. Variables in Markdown are explanatory until interpreted by an outside engine. `@DETERMINISTIC` does not create mathematical determinism.

## II. Enforcement order (mock gateway)

1. Recover frozen `run` and compare exact contract text SHA-256.
2. Check request_id for idempotent replay or incompatible reuse.
3. Require run state among ready/running/awaiting_approval.
4. Require action on hardcoded `MOCK_ACTIONS` allowlist; no aliases or dynamic code loading.
5. Require action in scope.include and not in scope.exclude.
6. Enforce explicit policy default `deny`, or `approval_required`.
7. For approval: validate **Ed25519** signature against public key pinned to run, exact claim fields including action, target, args digest, run, contract hash, exact cost, expiry.
8. For all actions enforce atomic cumulative declared cost ≤ contract cap.
9. Simulate (never call real system), atomically record successful request, consume nonce, update budget, and append audit event in SQLite transaction.
10. Denied actions do not consume tokens and do not invoke adapters.

## III. Token claim schema

```json
{
  "version": "0.5",
  "kind": "tool",
  "run_id": "<random run ID>",
  "contract_sha256": "<sha256 raw file bytes>",
  "action": "send_report",
  "target": "preview",
  "args_sha256": "<sha256 canonical JSON of args>",
  "cost_hkd": "0.00",
  "issued_at": 0,
  "expires_at": 0,
  "nonce": "<random unique value>"
}
```

`human_review` token is similarly signed but action=`human_review`, target=`run_id`, args digest binds the exact `decision_sha256` and all human check IDs. Host *must* keep the private signing key outside the model/tool security boundary.

## IV. State machine

```text
ready  ──allowed mock request────→ running
  │                               │
  ├── guarded request/no token ───┤ → awaiting_approval
  │                               │            │
  └── decision verified ──────────┴─→ verifying  │ signed action → running
                                    │
                         signed human review
                                    ↓
                                completed

failed evidence → blocked (can retry evaluation)
```

All SQLite writes are transactional. Checkpoints store phase and structured data but never give a permission. `completed` is a terminal state; no new action is allowed. SQLite WAL + FULL synchronous used for demo durability. No scheduled background worker.

## V. Audit / evidence

Audit is a locally recomputable SHA-256 chain. It detects simple local edits but **is not tamper-proof**: a privileged attacker can rewrite the whole DB and hashes. Verification results use synthetic input whose publisher identities and evidence fields are **self-asserted**, not independently verified. Completion requires explicit operator attestation but does not independently prove that real-world success criteria were met.

## VI. Hard limits and missing production capabilities

No host authentication or identity proof, private-key isolation, OS sandbox, remote tool enforcement, signed audit root, quota isolation, real external approvals, distributed outbox, full retry policy, cancellation workflow, race safety around real outside side effects, or cross-platform agent integration. `mock_send_report` never sends. This prototype **cannot secure arbitrary agents** and must not be plugged into real privileged tools as-is.
