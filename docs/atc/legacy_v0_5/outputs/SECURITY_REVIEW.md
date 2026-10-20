# ATC v0.5 Security Review (Mock Only)

## Attested-by-code demonstration

| Attempt | Simulated Gateway outcome | Why |
|---|---|---|
| `research` in scope | ALLOW | Contract declares `allow` |
| `send_report` without token | DENY | `approval_required` |
| `send_report` with signed scoped token | ALLOW | Valid Ed25519, exact action/target/args/run/contract/cost/expiry |
| Reuse signed token for a second request | DENY | Nonce already consumed |
| Change contract bytes | REJECT | Frozen SHA-256 mismatch |
| Change request parameters | DENY | Token argument SHA-256 mismatch |
| Make a tool-name alias | DENY | Static mock-adapter allowlist |
| Try to spend beyond cap | DENY | Transactional budget check |
| Resume after checkpoint | RECOVER | State and checkpoint restored; no permission granted |
| Result computed, not signed | PENDING | State is `verifying` |
| Fictional operator signs sample | COMPLETED (demo only) | Signed attestation of human checks; not proof of real source truth |

## Unresolved security requirements

**This is not a production host.** Agent must not have alternate direct tool routes, write access to SQLite, access to operator private key, or the ability to initialize an untrusted host. At present there is no operational isolation or integration. No real mail, paid purchase, deployment, web data collection, or secret handling was carried out. The audit hash chain is integrity-checkable but NOT protected from privileged re-writing. Operator signoff in generated example is synthetic, not user consent.
