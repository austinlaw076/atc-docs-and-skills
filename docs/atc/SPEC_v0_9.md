# ATC v0.9 Technical Specification (prototype)

## Document model

- `product_contract` (`product.yaml`): scope, requirement IDs, permitted action ceiling, explicitly denied actions, write path roots, product acceptance criteria.
- `work_plan` (`work_plan.yaml`): product id/version linkage, order filenames, dependency policy, maximum logical wave size and retry count.
- `work_order` (`work_orders/Txx.yaml`): one independently delegated worker contract, requirement references, dependencies, minimum required capabilities, allowed actions, write paths, deliverables and acceptance checks.
- `atc_work_graph_ir` (`compile` output): snapshot of all documents, sorted topological layers, contract SHA-256, traceability, explicit non-executable semantics.

Each object must pass its Draft 2020-12 JSON Schema. Nested unknown keys are rejected in v0.9. Structural, referential, workflow and security invariants are verified separately by `Bundle`.

## Fail-closed checks

1. Product/plan/order parent id+version must match exactly.
2. Every requirement must have product acceptance AND must be assigned to at least one order.
3. Every order's deliverable must be mentioned in at least one acceptance check.
4. Dependencies must refer to known orders; a DAG is mandatory.
5. Child allowed actions must be a subset of parent `allow_actions`; child's `approval_required` must be a subset of parent `approval_required_actions`; explicit parent denials can never become child allowed actions.
6. Parent write roots and child write paths must use safe relative POSIX paths. No drive letters, dot segments, absolute paths, or escape outside parent roots.
7. Two independent tasks cannot have intersecting declared write paths; if one is transitively dependent on the other, overlap can be allowed for sequential work. Actual MockWorker output is separately isolated per task.
8. IDs contain only ASCII letters, numbers, `_` and `-` after the initial letter.
9. Compiled IR includes a SHA-256 of the full product/plan/orders; opening an existing SQLite run with a different hash is rejected.

## Runtime semantics

Task states: `pending` → `running` → `submitted` → (`accepted` | `rejected` | `awaiting_review`); injected failures go through `retry_pending` until `max_attempts`, then `failed`. Missing capabilities mark `blocked`.

The coordinator only dispatches orders whose dependencies are `accepted`; not merely `submitted`. A logical wave respects `max_parallel_agents` and does not double-book a named mock agent. It is simulated serially, not parallel threads/processes.

MockWorker creates marker files in `workspace/workspaces/<task_id>/<declared_artifact_path>`, with content hash, producer and synthetic provenance in a per-task manifest. Verifier recalculates file hash and verifies nonempty. A `human_review` acceptance remains pending: there is no mechanism for model self-approval. SQLite stores task states and append-only-by-application events. Audit is **not tamper-proof**.

A product with all work orders accepted and only machine-checkable `all_work_orders_accepted` criteria gets `accepted_mock_only`. With product `human_review` acceptance it gets `needs_product_review` regardless of mock pass results.

## Adapter contracts

`adapter generic`: offline ATC work order envelope with parent, contract hash, bounded per-task authorization.

`adapter a2a-preview`: an A2A-like `Message` with human-readable text parts and an ATC metadata sidecar. It is **NOT a certified A2A request** and cannot be sent directly to agents by this CLI.

`adapter langgraph-preview`: proposed input mapping for a LangGraph worker, without importing, running or initializing LangGraph.

All adapter outputs include `authorized_to_send: false`.

## Deliberately unsupported

Real external subagent communication, Task/A2A protocol conformance, MCP tool integration, authenticated user approvals, distributed concurrency, cost metering, semantic source validation, artifact content-level verification, OS sandboxing, and a production orchestration engine. Integration of actual agents must go behind a separate trusted host authorization boundary.
