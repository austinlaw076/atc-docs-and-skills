# Evidence Lineage｜資料追溯清單

**Contract**：`memory-selection` · **Dataset**：`memory-synthetic`
**狀態**：`recommendation_ready_pending_review` · **建議**：`system-a`

> 本清單只展示輸入數據的來源關聯與計算，不證明網址內容存在、發布者獨立或數字正確。

| 候選 | 指標 | 計算值 | 獨立發布者數 | 來源 ID | 疑點 |
|---|---|---:|---:|---|---|
| system-a | accuracy | 91 | 2 | publisher-one, publisher-two | — |
| system-a | cost | 40 | 2 | publisher-one, publisher-two | — |
| system-b | accuracy | 93 | 2 | publisher-one, publisher-two | — |
| system-b | cost | 100 | 2 | publisher-one, publisher-two | — |

## 候選排名 / 決策過程
```json
[
  {
    "method": "tolerance_then_secondary",
    "primary": "accuracy",
    "best": 93.0,
    "tolerance": 3,
    "shortlist_threshold": 90.0,
    "secondary": "cost"
  }
]
```

## 每條來源連結與觀察值

### system-a / accuracy
- `publisher-one` / publisher `research-lab-one` / value `91` / URL `https://example.org/synthetic/source-1`
- `publisher-two` / publisher `research-lab-two` / value `91` / URL `https://example.org/synthetic/source-2`

### system-a / cost
- `publisher-one` / publisher `research-lab-one` / value `40` / URL `https://example.org/synthetic/source-1`
- `publisher-two` / publisher `research-lab-two` / value `40` / URL `https://example.org/synthetic/source-2`

### system-b / accuracy
- `publisher-one` / publisher `research-lab-one` / value `93` / URL `https://example.org/synthetic/source-1`
- `publisher-two` / publisher `research-lab-two` / value `93` / URL `https://example.org/synthetic/source-2`

### system-b / cost
- `publisher-one` / publisher `research-lab-one` / value `100` / URL `https://example.org/synthetic/source-1`
- `publisher-two` / publisher `research-lab-two` / value `100` / URL `https://example.org/synthetic/source-2`

**Human verification**：pending；**Task complete**：false
