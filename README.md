# EFR-EFX Searcher

Exhaustive computational search for **fair-division counterexamples** — instances
where no allocation satisfies both EFX and EFR fairness guarantees.

---

## Why This Matters

Fair division is a core problem in resource allocation: how do you split
indivisible goods among agents so that no one feels treated unfairly?

This problem arises everywhere — from dividing inheritances and divorce
settlements to allocating cloud compute resources, scheduling tasks on
machines, and distributing organs for transplant. The central challenge is
that envy-freeness (no agent prefers another's bundle) is **impossible to
guarantee** for indivisible goods in general. EFX and EFR are the strongest
known relaxations that are conjectured to always exist.

Proving that an EFX allocation *always* exists is a major open question in
theoretical computer science and economics (the "EFX existence conjecture").
If EFX always exists, we can build practical algorithms that find such
allocations. If it does not, understanding *exactly where* it fails tells us
which weaker fairness guarantees to target instead. Counterexamples — especially
"neither" instances that fail both EFX and EFR — draw the boundary of what is
achievable and guide the design of fair mechanisms for real systems.

---

## Motivation

Two earlier papers presented candidate counterexamples to EFX:

- **Akrami et al.** (SAT-generated, general monotone valuations)
- **The "other" paper** (ordinal/rank-based valuations with cyclic structure)

Upon verification, both papers' examples turned out to **satisfy EFR** despite
**failing EFX**. They were not the clean counterexamples they appeared to be —
each admitted an EFR allocation.

This raised a natural question: *can we find simpler, structured instances that
fail **both** EFX **and** EFR?* Such "neither" counterexamples would be
stronger and more informative. To answer this, we turned to the framework of
[**Mackenzie & Suzuki**](paper.md) ("Counterexamples to EFX for Submodular
and Subadditive Valuations"), which offers a compact, symmetric construction
of goods and valuations — making exhaustive search tractable.

---

## The Gap: EFR but not EFX

Two concrete examples from [Examples.md](Examples.md) illustrate the problem
and motivate the search.

### Example 1 — Akrami et al.

8 goods, 3 agents with general monotone valuations:

| Agent | Bundle | Value |
|:-----:|:------:|:-----:|
| 0 | {1, 2, 3, 8} | 120 |
| 1 | {4, 6} | 64 |
| 2 | {5, 7} | 79 |

**EFX fails:** Agent 2 views Agent 0's bundle without good 3 as worth 91,
but Agent 2's own bundle is only worth 79. So Agent 2 strongly envies Agent 0.

**EFR is satisfied:** The *average* value Agent 2 gets from Agent 0's bundle
after removing a random good is 67.00, which is less than 79. Agent 2 does
not envy the expected value.

```
AGENT 2: own bundle [5,7] = 79
  Agent 0's bundle [1,2,3,8]:
    remove 1 → 31,  remove 2 → 68,  remove 3 → 91,  remove 8 → 78
    average = 268/4 = 67.00   →   79 >= 67  ✓ EFR
    but max  = 91              →   79 < 91   ✗ EFX
```

### Example 2 — Rank-based (cyclic structure)

This is the type of instance that Mackenzie & Suzuki's framework formalizes.
3 agents, 8 goods of types A, B, C, x, y with cyclic valuations:

| Agent | Bundle | Rank |
|:-----:|:------:|:----:|
| 0 | {B, C, x, y} | 7 |
| 1 | {A, B} | 5 |
| 2 | {A, C} | 5 |

**EFX fails:** Agent 1 views Agent 0's bundle without good x as rank 6, but
Agent 1's own bundle has rank 5. Strong envy.

**EFR is satisfied:** The average rank Agent 1 gets from Agent 0's bundle after
removing a random good is 4.75, which is less than 5.

```
AGENT 1: own bundle [A,B] = 5
  Agent 0's bundle [B,C,x,y]:
    remove B → 6,  remove C → 4,  remove x → 3,  remove y → 6
    average = 19/4 = 4.75   →   5 >= 4.75  ✓ EFR
    but max  = 6             →   5 < 6      ✗ EFX
```

Both examples show the same pattern: an allocation that survives EFR but
not EFX. Our goal is to find instances where **no** allocation survives
**either** condition — a "neither" counterexample.

---

## Fairness Definitions

Given 3 agents $N = \{0, 1, 2\}$ and 8 goods, each agent $i$ has a **rank
function** $r_i : 2^M \to \{0, 1, \dots, 7\}$ that assigns a rank to every
bundle. An allocation is $X = (X_0, X_1, X_2)$ where $X_i$ is agent $i$'s
bundle.

### EFX — Envy-Free up to any eXception

> Allocation $X$ is **EFX** if for every agent $i$, every agent $j \neq i$,
> and every good $g \in X_j$:
>
> $$r_i(X_i) \;\ge\; r_i(X_j \setminus \{g\})$$

Agent $i$ does not envy any other agent's bundle, even after removing the
single best item from that bundle.

### EFR — Envy-Free up to any item (Relaxed)

> Allocation $X$ is **EFR** if for every agent $i$ and every agent $j \neq i$:
>
> $$r_i(X_i) \;\ge\; \frac{1}{|X_j|} \sum_{g \in X_j} r_i(X_j \setminus \{g\})$$

Agent $i$ does not envy the *expected* value of another agent's bundle after
a uniformly random item is removed.

Every EFX allocation is automatically EFR, but the converse is not true. The
strongest counterexample is one where **neither** holds — what we call a
**"neither" instance**.

---

## The Mackenzie & Suzuki Framework

The key insight is that 8 goods can be grouped into **types**, and valuations
can be defined purely in terms of which types are present in a bundle.

### Goods and Types

Each of the 8 goods is assigned one of several types:

| Goods | Type |
|:-----:|:----:|
| $A, A$ | type A |
| $B, B$ | type B |
| $C, C$ | type C |
| $x$ | type x |
| $y$ | type y |

The two singletons $x$ and $y$ are "exceptional" — they participate in
special triple-rank rules.

### Rank Functions

Each agent's valuation is a rank function $r : 2^M \to \{0, \dots, 7\}$:

| Bundle size | Rule |
|:-----------:|:-----|
| $\emptyset$ | rank 0 |
| 1 good | rank 1 (always) |
| 2 goods | rank in $\{1, \dots, 6\}$ — one value per pair of types |
| 3 goods | rank 7 if "exceptional" (one from $A \cup \{x\}$, one from $B$, one from $C$), otherwise the max of internal pair ranks |
| $\ge 4$ goods | max rank over all internal triples |

### Cyclic Relabeling

All three agents share the same valuation template — they differ only by a
**cyclic permutation** of the type labels:

$$\sigma = (A \to B \to C \to A)$$

So agent 1's valuation is $r_1(S) = r_0(\sigma(S))$ and agent 2's is
$r_2(S) = r_0(\sigma^2(S))$. This symmetry is powerful: it reduces the
allocation search by a factor of ~3 (Lemma 2.4 in the paper) and makes
instances human-verifiable.

---

## Repository Structure

```
EFR-EFX-Searcher/
├── Support3/          Exhaustive search: 3 types of goods
├── Support4/          Exhaustive search: 4 types of goods
├── InstanceChecker/   Independent verification of counterexample candidates
├── paper.md           Annotated summary of the Mackenzie & Suzuki paper
├── Examples.md        Detailed examples from Akrami et al. and the other paper
├── comparison.md      Side-by-side comparison of Supp3 vs Supp4 search spaces
└── .github/workflows/ CI workflows for distributed search
```

### `Support3/` — 3-Type Exhaustive Search

Searches the complete space of rank-based instances with **3 goods types**
(A, B, C) and distributions like (3,3,2), (4,2,2), etc.

| Metric | Value |
|:-------|:------|
| Instances per distribution | ~47.8 million |
| Total (4 distributions) | **191 million** |
| Allocations per instance | 1,400 (700 canonical) |
| Worst-case allocation checks | ~268 billion |

**Result:** Exhaustive check of all 191M instances found **zero** counterexamples.
Every instance admits an EFX allocation within this search space.

Key files: `main.py`, `fast_search.py`, `hot_loop.c` (C extension for
allocation checking), `instance.py`, `checker.py`

### `Support4/` — 4-Type Exhaustive Search

Scales the search to **4 goods types** (A, B, C, D), dramatically expanding
the space.

| Metric | Value |
|:-------|:------|
| Pair types | 10 (vs 6 in Supp3) |
| Triple types | 20 (vs 10 in Supp3) |
| Pair value combos | $6^{10} = 60.5$ million |
| Exceptional subsets | $2^{20} = 1.05$ million |
| Instances per distribution | **~63.4 trillion** |
| Total (5 distributions) | **~317 trillion** |

Key files: `main.py`, `fast_search.py`, `instance.py`, `checker.c`

### `InstanceChecker/` — Independent Verification

Re-checks candidate "neither" instances from output files using a naive
brute-force allocation enumeration. Confirms that counterexamples are genuine.

Key files: `instance_verifier.py`, `failures_neither.txt` (~148K candidate instances)

---

## Computational Hardness

The search space grows **exponentially** with the number of goods types:

```
  Types    Pair combos     Exceptional subsets    Instances/dist
  ─────    ───────────     ───────────────────    ──────────────
     3     6^6 = 46,656    2^10 = 1,024           ~48 million
     4     6^10 ≈ 60M      2^20 ≈ 1 million       ~63 trillion
     5     6^15 ≈ 4.7×10^11  2^35 ≈ 34 billion    ~16 sextillion
```

Each instance requires checking up to 1,400 allocations (700 with cyclic
symmetry pruning). Supp4's **~317 trillion** instances × 399 canonical
allocations = **~1.27 × 10^14** allocation checks in the worst case.

At ~0.3 ms per check, a single-threaded full search of Supp4 would take
**over 1,200 years**. Even distributed across CI with early stopping, the
search space is barely scratched.

This computational intractability is precisely why structured frameworks
like Mackenzie & Suzuki's are valuable: the cyclic symmetry and type-based
valuation structure compress an otherwise intractable problem into something
that can be (partially) explored.

---

## Workflows

GitHub Actions workflows distribute the search across parallel matrix jobs:

| Workflow | Search space | Jobs |
|:---------|:-------------|:-----|
| `search-efx-support3.yml` | 3 types, 4 distributions | ~100 matrix jobs |
| `search-efx-2222.yml` | 4 types, distribution (2,2,2,2) | Distributed |
| `search-efx-3221.yml` | 4 types, distribution (3,2,2,1) | Distributed |

Each workflow:
1. Shards the task space into batches
2. Compiles C extensions for hot loops
3. Runs the search with checkpointing (SQLite WAL)
4. Merges results and reports counterexample candidates

Checkpointing ensures interrupted runs resume from the last saved state — no
work is lost.

---

## Running Locally

```bash
# Support3 — full search
cd Support3
cc -O3 -shared -fPIC -o hot_loop.so hot_loop.c
python main.py --all --fail-only --split-results --output results.txt --workers 0

# Support4 — all distributions
cd Support4
python main.py --all --workers 0

# InstanceChecker — verify candidates
cd InstanceChecker
python instance_verifier.py
```

---

## References

- Hannaneh Akrami et al. *A counterexample to EFX: n ≥ 3 agents, m ≥ n + 5
  items, monotone valuations via SAT-solving*, 2026.
- Simon Mackenzie, Mashbat Suzuki. *Counterexamples to EFX for Submodular
  and Subadditive Valuations*.
