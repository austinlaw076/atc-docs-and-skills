# Migration note: v0.5 → v0.6

This is a **feature addition with a deliberately incompatible authoring grammar**, not an in-place schema upgrade.

- Retain all v0.5 mock-gateway files under `legacy_v0_5/` unchanged.
- Introduce v0.6 as the contract authoring and review format, including broader writing and workflow tasks.
- v0.6 `priority` can be incomplete during drafting; v0.5 decision contracts require explicit formal metrics and evaluators.
- v0.6 `verify` checks only minimum output existence and human review; v0.5 has stronger specific evidence/decision recomputation mechanisms for synthetic datasets.
- **No v0.6→v0.5 translator** exists; conversion would require explicit semantic mapping, policy validation, checks and user approval.
- Never equate the rendered HTML or proposed diff with a signing authority.

Run the sample commands in README to compare old and new workflows.
