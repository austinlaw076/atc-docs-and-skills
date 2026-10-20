# 權限模式

以下 CLI／Callback 範例只適用 advisory 模式。runtime_policy=seccomp_python_stdio_v1 時，改讀 restricted-runtime.md 並用 IsolatedPythonRuntime＋HostDispatcher；不可回退普通子 Agent 或自造隔離回執。

# Host 接駁與恢復

## 路徑與依賴

將下例 `ATC_SKILL` 換成技能安裝絕對路徑、`PRD` 換成工作 PRD、`RUN` 換成工作輸出。所有範例都應在工作目錄執行；不把 run.sqlite 或實跑結果寫入技能資料夾。

```bash
python -m pip install -r "$ATC_SKILL/scripts/runtime/requirements.txt"
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" compile > compiled.json
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" dispatch R1 --ttl 900 > request.json
python "$ATC_SKILL/scripts/prepare_prompt.py" request.json > worker-prompt.txt
```

`prepare_prompt.py` 檢查原始 request 的 input_hash，將完整 envelope、來源及 result/review Schema 包入 Prompt。不重新計算或改寫 request_id、contract_hash、input_hash。每個來源同時有完整 text、lines 與 Host 固定的 sha256；行號從 1 開始，引文不包含自行添加的行號標籤。

## 真實 Host Handoff

1. 用主機可用的 Agent Runtime 啟動工具建立 Session，把 Prompt **實際內容**傳入，不能只提及父 Agent 的工具輸出。Worker 只輸出符合 result Schema 的 JSON。主機能停用工具就停用；不能強制時紀錄 advisory mode。
2. 保存工具回傳的實際 Session ID。以 request 的 request_id 及該 ID bind，不能接受模型自報身份。若啟動失敗，對既有 request fail，不偽造一個 Host ID。
3. 先以 delivered 記錄實際送出 Prompt 的 SHA-256 及 Host 回執 ID；回執是可信 Host 的送出聲明，不是遠端模型已讀完全部內容的簽章證明。取得該 Session 的原始 JSON，原樣保存為 worker-response.json。不要替 Worker 補寫 claims、引文或雜湊；必要修訂交回 Worker，或失敗後用新工單嘗試。

```bash
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" bind REQUEST_ID HOST_AGENT_ID
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" delivered REQUEST_ID HOST_AGENT_ID SENT_PROMPT_SHA256 HOST_RECEIPT_ID
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" receive REQUEST_ID HOST_AGENT_ID worker-response.json
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" dispatch R1 --role reviewer > reviewer-request.json
python "$ATC_SKILL/scripts/prepare_prompt.py" reviewer-request.json > reviewer-prompt.txt
```

4. 建立不同的 Reviewer Session，交付 reviewer-prompt.txt。Reviewer 審查每項 claim、其 evidence、依賴及所有 acceptance，回傳 review Schema；不可只回「同意」。逐項回傳 criteria（criterion_id/satisfied/claim_refs/reason），並完成同樣 bind／delivered／receive，身份須不同且角色不可互換。
5. 對下一張可執行工單重複。report 不完整時，清楚列出 pending、running、submitted、reviewing、rejected、failed，不能把它們當成功。

## 故障／恢復

```bash
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" report
python "$ATC_SKILL/scripts/atc.py" --prd "$PRD" --run "$RUN" fail REQUEST_ID 'actual runtime timeout'
```

- 只有真實故障／過期／拒收才 retry，維持相同 PRD 與來源。worker 重試產生新 request，受 max_attempts 限制。
- running／reviewing 且過期不會自動變成接受；Host 先 fail，再重派。停止遠端推論與費用由 Host 管理。
- reviewer runtime 故障回到 submitted，可建立新 Reviewer request；已 accepted 的任務不可重播。
- worker 回覆驗證失敗時不會收到 submitted，保留原始回覆及錯誤後 fail。語義拒收則是正式 rejected，不改寫 DB。
- PRD／來源變更會產生不同 contract_hash；使用新 RUN，不把新合約硬塞入舊紀錄。
- report 出現 integrity_errors 時先處理變更，不能繼續承認既有 acceptance。不可修改儲存的 hash 來隱藏問題。

## Callback API

若 Host 可提供真正 async start/collect API，將 `scripts/runtime` 加入 Python import path，使用 `atc10.runtime.CallbackHostRuntime(start_agent, collect_agent)` 配合 `HostDispatcher`。start_agent 接收 `prompt` 和 `tools=[]` 並回傳真實 Session ID；collect_agent 接收 Session ID 和 timeout_seconds，回傳該 Session 的 JSON。

此介面沒有內置付費供應商或假造網絡端點。CLI handoff 可真實運作，但測試 callback 的 fixture 只驗證程式流程，不自動證明某個供應商已 live-connected。不要在回覆中將兩者混為一談。

## v1.1 恢復要求

本版使用新的 run 目錄。compiled.version=1.1，新的 *_v1_1 Schema 要求逐項 criteria。每個派單 envelope 都保留 product_context；dispatch 已保存完整實際 Prompt 至 run/deliveries。可用 `prompt REQUEST_ID` 輸出該檔原始文字，再計算送出位元組的 SHA-256。不同工單不能共用 Worker ID。
