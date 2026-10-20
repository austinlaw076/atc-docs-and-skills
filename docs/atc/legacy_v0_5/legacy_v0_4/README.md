# Agent Task Contract (ATC) v0.4

A **self-contained experimental Human-Agent task contract format**, inspired by Englang's readable Markdown/YAML approach. **ATC is not part of the official Englang standard.**

## What this release does

This release adds three pieces to v0.3:

1. **General Decision DSL**: three deterministic ranking strategies (`tolerance_then_secondary`, `lexicographic`, `weighted_score`) over declared metrics, directions, units, and comparison contexts. Demonstrations cover memory-system research, job selection, and infrastructure choice.
2. **Evidence lineage**: source → assertion flags → observation → publisher-level aggregation → metric → decision. It rejects missing/conflicting data instead of silently removing inconvenient candidates. Synthetic source URLs and publisher assertions are NOT proof of genuine provenance.
3. **Contract diff and approval request**: changes to goals, permissions, evidence rules, verification, budgets and readable instructions are flagged before adoption. Diff shows old/new file hashes, change request ID and **approval_granted: false**. No actual user permission is obtained or granted by this tool.

Also ships a **human-readable Contract Review** and a **detailed Evidence Lineage** trace.

## Boundaries and honest limitations

- **Read-only/offline** governance prototype. Does not run agents, browse URLs, publish reports, send email, deploy systems, pay money, or touch production resources.
- `check-action` reports *contract intent* only. It does **not** intercept real tools, grant privilege, or bypass platform permissions.
- `reviewed_asserted` and `independent_asserted` in the synthetic fixture are dataset claims. The tool never verifies publisher ownership, source content, independence, freshness or real-world metrics.
- This version deliberately accepts **only synthetic fixtures** (`synthetic: true`) to prevent the demo algorithm being mistaken for a trustworthy real-data evaluation system.
- `task_completed` is always `false`; required human review is always pending. `max_spend_hkd` / retries are declared but NOT monitored or enforced.
- Change severity classification is **heuristic**, not a complete security policy. All byte changes are raised for human review; a host must implement the actual approval gate.
- Native v0.3 files are retained under `legacy_v0_3/` for reproducibility. v0.4 has a **new** schema and CLI: v0.3 contracts do **not** work directly in v0.4.

## Requirements and usage

Python 3.10+, PyYAML and jsonschema:

```bash
python -m pip install -r requirements.txt
python atc.py validate examples/memory.contract.md
python atc.py evaluate examples/memory.contract.md examples/memory.synthetic.yaml --out outputs/memory.decision.json
python atc.py review examples/memory.contract.md --dataset examples/memory.synthetic.yaml --out outputs/CONTRACT_REVIEW.md
python atc.py lineage examples/memory.contract.md examples/memory.synthetic.yaml --out outputs/EVIDENCE_LINEAGE.md
python atc.py check-action examples/memory.contract.md deploy
python atc.py diff examples/memory.contract.md examples/memory.proposed.contract.md --out outputs/CHANGE_REVIEW.md
python atc.py diff examples/memory.contract.md examples/memory.proposed.contract.md --format json
python -m unittest discover -s tests -v
```

Alternative profiles:

```bash
python atc.py evaluate examples/job.contract.md examples/job.synthetic.yaml
python atc.py evaluate examples/architecture.contract.md examples/architecture.synthetic.yaml
```

Expected synthetic decisions: `system-a`, `offer-a`, `stack-y`; every one is `recommendation_ready_pending_review`, NOT task completion.

## Files

| File | Purpose |
|---|---|
| `SPEC.md` | v0.4 normative experimental spec |
| `QUICK_GUIDE_zh-HK.md` | Quickstart and reading guide in Traditional Chinese |
| `HOST_INTEGRATION_PLAN.md` | **Not implemented** host enforcement and approval design |
| `MIGRATION_v0_3_to_v0_4.md` | Breaking-change migration notes |
| `atc_core.py` / `atc.py` | Offline evaluator and CLI |
| `schemas/` | JSON Schema Draft 2020-12 input definitions |
| `examples/` | Three fully synthetic profiles and a high-risk proposal |
| `outputs/` | Derived decision, review, lineage and change review |
| `tests/` | Automated tests including adversarial fixtures |
| `make_examples.py` | Regenerate reproducible synthetic examples |
| `legacy_v0_3/` | Archived previous code and examples (no active dependency) |

No file in this package is an approval token, real benchmark result, or external verification.
