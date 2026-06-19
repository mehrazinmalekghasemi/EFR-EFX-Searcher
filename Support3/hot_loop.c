/*
 * hot_loop.c — Summary tables + allocation check for EFX/EFR
 *
 * Compile: gcc -O3 -shared -fPIC -o hot_loop.so hot_loop.c
 *      or: cc -O3 -shared -fPIC -o hot_loop.so hot_loop.c
 *
 * Does exactly the same checks as the Python code, just faster.
 */

static void compute_summary(
    const int *values,
    const int *reduced_masks,
    const int *reduced_counts,
    int *max_without,
    int *sum_without
) {
    for (int mask = 0; mask < 256; mask++) {
        int cnt = reduced_counts[mask];
        if (cnt == 0) continue;
        int base = mask * 8;
        int mx = values[reduced_masks[base]];
        int sm = mx;
        for (int i = 1; i < cnt; i++) {
            int val = values[reduced_masks[base + i]];
            sm += val;
            if (val > mx) mx = val;
        }
        max_without[mask] = mx;
        sum_without[mask] = sm;
    }
}

int check_allocations(
    const int *v0, const int *v1, const int *v2,
    const int *reduced_masks,
    const int *reduced_counts,
    const int *count_without,
    const int *allocs,
    int n_allocs,
    int *efr_idx
) {
    int max0[256], sum0[256];
    int max1[256], sum1[256];
    int max2[256], sum2[256];

    compute_summary(v0, reduced_masks, reduced_counts, max0, sum0);
    compute_summary(v1, reduced_masks, reduced_counts, max1, sum1);
    compute_summary(v2, reduced_masks, reduced_counts, max2, sum2);

    *efr_idx = -1;
    for (int i = 0; i < n_allocs; i++) {
        int a0 = allocs[i * 3];
        int a1 = allocs[i * 3 + 1];
        int a2 = allocs[i * 3 + 2];

        if (v0[a0] >= max0[a1] && v0[a0] >= max0[a2] &&
            v1[a1] >= max1[a2] && v1[a1] >= max1[a0] &&
            v2[a2] >= max2[a0] && v2[a2] >= max2[a1]) {
            return 1;
        }

        if (*efr_idx < 0) {
            int c0 = count_without[a0];
            int c1 = count_without[a1];
            int c2 = count_without[a2];
            if (v0[a0] * c1 >= sum0[a1] && v0[a0] * c2 >= sum0[a2] &&
                v1[a1] * c2 >= sum1[a2] && v1[a1] * c0 >= sum1[a0] &&
                v2[a2] * c0 >= sum2[a0] && v2[a2] * c1 >= sum2[a1]) {
                *efr_idx = i;
            }
        }
    }
    return 0;
}
