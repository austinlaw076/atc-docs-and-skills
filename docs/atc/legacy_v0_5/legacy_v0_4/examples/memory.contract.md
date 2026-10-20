---
contract_version: '0.4'
id: memory-selection
title: AI 記憶系統比較
language: zh-HK
mode: advisory
goal:
  outcome: 比較符合要求嘅候選，產出可追溯但未經人類批准嘅建議
  audience: 人類任務決策者
scope:
  include:
  - research
  - compare
  - recommend
  - send_report
  exclude:
  - deploy
  - purchase
  - delete_data
priority:
  metrics:
  - id: accuracy
    direction: max
    unit: '%'
    context: same-testset-v1
  - id: cost
    direction: min
    unit: HKD/month
    context: same-monthly-pricing-v1
  eligibility:
  - metric: accuracy
    op: '>='
    value: 85
  selection:
    method: tolerance_then_secondary
    primary: accuracy
    tolerance: 3
    secondary: cost
decide:
  min_distinct_publishers: 2
  max_spread:
    accuracy: 0
    cost: 0
  on_missing: abstain
  on_conflict: escalate
authorization:
  default: deny
  actions:
    research: allow
    compare: allow
    recommend: allow
    send_report: approval_required
    deploy: deny
    purchase: deny
    delete_data: deny
  approval:
    scope: single_action
    expires_minutes: 30
verify:
  pass_when: all
  checks:
  - id: provenance-linked
    kind: programmatic
    criterion: 資料與來源 ID 有可追溯關聯（只檢查結構）
  - id: evidence-sufficiency
    kind: programmatic
    criterion: 每個候選每項指標具有足夠來源並符合一致性要求
  - id: decision-recomputed
    kind: programmatic
    criterion: 按指定確定性規則重新計算出推薦或無合格候選
  - id: reviewer-signoff
    kind: human
    criterion: 人類覆核真實來源、風險、決策與報告
limits:
  max_research_rounds: 3
  max_retries_per_step: 2
  max_spend_hkd: 0
deliverables:
- id: review
  description: 決策摘要及證據追溯報告
  required: true
lifecycle:
  initial_state: ready
  terminal_states:
  - completed
  - failed
  - cancelled
---

# CONTEXT
這是一份純合成演示，不能當成真實市場證據。

# CONSTRAINTS
- MUST 只評估有可追溯來源連結嘅觀察數據。
- MUST NOT 將 dataset 自述 reviewed 或 independent 當成第三方真實性認證。
- MUST NOT 購買、部署或將 advisory 當成授權。

# TASK
按 YAML policy 確定性計算；缺資料就棄權，存在衝突就升級；輸出審核軌跡。

# INPUT
資料集位於 `examples/memory.synthetic.yaml`。

# OUTPUT
JSON 決策及人類可讀 Contract Review；human_review 一律 pending。
