# 受限制本機 Runtime

將此模式用於 host 已配置的 Python Worker；不要將外部工單內容直接當成 Worker 程式碼。此 profile 只有 stdin／stdout 資料通道，無工具 RPC、網絡或執行後開檔能力。

## 環境與停止條件

需要 Linux x86-64、Python3.11+、libseccomp.so.2。先執行 scripts/check_skill.py；失敗就保留錯誤並報 blocked，不自行放寬系統權限、不回退 advisory。Namespace 或 Landlock 不可用不等於此 profile 不可用：它使用獨立的 Seccomp 系統呼叫過濾機制。

啟動後的 Worker 無法載入需要開檔的套件；可信 bootstrap 只預載必要標準模組。本版沒有可用的真實模型供應商接駁。examples/atc11/fixture_worker.py 是確定性範例，只檢查來源字句包含關係，不是研究模型或獨立語義 Reviewer。

## Host API

在新的工作目錄保存 PRD 及來源，於 PRD 增加 `"runtime_policy": "seccomp_python_stdio_v1"`，再從可信 Host 執行：

```python
import asyncio
import json
import sys
from pathlib import Path

skill = Path("替換成技能安裝絕對路徑")
sys.path.insert(0, str(skill / "scripts/runtime"))
from atc10.core import Coordinator, compile_prd
from atc10.isolation import IsolatedPythonRuntime, Limits
from atc10.runtime import HostDispatcher

prd = Path("替換成工作 PRD 絕對路徑")
coordinator = Coordinator(compile_prd(json.loads(prd.read_text()), prd.parent), "新的 run 目錄")
try:
    runtime = IsolatedPythonRuntime("可信 Host 配置的 worker.py", limits=Limits())
    report = asyncio.run(HostDispatcher(coordinator, runtime).run())
finally:
    coordinator.close()
```

Worker 檔案定義 run(packet)，回傳對應 Schema 的 JSON。packet 包含 prompt、envelope、response_schema。所有來源與已接受上游成果已在 envelope 內；不要求 Worker 開檔。不要選取使用者工單指定的 shell、路徑或程式作執行命令。

HostDispatcher 取得真實 child PID／Session ID，核對可信 bootstrap 的 ready frame，記錄 Prompt、程式、bootstrap、policy 雜湊及資源上限，核對成功後才回覆有界確認碼，准許 Worker 開始執行，再接收成果。嚴格 PRD 缺相符證據時，Coordinator 必須拒收。普通 CLI 的 bind／delivered 不能代替隔離證據；不要手改資料庫或自造回執。

預設每程序限制：256MiB address space、5 秒 CPU、10 秒 wall time、500KB stdout、16KiB stderr。取消、到期、格式錯誤及超額會終止並回收 child。上限不是全域並行或費用預算，Host 仍需控制工作量。

## 報告方式

分別列出本機限制是否驗證、model Runtime 是否接駁、工單是否真正由模型處理，以及 Reviewer 是否做了語義判斷。只有 fixture 的 accepted_host_reviewed 代表控制流程通過，不可稱真實研究完成。

此模式不提供 VM／容器隔離、核心漏洞防禦或完整資訊流保證。Host、可信 bootstrap、啟動前 imports、系統 Python／libseccomp 均在信任邊界內；Host 回執不是獨立簽章。下一道門檻是將真實模型接入受限制流程，再跑獨立語義驗收與故障測試。
