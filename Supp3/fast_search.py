import ctypes
import os
from itertools import combinations, combinations_with_replacement, product

from efx_checker import _allocation_masks, masks_to_allocation
from instance import DISTRIBUTIONS, TYPE_LABELS, make_goods, type_rotation, get_cycle_types


PAIR_TYPES = tuple(combinations_with_replacement(range(3), 2))
TRIPLE_TYPES = tuple(combinations_with_replacement(range(3), 3))
PAIR_LABELS = tuple(frozenset(TYPE_LABELS[t] for t in pair) for pair in PAIR_TYPES)
TRIPLE_LABELS = tuple(tuple(TYPE_LABELS[t] for t in triple) for triple in TRIPLE_TYPES)
PAIR_INDEX = {pair: index for index, pair in enumerate(PAIR_TYPES)}
TRIPLE_INDEX = {triple: index for index, triple in enumerate(TRIPLE_TYPES)}
PAIR_VALUE_COMBOS = tuple(product(range(1, 7), repeat=len(PAIR_TYPES)))
N_TRIPLE_TYPES = len(TRIPLE_TYPES)
COUNT_WITHOUT = tuple(mask.bit_count() for mask in range(1 << 8))
REDUCED_MASKS = tuple(
    tuple(mask & ~(1 << good) for good in range(8) if mask & (1 << good))
    for mask in range(1 << 8)
)
ALLOCATIONS = tuple(_allocation_masks())
CANONICAL_ALLOCATIONS = tuple(
    alloc for alloc in ALLOCATIONS if alloc[0] <= alloc[2]
)
MASKS_BY_SIZE = tuple(
    tuple(mask for mask in range(256) if mask.bit_count() == size)
    for size in range(9)
)


def _equity_key(alloc):
    return max(m.bit_count() for m in alloc)

ORDERED_ALLOCATIONS = tuple(sorted(ALLOCATIONS, key=_equity_key))
ORDERED_CANONICAL = tuple(sorted(CANONICAL_ALLOCATIONS, key=_equity_key))


# ---------------------------------------------------------------------------
# C extension loading
# ---------------------------------------------------------------------------

_c_lib = None
_c_reduced_masks = None
_c_reduced_counts = None
_c_count_without = None
_c_allocs_flat = None
_c_allocs_list = None
_c_canonical_flat = None
_c_canonical_list = None

_c_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hot_loop.so')
if os.path.exists(_c_path):
    try:
        _c_lib = ctypes.CDLL(_c_path)
        _c_lib.check_allocations.restype = ctypes.c_int
        _c_lib.check_allocations.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
        ]

        _c_reduced_masks = (ctypes.c_int * (256 * 8))()
        _c_reduced_counts = (ctypes.c_int * 256)()
        _c_count_without = (ctypes.c_int * 256)()
        for mask in range(256):
            rms = REDUCED_MASKS[mask]
            _c_reduced_counts[mask] = len(rms)
            for i, rm in enumerate(rms):
                _c_reduced_masks[mask * 8 + i] = rm
            _c_count_without[mask] = COUNT_WITHOUT[mask]

        allocs_flat = []
        for a in ORDERED_ALLOCATIONS:
            allocs_flat.extend(a)
        _c_allocs_flat = (ctypes.c_int * len(allocs_flat))(*allocs_flat)
        _c_allocs_list = ORDERED_ALLOCATIONS

        canon_flat = []
        for a in ORDERED_CANONICAL:
            canon_flat.extend(a)
        _c_canonical_flat = (ctypes.c_int * len(canon_flat))(*canon_flat)
        _c_canonical_list = ORDERED_CANONICAL

    except Exception:
        _c_lib = None


def _check_allocations_c(v0, v1, v2, use_canonical):
    if use_canonical:
        flat = _c_canonical_flat
        lst = _c_canonical_list
        n = len(ORDERED_CANONICAL)
    else:
        flat = _c_allocs_flat
        lst = _c_allocs_list
        n = len(ORDERED_ALLOCATIONS)

    v0_arr = (ctypes.c_int * 256)(*v0)
    v1_arr = (ctypes.c_int * 256)(*v1)
    v2_arr = (ctypes.c_int * 256)(*v2)
    efr_idx = ctypes.c_int(-1)

    has_efx = _c_lib.check_allocations(
        v0_arr, v1_arr, v2_arr,
        _c_reduced_masks, _c_reduced_counts, _c_count_without,
        flat, n, ctypes.byref(efr_idx)
    )
    if has_efx:
        return True, None
    if efr_idx.value >= 0:
        return False, lst[efr_idx.value]
    return False, None


# ---------------------------------------------------------------------------
# Tables and rotation
# ---------------------------------------------------------------------------

def _rotated_triple_mask(exc_mask, agent, dist):
    rotated = 0
    for index, triple in enumerate(TRIPLE_TYPES):
        if exc_mask & (1 << index):
            rotated_triple = tuple(sorted(
                type_rotation(dist, type_id, -agent) for type_id in triple
            ))
            rotated |= 1 << TRIPLE_INDEX[rotated_triple]
    return rotated


ROTATED_EXCEPTIONAL_MASKS = {}
for _dist in DISTRIBUTIONS:
    ROTATED_EXCEPTIONAL_MASKS[_dist] = tuple(
        tuple(_rotated_triple_mask(_exc_mask, _agent, _dist)
              for _agent in range(3))
        for _exc_mask in range(1 << N_TRIPLE_TYPES)
    )


def _dist_tables(dist):
    base_goods = tuple(TYPE_LABELS.index(label) for label in make_goods(dist))
    goods_by_agent = tuple(
        tuple(type_rotation(dist, type_id, agent) for type_id in base_goods)
        for agent in range(3)
    )

    pair_index_by_agent = []
    triple_index_by_agent = []
    triple_pairs = []
    large_triples = []
    large_triple_exception_masks = []

    for agent_goods in goods_by_agent:
        agent_pair_indices = [0] * 256
        agent_triple_indices = [0] * 256
        agent_triple_pairs = [[] for _ in range(256)]
        agent_large_triples = [[] for _ in range(256)]
        agent_large_exception_masks = [0] * 256

        for mask in range(256):
            goods = [good for good in range(8) if mask & (1 << good)]
            size = len(goods)
            if size == 2:
                pair = tuple(sorted(agent_goods[good] for good in goods))
                agent_pair_indices[mask] = PAIR_INDEX[pair]
            elif size == 3:
                triple = tuple(sorted(agent_goods[good] for good in goods))
                agent_triple_indices[mask] = TRIPLE_INDEX[triple]
                agent_triple_pairs[mask] = [
                    (1 << first) | (1 << second)
                    for first, second in combinations(goods, 2)
                ]
            elif size > 3:
                masks = []
                exception_mask = 0
                for triple_goods in combinations(goods, 3):
                    triple_mask = 0
                    for good in triple_goods:
                        triple_mask |= 1 << good
                    masks.append(triple_mask)
                    exception_mask |= 1 << agent_triple_indices[triple_mask]
                agent_large_triples[mask] = masks
                agent_large_exception_masks[mask] = exception_mask

        pair_index_by_agent.append(tuple(agent_pair_indices))
        triple_index_by_agent.append(tuple(agent_triple_indices))
        triple_pairs.append(tuple(tuple(m) for m in agent_triple_pairs))
        large_triples.append(tuple(tuple(m) for m in agent_large_triples))
        large_triple_exception_masks.append(tuple(agent_large_exception_masks))

    return {
        'dist': dist,
        'masks_by_size': MASKS_BY_SIZE,
        'pair_index_by_agent': tuple(pair_index_by_agent),
        'triple_index_by_agent': tuple(triple_index_by_agent),
        'triple_pairs': tuple(triple_pairs),
        'large_triples': tuple(large_triples),
        'large_triple_exception_masks': tuple(large_triple_exception_masks),
    }


DIST_TABLES = {dist: _dist_tables(dist) for dist in DISTRIBUTIONS}


# ---------------------------------------------------------------------------
# Value computation
# ---------------------------------------------------------------------------

def _base_values_for_agent(tables, agent, pair_values):
    values = [0] * 256
    masks_by_size = tables['masks_by_size']
    pair_indices = tables['pair_index_by_agent'][agent]
    triple_pairs = tables['triple_pairs'][agent]
    large_triples = tables['large_triples'][agent]

    for mask in masks_by_size[1]:
        values[mask] = 1
    for mask in masks_by_size[2]:
        values[mask] = pair_values[pair_indices[mask]]
    for mask in masks_by_size[3]:
        first, second, third = triple_pairs[mask]
        v = values[first]
        s = values[second]
        t = values[third]
        if s > v:
            v = s
        if t > v:
            v = t
        values[mask] = v
    for size in range(4, 9):
        for mask in masks_by_size[size]:
            v = 0
            for triple in large_triples[mask]:
                tv = values[triple]
                if tv > v:
                    v = tv
            values[mask] = v
    return values


def _apply_exceptional(agent_values, tables, agent, rotated_exc_mask):
    masks_by_size = tables['masks_by_size']
    triple_indices = tables['triple_index_by_agent'][agent]
    large_exception_masks = tables['large_triple_exception_masks'][agent]

    for mask in masks_by_size[3]:
        if rotated_exc_mask & (1 << triple_indices[mask]):
            agent_values[mask] = 7
    for size in range(4, 9):
        for mask in masks_by_size[size]:
            if rotated_exc_mask & large_exception_masks[mask]:
                agent_values[mask] = 7


# ---------------------------------------------------------------------------
# Python fallback for summary + allocation check
# ---------------------------------------------------------------------------

def _summary_tables(values):
    max_without = []
    sum_without = []
    for agent_values in values:
        agent_max = [0] * 256
        agent_sum = [0] * 256
        for mask, reduced_masks in enumerate(REDUCED_MASKS):
            if not reduced_masks:
                continue
            first = agent_values[reduced_masks[0]]
            total = first
            maximum = first
            for reduced in reduced_masks[1:]:
                value = agent_values[reduced]
                total += value
                if value > maximum:
                    maximum = value
            agent_max[mask] = maximum
            agent_sum[mask] = total
        max_without.append(agent_max)
        sum_without.append(agent_sum)
    return max_without, sum_without


def _is_efx(values, max_without, allocation):
    a0, a1, a2 = allocation
    v0 = values[0][a0]
    if v0 < max_without[0][a1] or v0 < max_without[0][a2]:
        return False
    v1 = values[1][a1]
    if v1 < max_without[1][a2] or v1 < max_without[1][a0]:
        return False
    v2 = values[2][a2]
    if v2 < max_without[2][a0] or v2 < max_without[2][a1]:
        return False
    return True


def _is_efr(values, sum_without, allocation):
    a0, a1, a2 = allocation
    v0 = values[0][a0]
    if v0 * COUNT_WITHOUT[a1] < sum_without[0][a1]:
        return False
    if v0 * COUNT_WITHOUT[a2] < sum_without[0][a2]:
        return False
    v1 = values[1][a1]
    if v1 * COUNT_WITHOUT[a2] < sum_without[1][a2]:
        return False
    if v1 * COUNT_WITHOUT[a0] < sum_without[1][a0]:
        return False
    v2 = values[2][a2]
    if v2 * COUNT_WITHOUT[a0] < sum_without[2][a0]:
        return False
    if v2 * COUNT_WITHOUT[a1] < sum_without[2][a1]:
        return False
    return True


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _format_fast_result(dist, pair_values, exc_mask, result):
    base_goods = make_goods(dist)
    pair_dict = {PAIR_LABELS[i]: pair_values[i] for i in range(len(PAIR_LABELS))}
    exceptional_0 = tuple(sorted(
        TRIPLE_LABELS[index]
        for index in range(N_TRIPLE_TYPES)
        if exc_mask & (1 << index)
    ))

    cycle = get_cycle_types(dist)
    cycle_labels = [TYPE_LABELS[i] for i in cycle]
    if len(cycle) == 3:
        sigma_desc = f"3-cycle: {cycle_labels[0]}->{cycle_labels[1]}->{cycle_labels[2]}->{cycle_labels[0]}"
    else:
        fixed = [TYPE_LABELS[i] for i in range(3) if i not in cycle]
        sigma_desc = f"2-cycle: {cycle_labels[0]}<->{cycle_labels[1]}, {fixed[0]} fixed"

    lines = []
    lines.append(f"Distribution: {dist}")
    lines.append(f"Goods: {base_goods}")
    lines.append(f"Sigma: {sigma_desc}")
    lines.append(f"Pairs: {pair_dict}")
    lines.append(f"Exceptional (agent 0): {exceptional_0}")

    for agent in range(3):
        rotated_goods = [TYPE_LABELS[type_rotation(dist, TYPE_LABELS.index(t), agent)] for t in base_goods]
        rotated_exc = tuple(sorted(
            tuple(sorted(TYPE_LABELS[type_rotation(dist, TYPE_LABELS.index(t), -agent)] for t in triple))
            for triple in exceptional_0
        ))
        lines.append(f"Agent {agent}: types={rotated_goods}, exceptional={rotated_exc}")

    lines.append(f"EFX: {'YES' if result['has_efx'] else 'NO'}  "
                 f"EFR: {'YES' if result['has_efr'] else 'NO'}")
    if result.get('efr_allocation'):
        lines.append(f"  EFR alloc: {result['efr_allocation']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main batch check
# ---------------------------------------------------------------------------

def check_pair_batch(task):
    task_id, dist, pair_index, pair_values = task
    tables = DIST_TABLES[dist]
    rotated_masks_all = ROTATED_EXCEPTIONAL_MASKS[dist]
    use_canonical = len(get_cycle_types(dist)) == 2

    base0 = _base_values_for_agent(tables, 0, pair_values)
    base1 = _base_values_for_agent(tables, 1, pair_values)
    base2 = _base_values_for_agent(tables, 2, pair_values)

    checked = 0
    results = []
    for exc_mask in range(1 << N_TRIPLE_TYPES):
        checked += 1
        rm = rotated_masks_all[exc_mask]

        v0 = base0[:]
        v1 = base1[:]
        v2 = base2[:]
        _apply_exceptional(v0, tables, 0, rm[0])
        _apply_exceptional(v1, tables, 1, rm[1])
        _apply_exceptional(v2, tables, 2, rm[2])

        if _c_lib is not None:
            has_efx, efr_allocation = _check_allocations_c(v0, v1, v2, use_canonical)
        else:
            allocs = ORDERED_CANONICAL if use_canonical else ORDERED_ALLOCATIONS
            max_without, sum_without = _summary_tables((v0, v1, v2))
            has_efx = False
            efr_allocation = None
            for allocation in allocs:
                if _is_efx((v0, v1, v2), max_without, allocation):
                    has_efx = True
                    break
                if efr_allocation is None and _is_efr((v0, v1, v2), sum_without, allocation):
                    efr_allocation = allocation

        if has_efx:
            continue

        if efr_allocation is not None:
            result = {'has_efx': False, 'has_efr': True,
                      'efr_allocation': masks_to_allocation(efr_allocation)}
            results.append(('efr_not_efx',
                            _format_fast_result(dist, pair_values, exc_mask, result)))
        else:
            result = {'has_efx': False, 'has_efr': False, 'efr_allocation': None}
            results.append(('neither',
                            _format_fast_result(dist, pair_values, exc_mask, result)))

    return task_id, checked, results


def fast_tasks(distributions):
    task_id = 0
    for dist in distributions:
        for pair_index, pair_values in enumerate(PAIR_VALUE_COMBOS):
            yield task_id, dist, pair_index, pair_values
            task_id += 1


def total_instances(num_distributions):
    return num_distributions * len(PAIR_VALUE_COMBOS) * (1 << N_TRIPLE_TYPES)


def total_batches(num_distributions):
    return num_distributions * len(PAIR_VALUE_COMBOS)
