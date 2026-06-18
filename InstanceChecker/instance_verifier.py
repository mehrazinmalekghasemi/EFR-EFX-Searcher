import sys
import ast
import re
from itertools import product
import os

# ─── Parse instances from failures_neither.txt ────────────────────────────────

def parse_instances(filepath):
    """
    Parse Params lines from the log file.
    Each record is 2 lines:
      Params: singletons=..., pairs=..., exceptional=...
      EFX: NO  EFR: NO
    Returns list of (singletons, pairs, exceptional) dicts.
    """
    instances = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.startswith("Params:"):
                continue
            # Strip the "Params: " prefix
            body = line[len("Params:"):].strip()
            try:
                singletons, pairs, exceptional = _parse_params(body)
                instances.append((singletons, pairs, exceptional))
            except Exception as e:
                print(f"Warning: failed to parse line: {line[:80]}... => {e}", flush=True)
    return instances

def _parse_params(body):
    """
    Parse 'singletons={...}, pairs={...}, exceptional={...}' from a single string.
    """
    def extract_field(text, key):
        start = text.find(f'{key}=')
        if start == -1:
            raise ValueError(f"Key '{key}' not found")
        start += len(f'{key}=')
        val, _ = _extract_balanced(text, start)
        return val

    def _extract_balanced(text, start):
        """Extract a balanced {}-delimited or plain token from text[start:]."""
        c = text[start]
        if c == '{':
            depth = 0
            for i, ch in enumerate(text[start:]):
                if ch == '{': depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:start+i+1], start+i+1
        else:
            # No brace: read until comma or end
            end = text.find(',', start)
            if end == -1:
                end = len(text)
            return text[start:end], end
        raise ValueError("Unbalanced braces")

    singletons_str = extract_field(body, 'singletons')
    pairs_str = extract_field(body, 'pairs')
    exceptional_str = extract_field(body, 'exceptional')

    singletons = ast.literal_eval(singletons_str)
    pairs = eval(pairs_str, {"frozenset": frozenset})
    exceptional = eval(exceptional_str, {"frozenset": frozenset})

    return singletons, pairs, exceptional

# ─── Valuation ────────────────────────────────────────────────────────────────

def singletons_to_type_counts(singletons):
    """Convert {'A': nA, 'B': nB, 'C': nC} to (nA, nB, nC)."""
    return (singletons.get('A', 0), singletons.get('B', 0), singletons.get('C', 0))

def get_type(good, type_counts):
    nA, nB, nC = type_counts
    if good < nA: return 'A'
    elif good < nA + nB: return 'B'
    else: return 'C'

def rank0(bundle, type_counts, pairs, exceptional):
    bundle = tuple(bundle)
    if len(bundle) == 0:
        return 0
    if len(bundle) == 1:
        return 1
    if len(bundle) == 2:
        types = tuple(sorted(get_type(g, type_counts) for g in bundle))
        key = frozenset(types)
        return pairs.get(key, 1)
    if len(bundle) == 3:
        types = tuple(sorted(get_type(g, type_counts) for g in bundle))
        type_triple = tuple(sorted(types))
        if type_triple in exceptional:
            return 7
        # max over 2-subsets
        best = 0
        bl = list(bundle)
        for i in range(3):
            for j in range(i+1, 3):
                sub = (bl[i], bl[j])
                best = max(best, rank0(sub, type_counts, pairs, exceptional))
        return best
    # |S| >= 4: max over all 3-subsets
    best = 0
    bl = list(bundle)
    n = len(bl)
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                best = max(best, rank0((bl[i], bl[j], bl[k]), type_counts, pairs, exceptional))
    return best

def sigma_apply(good, type_counts, power=1):
    nA, nB, nC = type_counts
    blocks = [list(range(nA)), list(range(nA, nA+nB)), list(range(nA+nB, nA+nB+nC))]
    for block in blocks:
        if good in block:
            idx = block.index(good)
            new_idx = (idx + power) % len(block)
            return block[new_idx]
    return good

def valuation(agent, bundle, type_counts, pairs, exceptional):
    rotated = tuple(sigma_apply(g, type_counts, agent) for g in bundle)
    return rank0(rotated, type_counts, pairs, exceptional)

# ─── EFX / EFR ────────────────────────────────────────────────────────────────

def check_efx(allocation, type_counts, pairs, exceptional):
    n = len(allocation)
    for i in range(n):
        vi = valuation(i, allocation[i], type_counts, pairs, exceptional)
        for j in range(n):
            if i == j: continue
            bj = list(allocation[j])
            for g in bj:
                reduced = tuple(x for x in bj if x != g)
                if valuation(i, reduced, type_counts, pairs, exceptional) > vi:
                    return False
    return True

def check_efr(allocation, type_counts, pairs, exceptional):
    n = len(allocation)
    for i in range(n):
        for j in range(n):
            if i == j: continue
            bj = list(allocation[j])
            vj = valuation(i, tuple(bj), type_counts, pairs, exceptional)
            vi = valuation(i, allocation[i], type_counts, pairs, exceptional)
            if vj <= vi:
                continue
            found = any(
                valuation(i, allocation[i] + (g,), type_counts, pairs, exceptional) >= vj
                for g in bj
            )
            if not found:
                return False
    return True

# ─── Allocation Enumeration ───────────────────────────────────────────────────

def generate_allocations(goods, n_agents=3):
    goods = list(goods)
    n = len(goods)

    def helper(idx, bundles):
        if idx == n:
            yield tuple(tuple(b) for b in bundles)
            return
        g = goods[idx]
        for a in range(n_agents):
            bundles[a].append(g)
            yield from helper(idx + 1, bundles)
            bundles[a].pop()

    yield from helper(0, [[] for _ in range(n_agents)])

# ─── Test one instance ────────────────────────────────────────────────────────

def test_instance(type_counts, pairs, exceptional, max_allocs=None):
    goods = tuple(range(sum(type_counts)))
    found_efx = None
    found_efr = None
    count = 0

    for alloc in generate_allocations(goods):
        count += 1
        if max_allocs and count > max_allocs:
            break
        if found_efx is None and check_efx(alloc, type_counts, pairs, exceptional):
            found_efx = alloc
        if found_efr is None and check_efr(alloc, type_counts, pairs, exceptional):
            found_efr = alloc
        if found_efx and found_efr:
            break

    return found_efx, found_efr, count

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failures_neither.txt")
    # Remove limit to test all instances
    LIMIT = None

    print(f"Reading instances from {filepath} ...", flush=True)
    instances = parse_instances(filepath)
    print(f"  Parsed {len(instances)} instances.", flush=True)

    if LIMIT:
        instances = instances[:LIMIT]
        print(f"  Testing first {LIMIT} instances.", flush=True)

    print("=" * 60, flush=True)

    confirmed_neither = []
    progress_interval = 5000

    for idx, (singletons, pairs, exceptional) in enumerate(instances):
        # Convert singletons dict to type_counts tuple
        type_counts = singletons_to_type_counts(singletons)
        
        if (idx + 1) % progress_interval == 0:
            print(f"\n[{idx+1}/{len(instances)}] Progress checkpoint", flush=True)

        efx_alloc, efr_alloc, count = test_instance(type_counts, pairs, exceptional)

        has_efx = efx_alloc is not None
        has_efr = efr_alloc is not None

        if not has_efx and not has_efr:
            confirmed_neither.append((singletons, pairs, exceptional))

    print("\n" + "=" * 60, flush=True)
    print(f"Confirmed NEITHER: {len(confirmed_neither)}/{len(instances)}", flush=True)
    for s, p, e in confirmed_neither[:5]:
        print(f"  singletons={s}, pairs={dict(p)}, exceptional={e}", flush=True)

if __name__ == "__main__":
    main()
