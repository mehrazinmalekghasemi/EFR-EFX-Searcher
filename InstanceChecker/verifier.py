from itertools import product, combinations
import ast

def parse_instance():
    """Parse instance from stdin."""
    import sys
    lines = sys.stdin.read().strip().split('\n')
    
    distribution = None
    singletons = None
    pair_values = None
    exceptional = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('Distribution:'):
            dist_str = line.split(':', 1)[1].strip()
            distribution = eval(dist_str)
        elif line.startswith('Singletons:'):
            sing_str = line.split(':', 1)[1].strip()
            singletons = eval(sing_str)
        elif line.startswith('Pair values:'):
            pair_str = line.split(':', 1)[1].strip()
            pair_values = eval(pair_str)  # Changed from ast.literal_eval
        elif line.startswith('Exceptional triples:'):
            exc_str = line.split(':', 1)[1].strip()
            exceptional = eval(exc_str)  # Changed from ast.literal_eval
    
    if distribution is None or singletons is None or pair_values is None or exceptional is None:
        raise ValueError("Incomplete instance specification")
    
    return distribution, singletons, pair_values, exceptional

def setup_instance(distribution, singletons, pair_values, exceptional):
    """Set up the instance with type assignments."""
    n_goods = sum(distribution)
    n_types = len(distribution)
    
    # Create type labels
    type_labels = []
    for i, count in enumerate(distribution):
        label = chr(ord('A') + i)
        type_labels.extend([label] * count)
    
    # Map goods to types
    good_to_type = {i: type_labels[i] for i in range(n_goods)}
    
    print(f"\n=== INSTANCE SETUP ===")
    print(f"Number of goods: {n_goods}")
    print(f"Number of types: {n_types}")
    print(f"Distribution: {distribution}")
    print(f"Good to type mapping:")
    for g, t in good_to_type.items():
        print(f"  Good {g}: Type {t}")
    
    return n_goods, good_to_type

def rank0(bundle, good_to_type, singletons, pair_values, exceptional):
    """Compute rank for agent 0."""
    if not bundle:
        return 0
    
    if len(bundle) == 1:
        g = list(bundle)[0]
        return singletons[good_to_type[g]]
    
    if len(bundle) == 2:
        types = frozenset(good_to_type[g] for g in bundle)
        return pair_values.get(types, 1)
    
    if len(bundle) == 3:
        types_tuple = tuple(sorted(good_to_type[g] for g in bundle))
        if types_tuple in exceptional:
            return 7
        # Max of pairs
        return max(rank0(frozenset(pair), good_to_type, singletons, pair_values, exceptional) 
                   for pair in combinations(bundle, 2))
    
    # len >= 4: max rank of all 3-subsets
    return max(rank0(frozenset(triple), good_to_type, singletons, pair_values, exceptional) 
               for triple in combinations(bundle, 3))

def sigma(good, n_goods):
    """Cyclic permutation: i → i+2 (mod n_goods)."""
    return (good + 2) % n_goods

def valuation(agent, bundle, n_goods, good_to_type, singletons, pair_values, exceptional):
    """Compute valuation for agent i."""
    if agent == 0:
        return rank0(bundle, good_to_type, singletons, pair_values, exceptional)
    elif agent == 1:
        transformed = frozenset(sigma(g, n_goods) for g in bundle)
        return rank0(transformed, good_to_type, singletons, pair_values, exceptional)
    else:  # agent == 2
        transformed = frozenset(sigma(sigma(g, n_goods), n_goods) for g in bundle)
        return rank0(transformed, good_to_type, singletons, pair_values, exceptional)

def generate_allocations(n_goods):
    """Generate all possible allocations."""
    AGENTS = [0, 1, 2]
    for assignment in product(AGENTS, repeat=n_goods):
        alloc = [set(), set(), set()]
        for good, agent in enumerate(assignment):
            alloc[agent].add(good)
        yield tuple(frozenset(a) for a in alloc)

def check_efx(alloc, n_goods, good_to_type, singletons, pair_values, exceptional):
    """Check if allocation satisfies EFX."""
    AGENTS = [0, 1, 2]
    for i in AGENTS:
        Xi = alloc[i]
        for j in AGENTS:
            if i == j:
                continue
            Xj = alloc[j]
            if not Xj:
                continue
            # Check Xi ≥_i Xj \ {g} for all g in Xj
            for g in Xj:
                Xj_minus_g = Xj - {g}
                vi_Xi = valuation(i, Xi, n_goods, good_to_type, singletons, pair_values, exceptional)
                vi_Xj_minus_g = valuation(i, Xj_minus_g, n_goods, good_to_type, singletons, pair_values, exceptional)
                if vi_Xi < vi_Xj_minus_g:
                    return False
    return True

def check_efr(alloc, n_goods, good_to_type, singletons, pair_values, exceptional):
    """Check if allocation satisfies EFR."""
    AGENTS = [0, 1, 2]
    for i in AGENTS:
        Xi = alloc[i]
        for j in AGENTS:
            if i == j:
                continue
            Xj = alloc[j]
            # Check if there exists g in Xi such that Xi \ {g} ≤_i Xj
            envy_free = False
            if not Xi:
                envy_free = True
            else:
                for g in Xi:
                    Xi_minus_g = Xi - {g}
                    vi_Xi_minus_g = valuation(i, Xi_minus_g, n_goods, good_to_type, singletons, pair_values, exceptional)
                    vi_Xj = valuation(i, Xj, n_goods, good_to_type, singletons, pair_values, exceptional)
                    if vi_Xi_minus_g <= vi_Xj:
                        envy_free = True
                        break
            if not envy_free:
                return False
    return True

def main():
    # Parse instance
    distribution, singletons, pair_values, exceptional = parse_instance()
    
    # Setup instance
    n_goods, good_to_type = setup_instance(distribution, singletons, pair_values, exceptional)
    
    print(f"\nSingletons: {singletons}")
    print(f"Pair values: {pair_values}")
    print(f"Exceptional triples: {exceptional}")
    
    # Test all allocations
    print(f"\n=== TESTING ALL ALLOCATIONS ===")
    print(f"Total allocations to check: {3**n_goods}")
    
    efx_count = 0
    efr_count = 0
    total = 0
    
    efx_allocations = []
    efr_allocations = []
    
    for alloc in generate_allocations(n_goods):
        total += 1
        is_efx = check_efx(alloc, n_goods, good_to_type, singletons, pair_values, exceptional)
        is_efr = check_efr(alloc, n_goods, good_to_type, singletons, pair_values, exceptional)
        
        if is_efx:
            efx_count += 1
            efx_allocations.append(alloc)
        if is_efr:
            efr_count += 1
            efr_allocations.append(alloc)
        
        if total % 1000 == 0:
            print(f"  Checked {total} allocations...")
    
    print(f"\n=== RESULTS ===")
    print(f"Total allocations: {total}")
    print(f"EFX allocations: {efx_count}")
    print(f"EFR allocations: {efr_count}")
    
    if efx_count == 0 and efr_count == 0:
        print("\n✓ CONFIRMED: Neither EFX nor EFR allocation exists for this instance.")
    else:
        print(f"\n✗ Found {efx_count} EFX and/or {efr_count} EFR allocations.")
        
        if efx_allocations and efx_count <= 10:
            print("\nEFX allocations:")
            for i, alloc in enumerate(efx_allocations, 1):
                print(f"  {i}. Agent0: {set(alloc[0])}, Agent1: {set(alloc[1])}, Agent2: {set(alloc[2])}")
        
        if efr_allocations and efr_count <= 10:
            print("\nEFR allocations:")
            for i, alloc in enumerate(efr_allocations, 1):
                print(f"  {i}. Agent0: {set(alloc[0])}, Agent1: {set(alloc[1])}, Agent2: {set(alloc[2])}")

if __name__ == "__main__":
    main()
