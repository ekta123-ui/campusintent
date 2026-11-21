# RAG retrieval evaluation (768 test queries, embedder: hashing-v1)

- In-scope top-1 intent accuracy of retrieved entry: **0.926**
- In-scope hit@4 (right topic somewhere in top 4): **0.953**

| threshold | coverage (in-scope answered) | precision (right topic) | Out_of_Scope wrongly answered |
|---|---|---|---|
| 0.15 | 0.938 | 0.936 | 0.000 |
| 0.20 | 0.894 | 0.943 | 0.000 |
| 0.25 | 0.811 | 0.940 | 0.000 |
| 0.30 | 0.754 | 0.939 | 0.000 |
| 0.35 | 0.671 | 0.944 | 0.000 |
| 0.40 | 0.556 | 0.945 | 0.000 |
| 0.45 | 0.433 | 0.942 | 0.000 |
| 0.50 | 0.344 | 0.944 | 0.000 |
| 0.55 | 0.287 | 0.971 | 0.000 |

Current ANSWER_THRESHOLD for this embedder: 0.3
