# ATC v0.7 validation record

## Verified within this environment on 2026-10-14 (Asia/Hong_Kong)

```bash
PYTHONPATH="$PWD:$PWD/legacy_v0_5" python -m pytest -q tests legacy_v0_5/tests/test_gateway.py legacy_v0_5/tests/test_atc.py
# 183 passed, 31 subtests passed

cd legacy_v0_5/legacy_v0_4 && python -m pytest -q tests
# 40 passed, 31 subtests passed
```

These results cover v0.7, the retained v0.6 suite, v0.5 mock gateway and historical v0.4 independently. **Do not add the overlapping historical cases into a falsely unique total.**

### Key cases included

- Sources are exact substrings of the original user request; invalid citations rejected.
- LLM proposals cannot add authorization, spend, deployment, workflow, approval-token or free-form schema fields.
- Missing/contradictory priority grounding is rejected; v0.6-inferred unmentioned tie-breakers are removed.
- Negated actions like 「唔好寄出」 become DENY rather than `approval_required` for documented patterns.
- Document/sidecar SHA256 mismatch and edited original GOAL are detected.
- HTML escapes text and applies restrictive CSP; no script actions or approval buttons.
- Freezing a contract requires digest equality and an explicit local reviewer assertion. Sensitive changes require separate acknowledgement; receipt cannot grant execution capabilities.
- Handoff only creates `mock_only` read-only plan steps and rejects all external/mutating tool intents and tampering.
- `propose_http` refuses insecure HTTP endpoints and missing keys.
- 12 adversarial Cantonese/English short requests evaluated as explicit regression fixtures.

### Not verified

- A real external LLM service response (adapter tested offline only).
- Actual tool execution, permissions, identities, key custody or trusted approval tokens.
- General semantic accuracy of long ambiguous/multilingual requests.
- Reliability of independent evidence/sources or citations.
