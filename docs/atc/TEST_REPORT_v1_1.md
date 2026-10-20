# ATC v1.1.0 — 本機 Runtime 強制限制驗證

本版已完成受限制本機 Python Runtime、Coordinator 隔離證據驗收及越權測試。**未完成真實模型在此 profile 內的接駁及語義驗收**；不宣稱生產就緒或通用沙箱。

目的：將讀檔、寫檔、連網及啟動工具限制由指令轉為本機強制控制。受眾：可信 Host 操作者與 ATC 維護者。範圍：Linux x86-64、固定 bootstrap、Host 配置的 Python Worker、stdin 固定來源及 stdout JSON。成功條件：越權探測被拒、嚴格工單缺證據不可接受、故障不回退 advisory。

## 結果與證據

| 驗證 | 結果 | 可核對證據 |
|---|---|---|
| 完整 pytest | 282 passed、41 subtests passed | tests/ 及下列重現命令 |
| 內附 Runtime unittest | 104 passed，其中 v1.1 新增 26 項測試 | scripts/check_skill.py 自檢及 tests/test_atc11.py |
| v1.1 專用測試 | 26 passed、14 subtests passed | 原生 syscall、替代 ABI、FD、清理、資源及證據測試 |
| 真實子程序越權探測 | 23/23 被拒；canary 原樣保留 | outputs/atc11-isolation/ISOLATION_PROBE.json |
| 嚴格模式控制流程 | 3 張 fixture 工單、6 個受限子程序全部通過，無完整性錯誤 | FIXTURE_REPORT.json、run/run.sqlite 及 deliveries/ |
| 獨立審查 | Standards 與 Spec 兩軸均無剩餘阻塞 | 固定基線 e2f0739、修正後程式 c76014f |
| Skill 前向測試 | 新 Session 實跑 104 項自檢，正確區分 fixture 與模型接駁 | outputs/atc11-isolation/SKILL_TRIAL.md |

23 項探測涵蓋正常讀／寫／附加檔案、symlink／路徑穿越、unlink／mkdir／建立 symlink、TCP／UDP／Unix socket、fork、外部工具、thread、原生 open／openat／openat2、ptrace、父程序記憶體／信號探測、變更 filter／權限及原生 execve。Host 可讀寫同一可拋棄 canary 並可建立 TCP socket；子程序結果與 unchanged canary 均保存。測試在現有系統限制之上加上本版 profile，不表示移除外層限制後已逐項測試。

其他回歸測試涵蓋：可繼承 FD 無法 mmap 讀取、環境 Secret 不被繼承、CPU／記憶體／wall timeout、stdout／stderr 超額、400KB 正常輸出不截斷、取消後 child 被回收、advisory Runtime 不能接嚴格工單、缺失／錯誤／竄改隔離證據及 report／依賴完整性檢查。

## 審查發現與修正

1. 輸出超限時，asyncio pipe 暫停可令 kill 後 wait() 仍等待。已改為終止後分塊丟棄剩餘輸出並回收，補上超額及正常大輸出測試。
2. Spec 審查發現 child 發出 ready 後未等 Host 核對便執行 Worker。已加入有界 ACK（確認碼）握手，綁定整份 readiness record；缺失或錯誤 ACK 不進入 payload。包含延遲 Host 核對及錯誤 PID 的真實 child 競態測試。兩位審查者已獨立複驗修正。

最終實作程式提交：c76014f5c2dbb74719e1e44509886aea6a46f737。探測、fixture 及 Skill 內附 bootstrap／Worker 雜湊另與最終檔案核對，沒有把中途版本結果當成最終證據。

## 實測環境與重現

Linux x86-64，kernel 6.18.55；Python3.12.14；jsonschema4.26.0；libseccomp2 2.5.5-1ubuntu3.1。Namespace／Landlock 探測不可用，因此本版不以它們作隔離依據；原生 libseccomp filter 載入及檔案拒絕探測成功。

```bash
python -m pytest -q tests
python -m unittest discover -s tests -p 'test_atc1*.py' -q
python evaluation/run_isolation.py --output outputs/NEW-isolation-evidence
```

輸出目錄必須是新的目錄。缺 libseccomp、平台不支援或啟動證據失敗時必須 blocked/failed，不能跳過後報通過。Skill 的 --advisory-only 是明確略過隔離測試，該結果不構成隔離證據。

## 未驗證事項與下一道門檻

- 只驗證本機受限 Python 程序。v1.0.1 的真實模型 Session 是 advisory 歷史證據；不能與本版 fixture 結果拼成受限模型端到端成功。
- 本 profile 不能直接連遠端模型 API，也不能在執行後載入需開檔的套件。下一步需設計受控模型接駁，再以真正 Worker／獨立 Reviewer 完成研究工單與越權負向測試。
- Host、bootstrap、啟動前 imports、Python／libseccomp／kernel 仍須可信。回執不是簽章，無核心漏洞、側通道、完整資訊流或 VM／容器隔離保證。
- 限額按程序計，不等於全域容量、費用或 Reviewer 重試預算。未建立 Host 硬崩潰後的持久監督及高併發恢復保證。
- 新合約／Schema 為 v1.1，必須新建 run。舊 PRD 未設 runtime_policy 時仍是 advisory，不自動獲得隔離標籤。

設計依據：[Linux Seccomp filter](https://docs.kernel.org/userspace-api/seccomp_filter.html)、[Landlock](https://docs.kernel.org/userspace-api/landlock.html)。系統呼叫過濾是隔離元件，不等同完整沙箱；本報告的通過結論僅限列出的實測 profile 與案例。
