from efx_checker import (
    _allocation_masks,
    is_efx_masks,
    masks_to_allocation,
    removal_summary_tables,
    value_tables,
)
from efr_checker import is_efr_masks


def check_instance(instance, need_allocations=True):
    values = value_tables(instance)
    max_without, sum_without, count_without = removal_summary_tables(values)
    efx_mask = None
    efr_mask = None

    for alloc in _allocation_masks(instance.n_goods, instance.n_agents):
        if efx_mask is None and is_efx_masks(values, alloc, max_without):
            efx_mask = alloc
            if efr_mask is None:
                efr_mask = alloc
        if efr_mask is None and is_efr_masks(values, alloc, sum_without, count_without):
            efr_mask = alloc
        if efx_mask is not None and efr_mask is not None:
            break

    efx = masks_to_allocation(efx_mask) if need_allocations and efx_mask else None
    efr = masks_to_allocation(efr_mask) if need_allocations and efr_mask else None

    return {
        'has_efx': efx_mask is not None,
        'efx_allocation': efx,
        'has_efr': efr_mask is not None,
        'efr_allocation': efr,
    }


def check_instance_for_failures(instance):
    values = value_tables(instance)
    max_without, sum_without, count_without = removal_summary_tables(values)
    efr_mask = None

    for alloc in _allocation_masks(instance.n_goods, instance.n_agents):
        if is_efx_masks(values, alloc, max_without):
            return {
                'has_efx': True,
                'efx_allocation': None,
                'has_efr': True,
                'efr_allocation': None,
            }
        if efr_mask is None and is_efr_masks(values, alloc, sum_without, count_without):
            efr_mask = alloc

    if efr_mask is not None:
        return {
            'has_efx': False,
            'efx_allocation': None,
            'has_efr': True,
            'efr_allocation': masks_to_allocation(efr_mask),
        }

    return {
        'has_efx': False,
        'efx_allocation': None,
        'has_efr': False,
        'efr_allocation': None,
    }


def format_result(instance, result):
    lines = []
    lines.append(f"Params: singletons={instance.singleton_vals}, "
                 f"pairs={instance.pair_vals}, "
                 f"exceptional={instance.exceptional_type_tuples}")
    lines.append(f"  EFX: {'YES' if result['has_efx'] else 'NO'}  "
                 f"EFR: {'YES' if result['has_efr'] else 'NO'}")
    if result['efx_allocation']:
        lines.append(f"  EFX alloc: {result['efx_allocation']}")
    if result['efr_allocation']:
        lines.append(f"  EFR alloc: {result['efr_allocation']}")
    return "\n".join(lines)
