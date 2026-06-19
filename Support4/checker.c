#include <stdint.h>

/*
 * check_allocations — check EFX/EFR for all canonical allocations.
 *
 * tables:        9 * 256 ints = [v0, v1, v2, mw0, mw1, mw2, sw0, sw1, sw2]
 * count_without: 256 ints
 * allocs:        3 * alloc_count ints (flattened triples)
 * alloc_count:   number of allocations
 *
 * Returns: 0 = neither, 1 = efr_not_efx, 2 = has_efx
 */
int check_allocations(
    const int *tables,
    const int *count_without,
    const int *allocs,
    int alloc_count
) {
    const int *v0  = tables;
    const int *v1  = tables + 256;
    const int *v2  = tables + 512;
    const int *mw0 = tables + 768;
    const int *mw1 = tables + 1024;
    const int *mw2 = tables + 1280;
    const int *sw0 = tables + 1536;
    const int *sw1 = tables + 1792;
    const int *sw2 = tables + 2048;

    int efr_found = 0;

    for (int i = 0; i < alloc_count; i++) {
        int a0 = allocs[i * 3];
        int a1 = allocs[i * 3 + 1];
        int a2 = allocs[i * 3 + 2];

        /* EFX: check first, return immediately */
        if (v0[a0] >= mw0[a1] && v0[a0] >= mw0[a2] &&
            v1[a1] >= mw1[a2] && v1[a1] >= mw1[a0] &&
            v2[a2] >= mw2[a0] && v2[a2] >= mw2[a1]) {
            return 2;
        }

        /* EFR: record but keep searching for EFX */
        if (!efr_found &&
            v0[a0] * count_without[a1] >= sw0[a1] &&
            v0[a0] * count_without[a2] >= sw0[a2] &&
            v1[a1] * count_without[a2] >= sw1[a2] &&
            v1[a1] * count_without[a0] >= sw1[a0] &&
            v2[a2] * count_without[a0] >= sw2[a0] &&
            v2[a2] * count_without[a1] >= sw2[a1]) {
            efr_found = 1;
        }
    }

    return efr_found;
}
