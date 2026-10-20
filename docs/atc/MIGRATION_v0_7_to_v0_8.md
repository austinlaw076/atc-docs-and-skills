# v0.7 → v0.8 migration

- All old `atc7.py`/`atc.py` commands and existing authoring files remain supported.
- No automatic conversion of v0.7 drafts into fully executable tasks.
- New v0.8 CLI is `atc8.py`. `evaluate` is offline by default, `compile` is read-only, `host-init` requires independent signed grant.
- `contract_version` frontmatter remains `'0.6'`; this is intentional, because v0.8 is a restricted compiler/runtime integration layer over authoring v0.6 and review v0.7.
- Compiler outputs include `contract_semantics`, `non_executable_semantics` and `compiler_assurance`; do not remove these fields to simplify execution.
- The original v0.5 Mock Gateway remains bundled as legacy reference only and is NOT a direct runtime for v0.8 IR.
- The `examples/atc8/research.freeze.json` is a **synthetic demo fixture**, not evidence of personal review.
