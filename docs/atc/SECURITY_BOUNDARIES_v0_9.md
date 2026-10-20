# ATC v0.9 Security and Trust Boundaries

**Do not use v0.9 for production orchestration or privileged tools.**

### Tested offline properties

- Work order permissions cannot exceed the product action allowlist.
- Unknown/extra fields in governance schemas fail validation.
- Unsafe relative paths and task IDs are rejected.
- Paths outside parent writing roots and graph cycles are rejected.
- Independently parallel orders cannot share declared write locations.
- SQLite checkpoint refuses reuse with another contract hash.
- Work orders cannot move dependents forward before they are accepted.
- Human review criteria cannot be fulfilled by a fake agent response.
- Mock artifact mutation after recording the hash causes verification failure.
- Simulated worker refuses symlink output paths, including directory symlinks.

### Still not guaranteed

- Authorized actors could alter the SQLite DB or its event log. There is no tamper-evident remote audit service.
- Mock actors are all executed by the same Python process/user. There is no process/container sandbox, independent identity, or authentic permission enforcement for real tools.
- Outputs under workspace paths may be changed by the filesystem owner. Artifact hash proof is relative to the stored manifest, which is not independently trusted.
- A2A-shaped messages are illustrative and do not imply transport authentication, compatibility or network delivery.
- The simulated `accepted_mock_only` state does not assert real requirements are met.
- No user approval is synthesized. All proposed adapter packets are offline JSON outputs.

### Suggested next hardening

Separate agent runtime and host into distinct OS identities, use one-time signed grants bound to exact work-order hashes and parameters, enforce isolated filesystems, add independent evidence validators, and test A2A interop using an actual reference implementation before enabling remote sends.
