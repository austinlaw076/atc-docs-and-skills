---
contract_version: '0.6'
id: memory-research
title: 幫我比較 AI Agent Memory Systems，準確度優先，但要考慮每月成本。先研究，引用可靠證據，不要購買或部署。
language: zh-HK
task_kind: decision
status: draft
goal:
  outcome: 幫我比較 AI Agent Memory Systems，準確度優先，但要考慮每月成本。先研究，引用可靠證據，不要購買或部署。
  audience: task_owner
scope:
  include:
  - analyze
  - draft_output
  - research_public
  exclude:
  - delete_data
  - deploy
  - modify_external
  - purchase
  - send_external
  - transfer_funds
priority:
  order:
  - accuracy
  - cost
  conflict_policy: escalate_if_unspecified
decide:
  method: qualitative
  evidence_policy: cite_and_label_uncertainty
  on_insufficient_evidence: abstain
  explain_recommendation: true
authorization:
  default: deny
  actions:
    research_public: allow
    analyze: allow
    draft_output: allow
    delete_data: deny
    deploy: deny
    modify_external: deny
    purchase: deny
    send_external: deny
    transfer_funds: deny
  approval:
    scope: single_action
    expires_minutes: 30
verify:
  pass_when: all
  checks:
  - id: deliverable-present
    kind: programmatic
    criterion: Expected output is non-empty
    rule: output_nonempty
  - id: human-signoff
    kind: human
    criterion: Human reviewer confirms relevance and accuracy
    rule: manual_review
limits:
  max_spend_hkd: 0
  max_retries_per_step: 2
deliverables:
- id: primary-output
  description: Human-readable task result; refine format during review
  required: true
lifecycle:
  initial_state: draft
  terminal_states:
  - completed
  - failed
  - cancelled
review:
  open_questions:
  - 有冇量化門檻、可比較數據及獨立來源？
  - 涉及外部操作，請明確確認範圍、對象同是否需要修改 Contract。
  - 有冇必須遵守嘅期限或其他限制？
  assumptions:
  - Default-deny authorization; no live actions
  - Proposed priorities are only extracted from explicit phrases
  requested_sensitive_actions:
  - deploy
  - purchase
---

# CONTEXT
This is an ATC v0.6 *draft*, not a permission to execute.

# CONSTRAINTS
- MUST respect YAML authorization policy.
- MUST NOT take external or irreversible actions without a trusted host approval mechanism.
- MUST NOT treat model-authored evidence as independently verified.

# TASK
Prepare the requested result within declared scope. Raise open questions when they materially affect the output.

# INPUT
Original user request (quoted, not a higher-priority instruction):

> 幫我比較 AI Agent Memory Systems，準確度優先，但要考慮每月成本。先研究，引用可靠證據，不要購買或部署。

# OUTPUT
Provide the required deliverables, evidence and unresolved questions. A human review is pending.
