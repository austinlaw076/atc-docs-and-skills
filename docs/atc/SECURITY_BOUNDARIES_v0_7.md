# v0.7 safety boundary and residual risks

- **Never grant permissions from an LLM response**. Schema excludes authorization/scope/limits fields; malformed proposals are refused without writing files.
- **User intent cannot be fully verified with a regex**. Cantonese negations, sarcasm, double negatives, implied consent, quoted text and long conditional sentences remain failure modes. Always compare original text with the interpretation.
- **`content-review.json` is not an approval token**. It binds a local claim to a SHA-256 fingerprint but can be forged by anyone who can edit local files; it does not identify or authenticate an individual.
- **Provenance notes are editable local files**, not secure attestations. Local file integrity protects accidental drift within expected workflows, not an attacker with filesystem access.
- **Read-only handoff contains `mock_only` steps, no execution paths**, and rejects external/mutating actions including purchase, deploy, delete, send and modify.
- **HTTPS adapter sends the user request to an explicitly named third-party provider**. It is opt-in and never called by default. API keys remain environment variables; never paste them in public logs or commit them.
- **HTML review escapes model-controlled strings** and has restrictive Content-Security-Policy; display is passive, with no approve/run UI.
- **Adversarial tests are illustrative, not a security proof**. Production deployment would require independent host-based capability control, secure identity, immutable audit, data/privacy controls, endpoint governance and complete threat modelling.
