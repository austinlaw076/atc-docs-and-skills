# ATC v1.0.1 — 驗證報告

版本定位：只讀研究試行系統（research pilot），未達生產就緒。

## 已完成變更

- PRD、Coordinator 內部快照及派單 envelope 使用深拷貝；來源文字、SHA-256 與行陣列一致性驗證。
- 限制 JSON 大小、深度、節點、欄位、鍵及字串；拒絕超大輸入，限制 Schema 錯誤回報。
- 驗證後、檔案寫入後及 SQL UPDATE 前後重查 lease；過期時回滾並清理未接收成果。
- Prompt 包含產品目的、受眾、範圍、完整工單、證據及回傳 Schema；保存精確 Prompt 與雜湊。
- 接收成果前要求已綁定 Agent 的主機派送回執；不同工單不得重用同一研究 Agent 身分。
- Reviewer 必須逐一核對 criterion、引用已支持的 claim，並保持總結與逐項判定一致。
- 派單準備失敗可恢復生命週期；恢復錯誤保留原始異常。

## 測試與獨立審查

- 完整 pytest：256 passed，27 subtests passed。
- v1.0/v1.0.1 專用 unittest：78 passed；其中新增 33 項回歸測試。
- Python 編譯檢查與 git diff --check 通過。
- 中斷恢復後重新安裝原 requirements 範圍內依賴，完整測試再次通過：Python 3.12.14、jsonschema 4.26.0、pytest 9.1.1。Skill 可攜自檢及 78 項內附測試通過。
- 兩位獨立審查者核對規格及實作。審查發現的超長 JSON 鍵預檢繞過及派單準備失敗狀態問題均已修正並複驗；補上 SQL UPDATE 後到期回滾測試。

## 真實派單證據

本次 corpus 固定於 candidate `f1f798bd6853919f012dc8c318fd73df891c38d0` 的程式碼節錄；完整快照及七段行號映射保存在 `examples/atc101/`。節錄與原檔逐段核對通過，未把 candidate 完整檔案雜湊冒充最終版本雜湊。

本次真實派單結果：`accepted_host_reviewed`；R1、R2、R3 全部 accepted，`integrity_errors={}`。三位不同研究 Agent 各執行一次，三份有效的獨立 Reviewer 回覆合共核對 9 項 claim 及 6 項 criterion，全部支持／滿足。R3 只在 R1/R2 接受並重驗後解鎖。

中斷令原 R3 Reviewer lease 到期；保留其原始 accept 回覆但未接收，以 fail 正式失效後建立新 request，交由另一真實 Reviewer 重審。共 7 個真實獨立 Session、7 份派單 Prompt 與回執、7 份原始回覆；其中 6 份回覆正式接收。沒有重跑已接受的 Worker，也沒有把舊回覆改綁新工單。

證據位於 `outputs/atc101-live/REPORT.json`、`LIVE_NOTES.md`、原始 request/response、host receipt、deliveries 及 run.sqlite。7 份 Prompt 副本與 Coordinator 保存檔逐 byte 相符。最終程式重讀相同 run，報告與 Host 產生的 REPORT 完全一致。獨立審查者另以唯讀資料庫重算報告，核對全部 Prompt／Schema／回執／原始回覆／逐項理由及到期失效紀錄，未發現阻塞問題。

歷史 v1.0 證據不計作 v1.0.1 新驗證。

實跑使用 Skill 的 CLI host bridge；自動 callback loop 只經 fixture 測試。實跑期間的預檢鍵名上限與派單準備失敗修正，另由最終版專用回歸測試核對；實跑完成後再用最終程式重驗整份 run。

## 驗證邊界與潛藏問題

1. 工具、檔案及網絡限制目前依賴可信主機與 Agent 遵守指令；尚未通過技術強制隔離及越權負向測試。
2. 派送回執只證明可信主機聲明已送出指定 Prompt；不是遠端模型讀取全部 token 的密碼學證明。
3. Schema、引文及雜湊核對驗證結構與追溯；來源可信度、推理正確性及 Reviewer 誤判仍需評估。
4. Lease 在本地提交準備階段重查，不是作業系統即時期限或遠端程序強制取消保證。
5. 本次流程驗證限於三張只讀研究工單；未證明高併發、故障轉移、長期儲存損毀復原或生產容量。
6. v1.0 PRD 格式可沿用，但受新增複雜度與大小限制；舊 run 不自動遷移，需建立新 run。
7. max_attempts 目前限制 Worker 嘗試次數；Reviewer 故障重試未有獨立總預算。可信 Host 仍需控制重試、遠端費用及紀錄增長。

下一階段門檻：以隔離 Runtime 強制限制工具、可讀路徑及外連，加入越權負向測試、重啟恢復及故障注入測試，再決定是否擴大試行。
