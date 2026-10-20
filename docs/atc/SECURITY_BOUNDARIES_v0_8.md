# Security boundaries: ATC v0.8

**Research prototype, not a security boundary against an arbitrary shell-capable agent.**

## Defended within this controlled test harness

- Unrecognized operations and unlisted documents are denied.
- Contract content edits, sidecar mismatch and freeze mismatch cannot compile.
- Permission increases or any in-scope mutating/external operation are rejected by curated-read compiler.
- IR edits break hash verification unless fully rehashed, and a rehashed IR no longer matches host's pinned digest and operator signature.
- Forged grants, wrong pinned operator key, wrong corpus root and expired grants are rejected.
- Path traversal and final-component symlinks are rejected; intermediate components are opened no-follow via directory file descriptors.
- SHA256 mismatch means no document content is returned.

## Not defended (mandatory for production)

- **Trust-root control:** if agent controls the operator signing key or host-pinned public key/configuration, it can forge grants. Put those outside agent access with independent identities and permissions.
- **Process isolation:** if agent has direct filesystem/shell access it may bypass this adapter; run host under a separate restricted service account/container or equivalent enforced boundary.
- **Credential confidentiality:** do not put secrets in curated corpus or logs; signs do not imply human identity. The demo keys used during testing are not included in release.
- **Audit integrity:** local SQLite hashing is not immutable; a privileged actor may rewrite records consistently. External anchoring/WORM storage needed for serious audit trails.
- **Signer replay:** global nonce consumption not implemented across multiple DB runs.
- **Race/volume:** no resource exhaustion or multi-tenant abuse hardening; no open-document lifecycle state machine for production.
- **Grounding:** source quote matching and Markdown review are heuristics; a passing contract may still misunderstand the user's meaning.
- **Live inference:** OpenAI-compatible provider behavior has not been tested; network calls may reveal benchmark prompt text to provider and incur cost.
- **Catalog trust:** a malicious operator could sign a corpus including private data; host relies on explicitly authorized catalog and pinned root.

## Deployment gate

Do not connect real writable/external systems until an independently pinned trust anchor, OS/process isolation, validated permission graph, revocation, reliable audit, and real model evaluation are in place.
