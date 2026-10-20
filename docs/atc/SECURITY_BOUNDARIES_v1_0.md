# ATC v1.0 trust and authority boundaries

## Enforced in the coordinator

- Worker output is data validated against fixed schemas. No worker-supplied shell command, function, arbitrary tool, URL or write path is executed.
- Sources are read and pinned by the trusted host from a bounded, explicitly allowed corpus. Relative path and symlink checks reject escapes. Source snapshot budgets: 200 KB/file, 500 KB total; response budget 500 KB.
- Only Coordinator-selected artifact locations are written. No worker receives a coordinator credential, filesystem-write API or acceptance API through this bridge.
- The authenticated identity comes from the host runtime's start result, not from a response field. Binding and receive are host-only control-plane operations. Review and producer roles cannot share a session identity.
- Request/contract/input/artifact hashes and one-use expiring requests bind review and return packets. Dependency artifacts revalidate before dispatch and acceptance; accepted artifacts revalidate on reporting.
- SQLite transactions serialize state mutations. Exclusive artifact creation prevents replacement. The run is bound to the compiled contract hash.

## Host obligations and measured limitations

The ChatGPT Work live run used actual separate agent sessions. The agents were instructed to use only delivered text and no tools; they complied in the observed run. The underlying host tool catalog was **not technically removed**. This is advisory tool restriction, **not enforced OS/process isolation** or proof of safe execution against a malicious agent.

A bubblewrap namespace probe in this environment failed with `Operation not permitted`. No attempt was made to circumvent it. A deployment requiring adversarial low-privilege guarantees must provide an externally restricted runtime (tools disabled, separate OS identity or a properly enforced sandbox) through `HostRuntime` before granting any external action. `authority.enforcement: host_trust_boundary` explicitly avoids claiming such a sandbox.

The host controls `bind`, `receive`, SQLite, source snapshots and audit records. Someone with host/filesystem access can forge identities or rewrite the database. Hashes are evidence bindings, not signatures or an independent tamper-proof audit log. Artifact path checks do not defend against concurrent malicious filesystem owners/TOCTOU. Do not expose the CLI or its state directory directly to untrusted workers.

Reviewer independence means a different session and role, not a separate model/provider or guaranteed unbiased reasoning. A reviewer can make mistakes. Exact quote validation proves provenance; it does not establish entailment. The independent reviewer supplies that semantic judgment for this limited research scope. Source text/prompt injection is treated as data by instruction; this is not a certified injection defense.

No generated code is executed as a verification step. Unit tests verify the ATC implementation, while JSON schemas, evidence checks and reviewer decisions verify research artifacts. There are no network fetch tools, arbitrary provider endpoints, production actions, paid API integrations, human-approval emulation, A2A transport or external secret requirements in this release.

The runtime adapter bounds local awaits and refuses late responses; stopping or billing remote inference is the host's responsibility. A crash after exclusive artifact creation but before state commit may leave an orphan attempt artifact. It is not accepted; the host must fail the request and retry a new attempt. The local operator may need to inspect orphan files. State/output ownership must remain private to the host.
