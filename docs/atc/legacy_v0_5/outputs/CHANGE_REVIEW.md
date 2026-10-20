# ATC 合約變更審閱

**狀態**：`proposed_not_approved` · **風險**：`high`
**請求 ID**：`1e49e2723aba38ffbe54`
**舊版本 SHA-256**：`fdb52e3d68e7f1671537cd8cc83b871fab61e0c4494b5d7d016353d07ed35db0`
**新版本 SHA-256**：`66875affb86780d96f83a700f9fd761d4b6e773636e5b1b7ab27ba638a1ddf12`

## 變更項目
- **HIGH** `authorization.actions.deploy`：`"deny"` → `"approval_required"`
- **HIGH** `limits.max_spend_hkd`：`0` → `500`
- **HIGH** `mode`：`"advisory"` → `"execution"`
- **HIGH** `scope.exclude`：`["deploy", "purchase", "delete_data"]` → `["purchase", "delete_data"]`
- **HIGH** `scope.include`：`["research", "compare", "recommend", "send_report"]` → `["research", "compare", "recommend", "send_report", "deploy"]`

**需要人類批准**：是
**已取得批准**：否（此工具無批准發放能力）

> 要正式採納變更，Host 必須向用戶展示完整 Diff、取得明確同意、核對新合約指紋，並在每次真實操作前重新執行權限檢查。
