# Threat Model & Security Boundaries — v0.5

| Scenario | Prototype response | Remaining caveat |
|---|---|---|
| Agent calls `send_report` without permission | Blocked with `approval_required` | Only if calls go through gateway |
| Token payload altered | Signature rejected | Host must protect public key and DB |
| Approval token reused | Nonce consumed once; no second simulated execution | Request_id replay can return prior result without execution |
| Changed action / target / args / cost | Scope mismatch | Only canonical JSON objects supported |
| Expired approval | Denied | Local clock must be trustworthy |
| Contract changed after approval | Frozen SHA-256 mismatch | Secure contract storage is a host duty |
| Model invents new tool alias | Unknown mock adapter denied | Whitelist is small and static |
| Agent claims research complete | State stays pending until verification/signoff | Underlying facts remain unverified |
| Program crashes and resumes | Checkpoint persists, no automatic tool replay | Real side effects would need an outbox / idempotent adapters |
| Unauthorized DB access | **Not defended** | DB must be isolated and access-controlled |
| Model obtains signing key | **Not defended** | Never give operator key to model; operator CLI must be isolated |
| Privileged DB rewrite | Audit chain can be recomputed | Independent signed audit anchor required |
| Compromised human signer | **Not defended** | Separate identity provider, revocation and MFA needed |

**Important:** Do not expose `operator_cli.py`/private key to any Agent's tool set. The demo runs on a single local machine, so process separation is procedural rather than hardened. This is a *proof of policy logic*, not an operational access-control service.

A future host implementation must pin the trusted policy version outside model-generated files and route **every** privileged API/tool call through a service that the agent cannot bypass. Authorization is a necessary precondition, never a substitute for platform permissions.
