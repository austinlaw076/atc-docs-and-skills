# Suggested v0.7 priorities

1. **Explicit semantic approval for *draft contents*, not execution**: review edits and sign a frozen contract for use by a separate host. Design a safe transition from `draft` to reviewed specification without conflating policy review and tool authorization.
2. **LLM-authoring adapter with adversarial evaluation**: an optional, swappable external LLM produces a proposal; schema validation, traceable uncertainties, human correction and evaluation dataset test fidelity.
3. **v0.6 → runtime adapter spec (NOT auto-deployment)**: support safe read-only tools first; define semantic loss checks and a complete default-deny action mapping. Require isolated host control and explicit approval before any real external side effects.
4. **Review UX**: side-by-side original request vs Contract with changed/uncertain clauses highlighted; no deceptive automatic 'Approve & Run' action.
