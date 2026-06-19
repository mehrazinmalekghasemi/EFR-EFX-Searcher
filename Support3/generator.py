"""
generator.py
------------
Exhaustively generates all valid Instance objects for each type distribution.

This module enumerates every valid valuation within the modeled search space.
It does not itself perform allocation reasoning; instead it generates the
candidate Instance objects that can be checked later for allocation, fairness,
or other properties.

The search space is exhaustive under the stated constraints:
  - singleton values are fixed to 1 for each type,
  - pair values are chosen for each unordered pair, with each value in 1..6 and
    pair_val(XY) >= max(singleton_val(X), singleton_val(Y)),
  - exceptional triples are chosen from the set of unordered type-triples with
    repetition, with selected triples receiving rank 7.

The pruning is sound: it only excludes valuations that violate the model's
monotonicity constraints, and it still iterates over every remaining valid
combination of pair values and exceptional-triple subsets.

Performance estimate:
  - pair assignments: at most 6^6 = 46,656 combinations,
  - exceptional subsets: 2^10 = 1,024 combinations,
  - instances per distribution: up to 47,748,736,
  - across 5 distributions: about 238,743,680 generated instances.
Pure Python generation over this space is expensive and may take minutes on a
modern machine, depending on downstream Instance construction and processing.

Possible improvements:
  - cache the fixed type-pair and type-triple lists at import time,
  - reduce inner-loop overhead with local aliases and direct zip-based dict
    construction,
  - if Instance can accept a compact representation, avoid building Python sets
    for every exceptional subset,
  - parallelize independent parts of the search when evaluating many
    distributions.
"""

from itertools import product, combinations_with_replacement
from instance import Instance, TYPE_LABELS, DISTRIBUTIONS

TYPE_TRIPLES = [tuple(sorted(t)) for t in combinations_with_replacement(TYPE_LABELS, 3)]
TYPE_PAIRS = [frozenset([a, b]) for a, b in combinations_with_replacement(TYPE_LABELS, 2)]


def all_type_triples():
    """All unordered type-triples with repetition (10 total for 3 types)."""
    return TYPE_TRIPLES


def all_type_pairs():
    """All unordered type-pairs with repetition (6 total for 3 types)."""
    return TYPE_PAIRS


def generate_instances(dist, verbose=False):
    """
    Generator: yields every valid Instance for the given type distribution.

    Yields Instance objects one at a time to keep memory low.
    """
    triples = all_type_triples()        # list of 10 sorted tuples
    pairs = all_type_pairs()            # list of 6 frozensets (with repetition)
    n_triples = len(triples)            # 10
    n_pairs = len(pairs)                # 6

    singleton_vals = {t: 1 for t in TYPE_LABELS}

    total = 0

    # Enumerate pair values with monotonicity:
    # pair_val(XY) >= max(singleton_val(X), singleton_val(Y))
    # pair_val in 1..6
    pair_ranges = []
    pair_key_list = []
    for fs in pairs:
        types_in_pair = list(fs)
        if len(types_in_pair) == 1:
            # Same-type pair: AA, BB, or CC
            lo = singleton_vals[types_in_pair[0]]
        else:
            lo = max(singleton_vals[t] for t in types_in_pair)
        pair_ranges.append(range(lo, 7))  # lo..6
        pair_key_list.append(fs)

    for pv in product(*pair_ranges):
        pair_vals = dict(zip(pair_key_list, pv))

        # Enumerate exceptional triple subsets: 2^10 = 1024
        for exc_mask in range(1 << n_triples):
            exceptional = {triples[bit] for bit in range(n_triples) if exc_mask & (1 << bit)}

            yield Instance(dist, singleton_vals, pair_vals, exceptional)
            total += 1

    if verbose:
        print(f"Generated {total} instances for distribution {dist}")


def generate_all(verbose=False):
    """Yield instances over all 5 distributions."""
    for dist in DISTRIBUTIONS:
        yield from generate_instances(dist, verbose=verbose)
