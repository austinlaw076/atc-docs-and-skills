# ATC v0.6 Security Boundaries

**This is not a production security control.**

- Rule-based language identification is not comprehensive. A missed external-action verb may yield an incomplete risk list. The generated file remains `draft`; unmentioned actions are denied by default.
- YAML directives are not real sandbox permissions. Every real adapter would require an externally enforced, complete allowlist and default deny.
- `approval_required` is not an approval. No trusted signature, active token, UI confirmation or permission escalation exists in the v0.6 Studio.
- v0.5 Mock Gateway is preserved under `legacy_v0_5/` for reference, but **only accepts v0.5 contracts and mock actions**. No auto-conversion is performed.
- Priority inference is narrow, based on exact phrases. No quantitative threshold, weighting, or independent evidence is inferred.
- Programmatic verification can only check output non-emptiness. Human signoff is not represented as complete; `verified_complete` is always false in this standalone authoring CLI.
- The review HTML escapes user-controlled data, includes no network, JavaScript, remote links, approval button or form. It is a local preview, not a trust boundary or authorisation interface.
- Linter checks structure and certain semantic invariants. It cannot prove that output instructions are safe, accurate, consistent with user intent, or that requested external actions are completed.
- Contract diff flags path changes for human review; it is not a full semantic or security review.
