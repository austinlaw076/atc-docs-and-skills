# ATC v1.0 — Evidence-bound research workflow

## Purpose, audience, scope, success criteria

For a trusted Host/Coordinator operator turning a **structured PRD** into several read-only research work orders, delegating them to distinct real LLM sessions, and accepting results only after machine checks plus an independent reviewer session. The pilot corpus is the supplied v0.9 test report and source snapshots. This is not a general software-development agent, arbitrary PRD prose parser, A2A service, or production security sandbox.

Success requires:
1. Deterministic PRD compilation with requirement coverage, source allowlists and dependency DAG validation.
2. Real host sessions with authenticated host-returned identities; workers return JSON only and do not choose executable tools or output paths.
3. JSON Schema checks; nonempty, unique claims; requirement references; per-claim exact source quotes, one-based line ranges and SHA-256 snapshot binding.
4. An independently bound reviewer checks every claim and all work-order acceptance criteria. Producer identities cannot act as reviewer anywhere in the run. Acceptance requires supported claims and `acceptance_satisfied: true`.
5. The Coordinator, never the worker/reviewer, changes task/product state. Reviews bind the exact artifact hash and dispatch input, request and contract hashes.
6. Dependencies unblock only after acceptance and fresh integrity rechecks. Replays, stale responses, expiry, contract mismatch and output tampering fail closed.
7. Persist raw valid responses, requests, identities, hashes, attempts, review decisions and sequenced host events. Unit fixtures must never be described as live proof.

## Modules and state

- `atc10/core.py`: structured PRD compiler, immutable source snapshots, SQLite coordinator and independent evidence gates.
- `atc10/runtime.py`: asynchronous `HostDispatcher`, `HostRuntime` protocol and concrete callback bridge. Complete standalone prompt renderer prevents dependence on inherited host context. Worker/reviewer instructions are separate.
- `python -m atc10`: inspectable trusted-host bridge for compile/dispatch/bind/receive/fail/report.
- `schemas/*_v1_0.schema.json`: Draft 2020-12 strict PRD/result/review shapes.

Task state: `pending → running → submitted → reviewing → accepted | rejected`.
Runtime failure marks a worker `failed`; a reviewer failure returns the task to `submitted`. An explicit retry creates a fresh request. Worker attempts have a PRD budget; accepted tasks are never automatically replayed. An expired in-flight lease requires host `fail` recovery. The adapter runs sequentially in dependency order; simultaneous host work is possible but no built-in parallel scheduling claim is made.

There is one work order per explicit PRD requirement, with declared dependencies and source grants. Natural-language decomposition remains a separate authoring responsibility. Existing v0.6–0.9 entry points and schemas retain their old behavior; v1.0 uses a separate research PRD schema to avoid silently changing old permissions or mock semantics.

## Product decision

`accepted_host_reviewed` means every PRD requirement's work order has passed machine checks, its independent reviewer has marked all criteria satisfied, and all accepted artifacts/dependencies revalidate. It asserts acceptance of the **specific pinned-corpus research**, not correctness of every possible factual claim, live Internet freshness, code-generation success, or a security certification.

## Tests

The test suite must cover happy-path compilation and end-to-end dispatch; schema/unknown field failures; bad evidence, hashes and ranges; missing and duplicate claims; dependency gates/cycles; binding/role/replay restrictions; retry/timeout recovery; tampering and restart; and callback adapter failure handling. Independent semantic review remains necessary because an exact but irrelevant quote can pass the deterministic checks.
