# Supp3 vs Supp4 — Search Space Comparison

Both search for counterexamples to EFX/EFR fairness in 3-agent, 8-good instances with rank-based valuations. Based on the paper "Counterexamples to EFX for Submodular and Subadditive Valuations" (Mackenzie & Suzuki).

## Setup

| Parameter | Supp3 (3 types) | Supp4 (4 types) |
|---|---|---|
| Agent count | 3 | 3 |
| Good count | 8 | 8 |
| Type labels | A, B, C | A, B, C, D |
| Distributions | (3,3,2), (4,2,2), (4,3,1), (5,2,1), (6,1,1) | (2,2,2,2), (3,2,2,1), (3,3,1,1), (4,2,1,1), (5,1,1,1) |
| Singleton values | Fixed to 1 | Fixed to 1 |
| Cyclic symmetry | A->B->C->A (all 3 rotate) | Non-singleton types cycle; singleton types fixed |
| Pair value range | 1..6 per pair type | 1..6 per pair type |
| Exceptional triples | Rank 7; others = max of pair ranks | Rank 7; others = max of pair ranks |

## Search Space Size

| Component | Supp3 | Supp4 | Ratio (Supp4 / Supp3) |
|---|---|---|---|
| Pair types | 6 (C(3,2)+3) | 10 (C(4,2)+4) | 1.67x |
| Triple types | 10 (C(3+2,3)) | 20 (C(4+2,3)) | 2.0x |
| Pair value combos | 6^6 = 46,656 | 6^10 = 60,466,176 | ~1,296x |
| Exceptional subsets | 2^10 = 1,024 | 2^20 = 1,048,576 | 1,024x |
| **Instances per distribution** | **47,775,744** | **~63.4 trillion** | **~1,326,545x** |
| **Total instances (5 distributions)** | **238,878,720** | **~317 trillion** | **~1,326,545x** |

## Allocation Checking

| Parameter | Supp3 | Supp4 |
|---|---|---|
| Total allocations per instance | 1,400 | 1,400 |
| Canonical allocations (Lemma 2.4) | 1,400 (no pruning) | 399 |
| Worst-case allocation checks (total) | 334,430,208,000 | ~1.27 x 10^14 |
| Worst-case allocation checks (per dist) | 66,886,041,600 | ~2.53 x 10^13 |

## Performance

| Metric | Supp3 | Supp4 |
|---|---|---|
| Per-check time | Not benchmarked (Instance objects) | ~0.27-0.3 ms |
| Per batch time (single-thread) | Not benchmarked | ~280 s |
| Allocation pruning | None | Lemma 2.4 (~3.5x reduction) |
| Checkpointing | SQLite WAL | SQLite WAL |
| Early stopping | No (full search) | Yes (stops at first no-EFX + first no-EFR) |

## Instance Count Breakdown per Distribution

### Supp3 (47,775,744 instances per distribution)

Each distribution has 6 pair types, each pair value in {1..6} (since singletons are all 1, monotonicity lower bound = 1 for all pairs). So 6^6 = 46,656 pair value combinations. For each, 2^10 = 1,024 exceptional triple subsets. Total: 46,656 x 1,024 = 47,775,744.

### Supp4 (~63.4 trillion instances per distribution)

Each distribution has 10 pair types, each pair value in {1..6}. So 6^10 = 60,466,176 pair value combinations. For each, 2^20 = 1,048,576 exceptional triple subsets. Total: 60,466,176 x 1,048,576 = 63,394,462,715,904 (~63.4 trillion).

## Scale Comparison

Supp4's search space is approximately **1.3 million times larger** than Supp3's per distribution. The key drivers are:

1. **More pair types**: 10 vs 6 (from 4 vs 3 types) — contributes 6^4 = 1,296x more pair combos
2. **More triple types**: 20 vs 10 — contributes 2^10 = 1,024x more exceptional subsets
3. **Combined**: 1,296 x 1,024 = 1,327,104x (matches the ~1,326,545x ratio)

Supp4 compensates partially with Lemma 2.4 canonical allocation pruning (3.5x reduction) and early stopping, but the search space remains orders of magnitude larger.
