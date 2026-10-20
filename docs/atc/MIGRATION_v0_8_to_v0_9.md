# v0.8 → v0.9

v0.8 is retained as separate modules (`atc8.py`, `atc7.py`, `atc6/`, `legacy_v0_5/`). v0.9 introduces a **new** three-document contract model rather than attempting to run v0.8 single-task YAML unchanged.

- Existing 0.8 single-task drafts and frozen read-only IR keep their own tooling and security semantics.
- New 0.9 PRD and work orders have distinct JSON Schemas and their own offline compiler + mock coordinator.
- No implicit upgrade of permissions or old approvals is performed. v0.9 does not accept v0.8 operator grants.
- To migrate a real PRD, author `product.yaml`, `work_plan.yaml` and separate `work_orders/*.yaml`, then run `lint` and visually inspect `review` before allowing a future external dispatcher to use any plan.
