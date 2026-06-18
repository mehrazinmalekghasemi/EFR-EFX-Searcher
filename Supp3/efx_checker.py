from functools import lru_cache
from itertools import combinations, product


N_GOODS = 8
N_AGENTS = 3
ALL_ALLOCATION_MASKS = None
MASK_WITHOUT_GOODS = None


def all_allocations(n_goods=8, n_agents=3):
    other_agents = [agent for agent in range(n_agents) if agent != 1]
    for agent_one_goods in combinations(range(n_goods), 2):
        agent_one_set = frozenset(agent_one_goods)
        remaining_goods = [good for good in range(n_goods) if good not in agent_one_set]
        for assignment in product(other_agents, repeat=len(remaining_goods)):
            if any(assignment.count(agent) < 2 for agent in other_agents):
                continue
            bundles = [[] for _ in range(n_agents)]
            bundles[1].extend(agent_one_goods)
            for good, agent in zip(remaining_goods, assignment):
                bundles[agent].append(good)
            yield tuple(frozenset(b) for b in bundles)


def _allocation_masks(n_goods=N_GOODS, n_agents=N_AGENTS):
    global ALL_ALLOCATION_MASKS
    if n_goods == N_GOODS and n_agents == N_AGENTS and ALL_ALLOCATION_MASKS is not None:
        return ALL_ALLOCATION_MASKS

    all_goods_mask = (1 << n_goods) - 1
    allocations = []
    for agent_one_goods in combinations(range(n_goods), 2):
        agent_one_mask = 0
        for good in agent_one_goods:
            agent_one_mask |= 1 << good
        remaining_mask = all_goods_mask ^ agent_one_mask
        submask = remaining_mask
        while submask:
            agent_zero_mask = submask
            agent_two_mask = remaining_mask ^ agent_zero_mask
            if agent_zero_mask.bit_count() >= 2 and agent_two_mask.bit_count() >= 2:
                allocations.append((agent_zero_mask, agent_one_mask, agent_two_mask))
            submask = (submask - 1) & remaining_mask

    if n_goods == N_GOODS and n_agents == N_AGENTS:
        ALL_ALLOCATION_MASKS = allocations
    return allocations


def _mask_without_goods(n_goods=N_GOODS):
    global MASK_WITHOUT_GOODS
    if n_goods == N_GOODS and MASK_WITHOUT_GOODS is not None:
        return MASK_WITHOUT_GOODS

    table = []
    for mask in range(1 << n_goods):
        reduced = []
        for good in range(n_goods):
            if mask & (1 << good):
                reduced.append(mask & ~(1 << good))
        table.append(tuple(reduced))

    if n_goods == N_GOODS:
        MASK_WITHOUT_GOODS = table
    return table


def _mask_to_bundle(mask):
    return frozenset(good for good in range(N_GOODS) if mask & (1 << good))


def masks_to_allocation(allocation):
    return tuple(_mask_to_bundle(mask) for mask in allocation)


@lru_cache(maxsize=None)
def _subset_infos(goods):
    infos = []
    masks_by_size = [[] for _ in range(len(goods) + 1)]

    for mask in range(1 << len(goods)):
        goods_in_mask = [good for good in range(len(goods)) if mask & (1 << good)]
        size = len(goods_in_mask)
        masks_by_size[size].append(mask)

        if size == 0:
            info = ('empty',)
        elif size == 1:
            info = ('singleton', goods[goods_in_mask[0]])
        elif size == 2:
            first, second = goods_in_mask
            info = ('pair', frozenset([goods[first], goods[second]]))
        elif size == 3:
            triple = tuple(sorted(goods[good] for good in goods_in_mask))
            pair_masks = []
            for first, second in combinations(goods_in_mask, 2):
                pair_masks.append((1 << first) | (1 << second))
            info = ('triple', triple, tuple(pair_masks))
        else:
            triple_masks = []
            for triple_goods in combinations(goods_in_mask, 3):
                triple_mask = 0
                for good in triple_goods:
                    triple_mask |= 1 << good
                triple_masks.append(triple_mask)
            info = ('large', tuple(triple_masks))

        infos.append(info)

    return tuple(infos), tuple(tuple(masks) for masks in masks_by_size)


def value_tables(instance):
    tables = []
    for agent in range(instance.n_agents):
        values = [0] * (1 << instance.n_goods)
        infos, masks_by_size = _subset_infos(tuple(instance.rank[agent].goods))
        exceptional = instance.rank[agent].exceptional
        singleton_vals = instance.rank[agent].singleton_vals
        pair_vals = instance.rank[agent].pair_vals

        for size, masks in enumerate(masks_by_size):
            for mask in masks:
                info = infos[mask]
                kind = info[0]
                if kind == 'empty':
                    values[mask] = 0
                elif kind == 'singleton':
                    values[mask] = singleton_vals[info[1]]
                elif kind == 'pair':
                    values[mask] = pair_vals[info[1]]
                elif kind == 'triple':
                    values[mask] = 7 if info[1] in exceptional else max(values[pair] for pair in info[2])
                else:
                    values[mask] = max(values[triple] for triple in info[1])

        tables.append(values)
    return tables


def removal_summary_tables(values):
    without_goods = _mask_without_goods()
    max_without = []
    sum_without = []
    count_without = [len(reduced) for reduced in without_goods]

    for agent_values in values:
        agent_max = [0] * len(without_goods)
        agent_sum = [0] * len(without_goods)
        for mask, reduced_masks in enumerate(without_goods):
            if reduced_masks:
                reduced_values = [agent_values[reduced] for reduced in reduced_masks]
                agent_max[mask] = max(reduced_values)
                agent_sum[mask] = sum(reduced_values)
        max_without.append(agent_max)
        sum_without.append(agent_sum)

    return max_without, sum_without, count_without


def is_efx_masks(values, allocation, max_without=None):
    if max_without is None:
        max_without = removal_summary_tables(values)[0]

    for i in range(N_AGENTS):
        val_i = values[i][allocation[i]]
        for j in range(N_AGENTS):
            if i != j and val_i < max_without[i][allocation[j]]:
                return False
    return True


def is_efx(instance, allocation):
    if allocation and isinstance(allocation[0], int):
        return is_efx_masks(value_tables(instance), allocation)

    for i in range(instance.n_agents):
        vi = instance.rank[i]
        val_i = vi(allocation[i])
        for j in range(instance.n_agents):
            if i == j:
                continue
            pj = allocation[j]
            for g in pj:
                if val_i < vi(pj - {g}):
                    return False
    return True


def find_efx(instance):
    values = value_tables(instance)
    max_without = removal_summary_tables(values)[0]
    for alloc in _allocation_masks(instance.n_goods, instance.n_agents):
        if is_efx_masks(values, alloc, max_without):
            return masks_to_allocation(alloc)
    return None
