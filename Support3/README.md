# Support3: Exhaustive Search for EFX/EFR Counterexamples (3 Types)

Exhaustive search for EFX/EFR counterexamples in three-agent, eight-good
fair-division instances with **3 types** of goods (A, B, C). This extends the
framework from "Counterexamples to EFX for Submodular and Subadditive Valuations"
(Mackenzie & Suzuki).

## What This Code Does

This is a **complete, exhaustive** brute-force search. It does NOT sample or
approximate — it checks **every single valid instance** in the defined search
space. If no counterexample exists in this space, this code will prove it by
checking all ~191 million instances and finding zero failures.

### The Problem

Given 3 agents and 8 goods, can we always find an allocation that is:

- **EFX** (Envy-Free up to any eXception): Each agent values their bundle at
  least as much as any other agent's bundle after removing any single good.
- **EFR** (Envy-Free up to any item, relaxed): Each agent values their bundle
  at least as much as the average value any other agent gets from removing one
  good at a time.

This code searches for instances where EFX or EFR **fails** — i.e., no valid
allocation satisfies the fairness guarantee.

### What It Checks

For every instance, the code checks all **1,400 possible allocations** (or 700
canonical ones using cyclic symmetry pruning) to determine:

1. **Does an EFX allocation exist?** If yes, the instance is "safe."
2. **Does an EFR allocation exist?** If yes, but no EFX, it's classified as
   "EFR-not-EFX."
3. **Neither exists?** It's classified as "neither" — the strongest
   counterexample.

## Search Space

| Parameter | Value |
|---|---|
| Agent count | 3 |
| Goods count | 8 |
| Type count | 3 (A, B, C) |
| Distributions | (3,3,2), (4,2,2), (4,3,1), (5,2,1) |
| Pair types | 6 (AA, AB, AC, BB, BC, CC) |
| Triple types | 10 (with repetition) |
| Pair value combos per dist | 6^6 = 46,656 |
| Exceptional subsets | 2^10 = 1,024 |
| **Instances per distribution** | **47,775,744** |
| **Total instances (4 dists)** | **191,102,976** |
| Allocations per instance | 1,400 |
| Canonical allocations (Lemma 2.4) | 700 |
| **Total allocation checks (worst-case)** | **267,544,166,400** |

## Theory

### Instance Model

- **Goods**: 8 goods, each labeled by one of 3 types (A, B, C).
- **Type distribution**: How many goods of each type, e.g. (3,3,2) means
  3 A-goods, 3 B-goods, 2 C-goods.
- **Valuations**: Each agent has a rank function r: 2^{goods} -> {0,1,...,7}.
  - **Singletons** (1 good): rank 1 for every good.
  - **Pairs** (2 goods): rank in {1,...,6}, monotone: r({x,y}) >= max(r({x}), r({y})).
  - **Triples** (3 goods): rank 7 if "exceptional", otherwise max of internal pair ranks.
  - **Larger sets** (4+ goods): max rank over all internal triples.

### Agent Derivation (Cyclic Symmetry)

Agent 0's valuation is parameterized directly. Agents 1 and 2 are derived by
applying a cyclic permutation sigma to the type labels:

| Distribution | Sigma | Fixed types |
|---|---|---|
| (3,3,2) | A->B->C->A (3-cycle) | none |
| (4,2,2) | A->B->C->A (3-cycle) | none |
| (4,3,1) | A<->B (2-cycle) | C |
| (5,2,1) | A<->B (2-cycle) | C |

Sigma only permutes types with count >= 2. Types with exactly 1 good are fixed.

### Fairness Notions

**EFX**: Allocation X = (X0, X1, X2) is EFX if for all agents i, j and all
goods g in Xj: r_i(Xi) >= r_i(Xj \ {g}).

**EFR**: Allocation X is EFR if for all agents i, j:
r_i(Xi) >= (1/|Xj|) * sum_{g in Xj} r_i(Xj \ {g}).

### Lemma 2.4 (Cyclic Symmetry Pruning)

If X = (X0, X1, X2) is EFX, then X^sigma = (sigma(X1), sigma(X2), sigma(X0))
is also EFX. We only check one canonical allocation per cyclic orbit of size 3,
reducing the allocation search by ~2x (1,400 -> 700).

## How It Works

### Fast Path (batched, with C acceleration)

The recommended execution mode. Instead of building full Instance objects:

1. **Pair values** are the primary key: 46,656 combinations of 6 pair ranks.
2. For each pair combo, **1,024 exceptional triple subsets** are enumerated.
3. For each (pair_values, exc_mask), **value tables** (256 entries per agent)
   are computed in Python.
4. **Allocation checks** run in C via `hot_loop.so` — computing summary tables
   (max_without, sum_without) and checking all 700 canonical allocations.
5. If EFX is found, the batch is skipped early. Results are classified as
   "EFR-not-EFX" or "neither" when EFX fails.

### C Extension (`hot_loop.c`)

A performance-critical C extension that:
- Computes summary tables (max value without each good, sum of values without
  each good) for all 256 subsets.
- Iterates over all canonical allocations checking EFX and EFR conditions.
- Returns immediately when EFX is found (early termination).

Compile: `cc -O3 -shared -fPIC -o hot_loop.so hot_loop.c`

### Checkpointing

Progress is saved to SQLite after every batch. If interrupted, resume by
running the same command — completed batches are automatically skipped.

## Running Locally

### Prerequisites

- Python 3.10+
- A C compiler (clang or gcc)

### Compile the C extension

```bash
cc -O3 -shared -fPIC -o hot_loop.so hot_loop.c
```

### Quick test (single distribution, small range)

```bash
python main.py --dist 3 3 2 --fail-only --split-results \
    --output results.txt --no-resume --workers 1 \
    --task-start 0 --task-end 10
```

This checks 10 batches (10,240 instances) and takes ~1 second.

### Full search (all distributions, all cores)

```bash
python main.py --all --fail-only --split-results \
    --output results.txt --workers 0
```

`--workers 0` uses all CPU cores. Expected runtime: several hours depending
on hardware.

### Single distribution, all cores

```bash
python main.py --dist 3 3 2 --fail-only --split-results \
    --output results.txt --workers 0
```

### Resume after interruption

```bash
python main.py --all --fail-only --split-results \
    --output results.txt --workers 0
# Automatically resumes from checkpoint
```

### Start fresh (ignore checkpoint)

```bash
python main.py --all --fail-only --split-results \
    --output results.txt --workers 0 --no-resume
```

### Matrix splitting (for GitHub Actions or multi-machine)

```bash
# Machine 1: batches 0-93311
python main.py --all --fail-only --split-results \
    --output results_shard_0.txt --no-resume --workers 4 \
    --task-start 0 --task-end 93312

# Machine 2: batches 93312-186623
python main.py --all --fail-only --split-results \
    --output results_shard_93312.txt --no-resume --workers 4 \
    --task-start 93312 --task-end 186624
```

## CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--dist sA sB sC` | — | Single distribution, e.g. `--dist 3 3 2` |
| `--all` | — | Search all 4 distributions |
| `--fail-only` | off | Only write instances where EFX fails |
| `--split-results` | off | Write separate files per category |
| `--output FILE` | `results.txt` | Output file prefix |
| `--workers N` | 1 | Parallel workers. 0 = all CPU cores |
| `--chunksize N` | 100 | Instances per worker batch |
| `--no-resume` | off | Ignore existing checkpoint |
| `--task-start N` | 0 | First task_id (inclusive) |
| `--task-end N` | None | Last task_id (exclusive) |

## Output

When using `--fail-only --split-results`, three files are written:

| File | Contents |
|---|---|
| `*_efr_not_efx.txt` | Instances with no EFX allocation, but EFR exists |
| `*_neither.txt` | Instances with neither EFX nor EFR (strongest counterexample) |
| `*_efx_not_efr.txt` | Always empty (every EFX allocation is also EFR) |

### Run results (completed)

A full run over all 4 distributions checked **191,102,976 instances** and found
**zero counterexamples**:

```
Done. Checked 191102976 instances, wrote 0 to failures.txt.
Total instances expected: 191102976
Total allocation checks worst-case: 267544166400
  efx_not_efr: 0 -> failures_efx_not_efr.txt
  efr_not_efx: 0 -> failures_efr_not_efx.txt
  neither: 0 -> failures_neither.txt
```

This means: **within the defined search space (3 types, rank-based valuations
with the stated constraints), no counterexample to EFX exists.** Every instance
admits an EFX allocation.

## GitHub Actions

A CI workflow is available at `.github/workflows/search-efx-support3.yml`.
It shards 186,624 batches across ~100 matrix jobs, compiles the C extension,
runs the search, and merges results.

Trigger manually from the Actions tab with configurable:
- `num_jobs`: number of parallel matrix jobs (default 100)
- `workers_per_job`: multiprocessing workers per job (default 2)

## Files

| File | Description |
|---|---|
| `main.py` | CLI entry point, multiprocessing, checkpointing, result I/O |
| `fast_search.py` | Bitmask-based batch evaluation, C extension interface |
| `hot_loop.c` | C extension: summary tables + allocation checking |
| `instance.py` | Instance class, rank functions, type permutation logic |
| `generator.py` | Exhaustive instance generator (naive path) |
| `checker.py` | Instance checker (naive path) |
| `efx_checker.py` | EFX checking logic, allocation enumeration |
| `efr_checker.py` | EFR checking logic |
| `all_code.txt` | Monolithic copy of all source files |
| `README.md` | This file |

## Performance

| Metric | Value |
|---|---|
| Per-batch (1,024 instances) | ~0.5s with C, ~5s pure Python |
| Full search (186,624 batches) | ~26 hours single-threaded |
| Full search (8 cores) | ~3-4 hours |
| GitHub Actions (100 jobs) | ~20 minutes |
| Memory usage | ~50 MB per worker |
