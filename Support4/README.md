# Supp4: Counterexample Search for 4 Types of Goods

Exhaustive search for EFX/EFR counterexamples in three-agent, eight-good instances
with **4 types** of goods (A, B, C D), extending the paper
"Counterexamples to EFX for Submodular and Subadditive Valuations" (Mackenzie & Suzuki).

## Theory

### Setup

- **Agents**: N = {0, 1, 2}
- **Goods**: M = {0, ..., 7}, each belonging to one of 4 types
- **Type distributions** (number of goods of each type):
  (2,2,2,2), (3,2,2,1), (3,3,1,1), (4,2,1,1), (5,1,1,1)

### Valuations (Rank Functions)

Each agent has a monotone rank function r: 2^M -> {0, 1, ..., 7}.

**Singletons** (size 1): rank 1 for every good.

**Pairs** (size 2): a symmetric 4x4 table of values in {1, ..., 6}, one per
unordered pair of types (with repetition). Monotonicity: pair(A,B) >= max(r({a}), r({b})).

**Triples** (size 3): 20 possible type-triples with repetition. Any subset of these
20 triples can be declared "exceptional" (rank 7). Non-exceptional triples get the
maximum rank of their internal pairs.

**Larger sets** (size >= 4): rank = max rank over all internal triples.

### Agent Derivation (Cyclic Symmetry)

Agent 0's valuation is parameterized directly. Agents 1 and 2 are derived by
cyclic permutation of **non-singleton types only**:

| Distribution | Cycle | Singleton types (fixed) |
|---|---|---|
| (2,2,2,2) | A->B->C->D->A | none |
| (3,2,2,1) | A->B->C->A | D |
| (3,3,1,1) | A->B->A | C, D |
| (4,2,1,1) | A->B->A | C, D |
| (5,1,1,1) | (trivial) | B, C, D |

For agent k, if good i has type T, agent k sees it as perm^k(T).
Exceptional triples are correspondingly rotated.

### Fairness Notions

**EFX** (Envy-Free up to any eXception): Allocation X = (X0, X1, X2) is EFX if for
all i, j in N and all g in Xj: r_i(Xi) >= r_i(Xj \ {g}).

**EFR** (Envy-Free up to any item, relaxed): Allocation X is EFR if for all i, j:
r_i(Xi) >= (1/|Xj|) * sum_{g in Xj} r_i(Xj \ {g}).

### Lemma 2.4 (Cyclic Symmetry Pruning)

If X = (X0, X1, X2) is EFX, then X^sigma = (sigma(X1), sigma(X2), sigma(X0)) is
also EFX. We only check one canonical allocation per cyclic orbit of size 3,
reducing the allocation search by ~3x.

## Search Space

| Parameter | Value |
|---|---|
| Pair types | 10 (C(4,2) + 4) |
| Triple types | 20 (C(4+3-1, 3)) |
| Pair value combos | 6^10 = 60,466,176 |
| Exceptional subsets | 2^20 = 1,048,576 |
| **Instances per distribution** | **~63.4 trillion** |
| **Total across 5 distributions** | **~317 trillion** |
| Allocations per instance | 1,400 |
| **Canonical allocations** | **399** (with Lemma 2.4 pruning) |
| Per-check time | ~0.3 ms |
| Per batch (one pair combo) | ~280 s (single-thread) |

## Running the Code

### Quick test (single worker, all distributions)
```bash
python main.py --all --workers 1
```

### Full parallel run (all CPU cores)
```bash
python main.py --all --workers 0
```

### Single distribution
```bash
python main.py --dist 3 2 2 1 --workers 0
```

### Resume after interruption
```bash
python main.py --all --workers 0   # automatically resumes from checkpoint
```

### Start fresh (ignore checkpoint)
```bash
python main.py --all --workers 0 --no-resume
```

### Flags
- `--workers 0` : use all CPU cores
- `--workers N` : use N workers
- `--output FILE` : output file (default: results.txt)
- `--no-resume` : ignore existing checkpoint

## Checkpointing

Progress is saved to `results.txt.checkpoint.sqlite3` after every batch (one pair-value
combination). On resume, completed batches are skipped automatically.

## Output

Two output files are created:
- `results_efr_not_efx.txt` : instances with no EFX allocation (but EFR exists)
- `results_neither.txt` : instances with neither EFX nor EFR

## Files

| File | Description |
|---|---|
| `instance.py` | Instance class, permutation logic, rank functions |
| `fast_search.py` | Bitmask-based evaluation, Lemma 2.4 pruning |
| `main.py` | CLI entry point with multiprocessing and checkpointing |
| `README.md` | This file |

## Early stopping

The search stops as soon as it finds ONE no-EFX instance and ONE no-EFR instance,
then prints the counterexample parameters.


# Distribution (2,2,2,2)
```
python3 main.py --dist 2 2 2 2 --workers 8 --no-resume
Searching 1 distribution(s), 8 worker(s)
Total instances to check: 10,668,672
Checkpoint: results.txt.checkpoint.sqlite3

  100000/10668672 checked
  200000/10668672 checked
  300000/10668672 checked
  400000/10668672 checked
  500000/10668672 checked
  600000/10668672 checked
  700000/10668672 checked
  800000/10668672 checked
  900000/10668672 checked
  1000000/10668672 checked
  1100000/10668672 checked
  1200000/10668672 checked
  1300000/10668672 checked
  1400000/10668672 checked
  1500000/10668672 checked
  1600000/10668672 checked
  1700000/10668672 checked
  1800000/10668672 checked
  1900000/10668672 checked
  2000000/10668672 checked
  2100000/10668672 checked
  2200000/10668672 checked
  2300000/10668672 checked
  2400000/10668672 checked
  2500000/10668672 checked
  2600000/10668672 checked
  2700000/10668672 checked
  2800000/10668672 checked
  2900000/10668672 checked
  3000000/10668672 checked
  3100000/10668672 checked
  3200000/10668672 checked
  3300000/10668672 checked
  3400000/10668672 checked
  3500000/10668672 checked
  3600000/10668672 checked
  3700000/10668672 checked
  3800000/10668672 checked
  3900000/10668672 checked
  4000000/10668672 checked
  4100000/10668672 checked
  4200000/10668672 checked
  4300000/10668672 checked
  4400000/10668672 checked
  4500000/10668672 checked
  4600000/10668672 checked
  4700000/10668672 checked
  4800000/10668672 checked
  4900000/10668672 checked
  5000000/10668672 checked
  5100000/10668672 checked
  5200000/10668672 checked
  5300000/10668672 checked
  5400000/10668672 checked
  5500000/10668672 checked
  5600000/10668672 checked
  5700000/10668672 checked
  5800000/10668672 checked
  5900000/10668672 checked
  6000000/10668672 checked
  6100000/10668672 checked
  6200000/10668672 checked
  6300000/10668672 checked
  6400000/10668672 checked
  6500000/10668672 checked
  6600000/10668672 checked
  6700000/10668672 checked
  6800000/10668672 checked
  6900000/10668672 checked
  7000000/10668672 checked
  7100000/10668672 checked
  7200000/10668672 checked
  7300000/10668672 checked
  7400000/10668672 checked
  7500000/10668672 checked
  7600000/10668672 checked
  7700000/10668672 checked
  7800000/10668672 checked
  7900000/10668672 checked
  8000000/10668672 checked
  8100000/10668672 checked
  8200000/10668672 checked
  8300000/10668672 checked
  8400000/10668672 checked
  8500000/10668672 checked
  8600000/10668672 checked
  8700000/10668672 checked
  8800000/10668672 checked
  8900000/10668672 checked
  9000000/10668672 checked
  9100000/10668672 checked
  9200000/10668672 checked
  9300000/10668672 checked
  9400000/10668672 checked
  9500000/10668672 checked
  9600000/10668672 checked
  9700000/10668672 checked
  9800000/10668672 checked
  9900000/10668672 checked
  10000000/10668672 checked
  10100000/10668672 checked
  10200000/10668672 checked
  10300000/10668672 checked
  10400000/10668672 checked
  10500000/10668672 checked
  10600000/10668672 checked

Writing results to results.txt...

Final: 10,668,672/10,668,672 instances checked
No counterexamples found yet. Resume with the same command.
```
Run on local.
***No counterexamples found yet. Resume with the same command.***

# Distribution (3,2,2,1)