"""
instance.py
-----------
Represents a single 3-agent, 8-good instance with rank-based valuations.

Goods are FIXED -- all agents see the same physical goods.
Agents differ only in how they VALUE goods, via a type-permutation sigma.

sigma only permutes types that appear >= 2 times in the distribution.
Types with exactly 1 instance are fixed by sigma.

Type distributions supported (sizes of groups A, B, C):
  (3,3,2), (4,2,2) -- all types >= 2, sigma is a 3-cycle A->B->C->A
  (4,3,1), (5,2,1) -- type C has 1 instance, sigma is a 2-cycle A<->B

Agent 0's valuation is defined by:
  - singleton_vals: dict {type_label -> int in 1..6}
  - pair_vals:      dict {frozenset({t1,t2}) -> int in 1..6}, monotone
  - exceptional:    frozenset of frozensets of type-labels (triples, with repetition)
                    these get rank 7; all other triples get max of their pair ranks

Agents 1 and 2 are derived by applying sigma^k to type labels.
"""

from itertools import combinations
from fractions import Fraction


# ---------------------------------------------------------------------------
# Type distribution helpers
# ---------------------------------------------------------------------------

DISTRIBUTIONS = [(3, 3, 2), (4, 2, 2), (4, 3, 1), (5, 2, 1)]
TYPE_LABELS = ['A', 'B', 'C']


def make_goods(dist):
    """
    Given dist = (sA, sB, sC), return a list of 8 goods each labeled by type.
    goods[i] = type label ('A', 'B', or 'C')
    Goods are ordered: all A's first, then B's, then C's.
    """
    sA, sB, sC = dist
    assert sA + sB + sC == 8
    return (['A'] * sA) + (['B'] * sB) + (['C'] * sC)


def get_cycle_types(dist):
    """Return type indices that are in the permutation cycle (types with count >= 2)."""
    return tuple(i for i, count in enumerate(dist) if count >= 2)


def type_rotation(dist, type_id, k):
    """Apply k steps of sigma to type_id.
    sigma cyclically permutes types with count >= 2.
    Types with count = 1 are fixed by sigma."""
    cycle = get_cycle_types(dist)
    n = len(cycle)
    if n == 3:
        return (type_id + k) % 3
    elif n == 2:
        if type_id not in cycle:
            return type_id
        pos = cycle.index(type_id)
        return cycle[(pos + k) % 2]
    return type_id


def cyclic_rotate(type_label, k):
    """Rotate type label A->B->C->A by k steps."""
    idx = TYPE_LABELS.index(type_label)
    return TYPE_LABELS[(idx + k) % 3]


def rotate_goods(goods, k, dist=None):
    """Apply k steps of sigma to a list of type labels."""
    if dist is not None:
        return [TYPE_LABELS[type_rotation(dist, TYPE_LABELS.index(t), k)] for t in goods]
    return [cyclic_rotate(t, k) for t in goods]


# ---------------------------------------------------------------------------
# Rank function for a single agent
# ---------------------------------------------------------------------------

class RankFunction:
    """
    Rank function r: 2^{0..7} -> {0,1,...,7}
    Defined by agent 0's parameters; other agents are derived by rotating goods.

    Parameters (all from agent 0's perspective):
      goods          : list of 8 type labels as seen by THIS agent
                       (for agent k, this is rotate_goods(base_goods, k))
      singleton_vals : {type -> int}   rank of a single good of that type
      pair_vals      : {frozenset({t1,t2}) -> int}  rank of any pair of those types
      exceptional    : set of frozenset of type-labels (size-3 multisets)
                       triples whose type-multiset is in this set get rank 7
    """

    def __init__(self, goods, singleton_vals, pair_vals, exceptional):
        self.goods = goods           # goods[i] = type label as seen by this agent
        self.singleton_vals = singleton_vals
        self.pair_vals = pair_vals
        self.exceptional = exceptional   # set of frozenset (type multisets of size 3)

    def _type_multiset(self, S):
        """Return sorted tuple of type labels for goods in S."""
        return tuple(sorted(self.goods[i] for i in S))

    def __call__(self, S):
        """Compute r(S) for a set S (given as a frozenset or iterable of good indices)."""
        S = frozenset(S)
        n = len(S)

        if n == 0:
            return 0
        if n == 1:
            (i,) = S
            return self.singleton_vals[self.goods[i]]
        if n == 2:
            i, j = sorted(S)
            key = frozenset([self.goods[i], self.goods[j]])
            return self.pair_vals[key]
        if n == 3:
            tms = frozenset(self._type_multiset(S))
            # Check exceptional: compare as sorted tuples stored as frozensets
            tms_tuple = tuple(sorted(self.goods[i] for i in S))
            if tms_tuple in self.exceptional:
                return 7
            # Otherwise max of pair ranks
            return max(self(pair) for pair in combinations(S, 2))
        # n >= 4: max over all triples
        return max(self(triple) for triple in combinations(S, 3))


# ---------------------------------------------------------------------------
# Full instance: 3 agents derived cyclically from agent 0
# ---------------------------------------------------------------------------

class Instance:
    """
    A full 3-agent, 8-good instance.

    Goods are FIXED -- all agents see the same physical goods.
    Agents differ only in how they VALUE goods, via type-permutation sigma.

    sigma cyclically permutes types with count >= 2.
    Types with count = 1 are fixed by sigma.

    Agent k's type labels are sigma^k applied to the base types.
    Agent k's exceptional triples are sigma^{-k} applied to agent 0's.
    """

    def __init__(self, dist, singleton_vals, pair_vals, exceptional_type_tuples):
        """
        dist                  : (sA, sB, sC) tuple
        singleton_vals        : {type -> int in 1..6}
        pair_vals             : {frozenset({t1,t2}) -> int in 1..6}
        exceptional_type_tuples : set of sorted tuples of type labels
                                  e.g. {('A','A','B'), ('A','B','C')}
                                  these are agent 0's exceptional triple types
        """
        self.dist = dist
        self.singleton_vals = singleton_vals
        self.pair_vals = pair_vals
        self.exceptional_type_tuples = exceptional_type_tuples  # for agent 0

        base_goods = make_goods(dist)  # type label for each good index

        self.rank = []
        for agent in range(3):
            rotated_goods = rotate_goods(base_goods, agent, dist)

            # Rotate agent 0's exceptional triples by -agent steps.
            # Agent k's exceptional triples: apply sigma^{-k} to each type.
            rotated_exceptional = set()
            for tup in exceptional_type_tuples:
                rotated_tup = tuple(sorted(
                    TYPE_LABELS[type_rotation(dist, TYPE_LABELS.index(t), -agent)]
                    for t in tup
                ))
                rotated_exceptional.add(rotated_tup)

            self.rank.append(RankFunction(
                rotated_goods, singleton_vals, pair_vals, rotated_exceptional
            ))

        self.n_agents = 3
        self.n_goods = 8

    def valuation(self, agent, S):
        """v_i(S) = r_i(S)."""
        return self.rank[agent](S)

    def describe(self):
        """Return a human-readable string describing the instance."""
        lines = []
        cycle = get_cycle_types(self.dist)
        cycle_labels = [TYPE_LABELS[i] for i in cycle]
        lines.append(f"Distribution: {self.dist}")
        lines.append(f"Goods: {make_goods(self.dist)}")
        if len(cycle) == 3:
            lines.append(f"Sigma: {cycle_labels[0]}->{cycle_labels[1]}->{cycle_labels[2]}->{cycle_labels[0]} (3-cycle)")
        elif len(cycle) == 2:
            fixed = [TYPE_LABELS[i] for i in range(3) if i not in cycle]
            lines.append(f"Sigma: {cycle_labels[0]}<->{cycle_labels[1]} (2-cycle), {fixed[0]} fixed")
        lines.append(f"Singleton values: {self.singleton_vals}")
        lines.append(f"Pair values:")
        for k, v in sorted(self.pair_vals.items(), key=lambda x: sorted(x[0])):
            lines.append(f"  {set(k)}: {v}")
        lines.append(f"Exceptional triple types (agent 0): {sorted(self.exceptional_type_tuples)}")
        lines.append("")
        goods = make_goods(self.dist)
        all_goods = frozenset(range(8))
        for agent in range(3):
            lines.append(f"Agent {agent} (types: {rotate_goods(goods, agent, self.dist)}):")
            for i in range(8):
                lines.append(f"  v({i}) = {self.valuation(agent, frozenset([i]))}")
            lines.append(f"  v(all) = {self.valuation(agent, all_goods)}")
        return "\n".join(lines)
