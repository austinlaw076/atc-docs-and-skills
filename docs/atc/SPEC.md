# ATC v0.6 Authoring Protocol (Prototype Specification)

## Scope & compatibility

This release separates a declarative **authoring protocol** (v0.6) from the previously built offline **mock enforcement protocol** (v0.5). They are not interchangeable. This codebase DOES NOT execute any actions from v0.6 contracts. No approval tokens are issued or accepted by the v0.6 Studio.

## Formal form

A contract is UTF-8 text beginning with YAML frontmatter delimited by `---`, followed by Markdown sections `# CONTEXT`, `# CONSTRAINTS`, `# TASK`, `# INPUT`, `# OUTPUT`. Frontmatter is checked using JSON Schema Draft 2020-12 with duplicate YAML keys rejected. `additionalProperties: false` restricts arbitrary policy fields.

- `contract_version`: exactly `0.6`.
- `status`: exactly `draft` and `lifecycle.initial_state`: exactly `draft`.
- `task_kind`: `research`, `decision`, `writing`, `workflow`.
- `goal`: human-readable desired result and intended audience.
- `scope`: named include/exclude action vocabulary; no overlap.
- `priority.order`: explicit ordinal objective names or empty if missing; no inferred weights.
- `decide.method`: `qualitative` only; `quantitative` is reserved and rejected by linter to prevent implied support.
- `authorization.default`: `deny`; `actions`: allow / approval_required / deny, with high-risk auto-allow rejected; `approval_required` is only a proposed policy value.
- `verify`: one local output nonempty check and one manual human review check; arbitrary other verification is not implemented.
- `limits`: max_spend_hkd forced 0.
- `review`: open questions, assumptions, requested sensitive actions.

## Compiler / reviewer pipeline

1. Accept user request (1 to 12,000 Unicode characters) and slug ID.
2. Extract only recognized task-category words, a small set of explicit priority phrases and requested external-action verbs; preserve original as quoted text.
3. Populate safe defaults: `status=draft`, `default=deny`, high-risk operation blocked or proposed approval-required, spend=0, no real tools.
4. Validate YAML, required Markdown headings, action scope consistency, risk posture, unique check IDs, unsupported algorithms and human-review presence.
5. Render Markdown and fully escaped, offline HTML. No approval form, JS, remote dependencies or external commands.
6. Record proposed contract diffs. Diff always has `approved: false`; flags changes to auth/scope/limits/priority/decide/verify/goal.
7. Standalone output check returns `verified_complete: false`, regardless of input or claimed signoff. The local tool cannot verify an external trusted attestation.

## Known semantic limits

The extractor can incorrectly classify requests; language may be ambiguous; it cannot invent valid benchmarks, reliable source identities, effective authorization, model confidence, faithful quantitative scoring, or real-world success. A parser/linter is not a trustworthy semantic reasoner. If a rule is ambiguous, review and refine the draft; integration with an LLM is a separate, untrusted authoring input step.

## Security boundary

A generated YAML policy is data; the text has **no authority to grant real tool access**. Once real adapters are introduced in a future release, an independently trusted host must enforce permissions, isolate credentials, hash exact requests and check scoped approvals. Never place operator signing keys inside an Agent tool context. Static HTML is **review-only**.
