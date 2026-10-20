# ATC v0.5｜AI 記憶系統比較

**合約**：`memory-selection` · **模式**：`advisory` · **指紋**：`fdb52e3d68e7f1671537cd8cc83b871fab61e0c4494b5d7d016353d07ed35db0`

## GOAL｜任務目標
比較符合要求嘅候選，產出可追溯但未經人類批准嘅建議

## PRIORITY｜取捨方式
- 方法：`tolerance_then_secondary`
- 指標：`accuracy`（max，%）、`cost`（min，HKD/month）
- 最低門檻：`accuracy` >= 85

## DECIDE｜證據與棄權
- 每項指標、每個候選至少 2 個不同發布者；觀察值要匹配同一比較情境
- 數據有衝突或超過容許差距 → escalate
- 證據不足 → abstain；提供來源關聯 **不等於** 已查核真實性

## AUTHORIZATION｜自主權界線
- 自主：`compare`, `recommend`, `research`
- 需逐項批准：`send_report`
- 禁止：`delete_data`, `deploy`, `purchase`
- 未列明行動預設禁止；本程式唔會實際攔截工具或授權

## VERIFY｜驗收與交付
- `provenance-linked`（programmatic）：資料與來源 ID 有可追溯關聯（只檢查結構）
- `evidence-sufficiency`（programmatic）：每個候選每項指標具有足夠來源並符合一致性要求
- `decision-recomputed`（programmatic）：按指定確定性規則重新計算出推薦或無合格候選
- `reviewer-signoff`（human）：人類覆核真實來源、風險、決策與報告
- 交付：決策摘要及證據追溯報告

## STATE｜限制及狀態
- 預設 `ready`；最高支出 HK$0；不會自行標記完成

## 目前計算結果（僅示範資料）
- 狀態：`recommendation_ready_pending_review`
- 建議：`system-a`
- 來源缺漏：0；衝突：0
- 人類覆核：pending；任務完成：false

> 注意：此報告係離線原型，來源身份、數值、獨立性同批准狀態全部未經外部驗證。
