# ATC v0.8 · Human Review

> 發佈狀態：Offline prototype / 不具生產執行權限

## 1. 自然語言理解評測

- 規則式基線：**42 / 51（82.4%）**。特別不足：否定句、任務類型、英文修改權限。
- 評測集：51 個人工編寫測試情境，含廣東話／中英夾雜。
- 真實 LLM 測試：**未執行**。已有獨立 Semantic Prediction Schema、評分器及可選擇嘅 OpenAI-compatible API Adapter；必須另外提供 API 資格、明確決定供應商及成本。

## 2. Contract Compiler

- 編譯對象：經 v0.7 Review + 模擬 Content Freeze 嘅 v0.6 Contract。
- 會保留：`GOAL`、`PRIORITY`、`DECIDE`、`AUTHORIZATION`、`VERIFY`、`DELIVERABLES`。
- 可執行：**只有** `read_curated_document`、`list_curated_documents`。
- 未可執行：通用決策／驗收規則。IR 內有明確旗標聲明，不會假裝完成。

## 3. 本機只讀 Host

| 測試 | 結果 |
|---|---|
| Operator Ed25519 授權 | 驗證通過 |
| 讀取虛構 System A 基準文件 | Allowed |
| 要求部署 | Denied |
| 重複請求 | Cached，沒有再次讀取 |
| Audit 雜湊鏈檢查 | Passed |

所有操作只涉及**虛構本地測試資料**。Operator Key 與 Host 必須喺正式部署時受到獨立 OS／服務層保護。

## 4. 自動化測試

- v0.8 + v0.7：92 tests passed
- 歷史 v0.5：89 tests passed + 31 subtests
- 歷史 v0.4：40 tests passed

## 5. 下一個真正驗收閘門

1. 有 API 供應商與授權後，在獨立標註資料集測試 2 個真實模型；記錄模型誤判、不確定性、時間、費用。
2. 將簽名私鑰與 Host 信任錨交由獨立進程／帳戶，否則唔好聲稱已可抵禦 Shell-capable Agent。
3. 在完全只讀、白名單 Repo 先驗證一個真實外部 Connector，禁止跨範圍取資料。
