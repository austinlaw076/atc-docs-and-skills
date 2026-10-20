# ATC 0.4 — Experimental Specification

**Status:** self-contained prototype, not an official Englang extension.  
**Normative scope:** parsing, deterministic evaluation of synthetic observations, non-authorizing diff, and readable reporting.  
**Non-goals:** runtime enforcement, identity authentication, real evidence verification, safe automated actions, real human approval.

## 1. Document format

A UTF-8 Markdown document with a YAML frontmatter block delimited by `---` lines, then five human-readable level-one headings: `# CONTEXT`, `# CONSTRAINTS`, `# TASK`, `# INPUT`, `# OUTPUT`. A strict parser rejects duplicate YAML keys and unknown frontmatter properties. The file bytes must be fingerprinted before review.

Frontmatter sections:

| Section | Purpose |
|---|---|
| `goal` | Target outcome and audience |
| `scope` | Named actions in and out of the task |
| `priority` | Metrics, eligibility gates, ranking algorithm |
| `decide` | Evidence threshold and conflict/abstention behavior |
| `authorization` | Default deny, per-action advisory policy, declared approval requirements |
| `verify` | Programmatic validations plus mandatory human review |
| `limits` | Declared limits, NOT enforced by this program |
| `deliverables` | Required human-readable outputs |
| `lifecycle` | Declared states, NOT implemented as persistent task orchestration |

Canonical machine vocabulary is always English, while titles and content can be Traditional Chinese. The parsed YAML is the **structured decision source**; freeform Markdown is guidance/documentation and may contain more restrictive instructions, but cannot weaken any YAML policy. The code does not parse natural-language restrictions.

## 2. General Decision DSL

### Metrics
Each metric declares `id`, direction `max` or `min`, unit, and `context` string that identifies a *shared* basis across compared observations. Context equality is string equality, not proof of methodological comparability.

### Eligibility
An array of numeric gates `{metric, op, value}` with `op` one of `>=`, `>`, `<=`, `<`. Candidate ranking happens only after all candidates have the minimum evidence and no unresolved conflict; failure of a gate disqualifies that candidate **only after evidence sufficiency passes for everyone**.

### Algorithms

- `tolerance_then_secondary`: identify the best value of `primary` (max/min aware). Keep all eligible candidates within the **absolute** tolerance in primary units, then sort by `secondary` (max/min aware), then lexical candidate ID. Best-relative tolerance means the primary is an admissibility band, not the lexicographic first priority within it.
- `lexicographic`: compare all declared metrics, in specified `order`; max/min direction is honored; lexical candidate ID resolves a complete numerical tie.
- `weighted_score`: use fixed **bounds** `[lo, hi]` per metric (`lo < hi`), never recompute ranges from current candidates. A max metric has utility `(v-lo)/(hi-lo)`; a min metric has `(hi-v)/(hi-lo)`. Normalize positive weights by their total, sum utilities, rank descending; tie breaks lexically. Any eligible value outside defined fixed bounds causes **escalate/abstain**, never clipping.

Using more than one metric is possible; score weights in unrelated units are meaningful **only if the user approves the scales and weights**. Because bounds, weights and tolerances affect decisions, edits are high-risk contract changes.

## 3. Evidence lineage

Dataset format (`schemas/dataset.schema.json`):

- `candidates[]` identify evaluated options.
- `sources[]` hold a stable local source ID, publisher ID, HTTPS URL, retrieval date, method, positive sample size, and two **assertion** flags.
- `observations[]` hold `(candidate_id, metric, value, source_id, context)` rather than unattached candidate metric claims.
- `synthetic` **MUST** be `true` in this release.

Validation rejects dangling IDs, duplicate candidate/source IDs, duplicate `(candidate, metric, source)` observations, malformed dates, non-finite numbers and conflicting publisher claims tied to the same URL.

For each candidate+metric, accepted observations must have the declared comparison context plus `reviewed_asserted` and `independent_asserted`. Multiple observations from one `publisher_id` are collapsed to that publisher's median; different source IDs from the **same publisher never count twice**. Each metric needs at least `min_distinct_publishers` different publisher IDs. The aggregate value is the median across publisher-level medians. The publisher-level spread must not exceed `max_spread[metric]` **in the metric's native units**. Missing evidence leads to `insufficient_evidence`, and material conflicts to `escalate` or `abstain` per policy. One candidate's missing evidence blocks choosing a winner from the others.

**Caution:** Schema validation, source URL display, and input flags are not evidence that the URL is accurate, accessible, truly independent or freshly reviewed. Automated provenance-linked validation only verifies internal references. HTTP URLs are NOT fetched; all examples use reserved example.org and invented data.

## 4. Authorization and approval

`authorization.default: deny` is mandatory. Every in-scope action must be declared `allow` or `approval_required`. Out-of-scope and explicitly denied actions remain `deny`, even if a human later approves a *different* action. Advisory mode cannot permit known high-risk actions such as `purchase`, `deploy`, `modify_production`, `delete_data` or `transfer_funds`.

`check-action` performs a **dry-run inspection**, not a permission gate. It always returns `enforced: false`, `approval_granted: false`, including `allow_in_contract`. No change in a human-readable Markdown comment gives a tool permission to bypass declared rules.

### Diff

`diff` parses and validates both versions, recursively compares all machine-readable fields, detects Markdown body changes and byte-only frontmatter changes, and computes two SHA-256 fingerprints. A changed contract is a **proposal**, never a live update. Governance-sensitive sections (`scope`, `authorization`, `priority`, `decide`, `verify`, `mode`, budgets) are classified high risk. Other changes can be medium or low. All changes require explicit human approval in a future host integration, including formatting-only fingerprint changes. A deterministic `change_request_id` is a **tracking ID, not an approval signature**.

## 5. Verification and STATE

Exactly three programmatic checks exist in this prototype:

- `provenance-linked`: relational linkage passed schema validation; does not authenticate sources.
- `evidence-sufficiency`: minimum distinct publishers and consistency gates passed.
- `decision-recomputed`: deterministic decision function reached a recommendation or no eligible candidate.

At least one `human` check is mandatory. Human checks always produce `pending`; no system in this package can mark them `pass`. `task_completed` is always `false`. Candidate recommendation is `recommendation_ready_pending_review`, not `completed`. Declared lifecycle fields are validated, not backed by persistent execution state or a durable event log.

## 6. Determinism and identity

- Ranking and tie-breaking use stable candidate IDs and fixed metric definitions.
- Every generated decision file includes exact contract and dataset text SHA-256 hashes (CLI path).
- SHA-256 makes tampering detectable *when a trusted expected hash exists*; it is **not** a signature or human approval.
- The demo is deterministic for identical parsed inputs on a given Python execution environment, but floating-point arithmetic still applies. It does not promise cross-platform cryptographic reproducibility of numeric score formatting.

## 7. Fail-closed behavior

The library rejects unknown decision strategies, unknown observation metric IDs, non-finite numbers, malformed contracts, unsupported programmatic checks, and missing/contradictory evidence. It does not silently drop less convenient candidates. Production use would require stronger typed normalization, independent authentication, URL fetch plus content digests, controlled tool interception, actor identity, approval signature, replay protection, durable state and budget enforcement.

## 8. Host integration requirements (future work)

See `HOST_INTEGRATION_PLAN.md`. No real execution or consent mechanism ships in v0.4.
