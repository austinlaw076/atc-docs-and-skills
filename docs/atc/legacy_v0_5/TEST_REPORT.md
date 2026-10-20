# ATC v0.5 Test Report

Tests executed locally using Python 3.13. All contract inputs and source measurements are synthetic.

| Test suite | Result |
|---|---:|
| v0.5 gateway and adversarial tests | **49 passed** |
| v0.5 retained decision/CLI/schema tests | **40 passed** |
| original v0.4 regression suite | **40 passed**, plus 31 unittest subtests |
| end-to-end CLI demo | **Passed** |
| total named tests | **129 passed** |

Validation covers pinned contract digests, missing approvals, exact action/target/params/cost binding, altered signature, expired signature, signer mismatch, single-use approval, concurrent replay, idempotent request IDs, budget, state transitions, Checkpoint/Resume, signed reviewer assertion, failure-to-block, hash-linked audit event consistency and synthetic decision algorithms.

**Limitations:** no production API/agent integration; not a penetration test; no external source verification; no trusted identity provider, protected DB, private key isolation or independent audit anchoring. Test coverage does not establish security against an agent with unrestricted filesystem or direct tools.

See `outputs/GATEWAY_DEMO.json` and `outputs/SECURITY_REVIEW.md`.
