from itertools import combinations, product
from fractions import Fraction
from efx_checker import (
    _allocation_masks,
    masks_to_allocation,
    removal_summary_tables,
    value_tables,
)


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


def is_efr(instance, allocation):
    if allocation and isinstance(allocation[0], int):
        return is_efr_masks(value_tables(instance), allocation)

    for i in range(instance.n_agents):
        vi = instance.rank[i]
        val_i = Fraction(vi(allocation[i]))
        for j in range(instance.n_agents):
            if i == j:
                continue
            pj = allocation[j]
            if not pj:
                continue
            mean_val = Fraction(sum(vi(pj - {g}) for g in pj), len(pj))
            if val_i < mean_val:
                return False
    return True


def is_efr_masks(values, allocation, sum_without=None, count_without=None):
    if sum_without is None or count_without is None:
        _, sum_without, count_without = removal_summary_tables(values)

    for i in range(3):
        val_i = values[i][allocation[i]]
        for j in range(3):
            if i == j:
                continue
            count = count_without[allocation[j]]
            if count and val_i * count < sum_without[i][allocation[j]]:
                return False
    return True


def find_efr(instance):
    values = value_tables(instance)
    _, sum_without, count_without = removal_summary_tables(values)
    for alloc in _allocation_masks(instance.n_goods, instance.n_agents):
        if is_efr_masks(values, alloc, sum_without, count_without):
            return masks_to_allocation(alloc)
    return None
