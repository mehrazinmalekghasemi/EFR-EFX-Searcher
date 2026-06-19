"""
fast_search.py
--------------
Bitmask-based fast search for 4-type, 8-good, 3-agent instances.

Key optimizations:
  - C extension for allocation checking (checker.c / checker.so)
  - Cyclic symmetry pruning on pair values and exceptional subsets
  - Lemma 2.4 allocation pruning: canonical allocations only
  - Balanced-allocation ordering: check balanced first for faster early exit
"""

import array
import ctypes
import os
import subprocess
from itertools import combinations, combinations_with_replacement

from instance import DISTRIBUTIONS, TYPE_LABELS, make_goods, get_non_singleton_indices

PAIR_TYPES = tuple(combinations_with_replacement(range(4), 2))
TRIPLE_TYPES = tuple(combinations_with_replacement(range(4), 3))
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
# Cyclic symmetry pruning
# ---------------------------------------------------------------------------

def _compute_group(dist):
    ns = get_non_singleton_indices(dist)
    n_cycle = len(ns)
    group = []
    for k in range(n_cycle):
        perm = {}
        for idx in range(4):
            if idx in ns:
                pos = ns.index(idx)
                perm[idx] = ns[(pos + k) % n_cycle]
            else:
                perm[idx] = idx
        group.append(perm)
    return group


def _apply_perm_to_pair(perm, pair):
    return tuple(sorted(perm[t] for t in pair))


def _apply_perm_to_triple(perm, triple):
    return tuple(sorted(perm[t] for t in triple))


def _compute_orbits(items, group, apply_perm):
    seen = set()
    orbits = []
    for item in items:
        if item in seen:
            continue
        orbit = set()
        for perm in group:
            mapped = apply_perm(perm, item)
            orbit.add(mapped)
            seen.add(mapped)
        orbits.append(tuple(sorted(orbit)))
    return orbits


def _non_decreasing_sequences(length, max_val, min_val=1):
    if length == 0:
        yield ()
        return
    for first in range(min_val, max_val + 1):
        for rest in _non_decreasing_sequences(length - 1, max_val, first):
            yield (first,) + rest


def _make_canonical_pair_values(dist):
    group = _compute_group(dist)
    if len(group) <= 1:
        return None
    orbits = _compute_orbits(PAIR_TYPES, group, _apply_perm_to_pair)
    orbits = [tuple(sorted(orbit)) for orbit in orbits]
    result = []
    orbit_seqs = [_non_decreasing_sequences(len(o), 6) for o in orbits]
    for combo in __import__('itertools').product(*orbit_seqs):
        arr = [0] * N_PAIRS
        for orbit, values in zip(orbits, combo):
            for pair, val in zip(orbit, values):
                arr[PAIR_INDEX[pair]] = val
        result.append(tuple(arr))
    return result


def _make_canonical_exc_masks(dist):
    group = _compute_group(dist)
    orbits = _compute_orbits(TRIPLE_TYPES, group, _apply_perm_to_triple)
    n_orbits = len(orbits)
    if len(group) <= 1:
        return list(range(1 << N_TRIPLES))
    masks = []
    for mask in range(1 << n_orbits):
        exc_mask = 0
        for i in range(n_orbits):
            if mask & (1 << i):
                for triple in orbits[i]:
                    exc_mask |= 1 << TRIPLE_INDEX[triple]
        masks.append(exc_mask)
    return masks


# Precompute canonical search spaces per distribution
CANONICAL_SEARCH = {}
for dist in DISTRIBUTIONS:
    CANONICAL_SEARCH[dist] = {
        'pair_values': _make_canonical_pair_values(dist),
        'exc_masks': _make_canonical_exc_masks(dist),
    }


# ---------------------------------------------------------------------------
# Allocation generation (Lemma 2.4) — sorted by balance
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
# Distribution-specific tables
# ---------------------------------------------------------------------------

def _build_type_perm(dist, agent):
    ns = get_non_singleton_indices(dist)
    n_cycle = len(ns)
    perm = {}
    for idx in range(4):
        if idx in ns:
            perm[idx] = ns[(ns.index(idx) + agent) % n_cycle]
        else:
            perm[idx] = idx
    return perm


def _build_bit_perm(dist):
    perms = [_build_type_perm(dist, a) for a in range(3)]
    bit_perms = []
    for a in range(3):
        bp = [0] * N_TRIPLES
        for i in range(N_TRIPLES):
            rt = tuple(sorted(perms[a][t] for t in TRIPLE_TYPES[i]))
            bp[i] = TRIPLE_INDEX[rt]
        bit_perms.append(tuple(bp))
    return tuple(bit_perms)


def _rotated_mask(exc_mask, bp):
    result = 0
    m = exc_mask
    while m:
        lsb = m & -m
        idx = lsb.bit_length() - 1
        result |= 1 << bp[idx]
        m ^= lsb
    return result


def _build_dist_tables(dist):
    base_goods = tuple(TYPE_LABELS.index(l) for l in make_goods(dist))
    perms = [_build_type_perm(dist, a) for a in range(3)]
    goods_by_agent = tuple(
        tuple(perms[a][tid] for tid in base_goods) for a in range(3)
    )
    bit_perms = _build_bit_perm(dist)

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
        'bit_perms': bit_perms,
    }


_dist_cache = {}


def _get_dist_tables(dist):
    if dist not in _dist_cache:
        _dist_cache[dist] = _build_dist_tables(dist)
    return _dist_cache[dist]


# ---------------------------------------------------------------------------
# Instance checking
# ---------------------------------------------------------------------------

def _values_for_agent(tables, agent, pair_values, exc_mask):
    values = [0] * 256
    pi = tables['pair_idx'][agent]
    ti = tables['triple_idx'][agent]
    tp = tables['triple_pairs'][agent]
    lt = tables['large_triples'][agent]
    le = tables['large_exc_masks'][agent]
    bp = tables['bit_perms'][agent]
    rot_exc = _rotated_mask(exc_mask, bp)

    for mask in MASKS_BY_SIZE[1]:
        values[mask] = 1
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
        if rot_exc & (1 << ti[mask]):
            v = 7
        values[mask] = v
    for sz in range(4, 9):
        for mask in MASKS_BY_SIZE[sz]:
            if rot_exc & le[mask]:
                values[mask] = 7
            else:
                v = 0
                for tr in lt[mask]:
                    if values[tr] > v:
                        v = values[tr]
                values[mask] = v
    return values


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


def format_instance(dist, pair_values, exc_mask):
    pair_dict = {PAIR_LABELS[i]: pair_values[i] for i in range(N_PAIRS)}
    exceptional = {
        TRIPLE_LABELS[i] for i in range(N_TRIPLES) if exc_mask & (1 << i)
    }
    lines = []
    lines.append(f"Distribution: {dist}")
    lines.append(f"Singletons: {{'A': 1, 'B': 1, 'C': 1, 'D': 1}}")
    lines.append(f"Pair values: {pair_dict}")
    lines.append(f"Exceptional triples: {exceptional}")
    lines.append(f"Allocation (agents 0,1,2):")
    return "\n".join(lines)


def check_instance_fast(dist, pair_values, exc_mask):
    tables = _get_dist_tables(dist)
    values = [_values_for_agent(tables, a, pair_values, exc_mask) for a in range(3)]
    mw, sw = _summary_tables(values)

    if _lib is not None:
        # C fast path
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

    # Python fallback
    efr_found = False
    for alloc in ALL_ALLOCATIONS:
        if _is_efx(values, mw, alloc):
            return 'has_efx'
        if not efr_found and _is_efr(values, sw, alloc):
            efr_found = True
    return 'efr_not_efx' if efr_found else 'neither'


# ---------------------------------------------------------------------------
# Search interface
# ---------------------------------------------------------------------------

def check_pair_batch(task):
    task_id, dist, pair_index, pair_values = task
    checked = 0
    results = []
    for exc_mask in CANONICAL_SEARCH[dist]['exc_masks']:
        checked += 1
        result = check_instance_fast(dist, pair_values, exc_mask)
        if result != 'has_efx':
            results.append((result, dist, pair_values, exc_mask))
    return task_id, checked, results


def fast_tasks(distributions):
    task_id = 0
    for dist in distributions:
        pv_list = CANONICAL_SEARCH[dist]['pair_values']
        if pv_list is not None:
            for pi, pv in enumerate(pv_list):
                yield task_id, dist, pi, pv
                task_id += 1
        else:
            for pi, pv in enumerate(__import__('itertools').product(range(1, 7), repeat=N_PAIRS)):
                yield task_id, dist, pi, pv
                task_id += 1


def total_instances(num_distributions):
    count = 0
    for dist in DISTRIBUTIONS[:num_distributions]:
        cs = CANONICAL_SEARCH[dist]
        pv_count = len(cs['pair_values']) if cs['pair_values'] is not None else 6 ** N_PAIRS
        count += pv_count * len(cs['exc_masks'])
    return count


def total_batches(num_distributions):
    count = 0
    for dist in DISTRIBUTIONS[:num_distributions]:
        cs = CANONICAL_SEARCH[dist]
        count += len(cs['pair_values']) if cs['pair_values'] is not None else 6 ** N_PAIRS
    return count
