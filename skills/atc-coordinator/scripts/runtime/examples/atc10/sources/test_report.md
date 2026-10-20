# ATC v0.9 — Test Report

**Environment:** Python 3.13; PyYAML, jsonschema, cryptography installed.

## Verified checks

- v0.9 + inherited v0.6–v0.8 root test suite: **124 tests — PASS** (includes **32 dedicated v0.9 tests**).
- Legacy v0.5 tests run from the legacy subproject: **40 tests — PASS**. These overlap earlier-version functionality; no claim of unique independent safety assurance.
- CLI `lint` returned PASS for 5 work orders.
- CLI `graph` returned `[['T01','T02','T03'],['T04'],['T05']]`.
- CLI `compile` emitted a traceable IR with parent-and-child document hash.
- `adapter a2a-preview` generated offline JSON with `authorized_to_send: false`.
- `simulate --fail-once T02`: first wave T01 accepted, T02 retry_pending, T03 accepted; second wave T02 accepted; third wave T04 accepted; fourth wave T05 accepted; final status **`accepted_mock_only`**.
- SQLite task states and mock evidence manifest recorded, report generated.
- HTML and Markdown Review generated.

## Negative tests

- Parent/child contract mismatch; illegal permissions and approval escalations; parent permission conflict.
- Unknown requirement/dependency, missing product coverage, unaccepted deliverable, duplicate deliverable ID.
- Cyclic DAG, parallel write path collision, unsafe path segments and task IDs, output symlink.
- Missing qualified agent, forced retry max, dependency blocked, corrupted artifact, unsigned/unimplemented human review not counted as accepted, checkpoint hash mismatch, restart not replaying previously accepted work.

**Scope warning:** simulator test success establishes contract parsing, mock artifact production and control flow only. No actual software development, live LLM inference, real worker concurrency, A2A wire exchange, or independent security audit was performed.
