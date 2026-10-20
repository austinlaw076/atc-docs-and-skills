# ATC v0.9 快速指南（香港繁體中文）

## 呢套 ZIP 係乜？

v0.9 將 ATC 擴展成一套 **「PRD → 任務圖 → 獨立工單 → 模擬派單 → 驗收 → 追溯」** 嘅 Python 參考實作。適合你研究 Task Coordinator／Agent Orchestrator 應該如何清楚拆單及管理子 Agent。

**唔係** 已經可以自動寫 App 嘅平台。雖然示範工單包括 Backend、Frontend、安全、Integration、QA，但 Worker 只產生明確標記為 `MOCK ARTIFACT` 嘅文件，唔會實際寫出可用程式。

## 第一次使用（5 個指令）

先將 ZIP 解壓，再喺專案根目錄執行：

```bash
python -m pip install -r requirements.txt
python atc9.py lint --root examples/atc9
python atc9.py graph --root examples/atc9 --out outputs/ATC9_GRAPH.json
python atc9.py compile --root examples/atc9 --out outputs/ATC9_IR.json
python atc9.py review --root examples/atc9 --out outputs/my-review.md --html outputs/my-review.html
```

然後用瀏覽器打開 `outputs/my-review.html`。

## 模擬 Coordinator 派單／重試

```bash
python atc9.py simulate --root examples/atc9 --db outputs/my-run.sqlite --workspace outputs/my-run --fail-once T02 --out outputs/my-result.json
python atc9.py report --root examples/atc9 --db outputs/my-run.sqlite --workspace outputs/my-run --out outputs/my-audit.json
python atc9.py review --root examples/atc9 --db outputs/my-run.sqlite --workspace outputs/my-run --out outputs/my-review.md --html outputs/my-review.html
```

開啟 `outputs/my-audit.json`，可以睇到 T02 第一次失敗、下一輪重試、T04 依賴解鎖、每個 Mock Artifact 嘅 SHA-256 同驗收紀錄。

**繼續未完成嘅任務：** 使用原本嘅 DB、Workspace、同一份 Contract 再執行 `simulate`，已驗收工單唔會重複跑。

## 修改成你自己嘅專案

1. 改 `examples/atc9/product.yaml`：定義產品目標、需求（R01 ...）、最高權限及產品級驗收。
2. 改 `examples/atc9/work_orders/Txx.yaml`：每張工單列出對應需求、上游依賴、Agent 能力、可寫路徑、交付物與驗收。
3. 改 `examples/atc9/work_plan.yaml`：列出全部工單檔案、最大並行數同最大重試次數。
4. 跑 `lint`，必須顯示 `PASS` 先可跑 `graph`、`compile` 或 `simulate`。
5. 睇 `review.html`：檢查 PRD → 工單 → 交付 → 驗收有冇漏或矛盾。

## 三個特別重要嘅界線

- **合約描述權限 ≠ 真正外部執行權限。** 模擬器永遠唔會主動部署、發郵件、做付款或對外派單。
- **工作圖可並行 ≠ Worker 真正同時運作。** 目前只係排程語義及循序模擬。
- **Mock 驗收通過 ≠ 真實產品完成。** 純粹驗證合約流程，真實功能仍需獨立測試同人類覆核。
