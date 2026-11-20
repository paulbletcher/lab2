# Cached analysis capacity and runtime report

## Target

Process the expected next-year workload of 500 film records with the existing
analysis pipeline. The brief requires measured performance but supplies no
numeric runtime deadline; this check establishes capacity and observed runtime,
not a guaranteed meeting-time service level.

## Method

- **Hardware / container spec:** Native Windows 10 Pro, version 10.0.19045, 64-bit; Intel Core i5-6300U at 2.40 GHz, two cores/four logical processors; 8,454,778,880 bytes RAM (7.87 GiB). No container was used.
- **Environment:** Project virtual environment, Python 3.14.3 (64-bit); dependencies pinned in `requirements.txt`. Measurements taken on 20 November 2026 UTC.
- **What was timed:** Each helper starts `perf_counter()` immediately before launching `run_analysis.py` and stops when that child process exits. Includes Python startup, cache reads, transformation, analysis, integrity checks, and writing nine CSVs. Excludes live API acquisition, snapshot preparation, and synthetic dataset setup.
- **Runs, warm or cold:** Three sequential fresh Python processes per dataset, each reading an existing SQLite cache. No explicit warm-up or disk-cache flush; operating-system cache state and other laptop activity were not controlled. These are cached-data runs, not cold-start guarantees.
- **Isolation:** Scripts and existing cache/audits/validated IDs were copied into a temporary verification project. Its generated CSVs stayed there. All nine current-cache outputs matched the real analysis outputs byte-for-byte.
- **Synthetic input:** Repeats complete details-and-credits records whose fetch audit marks both responses successful. Each copy receives a unique test ID; exactly 500 IDs are analyzed. It tests row volume rather than 500 independently acquired films or live fetching.
- **Reported figures:** Median, maximum, and an interpolated empirical p95 from the three timings printed by each helper. For three sorted times, p95 is the second time plus 90% of the distance to the maximum. Three observations give a weak estimate of tail latency; it is descriptive, not a reliable production p95.

Run from the repository root using the project virtual environment:

```powershell
.\.venv\Scripts\python.exe benchmarks/benchmark_analysis.py
.\.venv\Scripts\python.exe benchmarks/benchmark_500.py
```

The first command normally refreshes `data/analysis/`; run it in a temporary
copy with the same local data if existing outputs must remain untouched. The
500-film command manages its own temporary project and removes it on completion.

## Results

| Scenario | Runs | Median | p95 | Worst | Target met? |
|---|---:|---:|---:|---:|---|
| Current cache: 112 of 117 validated IDs | 3 | 2.403 s | 2.635 s | 2.661 s | Baseline reproduced; nine CSVs each run |
| Synthetic cache: 500 of 500 IDs | 3 | 3.220 s | 3.633 s | 3.679 s | Yes: 500 records and nine CSVs each run |

| Dataset | Run 1 | Run 2 | Run 3 |
|---|---:|---:|---:|
| Current cache | 2.661 s | 2.403 s | 2.232 s |
| Synthetic 500 | 3.220 s | 3.075 s | 3.679 s |

## Before / after

| Query / stage | Before | After | Change |
|---|---|---|---|
| Cached analysis | No controlled pre-change measurement for a performance optimization | Capacity verification above | No speed-up claimed; this submission work changes documentation and packaging, not analysis logic |

Earlier README timings came from a different run. They are replaced by this
verification batch; differences cannot be attributed to an optimization because
the folder, operating-system caches, and background activity were not controlled.

## Caveats

The synthetic data repeats existing content, so genre, cast, collection, and
missing-value diversity do not increase with record count. Live fetching depends
on network and server behavior and is excluded. The five unavailable real IDs
remain audit failures; analysis still uses 112 acquired films. This three-run
sample on one laptop is not a broad benchmark or a guarantee of future runtime.
