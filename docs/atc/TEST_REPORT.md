# ATC v0.6 Test Report

## Environment and commands

- Python 3.11+; PyYAML and jsonschema available; pytest available.
- New authoring suite: `python -m unittest discover -s tests -q` → **40 tests OK**.
- Preserved v0.5 `cd legacy_v0_5 && python -m pytest -q tests` → **89 passed, 31 subtests passed**.
- Nested historical v0.4: `(cd legacy_v0_5/legacy_v0_4 && python -m unittest discover -s tests -p 'test_atc.py' -q)` → **40 tests OK**.

**169 executed top-level test cases** across separate suite runs; historical cases overlap with coverage already represented in the preserved v0.5 suite, so this is not 169 unique scenarios.

## New v0.6 coverage

- Input: valid, empty, oversized, invalid task ID, retained Cantonese original.
- Classification: research, decision, writing, workflow, send protection.
- Priority: explicit rankings extracted; unspecified rankings never invented.
- Authorization: send requires approval proposal; deploy, purchase and delete always denied in local drafts; spend=0.
- Parser/linter: duplicate YAML keys, schema tampering, unknown actions, scope collisions, denied-included actions, high-risk auto-allow, human review, unsupported decision methods.
- Review outputs: Markdown readability, HTML escaping, static/no-approval labels, sensitive diffs.
- Completion: never marks trusted completion, including for nonempty outputs.
- CLI: draft → lint → HTML + Markdown render → verify exits 2 for external verification pending.

## Limits

These tests confirm software behavior within an offline demo only. They do not establish robustness of natural-language understanding, identity-bound approval, production security, independent source verification, or true task completion.
