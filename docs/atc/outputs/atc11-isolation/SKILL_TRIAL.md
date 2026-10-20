# ATC v1.1 技能實測結果

日期：2026-10-20。技能：`/root/.codex/skills/remote-skills/skill-6ad679119ffc8191a8c45657dcf079f2`。

**結果：目前環境支援 ATC 的本機 seccomp Python stdio 技術限制；尚不能宣稱具備端到端受限真實模型研究能力。**

- 環境：Linux x86_64、Python 3.12.14、`libseccomp.so.2` 可用。
- 按技能執行完整 `scripts/check_skill.py`（沒有使用 `--advisory-only`），退出碼 0，104 項單元測試通過；輸出為 `status=pass`、`restricted_profile=verified_local_process_tests`。
- 通過項目包含 CLI／PRD DAG／完整 Prompt／竄改拒收／明確輸入／未完成不得報成功／Runtime 原始碼雜湊，以及 v1.1 的檔案讀寫、網絡、程序與執行緒限制、原始 syscall 越權探測、資源限制、ready/ack、隔離證據及嚴格派單流程測試。
- 所有測試回傳均是 fixture；`live_model_agents=false`。沒有派發真實研究工單，沒有接受任何真實模型成果，也沒有語義 Reviewer 驗收。

| 模式 | 目前可用範圍 |
|---|---|
| `seccomp_python_stdio_v1` | 可執行 Host 指定的本機 Python Worker、stdin/stdout 資料處理及 fixture 控制流程驗證。必須經 IsolatedPythonRuntime + HostDispatcher；不能把一般子 Agent 當作隔離 Worker。 |
| `host_trust_boundary`／未指定 | 可編譯工單與採用 Host Agent 協作，但限制屬 advisory；本次未執行真實 Agent 流程，不能視為已驗證技術強制限制。 |

目前可完成：準備及編譯結構化 PRD、來源與 DAG；產生可核對工單及 Prompt；驗證本機受限程序和 fixture 驗收流程。要求受限真實模型研究時，目前須停在已編譯工單並標示 model Runtime blocked。技能沒有可用的真實模型供應商接駁，本次未連任何外部模型或付費 API。

這是系統呼叫限制及可信 Host 證據，不是 VM／容器、核心漏洞防禦或完整資訊流保證。Host、bootstrap、啟動前 imports、Python、libseccomp 與核心仍在信任邊界內。

證據：同目錄 `self-check.stdout.json`、`self-check.stderr.log`（空）。測試由技能使用臨時目錄；沒有修改服務或技能，也沒有安裝依賴。執行時設定 `PYTHONDONTWRITEBYTECODE=1` 避免產生技能目錄快取。
