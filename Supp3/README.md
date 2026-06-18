Run the full fast search and split no-EFX instances by whether EFR exists:

python3 -u main.py --all --fail-only --split-results --output failures.txt --workers 10 --chunksize 1000

This automatically uses the compact batched fast path.

This writes:

- failures_efx_not_efr.txt
- failures_efr_not_efx.txt
- failures_neither.txt

The EFX-not-EFR file should stay empty because every EFX allocation is also EFR.

Full `--all` search size:

- 238,878,720 generated instances
- 1,400 candidate allocations per instance
- 334,430,208,000 worst-case allocation checks before pruning

Per distribution:

- 47,775,744 generated instances
- 66,886,041,600 worst-case allocation checks

## Run instructions

python main.py --all --fail-only --split-results --output failures.txt --no-resume --workers 0
--workers 0 = all CPU cores.



Done. Checked 191102976 instances, wrote 0 to failures.txt.
Total instances expected: 191102976
Total allocation checks worst-case: 267544166400
  efx_not_efr: 0 -> failures_efx_not_efr.txt
  efr_not_efx: 0 -> failures_efr_not_efx.txt
  neither: 0 -> failures_neither.txt