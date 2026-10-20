# ATC v0.5｜繁體中文快速指南

**一句話：** ATC 用 YAML 定義規則、用 Markdown 解釋任務；v0.5 會喺「呼叫模擬工具之前」檢查合約，而唔係只叫 AI 自律。

## 人類最需要閱讀嘅六項

| 區塊 | 回答咩問題？ | 例子 |
|---|---|---|
| GOAL | 最後要得到咩？ | 比較兩套 Agent Memory 架構 |
| PRIORITY | 多個目標有衝突點揀？ | 準確率相差 ≤ 3 個百分點，選較低成本 |
| DECIDE | 有咩資料先可以決定？ | 每候選每指標至少兩個不同發布者 |
| AUTHORIZATION | Agent 可以自己做啲咩？ | 研究可自主；報告對外發送需人類批准；部署禁止 |
| VERIFY | 完成嘅證據係乜？ | 數據核對通過 + 人類審核簽署 |
| STATE | 任務去到邊一步？ | `awaiting_approval`、`verifying`、`completed` |

## v0.5 最重要嘅安全規則

1. **預設拒絕**：未知工具、範圍外行動或者明確 `deny` 一律不執行。
2. **批准只可用一次**：批准綁定執行批次、Contract SHA-256、指定操作、目標、完整參數、成本同有效期；不能重播。
3. **Contract 不能偷改**：只要合約文字有改動，舊 Run 便拒絕；要建立新 Run 再攞批准。
4. **無核准就不當完成**：演算法有推薦只進入 `verifying`；人工簽署覆核後，先可進入 `completed`。
5. **狀態可恢復**：SQLite 保存 Checkpoint；Resume 唔會自動重做工具操作，亦唔會繞過批准。

## 預期流程

```text
人類需求
  ↓
YAML + Markdown Contract
  ↓
一頁式 Contract Review
  ↓
Gateway 檢查 Scope / Permissions / Approval / Budget / State
  ├─ ALLOW → 模擬工具執行 → Audit + Checkpoint
  ├─ APPROVAL REQUIRED → 等候個別操作批准
  └─ DENY → 拒絕執行
  ↓
資料運算與驗收（Verification）
  ↓
人類簽署指定結果
  ↓
Completed
```

## 你應該點用

先閱讀 `outputs/CONTRACT_REVIEW.md`，再看 `examples/memory.contract.md` 嘅 YAML。想親自試 Gateway，可跟 `README.md` 指令。核心程式係 `gateway.py` 和 `operator_cli.py`，後者**不能提供俾 Agent 執行，簽名私鑰亦不可讓 Agent 讀取**。

所有例子都係虛構資料：即使經過人類審核簽署，程式亦未有證明資料來源真實。v0.5 **唔會真正傳 Email、部署、購買或讀取網絡**。
