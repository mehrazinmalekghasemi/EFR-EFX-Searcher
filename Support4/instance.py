"""
instance.py
-----------
3-agent, 8-good instance with 4 types (A, B, C, D) and rank-based valuations.

Type distributions: (2,2,2,2), (3,2,2,1), (3,3,1,1), (4,2,1,1), (5,1,1,1)

Agent 0's valuation is defined by:
  - singleton_vals: fixed to 1 for each type
  - pair_vals:      dict {frozenset({t1,t2}) -> int in 1..6}, monotone
  - exceptional:    set of sorted tuples (type-triples with repetition)
                    these get rank 7; all other triples get max of their pair ranks

Agents 1 and 2 are derived by cyclic rotation of non-singleton types only.
Singleton types (count=1) are fixed across all agents.
"""

from itertools import combinations
from fractions import Fraction


DISTRIBUTIONS = [(2, 2, 2, 2), (3, 2, 2, 1), (3, 3, 1, 1), (4, 2, 1, 1), (5, 1, 1, 1)]
TYPE_LABELS = ['A', 'B', 'C', 'D']


def make_goods(dist):
    sA, sB, sC, sD = dist
    assert sA + sB + sC + sD == 8
    return (['A'] * sA) + (['B'] * sB) + (['C'] * sC) + (['D'] * sD)


def get_non_singleton_indices(dist):
    return [i for i, c in enumerate(dist) if c > 1]


def build_permutations(dist):
    ns = get_non_singleton_indices(dist)
    n_cycle = len(ns)
    perms = []
    for agent in range(3):
        perm = {}
        for idx in range(4):
            if idx in ns:
                pos = ns.index(idx)
                perm[idx] = ns[(pos + agent) % n_cycle]
            else:
                perm[idx] = idx
        perms.append(perm)
    return perms


def apply_perm(goods, perm):
    return [perm[t] for t in goods]


class RankFunction:
    def __init__(self, goods, singleton_vals, pair_vals, exceptional):
        self.goods = goods
        self.singleton_vals = singleton_vals
        self.pair_vals = pair_vals
        self.exceptional = exceptional

    def _type_tuple(self, S):
        return tuple(sorted(self.goods[i] for i in S))

    def __call__(self, S):
        S = frozenset(S)
        n = len(S)
        if n == 0:
            return 0
        if n == 1:
            (i,) = S
            return self.singleton_vals[self.goods[i]]
        if n == 2:
            i, j = sorted(S)
            return self.pair_vals[frozenset([self.goods[i], self.goods[j]])]
        if n == 3:
            tms = self._type_tuple(S)
            if tms in self.exceptional:
                return 7
            return max(self(pair) for pair in combinations(S, 2))
        return max(self(triple) for triple in combinations(S, 3))


class Instance:
    def __init__(self, dist, singleton_vals, pair_vals, exceptional_type_tuples):
        self.dist = dist
        self.singleton_vals = singleton_vals
        self.pair_vals = pair_vals
        self.exceptional_type_tuples = exceptional_type_tuples

        base_goods = make_goods(dist)
        perms = build_permutations(dist)
        self.n_agents = 3
        self.n_goods = 8

        self.rank = []
        for agent in range(3):
            perm = perms[agent]
            permuted_goods = apply_perm(base_goods, perm)
            rotated_exc = set()
            for tup in exceptional_type_tuples:
                rotated_exc.add(tuple(sorted(perm[t] for t in tup)))
            self.rank.append(RankFunction(
                permuted_goods, singleton_vals, pair_vals, rotated_exc
            ))

    def valuation(self, agent, S):
        return self.rank[agent](S)

    def describe(self):
        lines = [f"Distribution: {self.dist}", f"Goods: {make_goods(self.dist)}"]
        lines.append(f"Permutations: {build_permutations(self.dist)}")
        lines.append(f"Singleton values: {self.singleton_vals}")
        lines.append("Pair values:")
        for k, v in sorted(self.pair_vals.items(), key=lambda x: sorted(x[0])):
            lines.append(f"  {set(k)}: {v}")
        lines.append(f"Exceptional triples (agent 0): {sorted(self.exceptional_type_tuples)}")
        goods = make_goods(self.dist)
        all_goods = frozenset(range(8))
        for agent in range(3):
            perm = build_permutations(self.dist)[agent]
            lines.append(f"Agent {agent} (goods: {apply_perm(goods, perm)}):")
            for i in range(8):
                lines.append(f"  v({{{i}}}) = {self.valuation(agent, frozenset([i]))}")
            lines.append(f"  v(all) = {self.valuation(agent, all_goods)}")
        return "\n".join(lines)
