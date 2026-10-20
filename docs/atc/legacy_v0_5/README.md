# Agent Task Contract (ATC) v0.5 — Offline Policy Gateway Prototype

> **Status:** experimental, local **mock** tool runtime. **NOT production security, NOT a real agent integration, NOT vendor Englang syntax.**

ATC combines Markdown task intent with machine-readable YAML policies. v0.5 builds on v0.4 by implementing a **tool-call decision gate**, **operator-signed scoped approvals**, **SQLite checkpoints**, **single-use authorization**, and **audit/event records**. It deliberately provides **no real network, email, deployment, purchase, filesystem-write tool, or shell execution adapter**.

## What is inside

- `atc.py`, `atc_core.py`: v0.4-style contract parser, decision evaluation, evidence lineage, diff, review; upgraded to `contract_version: '0.5'`.
- `atc_gateway.py`, `gateway.py`: offline gateway and agent-facing CLI for four explicitly whitelisted mock adapters: `research`, `compare`, `recommend`, `send_report` (the last one **does not send anything**).
- `operator_cli.py`: separate operator-side signing CLI, requires a private key that **must not** be accessible to the agent or gateway process.
- `examples/`: three synthetic v0.5 task contracts, datasets, operator-demo request.
- `outputs/`: generated one-page review, sample gate decisions and audit summary; synthetic only.
- `tests/`: v0.4 decision tests and v0.5 attack/state tests; `legacy_v0_4/`: self-contained original v0.4 regression suite.
- `SPEC.md`, `SECURITY_BOUNDARIES.md`, `QUICK_GUIDE_zh-HK.md`, `MIGRATION_v0_4_to_v0_5.md`.

## Requirements

Python 3.10+, see `requirements.txt` (`PyYAML`, `jsonschema`, `cryptography`); `pytest` for tests.

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q tests
(cd legacy_v0_4 && python -m unittest discover -s tests -p 'test_atc.py' -q)
```

## Example: separate operator and agent contexts

```bash
# Operator-side only. Keep private key OUTSIDE agent tools/filesystem.
python operator_cli.py keygen --private /secure/operator.key --public /secure/operator.pub

# Gateway-side only; use the public key. Store run.sqlite outside agent's write authority.
python gateway.py init --db /secure/run.sqlite --contract examples/memory.contract.md --public-key /secure/operator.pub

# Allowed mock request; execution is simulation only.
python gateway.py invoke --db /secure/run.sqlite --contract examples/memory.contract.md \
  --action research --target example --args examples/mock_args.json --request-id r1

# This guarded mock action will be denied until a token is supplied.
python gateway.py invoke --db /secure/run.sqlite --contract examples/memory.contract.md \
  --action send_report --target preview --args examples/mock_args.json --request-id r2

# Operator CLI runs in independently trusted session (not a model tool).
python operator_cli.py approve --db /secure/run.sqlite --contract examples/memory.contract.md \
  --private /secure/operator.key --action send_report --target preview \
  --args examples/mock_args.json --out /secure/approval.json

# Gateway validates exact contract SHA256, run, action, target, args digest, cost, expiry, nonce.
python gateway.py invoke --db /secure/run.sqlite --contract examples/memory.contract.md \
  --action send_report --target preview --args examples/mock_args.json \
  --request-id r2 --token /secure/approval.json

# Save and reload a task checkpoint. No replay and no automatic reauthorization.
python gateway.py checkpoint --db /secure/run.sqlite --contract examples/memory.contract.md \
  --phase researching --data examples/checkpoint.json
python gateway.py resume --db /secure/run.sqlite --contract examples/memory.contract.md

# Recompute offline decision. State becomes 'verifying', NOT 'completed'.
python gateway.py verify --db /secure/run.sqlite --contract examples/memory.contract.md \
  --dataset examples/memory.synthetic.yaml

# Operator MUST independently review all human checks before issuing signoff.
python operator_cli.py signoff --db /secure/run.sqlite --contract examples/memory.contract.md \
  --private /secure/operator.key --out /secure/review-token.json --i-reviewed-evidence

python gateway.py finalize --db /secure/run.sqlite --contract examples/memory.contract.md \
  --token /secure/review-token.json
python gateway.py status --db /secure/run.sqlite
python gateway.py audit --db /secure/run.sqlite
```

**Do not actually reuse `/secure/` without configuring host isolation.** This is an illustrative path, not an installation recipe. The operator signs an assertion of review; the code does **not** prove the reviewer checked the sources.

## Limits

No live tools; no identity login; no hardened isolation; no cryptographically anchored audit store; no real evidence verification; no guarantee against a model that can alter the DB, bypass the gateway, or read the operator key. A future host integration must enforce *all calls* through this check and isolate trusted state from the model.
