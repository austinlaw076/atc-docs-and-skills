# ATC v0.9 · ATC Contract Studio
**Product ID:** `PRD-001` v1.0 · **Contract SHA-256:** `322fb77ba631df8c5d4cb3a5bbd28e6174bd87931b43dd62b97c2cdcb9c6f9b1`

**目標：** Create, review, and validate agent task contracts in a web app.

## 決策與授權邊界
- 自主容許：read_repository, write_workspace, run_tests, review_security, integrate_artifacts, run_qa
- 明確禁止：deploy_production, purchase, modify_secrets, send_external
- 批准後才可執行：無
- 最高支出：HK$0

## 工作波次（依賴圖；模擬平行，非真實同時執行）
1. T01, T02, T03
2. T04
3. T05

## 工單及驗收
| 工單 | 目標 | 需求 | 前置依賴 | 交付物 | 驗收 | 狀態 |
|---|---|---|---|---|---|---|
| T01 | Build a minimal contract generation API | R01 | — | D01, D02 | AC-T01-D01, AC-T01-D02 | accepted |
| T02 | Create human-readable review UI | R02 | — | D01 | AC-T02-D01 | accepted |
| T03 | Define contract security validation | R03 | — | D01 | AC-T03-D01 | accepted |
| T04 | Integrate frontend and backend | R01, R02 | T01, T02 | D01 | AC-T04-D01 | accepted |
| T05 | Final QA and product verification | R01, R02, R03 | T03, T04 | D01 | AC-T05-D01 | accepted |

## 需求 → 工單 → 交付物 → 驗收 → 產品驗收
### R01
- 工單：T01, T04, T05
- 交付物：T01:D01, T01:D02, T04:D01, T05:D01
- 工單驗收：T01:AC-T01-D01, T01:AC-T01-D02, T04:AC-T04-D01, T05:AC-T05-D01
- 產品驗收：PRD-AC01
### R02
- 工單：T02, T04, T05
- 交付物：T02:D01, T04:D01, T05:D01
- 工單驗收：T02:AC-T02-D01, T04:AC-T04-D01, T05:AC-T05-D01
- 產品驗收：PRD-AC01
### R03
- 工單：T03, T05
- 交付物：T03:D01, T05:D01
- 工單驗收：T03:AC-T03-D01, T05:AC-T05-D01
- 產品驗收：PRD-AC01

## 模擬結果
- Product status: `accepted_mock_only`
- Audit events: 18
- 證據詳見 `outputs/ATC9_AUDIT.json`，其中包含交付物 SHA-256 同每項驗收紀錄。

> **注意：** 這份 Review 不是批准證明。即使狀態是 `accepted_mock_only`，亦只代表模擬工單通過非空與雜湊驗證，並不代表真實產品已實作或驗收。
