"""
instance.py
-----------
3-agent, 8-good instance with 5 types (A, B, C, D, E) and rank-based valuations.

Type distribution: (2, 2, 2, 1, 1)

Paper's sigma = (0 1 2)(3 4 5) on goods:
  Agent k sees good i as the type of good sigma^k(i).

Agent 0's valuation is defined by:
  - singleton_vals: {type -> int in 1..6}
  - pair_vals:      {frozenset({t1,t2}) -> int in 1..6}, monotone
  - exceptional:    set of sorted tuples (type-triples for agent 0)
                    these get rank 7; all other triples get max of their pair ranks
"""

from itertools import combinations


DISTRIBUTIONS = [(2, 2, 2, 1, 1)]
TYPE_LABELS = ['A', 'B', 'C', 'D', 'E']
N_TYPES = 5

GOODS_SIGMA = [1, 2, 0, 4, 5, 3, 6, 7]
GOODS_SIGMA2 = [2, 0, 1, 5, 3, 4, 6, 7]


def make_goods(dist):
    sA, sB, sC, sD, sE = dist
    assert sA + sB + sC + sD + sE == 8
    return ['A'] * sA + ['B'] * sB + ['C'] * sC + ['D'] * sD + ['E'] * sE


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
        base_type_idx = [TYPE_LABELS.index(t) for t in base_goods]
        sigmas = [list(range(8)), GOODS_SIGMA, GOODS_SIGMA2]

        self.n_agents = 3
        self.n_goods = 8
        self.rank = []
        for agent in range(3):
            sig = sigmas[agent]
            agent_goods = [base_goods[sig[i]] for i in range(8)]

            if agent == 0:
                rotated_exc = set(exceptional_type_tuples)
            else:
                rotated_exc = set()
                for tup in exceptional_type_tuples:
                    exc_goods = sorted(
                        j for j in range(8) if base_goods[j] in tup
                    )
                    mapped_goods = [sig[j] for j in exc_goods]
                    mapped_types = tuple(sorted(base_goods[g] for g in mapped_goods))
                    rotated_exc.add(mapped_types)

            self.rank.append(RankFunction(
                agent_goods, singleton_vals, pair_vals, rotated_exc
            ))

    def valuation(self, agent, S):
        return self.rank[agent](S)

    def describe(self):
        base_goods = make_goods(self.dist)
        lines = [f"Distribution: {self.dist}", f"Goods: {base_goods}"]
        lines.append(f"Sigma: (0 1 2)(3 4 5) on goods")
        lines.append(f"Singleton values: {self.singleton_vals}")
        lines.append("Pair values:")
        for k, v in sorted(self.pair_vals.items(), key=lambda x: sorted(x[0])):
            lines.append(f"  {set(k)}: {v}")
        lines.append(f"Exceptional triples (agent 0): {sorted(self.exceptional_type_tuples)}")
        all_goods = frozenset(range(8))
        sigmas = [list(range(8)), GOODS_SIGMA, GOODS_SIGMA2]
        for agent in range(3):
            sig = sigmas[agent]
            ag = [base_goods[sig[i]] for i in range(8)]
            lines.append(f"Agent {agent} (goods seen as: {ag}):")
            for i in range(8):
                lines.append(f"  v({{{i}}}) = {self.valuation(agent, frozenset([i]))}")
            lines.append(f"  v(all) = {self.valuation(agent, all_goods)}")
        return "\n".join(lines)
