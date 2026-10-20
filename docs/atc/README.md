# Current release: ATC v1.1

See [README_v1_1.md](README_v1_1.md) for the restricted local Runtime, verified boundaries and model-integration limits. Earlier guides and saved runs below remain historical.

# Current release: ATC v1.0.1 research pilot

Read [README_v1_0_1.md](README_v1_0_1.md) for current CLI, receipt and criterion requirements. The guide below is retained historical context.

# Agent Task Contract v1.0 — research pilot

Turn a structured PRD into source-bound, read-only research work orders. Actual
host agents return JSON; a distinct reviewer checks every claim and the
Coordinator decides acceptance using schemas, provenance, hashes and reviews.

**Live Host Agent dispatch is verified through the CLI bridge. Hard runtime
permission isolation is NOT verified.** The Work-mode agents followed no-tool
instructions, but the platform did not technically remove their tool catalog.
Read `SECURITY_BOUNDARIES_v1_0.md` and `TEST_REPORT_v1_0.md` for exact limits.

## v1.0 quick start (Python 3.11+)

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -q
python -m atc10 compile
python -m atc10 --run outputs/my-run dispatch R1 --ttl 900 > request.json
```

The packet is a real work order, not a generated result. A trusted host must
start an agent, deliver the complete prompt and response schema, capture the
runtime-returned session ID, and import the actual final JSON:

```bash
python -m atc10 --run outputs/my-run bind REQUEST_ID ACTUAL_HOST_AGENT_ID
python -m atc10 --run outputs/my-run receive REQUEST_ID ACTUAL_HOST_AGENT_ID worker-response.json
python -m atc10 --run outputs/my-run dispatch R1 --role reviewer > review-request.json
# Start a DIFFERENT reviewer, bind its actual session ID, and receive its review.
python -m atc10 --run outputs/my-run report
```

Replace uppercase arguments with actual host values. Never let worker JSON
nominate its authenticated identity. Submitted artifacts are not accepted.
Dependencies unblock only after review and integrity rechecks. Use
`fail REQUEST_ID REASON` for actual runtime failure/expiry before retrying.

## v1.0 programmatic dispatcher

`HostDispatcher` runs worker → reviewer → dependent work. `CallbackHostRuntime`
bridges a trusted host's two async functions. The adapter renders a complete
standalone prompt; do not rely on inherited parent tool results.

```python
import asyncio
import json
from pathlib import Path
from atc10.core import Coordinator, compile_prd
from atc10.runtime import CallbackHostRuntime, HostDispatcher

# Implement using your actual trusted host API:
# async start_agent(*, prompt, tools): return a newly created session's real ID.
# async collect_agent(session_id, *, timeout_seconds): return its final JSON.
# Enforce tools=[] in the host before claiming technical tool restriction.

p = Path('examples/atc10/prd.json')
coordinator = Coordinator(compile_prd(json.loads(p.read_text()), p.parent), 'outputs/new-live-run')
try:
    runtime = CallbackHostRuntime(start_agent, collect_agent)
    report = asyncio.run(HostDispatcher(coordinator, runtime).run())
finally:
    coordinator.close()
```

Those two callables are explicit host integration points. There is no bundled
standalone LLM provider or API key. The actual Work pilot used real collaboration
sessions plus the CLI control-plane bridge. The callback loop was tested using
explicit fixtures; it was not a second live provider integration.

## v1.0 examples and verification

- `examples/atc10/prd.json`: explicit purpose, audience, sources and three
  requirements; compiles to R1/R2, followed by dependent R3.
- `outputs/atc10-live/`: actual requests, responses, identities, reviews, artifacts,
  SQLite state and final `REPORT.json`.
- `outputs/atc10-negative/`: deliberate false-claim fixture rejected by a real
  independent reviewer despite matching quotes/hashes.
- `SPEC_v1_0.md`, `TEST_REPORT_v1_0.md`, `RELEASE_STATUS_v1_0.json`: acceptance,
  evidence and incomplete hard-isolation gate.

```bash
python -m unittest discover -s tests -q
python -m pytest -q
(cd legacy_v0_5 && python -m pytest -q tests)
python -m atc10 --run outputs/atc10-live report
```

The PRD is structured: one explicitly authored requirement becomes one work
order. Arbitrary prose decomposition and open-Web research are outside scope.
Root pytest selects maintained tests; historical projects run separately.
Old v0.9 mock `.py` outputs are evidence files, not executable tests.

The v0.6–0.9 entry points retain their old behavior. Their output remains
mock-only. The original guide is preserved in `README_v0_9.md`; its text follows
for compatibility.

---

# Legacy v0.9 — Multi-Agent Work Order Coordinator

**Version:** 0.9 research prototype · **offline only** · **no real agent dispatch, network calls or production deployment**.

v0.9 adds a product-to-work-order contract model and an offline orchestration simulator to v0.8. The Englang-like Markdown/YAML approach remains a *custom ATC proposal*, not an official Englang or A2A standard.

## What works

1. **Product Contract / Work Order JSON Schema** — separate PRD, DAG work plan and delegated task contracts. `jsonschema` validates strict known fields; referential checks require every requirement to have product acceptance, every deliverable to have a work-order acceptance, and every requirement to appear on at least one work order.
2. **Task Graph Compiler** — topologically sorts work orders, rejects cycles, missing references, permission escalation, parallel writable-path overlap and path traversal, and generates a traceability matrix in IR.
3. **Offline Coordinator** — capability-based mock assignment, logical waves respecting parallel limit, dependency gating on accepted work orders only, retry simulation, persistent SQLite checkpoints and audit events. Its `MockWorker` only writes synthetic marker documents, **not working product code**.
4. **Agent Handoff Previews** — generic, `a2a-preview`, `langgraph-preview` JSON outputs; **no remote send and no claim of A2A wire conformance**.
5. **Human Review** — a one-page HTML and Markdown contract review covering goals, authority, work orders, traceability and mock execution status.

## Quick start

Run from the unzipped `agent_task_contract_v0_9` directory:

```bash
python -m pip install -r requirements.txt
python atc9.py lint --root examples/atc9
python atc9.py graph --root examples/atc9 --out outputs/ATC9_GRAPH.json
python atc9.py compile --root examples/atc9 --out outputs/ATC9_IR.json
python atc9.py adapter --root examples/atc9 --task T01 --format a2a-preview --out outputs/ATC9_A2A_PREVIEW.json
```

Mock coordinator test (T02 fails on first attempt and succeeds on retry):

```bash
python atc9.py simulate --root examples/atc9 \
  --db outputs/my-demo.sqlite \
  --workspace outputs/my-demo \
  --fail-once T02 \
  --out outputs/my-demo-result.json
python atc9.py report --root examples/atc9 \
  --db outputs/my-demo.sqlite \
  --workspace outputs/my-demo \
  --out outputs/my-demo-audit.json
python atc9.py review --root examples/atc9 \
  --db outputs/my-demo.sqlite \
  --workspace outputs/my-demo \
  --out outputs/my-demo-review.md \
  --html outputs/my-demo-review.html
```

**Resume:** Re-run `simulate` with the **same** DB, workspace and unmodified contract. Already accepted tasks are not rerun. If the contract hash differs, the run is rejected, not silently migrated.

**Tests:** `python -m unittest discover -s tests -p 'test_*.py' -q`

## Inputs & outputs

| File | Meaning |
|---|---|
| `examples/atc9/product.yaml` | Product goals, requirements, action ceilings and product acceptance |
| `examples/atc9/work_plan.yaml` | Dependency graph, file links, max concurrent agents, retry budget |
| `examples/atc9/work_orders/T01.yaml` ... `T05.yaml` | Standalone subagent contracts with inputs, scope, capabilities, artifacts and tests |
| `schemas/*_v0_9.schema.json` | Strict schema definitions |
| `atc9/core.py` | Validation + DAG compiler |
| `atc9/coordinator.py` | Mock worker, verifier, SQLite checkpoint and event log |
| `atc9/adapters.py` | Handoff JSON previews |
| `atc9/review.py` | Human-oriented contract review |
| `outputs/ATC9_IR.json` | Compiled, **non-authorizing** work graph |
| `outputs/ATC9_AUDIT.json` | Recorded mock events and artifact SHA-256 attestations |
| `outputs/CONTRACT_REVIEW_v0_9.html` | Open in any browser; no server required |

### Sample dependency graph

```text
T01 Backend ───┐
               ├──> T04 Integration ───┐
T02 Frontend ──┘                       ├──> T05 QA
T03 Security ──────────────────────────┘
```

`T01`, `T02`, `T03` belong to the initial graph layer. Logical waves respect `max_parallel_agents=3`; simulated agents **do not execute concurrently** in v0.9. Once T02 fails, T04 cannot proceed until T02 has been successfully retried **and accepted**.

## Why this is not a production agent orchestrator

- Subagents do not run. A mock worker creates synthetic text files with SHA-256 and records `provenance: synthetic_mock`.
- Acceptance uses non-empty artifacts and SHA-256 comparison; no source-code validity, test execution or semantic correctness is implied.
- A2A handoff is a JSON **preview**; no AgentCard discovery, A2A protocol version negotiation, identity/authentication, remote sending or streaming.
- SQLite state and audit events are mutable to the OS user; not tamper-proof.
- Any actual write permissions exist only as contract declarations; **v0.9 does not instantiate a remote tool host, process sandbox or real policy gateway**.
- Previous v0.8 tooling remains included unchanged, under `atc8/`, `atc7/`, `atc6/` etc. Those components have separate maturity/safety boundaries.

See `SECURITY_BOUNDARIES_v0_9.md`, `SPEC_v0_9.md`, and `QUICK_GUIDE_zh-HK.md`.
