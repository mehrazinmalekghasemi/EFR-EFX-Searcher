# Support5: EFX/EFR Counterexample Search for 5 Types (2,2,2,1,1)

Exhaustive search for EFX/EFR counterexamples in three-agent, eight-good instances
with **5 types** of goods (A, B, C, D, E), extending the paper
"Counterexamples to EFX for Submodular and Subadditive Valuations" (Mackenzie & Suzuki).

## Theory

### Setup

- **Agents**: N = {0, 1, 2}
- **Goods**: M = {0, ..., 7}, each belonging to one of 5 types
- **Type distribution**: (2, 2, 2, 1, 1)
  - A, B, C: 2 goods each (cyclically permuted)
  - D, E: 1 good each (fixed)

### Valuations (Rank Functions)

Each agent has a monotone rank function r: 2^M -> {0, 1, ..., 7}.

**Singletons** (size 1): rank 1 for every good (paper's default; can be varied).

**Pairs** (size 2): a symmetric table of values in {1, ..., 6}, one per
unordered pair of types (with repetition). The (D,D) and (E,E) entries are
undefined (only 1 good of those types). Monotonicity: pair(T1,T2) >= max(r({t1}), r({t2})).

**Triples** (size 3): 22 physically possible type-triples with repetition (out of 35 total).
Any subset of these can be declared "exceptional" (rank 7). Non-exceptional triples get the
maximum rank of their internal pairs.

**Larger sets** (size >= 4): rank = max rank over all internal triples.

### Agent Derivation (Cyclic Symmetry)

Agent 0's valuation is parameterized directly. Agents 1 and 2 are derived by
cyclic permutation of types A, B, C:

| Type | Cycle | Fixed |
|------|-------|-------|
| A | -> B | |
| B | -> C | |
| C | -> A | |
| D | | fixed |
| E | | fixed |

For agent k, if good i has type T, agent k sees it as sigma^k(T).
Exceptional triples are correspondingly rotated.

### Fairness Notions

**EFX** (Envy-Free up to any eXception): Allocation X = (X0, X1, X2) is EFX if for
all i, j in N and all g in Xj: r_i(Xi) >= r_i(Xj \ {g}).

**EFR** (Envy-Free up to any item, relaxed): Allocation X is EFR if for all i, j:
r_i(Xi) >= (1/|Xj|) * sum_{g in Xj} r_i(Xj \ {g}).

## Search Space

| Parameter | Value |
|---|---|
| Types | 5 (A, B, C, D, E) |
| Pair types | 15 (C(5,2) + 5) |
| Active pair types | 13 (excluding DD, EE) |
| Triple types (possible) | 22 (out of 35) |
| Pair value combos (canonical) | ~33M (with max_pair_val=6) |
| Exceptional subsets (canonical) | 256 |
| **Instances (max_pair_val=6)** | **~8.5 billion** |
| **Instances (max_pair_val=4)** | **~164 million** |
| Allocations per instance | ~5,796 |
| Per-check time | ~0.3 ms (C extension) |

### Canonical Pruning

The cyclic symmetry (A->B->C->A) reduces the search space:
- Pair values within each orbit are required to be non-decreasing
- Exceptional subsets are all-or-nothing within each orbit
- Only physically possible triple types are considered

## Running the Code

### Quick test (single worker)
```bash
python main.py --all --workers 1
```

### Full parallel run (all CPU cores)
```bash
python main.py --all --workers 0
```

### Faster search (restrict pair value range)
```bash
python main.py --all --workers 0 --max-pair-val 4
python main.py --all --workers 0 --max-pair-val 5
```

### Resume after interruption
```bash
python main.py --all --workers 0   # automatically resumes from checkpoint
```

### Start fresh (ignore checkpoint)
```bash
python main.py --all --workers 0 --no-resume
```

### Split work across machines
```bash
# Machine 1: tasks 0-16M
python main.py --all --workers 0 --task-start 0 --task-end 16000000
# Machine 2: tasks 16M-33M
python main.py --all --workers 0 --task-start 16000000
```

### Flags
- `--workers 0` : use all CPU cores
- `--workers N` : use N workers
- `--output FILE` : output file base name (default: results.txt)
- `--max-pair-val N` : maximum pair value, 1-6 (default: 6). Lower = faster.
- `--no-resume` : ignore existing checkpoint
- `--task-start N` : first task_id (inclusive)
- `--task-end N` : last task_id (exclusive)

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
| `instance.py` | Instance class, type definitions, rank functions |
| `fast_search.py` | Bitmask-based evaluation, canonical pair/exc generation |
| `checker.c` | C extension for fast allocation checking |
| `main.py` | CLI entry point with multiprocessing and checkpointing |
| `README.md` | This file |

## Early stopping

The search stops as soon as it finds ONE no-EFX instance and ONE no-EFR instance,
then prints the counterexample parameters.

## Expected Runtime

| max_pair_val | Pair combos | Total instances | Est. time (8 cores) |
|---|---|---|---|
| 4 | 640,000 | 163.8M | ~4 hours |
| 5 | 7,503,125 | 1.9B | ~2 days |
| 6 | 33,436,992 | 8.5B | ~8 days |

For fastest results, start with `--max-pair-val 4`. If no counterexamples are found,
increase to 5 or 6.

## Relation to the Paper

The paper constructs a specific counterexample for distribution (2,2,2,1,1) (using x,y
instead of D,E) with:
- Singletons: all 1
- Pair values: {A,B}=2, {A,C}=2, {B,C}=5, {A,x}=4, {B,y}=3, {C,y}=3, {A,y}=6, etc.
- Exceptional triples: ABC, BCD

This code exhaustively searches all valuations within the framework to find such
counterexamples automatically.
