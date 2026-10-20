# ATC v0.9 proposed priorities

1. **Real-model comparison**: with explicit API authorization and budget, run benchmark against at least two suitable chat-completions models, capture failure classes, latency and costs; inspect a blinded human-reviewed subset for scoring correctness.
2. **True sandboxed host**: separate agent and tool host processes/users, pin trusted public key outside agent control, add revocation and global grant nonce ledger.
3. **First external read-only connector**: start with manually allowlisted public GitHub repository contents; prove connector read limits, data provenance and no write path, then expand cautiously.
4. **Semantic lowering**: support limited executable evaluation/verification operators with validation of equivalence against the original policy, plus property-based tests.
5. **Human contract UI**: minimize review to goal, priorities, evidence, permissions, success criteria and exact changes; keep advanced technical details collapsible.
