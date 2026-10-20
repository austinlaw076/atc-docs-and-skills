# ATC 文檔與 Skills

Agent Task Contract（ATC）文檔、驗證報告，以及完整可安裝的 atc-coordinator Skill。最新版本：**v1.1.0**。

## 快速導覽

| 內容 | 入口 |
|---|---|
| 最新 ATC 使用說明 | [README v1.1](docs/atc/README_v1_1.md) |
| 最新規格與驗收條件 | [SPEC v1.1](docs/atc/SPEC_v1_1.md) |
| 測試結果與限制 | [TEST REPORT v1.1](docs/atc/TEST_REPORT_v1_1.md) |
| 版本狀態 | [RELEASE STATUS](docs/atc/RELEASE_STATUS_v1_1.json) |
| Skill 主文檔 | [SKILL.md](skills/atc-coordinator/SKILL.md) |
| 強制本機限制流程 | [Restricted Runtime](skills/atc-coordinator/references/restricted-runtime.md) |
| 信任邊界 | [Trust Boundaries](skills/atc-coordinator/references/trust-boundaries.md) |
| 越權驗證摘要 | [Evidence Summary](docs/atc/outputs/atc11-isolation/EVIDENCE_SUMMARY.json) |

## 目前狀態

- 本機 Linux x86-64 的 seccomp_python_stdio_v1 程序限制已驗證。
- 完整測試：282 項測試及 41 項子測試通過；23 項越權探測被拒。
- Skill 內附自檢：104 項測試通過。
- **真實模型在此受限 Runtime 內的接駁及獨立語義驗收仍未完成。** 確定性 fixture 的流程成功不能當成模型研究完成。
- v1.0.1 的真實模型 Session 屬 advisory 歷史證據，不能與 v1.1 的本機限制結果拼成端到端隔離成功。

## 使用 Skill

保留 skills/atc-coordinator 整個目錄；其中包括 SKILL.md、references、assets、scripts，以及內附 Runtime／Schema／測試。不要只複製 SKILL.md。

```bash
python -m pip install -r skills/atc-coordinator/scripts/runtime/requirements.txt
python skills/atc-coordinator/scripts/check_skill.py
```

完整限制自檢需要 Linux x86-64 與 libseccomp.so.2。只有明確檢查 advisory 模式時才使用 --advisory-only；該結果不構成隔離證據。執行實際工單前先閱讀 Skill 主文檔。

## 歷史文檔與來源

ATC 歷史規格、遷移說明及審查文檔保留在 docs/atc；舊版本命令及狀態須按各版本解讀。這是文檔與 Skill 倉庫，沒有完整 ATC 主專案的歷史實作及逐字工單資料庫；完整 Runtime 實作可見 Skill 內附 scripts/runtime。歷史文檔內的主專案操作命令及檔案路徑保留原始上下文。

文檔為來源快照；相關原始交付包仍保留完整研究執行紀錄。來源版本及檔案雜湊見 [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)。
