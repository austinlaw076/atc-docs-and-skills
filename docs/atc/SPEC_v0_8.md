# ATC v0.8 Technical Specification

## Scope

1. Ground-truth dataset of 51 task-intent statements, with explicit permission expectations, priority order, and task-kind expectations.
2. `rules`, `replay`, `live` evaluation modes; only `live` submits to explicitly supplied HTTPS OpenAI-compatible endpoint. The model receives an evaluation-only schema for task type, ordered metrics, all six sensitive action policies, and exact quote evidence. This differs intentionally from the v0.7 authoring proposal schema, which cannot propose permissions. Every case is scored separately; exact-case agreement requires all fields.
3. Curated-read IR profile, **not a general-purpose policy compiler**.
4. Host runtime for pre-approved, locally pinned, synthetic text files; no remote network I/O, no filesystem writes except SQLite audit.
5. Short-lived Ed25519 grant signed by separate operator key, binds IR digest, catalog digest, canonical corpus root and capabilities.

## Evaluation invariants

- Published gold labels are independent of results; failed cases are retained and exposed.
- The `rules` baseline is explicitly non-LLM and has no inference calls.
- Saved replay result files are explicitly non-live.
- Live evaluation requires caller-provided endpoint/model/environment key; may incur cost, so never automatic. Use `--max-cases 5` as a small paid smoke test. The live model classifier is non-executable; even an erroneous `allow` cannot be passed into a policy grant.
- `exact_case_accuracy = count(all checks true)/count(all cases)`, not accuracy of real-world downstream decisions. Safe defaults require all sensitive actions to remain non-`allow` and ground priority fields with verbatim evidence. Labels are single-author, not double-blind independently adjudicated.

## Compiler preconditions

- Valid ATC v0.6 draft schema, v0.7 `grounded_review` with no error diagnostics.
- Original source request must match sidecar hash and `GOAL` original request.
- Content freeze must have exact hash and `grants_tool_permissions: false`; open questions list must be empty.
- `research_public` explicitly in scope AND allowed; all mutations/external actions must be denied and out of scope.
- Spend limit is exactly zero.
- Explicit catalog with only `corpus_id`, 1–100 `{id,path,sha256}` rows; no duplicates/traversal.
- Every source metric and semantic field from the contract is preserved in `contract_semantics`; non-executable logic has explicit flags.

## Compiler postconditions

- Emit only `read_curated_document` and `list_curated_documents` (fixed mapping to demo public corpus).
- Store original Contract SHA256, original request SHA256, corpus digest and document hashes.
- Embed `compiler_assurance` that explicitly says decision and verification engines are NOT executable.
- `validate_ir` checks exact supported fields/operations, integrity, catalog and required annotations.
- A compiler output **cannot authorize a host operation**.

## Operator-signed host grant

- `sign_grant` only on operator side, with private key outside any agent path/process.
- Ed25519 signature covers IR digest, catalog digest, canonical absolute corpus root, fixed capability list, issued/expiry timestamps, random nonce.
- Host pins the public key supplied by its trusted configuration; MUST NOT accept public keys supplied by the agent.
- Signed grants valid up to 1800 s; checked at initialization and expiry checked per subsequent request.
- Demo CLI still requires explicit acknowledgement; acknowledgement alone is NOT sufficient.
- The prototype does not maintain an external global nonce ledger: the same signed grant could initialize more than one DB before expiry; production should add single-use grants across host instances.

## Runtime invariants

- No runs without operator-signed grant AND fixed IR digest.
- No arbitrary tool/action dispatch; unknown operation => deny.
- File is accessible only by allowlisted document ID/path; each directory component opened with no-follow, regular file only, max 131072 bytes, UTF-8 strict, exact SHA256.
- Root fixed to signed, canonical path; different root rejected.
- `request_id` idempotency: repeated same request gets cached result with `new_read: false`; mismatch rejected.
- SQLite hash-linked event records detect some changes but provide no independent anchoring or immutability.
- A successfully read document is an I/O result; it is NOT verification of accuracy nor task completion.

## Unsupported semantics and known gaps

- v0.6 `decide.method` remains qualitative and not executable by the v0.8 host.
- v0.7 content freeze is a local assertion, not an identity-backed review token.
- No actual LLM model run in this release without user-configured API credentials.
- No web search, GitHub, Gmail, deploy, purchase, external send or payment.
- No host/agent OS process isolation, key management service, multi-tenant access control, rate limiting or tamper-proof logs.
