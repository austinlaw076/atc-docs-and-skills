# ATC v0.7 specification — draft fidelity layer

## Protocol layers

1. **Intent source**: unmodified Cantonese/English original request. Content is data, not instructions to the developer/operator.
2. **Contract authoring profile**: YAML frontmatter schema v0.6 + Markdown `CONTEXT`, `CONSTRAINTS`, `TASK`, `INPUT`, `OUTPUT`.
3. **LLM proposal**: optional JSON with an allowlisted set of fields (`summary`, `priority_order`, `deliverable_description`, `open_questions`, `grounding`) — no permission keys.
4. **Provenance notes**: original text, candidate proposal, exact quote references, initial policy, SHA256 of contract and lint results.
5. **Independent semantic lint (partial)**: exact-match grounding; enum checks; detect some priority inversions; default-deny, schema, key and scope validation inherited from v0.6.
6. **Human review**: static HTML/Markdown comparing original and proposed, highlighting changed sensitive fields.
7. **Content freeze**: local acknowledgement binds reviewer-supplied label and timestamp to content hash; cannot grant capabilities or authenticate reviewer.
8. **Read-only handoff plan**: allowlisted mock steps only, with contract hash; host integration not implemented.

## Proposal and rejection policy

An invalid JSON schema, quote absent from original user text, ungrounded priority, or explicitly inverted priority is a **hard error**; no proposed contract or notes files are written. On valid proposal, accepted fields affect the draft only. Summary remains auxiliary text; `goal.outcome` remains verbatim user text.

## Frozen content and revisions

A user may revise the YAML and call `rebind` with the previous sidecar hash, producing a new sidecar. It does not sign changes or authenticate the reviewer. `freeze` requires the new exact SHA256, `I_REVIEWED_CONTRACT_CONTENT`, a nonempty reviewer label and no unresolved `review.open_questions`. Changes to `authorization`, `scope`, `limits`, `priority`, `decide`, `verify` or `goal` require `I_REVIEWED_SENSITIVE_CHANGES`. User-authored sidecars and receipts are **not tamper proof**.

## Non-goals

This release does not verify real-world evidence, determine model accuracy, normalize all language, guarantee output quality, validate true human identity, issue signed grants, connect to real external tools, or execute tasks. No model-authored request can bypass a real host. No real host exists here.

## Compatibility

- `atc6/` and `atc.py` remain operational.
- `legacy_v0_5/` remains operational only as independent historical **mock** reference.
- v0.7 does **not** compile to v0.5 gateway contracts. No misleading automatic conversion.
