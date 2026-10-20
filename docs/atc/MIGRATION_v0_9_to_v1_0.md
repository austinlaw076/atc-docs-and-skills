# v0.9 → v1.0

- Keep v0.9 contracts and mock commands unchanged; their results remain `accepted_mock_only`.
- New research input: `examples/atc10/prd.json`, validated by `schemas/prd_v1_0.schema.json`.
- New entry point: `python -m atc10`. Requires Python 3.11+; dependencies stay in `requirements.txt`.
- A fresh v1.0 run uses its own directory and SQLite file. Do not copy v0.9 state into it.
- Author explicit requirements, acceptance criteria, source IDs and dependencies; one requirement compiles to one work order.
- Actual agent IDs must come from the trusted runtime and be bound by the host. A fresh reviewer session must have a different identity and role.
- Submitted artifacts need schema/evidence checks plus independent semantic review before acceptance. Product status is `accepted_host_reviewed`, scoped to the approved research corpus.
- Use `render_prompt` for self-contained delivery; inherited parent tool outputs may be absent from child-agent context.
- Strong isolation is not provided by this package; attach an enforcing host before using it with untrusted workers or external-action tools.
