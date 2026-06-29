"""
fast_search.py
--------------
Bitmask-based fast search for 5-type, 8-good, 3-agent instances.

Paper's sigma = (0 1 2)(3 4 5) on goods.
Agent k sees good i as the type of good sigma^k(i).
Exc mask is the same for all agents (rotation captured by virtual types).
"""

import array
import ctypes
import os
import subprocess
from itertools import combinations, combinations_with_replacement, product

from instance import DISTRIBUTIONS, TYPE_LABELS, make_goods

N_TYPES = 5

# Paper's sigma = (0 1 2)(3 4 5)
GOODS_SIGMA = [1, 2, 0, 4, 5, 3, 6, 7]
GOODS_SIGMA2 = [2, 0, 1, 5, 3, 4, 6, 7]

PAIR_TYPES = tuple(combinations_with_replacement(range(N_TYPES), 2))
TRIPLE_TYPES = tuple(combinations_with_replacement(range(N_TYPES), 3))
PAIR_LABELS = tuple(frozenset(TYPE_LABELS[t] for t in p) for p in PAIR_TYPES)
TRIPLE_LABELS = tuple(tuple(TYPE_LABELS[t] for t in tr) for tr in TRIPLE_TYPES)
PAIR_INDEX = {p: i for i, p in enumerate(PAIR_TYPES)}
TRIPLE_INDEX = {tr: i for i, tr in enumerate(TRIPLE_TYPES)}
N_PAIRS = len(PAIR_TYPES)
N_TRIPLES = len(TRIPLE_TYPES)
COUNT_WITHOUT = tuple(mask.bit_count() for mask in range(1 << 8))
REDUCED_MASKS = tuple(
    tuple(mask & ~(1 << good) for good in range(8) if mask & (1 << good))
    for mask in range(1 << 8)
)
MASKS_BY_SIZE = tuple(
    tuple(mask for mask in range(256) if mask.bit_count() == size)
    for size in range(9)
)

# ---------------------------------------------------------------------------
# C extension loader
# ---------------------------------------------------------------------------

_lib = None


def _load_c_checker():
    global _lib
    dirn = os.path.dirname(os.path.abspath(__file__))
    so_path = os.path.join(dirn, 'checker.so')
    c_path = os.path.join(dirn, 'checker.c')
    if not os.path.exists(so_path) and os.path.exists(c_path):
        try:
            subprocess.run(
                ['cc', '-O3', '-shared', '-fPIC', '-o', so_path, c_path],
                check=True, capture_output=True,
            )
        except Exception:
            return None
    if os.path.exists(so_path):
        try:
            _lib = ctypes.CDLL(so_path)
            _lib.check_allocations.restype = ctypes.c_int
            _lib.check_allocations.argtypes = [
                ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_int),
                ctypes.c_int,
            ]
            return _lib
        except Exception:
            return None
    return None


_load_c_checker()


# ---------------------------------------------------------------------------
# Pair value rotation under A->B->C->A
# ---------------------------------------------------------------------------

# Rotation permutes pair indices: AA->BB->CC, AB->BC->AC, AD->BD->CD, AE->BE->CE, DE->DE
_ROTATION = [9, 2, 6, 10, 11, 0, 1, 3, 4, 5, 7, 8, 12, 13, 14]


def _rotate_pair_values(pv):
    """Apply one step of A->B->C->A rotation to pair values."""
    new_pv = [0] * N_PAIRS
    for i in range(N_PAIRS):
        new_pv[_ROTATION[i]] = pv[i]
    return tuple(new_pv)


def _is_lex_smallest_pair_values(pv):
    """Check if pv is the lex-smallest in its orbit under rotation."""
    r1 = _rotate_pair_values(pv)
    if r1 < pv:
        return False
    r2 = _rotate_pair_values(r1)
    if r2 < pv:
        return False
    return True


def _rotate_exc_mask(exc_mask):
    """Rotate an exc mask under the paper's sigma (type-level A->B->C->A)."""
    result = 0
    m = exc_mask
    while m:
        lsb = m & -m
        idx = lsb.bit_length() - 1
        rotated_type = tuple(sorted((idx // 5 + 1) % 3 if idx // 5 < 3 else idx // 5,
                                     (idx % 5 + 1) % 3 if idx % 5 < 3 else idx % 5))
        result |= 1 << TRIPLE_INDEX[rotated_type]
        m ^= lsb
    return result


# ---------------------------------------------------------------------------
# Canonical pair values: lex-smallest in orbit under rotation
# ---------------------------------------------------------------------------

def _non_decreasing_sequences(length, max_val, min_val=1):
    if length == 0:
        yield ()
        return
    for first in range(min_val, max_val + 1):
        for rest in _non_decreasing_sequences(length - 1, max_val, first):
            yield (first,) + rest


def _generate_canonical_pair_values(max_pair_val=6):
    """
    Generate ALL pair values that are lex-smallest in their rotation orbit.

    Approach: generate non-decreasing per-orbit PVs (33M for max_pair_val=6),
    compute the orbit lex-smallest min(pv, rotate(pv), rotate²(pv)) for each,
    and yield unique results. This naturally includes every possible pair value
    that is lex-smallest in its orbit.
    """
    seen = set()
    for o1 in _non_decreasing_sequences(3, max_pair_val):
        for o2 in _non_decreasing_sequences(3, max_pair_val):
            for o3 in _non_decreasing_sequences(3, max_pair_val):
                for o4 in _non_decreasing_sequences(3, max_pair_val):
                    for de_val in range(1, max_pair_val + 1):
                        pv = [0] * N_PAIRS
                        pv[0], pv[5], pv[9] = o1
                        pv[1], pv[6], pv[2] = o2
                        pv[3], pv[7], pv[10] = o3
                        pv[4], pv[8], pv[11] = o4
                        pv[13] = de_val
                        tpv = tuple(pv)
                        r1 = _rotate_pair_values(tpv)
                        r2 = _rotate_pair_values(r1)
                        lex_smallest = min(tpv, r1, r2)
                        if lex_smallest not in seen:
                            seen.add(lex_smallest)
                            yield lex_smallest


# ---------------------------------------------------------------------------
# Canonical exceptional masks (no rotation needed with paper's sigma)
# ---------------------------------------------------------------------------

def _make_canonical_exc_masks(dist):
    """Canonical subsets of possible type triples under paper's sigma orbits.
    
    Full-or-nothing per orbit (2^8 = 256 masks). The paper's specific exc mask
    {ABC, BCD} is NOT in this space (it's not lex-smallest in its exc-mask orbit),
    so it is checked as an extra mask per pair combo in check_pair_batch.
    """
    dist_tuple = dist

    def is_possible(triple):
        counts = [0] * N_TYPES
        for t in triple:
            counts[t] += 1
        return all(counts[i] <= dist_tuple[i] for i in range(N_TYPES))

    base_goods = tuple(TYPE_LABELS.index(l) for l in make_goods(dist))
    sigmas = [list(range(8)), GOODS_SIGMA, GOODS_SIGMA2]

    type_to_triples = {}
    for g in combinations_with_replacement(range(8), 3):
        tt = tuple(sorted(base_goods[i] for i in g))
        if is_possible(tt):
            type_to_triples.setdefault(tt, set()).add(g)

    def triple_type_orbit(tt):
        orbit = {tt}
        for sig in sigmas:
            for g in type_to_triples.get(tt, set()):
                mapped = tuple(sorted(sig[i] for i in g))
                mapped_tt = tuple(sorted(base_goods[i] for i in mapped))
                if is_possible(mapped_tt):
                    orbit.add(mapped_tt)
        return frozenset(orbit)

    seen = set()
    orbits = []
    for tt in sorted(type_to_triples.keys()):
        if tt in seen:
            continue
        orbit = triple_type_orbit(tt)
        for t in orbit:
            seen.add(t)
        orbits.append(tuple(sorted(orbit)))

    n_orbits = len(orbits)
    masks = []
    for bit in range(1 << n_orbits):
        exc_mask = 0
        for j in range(n_orbits):
            if bit & (1 << j):
                for tt in orbits[j]:
                    exc_mask |= 1 << TRIPLE_INDEX[tt]
        masks.append(exc_mask)
    return masks


CANONICAL_EXC_MASKS = {}
for _dist in DISTRIBUTIONS:
    CANONICAL_EXC_MASKS[_dist] = _make_canonical_exc_masks(_dist)


# ---------------------------------------------------------------------------
# Distribution-specific tables (paper's sigma)
# ---------------------------------------------------------------------------

def _build_dist_tables(dist):
    base_goods = tuple(TYPE_LABELS.index(l) for l in make_goods(dist))
    sigmas = [list(range(8)), GOODS_SIGMA, GOODS_SIGMA2]

    goods_by_agent = []
    for agent in range(3):
        sig = sigmas[agent]
        agent_types = tuple(base_goods[sig[i]] for i in range(8))
        goods_by_agent.append(agent_types)
    goods_by_agent = tuple(goods_by_agent)

    pair_idx = []
    triple_idx = []
    triple_pairs = []
    large_triples = []
    large_exc_masks = []

    for ag in goods_by_agent:
        pi = [0] * 256
        ti = [0] * 256
        tp = [[] for _ in range(256)]
        lt = [[] for _ in range(256)]
        le = [0] * 256

        for mask in range(256):
            gs = [g for g in range(8) if mask & (1 << g)]
            sz = len(gs)
            if sz == 2:
                pair = tuple(sorted(ag[g] for g in gs))
                pi[mask] = PAIR_INDEX[pair]
            elif sz == 3:
                triple = tuple(sorted(ag[g] for g in gs))
                ti[mask] = TRIPLE_INDEX[triple]
                tp[mask] = [(1 << f) | (1 << s) for f, s in combinations(gs, 2)]
            elif sz > 3:
                masks = []
                em = 0
                for tg in combinations(gs, 3):
                    tm = 0
                    for g in tg:
                        tm |= 1 << g
                    masks.append(tm)
                    em |= 1 << ti[tm]
                lt[mask] = masks
                le[mask] = em

        pair_idx.append(tuple(pi))
        triple_idx.append(tuple(ti))
        triple_pairs.append(tuple(tuple(m) for m in tp))
        large_triples.append(tuple(tuple(m) for m in lt))
        large_exc_masks.append(tuple(le))

    return {
        'pair_idx': tuple(pair_idx),
        'triple_idx': tuple(triple_idx),
        'triple_pairs': tuple(triple_pairs),
        'large_triples': tuple(large_triples),
        'large_exc_masks': tuple(large_exc_masks),
        'goods': goods_by_agent,
    }


_dist_cache = {}


def _get_dist_tables(dist):
    if dist not in _dist_cache:
        _dist_cache[dist] = _build_dist_tables(dist)
    return _dist_cache[dist]


# ---------------------------------------------------------------------------
# Value computation (exc mask same for all agents with paper's sigma)
# ---------------------------------------------------------------------------

def _values_for_agent(tables, agent, pair_values, exc_mask, singleton_vals=None):
    values = [0] * 256
    pi = tables['pair_idx'][agent]
    ti = tables['triple_idx'][agent]
    tp = tables['triple_pairs'][agent]
    lt = tables['large_triples'][agent]
    le = tables['large_exc_masks'][agent]

    if singleton_vals is None:
        for mask in MASKS_BY_SIZE[1]:
            values[mask] = 1
    else:
        for mask in MASKS_BY_SIZE[1]:
            gs = [g for g in range(8) if mask & (1 << g)]
            values[mask] = singleton_vals[tables['goods'][agent][gs[0]]]
    for mask in MASKS_BY_SIZE[2]:
        values[mask] = pair_values[pi[mask]]
    for mask in MASKS_BY_SIZE[3]:
        f, s, t = tp[mask]
        v = values[f]
        vs = values[s]
        vt = values[t]
        if vs > v:
            v = vs
        if vt > v:
            v = vt
        if exc_mask & (1 << ti[mask]):
            v = 7
        values[mask] = v
    for sz in range(4, 9):
        for mask in MASKS_BY_SIZE[sz]:
            if exc_mask & le[mask]:
                values[mask] = 7
            else:
                v = 0
                for tr in lt[mask]:
                    if values[tr] > v:
                        v = values[tr]
                values[mask] = v
    return values


# ---------------------------------------------------------------------------
# Summary tables
# ---------------------------------------------------------------------------

def _summary_tables(values):
    max_without = []
    sum_without = []
    for av in values:
        amax = [0] * 256
        asum = [0] * 256
        for mask, rm in enumerate(REDUCED_MASKS):
            if not rm:
                continue
            first = av[rm[0]]
            total = first
            maximum = first
            for r in rm[1:]:
                val = av[r]
                total += val
                if val > maximum:
                    maximum = val
            amax[mask] = maximum
            asum[mask] = total
        max_without.append(amax)
        sum_without.append(asum)
    return max_without, sum_without


# ---------------------------------------------------------------------------
# Allocation generation (sorted by balance for early exit)
# ---------------------------------------------------------------------------

def _build_allocations():
    all_goods_mask = (1 << 8) - 1
    allocs = []
    for a0 in range(1, all_goods_mask):
        for a1 in range(1, all_goods_mask):
            a2 = all_goods_mask ^ a0 ^ a1
            if a2 < 1:
                continue
            if a0 & a1 or a0 & a2 or a1 & a2:
                continue
            allocs.append((a0, a1, a2))
    return tuple(allocs)


ALL_ALLOCATIONS = _build_allocations()


def _alloc_sort_key(alloc):
    sizes = (alloc[0].bit_count(), alloc[1].bit_count(), alloc[2].bit_count())
    return (max(sizes) - min(sizes), -min(sizes))


ALL_ALLOCATIONS = tuple(sorted(ALL_ALLOCATIONS, key=_alloc_sort_key))

_FLAT_ALL = array.array('i', (x for a in ALL_ALLOCATIONS for x in a))
_N_ALL = len(ALL_ALLOCATIONS)


# ---------------------------------------------------------------------------
# Instance checking
# ---------------------------------------------------------------------------

def _is_efx(values, mw, alloc):
    a0, a1, a2 = alloc
    v0 = values[0][a0]
    if v0 < mw[0][a1] or v0 < mw[0][a2]:
        return False
    v1 = values[1][a1]
    if v1 < mw[1][a2] or v1 < mw[1][a0]:
        return False
    v2 = values[2][a2]
    if v2 < mw[2][a0] or v2 < mw[2][a1]:
        return False
    return True


def _is_efr(values, sw, alloc):
    a0, a1, a2 = alloc
    v0 = values[0][a0]
    if v0 * COUNT_WITHOUT[a1] < sw[0][a1]:
        return False
    if v0 * COUNT_WITHOUT[a2] < sw[0][a2]:
        return False
    v1 = values[1][a1]
    if v1 * COUNT_WITHOUT[a2] < sw[1][a2]:
        return False
    if v1 * COUNT_WITHOUT[a0] < sw[1][a0]:
        return False
    v2 = values[2][a2]
    if v2 * COUNT_WITHOUT[a0] < sw[2][a0]:
        return False
    if v2 * COUNT_WITHOUT[a1] < sw[2][a1]:
        return False
    return True


def _mask_to_bundle(mask):
    return frozenset(g for g in range(8) if mask & (1 << g))


def _masks_to_alloc(alloc):
    return tuple(_mask_to_bundle(m) for m in alloc)


# ---------------------------------------------------------------------------
# Format instance for output
# ---------------------------------------------------------------------------

def format_instance(pair_values, exc_mask, singleton_vals=None):
    pair_dict = {PAIR_LABELS[i]: pair_values[i] for i in range(N_PAIRS) if pair_values[i] > 0}
    exceptional = {
        TRIPLE_LABELS[i] for i in range(N_TRIPLES) if exc_mask & (1 << i)
    }
    if singleton_vals is None:
        singleton_vals = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1}
    lines = []
    lines.append(f"Distribution: (2, 2, 2, 1, 1)")
    lines.append(f"Sigma: (0 1 2)(3 4 5) on goods")
    lines.append(f"Singletons: {singleton_vals}")
    lines.append(f"Pair values: {pair_dict}")
    lines.append(f"Exceptional triples: {exceptional}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Check instance (C fast path or Python fallback)
# ---------------------------------------------------------------------------

def check_instance_fast(pair_values, exc_mask, singleton_vals=None):
    dist = DISTRIBUTIONS[0]
    tables = _get_dist_tables(dist)
    values = [_values_for_agent(tables, a, pair_values, exc_mask, singleton_vals) for a in range(3)]

    if _lib is not None:
        mw_sw = _summary_tables(values)
        mw, sw = mw_sw

        flat_tables = array.array('i')
        for agent_values in values:
            flat_tables.extend(agent_values)
        for agent_mw in mw:
            flat_tables.extend(agent_mw)
        for agent_sw in sw:
            flat_tables.extend(agent_sw)

        c_tables = (ctypes.c_int * len(flat_tables)).from_buffer_copy(flat_tables)
        c_cw = (ctypes.c_int * 256)(*COUNT_WITHOUT)
        c_allocs = (ctypes.c_int * len(_FLAT_ALL)).from_buffer_copy(_FLAT_ALL)

        result = _lib.check_allocations(c_tables, c_cw, c_allocs, _N_ALL)
        if result == 2:
            return 'has_efx'
        elif result == 1:
            return 'efr_not_efx'
        else:
            return 'neither'

    mw, sw = _summary_tables(values)
    efr_found = False
    for alloc in ALL_ALLOCATIONS:
        if _is_efx(values, mw, alloc):
            return 'has_efx'
        if not efr_found and _is_efr(values, sw, alloc):
            efr_found = True
    return 'efr_not_efx' if efr_found else 'neither'


# ---------------------------------------------------------------------------
# Batch check: one pair combo -> all exc masks
# ---------------------------------------------------------------------------

def check_pair_batch(task):
    task_id, pair_values, singleton_vals = task
    dist = DISTRIBUTIONS[0]
    exc_masks = CANONICAL_EXC_MASKS[dist]

    # Paper's exc mask: {ABC, BCD} — not in canonical space (not lex-smallest
    # in its exc-mask orbit), but checked as 1 extra mask per pair combo.
    paper_exc = (1 << TRIPLE_INDEX[(0, 1, 2)]) | (1 << TRIPLE_INDEX[(1, 2, 3)])

    checked = 0
    results = []
    for exc_mask in exc_masks:
        checked += 1
        result = check_instance_fast(pair_values, exc_mask, singleton_vals)
        if result != 'has_efx':
            results.append((result, pair_values, exc_mask, singleton_vals))

    # Also check paper's exc mask if not already in canonical space
    if paper_exc not in exc_masks:
        checked += 1
        result = check_instance_fast(pair_values, paper_exc, singleton_vals)
        if result != 'has_efx':
            results.append((result, pair_values, paper_exc, singleton_vals))

    return task_id, checked, results


# ---------------------------------------------------------------------------
# Singleton value combos (canonical: s_A <= s_B <= s_C, s_D, s_E free)
# ---------------------------------------------------------------------------

def generate_singleton_combos():
    """Generate all canonical singleton value combos.
    
    Canonical form: s_A <= s_B <= s_C (cyclic types), s_D and s_E free.
    Each value in {1, ..., 6}.
    """
    for sD in range(1, 7):
        for sE in range(1, 7):
            for sA in range(1, 7):
                for sB in range(sA, 7):
                    for sC in range(sB, 7):
                        yield {'A': sA, 'B': sB, 'C': sC, 'D': sD, 'E': sE}


def count_singleton_combos():
    """Count canonical singleton combos: C(8,3) * 6 * 6 = 56 * 36 = 2016."""
    return 56 * 36


# ---------------------------------------------------------------------------
# Task generation
# ---------------------------------------------------------------------------

def fast_tasks(max_pair_val=6, singleton_combos=None):
    """Generate tasks. If singleton_combos is None, singletons are fixed at 1."""
    if singleton_combos is None:
        singleton_combos = [None]  # None means all singletons = 1

    for sv in singleton_combos:
        for task_id, pv in enumerate(_generate_canonical_pair_values(max_pair_val)):
            yield task_id, pv, sv


def total_instances(max_pair_val=6, n_singletons=1):
    n = max_pair_val
    nseq = n * (n + 1) * (n + 2) // 6
    n_canon = nseq ** 4 * max_pair_val
    exc_count = len(CANONICAL_EXC_MASKS[DISTRIBUTIONS[0]])
    return n_singletons * n_canon * (exc_count + 1)


def total_batches(max_pair_val=6, n_singletons=1):
    n = max_pair_val
    nseq = n * (n + 1) * (n + 2) // 6
    return n_singletons * nseq ** 4 * max_pair_val
    return nseq ** 4 * max_pair_val
