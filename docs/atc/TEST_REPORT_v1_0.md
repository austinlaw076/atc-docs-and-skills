# ATC v1.0 — 實作及驗證報告

日期：2026-10-20（香港）
交付定位：**研究試行版**。真實 Host Agent 接駁、研究成果驗證及獨立覆核已實跑；強制 Runtime 權限隔離尚未完成。

## 結果

一份結構化 PRD 產生三張工單，交予三個真實研究 Agent；R1、R2 先驗收，R3 才可取得其已接受成果並進行綜合。另一個獨立 Reviewer Session 逐項審查；最終 Coordinator 回報 `accepted_host_reviewed`，三張工單皆 `accepted`，完整性錯誤為空。

此狀態只表示這份固定來源研究通過其工單驗收，不能當成整套 v1.0 已符合生產安全要求。

| 工單 | 真實 Producer（Host 回傳身分） | 工作 | 結果 |
|---|---|---|---|
| R1 | `/root/atc10_r1` | v0.9 派單能力與缺口 | accepted（第二次嘗試） |
| R2 | `/root/atc10_r2` | 完整性與語義驗收差異 | accepted（第二次嘗試） |
| R3 | `/root/atc10_r3` | 綜合接收條件與殘留限制 | accepted |

獨立 Reviewer：`/root/atc10_reviewer`，與三名 Producer 不同。它是另一個 Session，並非另一間供應商或另一種模型；不把 Session 獨立性誇大成完全獨立的外部審計。

## 真實執行與反例

1. **首輪缺來源 → 拒收。** Host 最初錯誤依賴父對話工具輸出會被子 Agent 繼承；兩名 Agent 都回報看不到來源並拒絕猜測。空白 claims 未通過 Schema，Host 記錄 runtime failure，重新派單。新版 `render_prompt` 明確包入整份工單與 Schema，不再依賴繼承內容。
2. **來源重新交付 → 真實研究 → 接收。** Host 明確傳入 S1 報告原文／行號；兩名 Agent 交回有逐字引文的成果。Coordinator 檢查來源 SHA-256、行號、引文、需求覆蓋與 Schema，再交 Reviewer 覆核全部主張及驗收條件。R3 接收已驗收的 R1/R2 摘要視圖及其成果雜湊，產生綜合研究；它明確揭示未直接讀取依賴成果原始位元組。
3. **正確引文＋錯誤結論 → Reviewer 拒收。** 在獨立負面測試 run，Host 刻意注入兩項與來源相反的主張，例如聲稱 v0.9 已驗證真實 LLM 推論。Schema／引文／雜湊檢查確實通過，成果只進入 `submitted`。真實 Reviewer 對兩項主張均判定 `supported:false`，回覆 `reject`，Coordinator 保持 `rejected`。此測試的 Producer 是明確標記的合成注入 fixture，只有審查是真實 Agent 執行；不冒稱另一張真實 Worker 工單。
4. **依賴與恢復。** R3 在 R1/R2 未接受前不能派發；請求不可重播。來源／合約／成果雜湊與一次性請求綁定。單元測試另外涵蓋重啟、過期、失敗重試、角色衝突及篡改。

主流程：`outputs/atc10-live/REPORT.json`、`run.sqlite`、各工單 request/response、`compiled.json` 及成果檔。
負面流程：`outputs/atc10-negative/REPORT.json`、`injected-result.json`、Reviewer request/response 及 SQLite。
Host 交付研究者的來源視圖限 S1；S2/S3 是合約允許且已固定的額外來源，不代表研究者已讀取。Reviewer 看的是逐項原文主張、引文及對應來源節錄，Coordinator 另行驗證完整成果雜湊。

## 自動化驗證

環境：Python 3.12；PyYAML、jsonschema、cryptography；pytest 9.1.1。

| 檢查 | 結果 | 解讀 |
|---|---|---|
| 升級前 root unittest 基線 | 124 PASS | v0.9 已有測試 |
| v1.0 專用 unittest | 45 PASS | 新增研究派單、驗證及 Host callback 測試 |
| 升級後 root unittest | 169 PASS | 124 + 45 |
| root pytest | 223 PASS；27 subtests PASS | 包含 unittest 與原有 pytest 測試；與上列重疊，不相加 |
| legacy_v0_5 pytest | 89 PASS；31 subtests PASS | 另在 legacy 子專案執行；不是新增獨立安全證明 |
| `compileall atc10` | PASS | 新模組語法檢查 |
| `git diff --check` | PASS | 差異空白檢查 |

新測試包括：PRD 分解、循環／未知依賴、來源路徑與 symlink、Schema／額外欄位、空白或重複主張、精確引文／行號／來源雜湊、身份綁定、自我覆核／跨角色、重播、逾時、重試額度、成果與依賴篡改、續跑、完整工作流、callback 傳遞與 runtime 錯誤。

起初直接在全目錄執行 pytest，誤收 legacy 重名測試與 v0.9 合成 `.py` 產物而出現 collection error。新增 `pytest.ini` 指定 root `tests`，legacy 獨立執行；上表為修正後結果，沒有刪除或跳過原有 root 測試。

`HostDispatcher`／`CallbackHostRuntime` 的自動循環以明確標示的 fixture 測試。真實 Work Agent 實跑使用 CLI Host Bridge；本報告不把兩者混稱為自動 callback API 的 live integration。

## 獨立程式審查

以匯入 v0.9 的 git commit `bb3d7e2` 為基準，兩名獨立程式審查 Agent 分開檢查 Standards 與 Spec。

- **Standards：**發現 P2：JSON Schema 允許整數值 `1.0`，但直接作 Python slice 行號會拋 `TypeError`。已在 Schema 驗證後轉為 `int`，新增回歸測試；原審查者再次確認修正。未發現其他可重現的阻擋問題。
- **Spec：**固定來源、可信 Host 研究範圍的需求已滿足；真實 Agent／Reviewer 身份、來源驗證及依賴驗收有證據。強制低權限 Runtime 未獲建立，須保留為未完成項。callback 測試與真實 CLI 橋接亦必須分開描述。審查另發現根目錄仍顯示舊版 README，交付前已補上 v1.0 指令、Runtime 接駁範例與明確範圍。

這是針對變更的程式與規格審查，並非第三方安全認證。

## 尚未完成／不能宣稱

- **強制權限隔離：**真實 Agent 在觀察中沒有呼叫工具，但平台未技術移除其工具目錄。限制屬指令與可信 Host 邊界；本環境 bubblewrap namespace 測試被拒絕（Operation not permitted），沒有 OS 沙箱證據。
- 沒有任意 PRD 散文自動拆解；輸入是具明確需求、來源和依賴的結構化 PRD，每項需求編譯為一張工單。
- 沒有開放網絡研究、付費 API、生產部署、外部資料修改、A2A wire transport 或任意成果程式碼執行。
- Hash／SQLite 紀錄由可信 Host 管理；不是防 Host 篡改的簽章或遠端審計。Reviewer 仍可能出錯。

## 下一個可驗收里程碑

接入可技術強制 `tools=[]`／隔離檔案與網絡的 Runtime，保持目前只讀來源範圍；執行工具越權、資料讀取、外部寫入及逾時取消等負面測試。這一項通過前，應將此交付維持為研究試行版，不提升為生產安全版本。
