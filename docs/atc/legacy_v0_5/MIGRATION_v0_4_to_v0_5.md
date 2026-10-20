# v0.4 → v0.5 Migration

1. Change contract `contract_version: '0.4'` to `'0.5'`. Existing policy sections remain the same; the version bump invalidates previous contract byte hashes by design.
2. Use `python atc.py validate path.contract.md` and `python atc.py evaluate ...` for unchanged offline decision behavior.
3. Create a new **separate** operator signing key in a trusted environment, then initialize the Gateway DB with only the public key.
4. Route only supported **mock** actions through `gateway.py`, never real tools. For actions requiring approval, the operator signs the exact request; agent cannot self-approve.
5. Add Checkpoints, signed reviewer attestation and audit inspection where useful. `completed` cannot be inferred from an LLM response.
6. Re-review any prior approval/decision: no migration of old permissions or consumed tokens.

`legacy_v0_4/` contains the exact prior implementation and tests to compare behavior; do not treat it as a gateway.
