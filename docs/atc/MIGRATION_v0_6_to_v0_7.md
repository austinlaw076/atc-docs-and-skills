# v0.6 → v0.7 migration

- Keep `atc.py` / `atc6` if only keyword draft + static preview is needed.
- Run `atc7.py author` to obtain a new sidecar `.notes.json` (required for grounded review).
- Do not point v0.7 authoring contracts at v0.5 gateway: their grammars differ.
- v0.7 frontmatter still has `contract_version: '0.6'`; the v0.7 improvement is a review envelope with a separate JSON proposal schema. This is intentional to avoid introducing undocumented execution compatibility.
- New CLI: `author`, `lint`, `review`, `rebind`, `freeze`, `handoff`; original v0.6 commands remain on `atc.py`.
- To upgrade existing v0.6 contract data: regenerate from its original `goal.outcome` instead of inventing a provenance sidecar for edited files. Re-check newly generated decision priorities and permissions manually.
