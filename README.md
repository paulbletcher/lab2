# Lab 2: TMDb movie pipeline

Validate movie IDs, acquire movie details and credits from TMDb, cache the raw
responses in SQLite, and compare franchise and standalone films using revenue
relative to budget. The analysis also summarizes first-billed actors and directors.

## Submission deliverables

- [Client memo](client_memo.md): recommendation, shortlists, both release windows, talent, deal note, and limits.
- [Data findings](data_findings.md): reconciliation, ranked risks, measured scenarios, and unresolved evidence.
- [Five architecture decision records](decisions/): ADR-001 through ADR-005 in the shared format.
- [Improvement beyond the brief](improvement.md): quarterly shortlist report and passing synthetic test.
- [Measurement report](measurement_report.md): hardware, method, timings, and the 500-record capacity check.
- [Profiling notebook](data_profile/tmdb_data_profile.ipynb): executed checks and supporting analysis.

The original [Word memo](docs/streamvault_licensing_memo.docx) and
[detailed diagnosis](docs/data_diagnosis.md) are retained as supporting documents.
The root-level Markdown files use the shared submission templates.

## Setup

Run these commands in PowerShell from the repository root. The pipeline has been
tested with Python 3.14.3 (pinned in `.python-version`). Each clone should use its own virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
New-Item -ItemType Directory -Force data/input
```

Edit the local `.env` and replace the placeholder for `TMDB_API_KEY` with your own
TMDb API key. Keep an existing `.env` when repeating setup.

Place the original input CSV at `data/input/id_list.csv`. It must have a `tmdb_id`
column. The input, credentials, cache, and generated CSVs are local files excluded
from Git, so a fresh clone needs its own `.env` and input CSV.

The direct dependencies are pinned in `requirements.txt`:

- `pandas==3.1.1`
- `requests==2.34.2`
- `python-dotenv==1.2.4`

All three pins installed successfully from the official PyPI index in a clean
Python 3.14.3 virtual environment on 20 November 2026 UTC; `pip check` found no
broken requirements. The versions were retained after verification.

## Run the pipeline

The canonical complete workflow is the runner, from the repository root:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py
```

It runs Validate, Extract, then Analyze and stops if a stage fails. To debug or
resume a prepared stage, these individual commands call the same entry points,
in the same prerequisite order:

```powershell
.\.venv\Scripts\python.exe pipeline/validate.py
.\.venv\Scripts\python.exe pipeline/extract.py
.\.venv\Scripts\python.exe run_analysis.py
```

1. **Validate:** trims IDs, accepts positive integers, normalizes leading zeros,
   and removes duplicates. Writes `data/validated/id_audit.csv` and
   `data/validated/validated_ids.csv`.
2. **Extract:** requests movie details and credits for each validated ID. Stores
   successful responses in `data/cache/tmdb.sqlite` and writes endpoint outcomes
   to `data/cache/fetch_audit.csv`. Successful cached responses are reused on
   later runs without an HTTP request. One HTTP session is reused for the run.
   Uncached GETs retry connection errors, timeouts, and HTTP 429, 500, 502, 503,
   and 504 up to three times after the first attempt (four attempts total).
   Retries honor a valid `Retry-After` header in seconds or as an HTTP date;
   otherwise they wait 1, 2, then 4 seconds.
   HTTP 401 or 403 stops the batch immediately; HTTP 429 stops it after the retry
   limit. HTTP 404 and other endpoint failures, including exhausted connection,
   timeout, or server-error retries, are recorded in the audit and acquisition
   continues. Inspect the audit even when the script exits successfully.
   Successful responses are committed to SQLite as they arrive, so a rerun
   reuses them even if a later request stopped the batch. Failed responses are
   not cached and are requested again on a later run. The fetch audit is replaced
   atomically after each endpoint, including a fatal stop. It contains every
   validated ID: saved responses remain `ok`, the stopping endpoint records its
   failure, and uncached requests not reached are marked `not attempted`.
   Importing `pipeline.extract` or `pipeline.validate` performs no acquisition
   or validation; their commands start execution through `main()`.
3. **Analyze:** `python run_analysis.py` reads the validated IDs and cached
   responses, transforms them, computes the analysis, checks integrity, and
   calls the loader to write nine CSV tables under `data/analysis/`.

`run_pipeline.py` defines the sequence once in `STAGES`, using the importable
stage modules. Each child process calls that module's `main()` with a timeout:
60 seconds for validation, 3,600 for acquisition, and 120 for analysis. It logs
stage starts/completions, reports the failing or timed-out stage, and stops before
later stages. Captured error output redacts the configured API key and `api_key`
query values. Saved acquisition responses survive a failure and are reused.
Validation must create the unique ID list before acquisition; analysis requires
the cache and fetch audit. The stages have these responsibilities:

| Stage     | Location and responsibility                                                                                                                                                                        |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Validate  | `pipeline/validate.py`: normalize and validate input IDs, remove duplicates, reconcile input counts, and write input audits                                                                        |
| Extract   | `pipeline/extract.py`: TMDb acquisition, response ID validation, SQLite cache, and fetch audit                                                                                                     |
| Transform | `pipeline/transform.py`: flatten details, lead actors, and directors; calculate usable ratios                                                                                                      |
| Analysis  | `pipeline/analysis.py`: comparisons, summaries, and rankings                                                                                                                                       |
| Check     | `pipeline/checks.py`: unique movie IDs, detail row counts, one-to-one actor and many-to-one director joins, unique movie-director pairs, audit/cache coverage, and comparison count reconciliation |
| Load      | `pipeline/load.py`: write final analysis CSVs after checks pass                                                                                                                                    |

`run_analysis.py` orchestrates transformation, analysis, checks, and loading without
making API requests. It requires the fetch audit alongside the cache. Acquisition
failures remain in `data/cache/fetch_audit.csv` and are printed during analysis;
they are not integrity failures when the audit agrees with cache coverage. In
particular, the five known IDs returning HTTP 404 do not block a valid run.
An integrity failure stops analysis before the loader writes any results.

## Improvement beyond the brief

The quarterly shortlist change report saves Adjoa from comparing four CSVs by
hand each quarter. It shows which films and franchises entered, dropped out,
moved in the rankings, or had a change in their revenue-to-budget ratio (reported
to two decimal places). It compares the same release window across runs:
all years against all years, and releases from 2000 onward against the same
window. Kwame can use the report to revisit his negotiation priorities. Adjoa
can check the acquisition audit (`data/cache/fetch_audit.csv`) or candidate list
(`data/input/id_list.csv`) to investigate why a title moved; the report itself
does not establish the cause.

Run these commands from the repository root using the project's Python
environment. If the virtual environment is not activated, replace `python` with
`.\.venv\Scripts\python.exe`. After the current analysis, save the baseline
before a later run overwrites the analysis CSVs:

```powershell
python shortlist_changes.py snapshot data/snapshots/baseline
```

After running the full pipeline for a later quarter, save its analysis results:

```powershell
python shortlist_changes.py snapshot data/snapshots/next_run
```

Then compare the two snapshots and write the Markdown report:

```powershell
python shortlist_changes.py compare data/snapshots/baseline data/snapshots/next_run --output shortlist_changes.md
```

`snapshot` reads the four ranked franchise and standalone CSVs from
`data/analysis/` by default; `--source` selects another analysis folder. It copies
them into a new snapshot folder. `compare` requires `--output`. Both commands
refuse to overwrite an existing destination, so use new quarter-specific folder
and report names for subsequent comparisons. If `shortlist_changes.md` already
exists, choose a new output filename to preserve it. Snapshots under `data/` are
excluded from Git. These commands use only Python's standard library and leave
the analysis CSVs and SQLite cache unchanged.

## Analysis outputs

| CSV                           | Contents                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------- |
| `comparison.csv`              | Franchise and standalone comparison for all years and releases from 2000 onward |
| `franchises_all_years.csv`    | Top three collections with at least three usable film ratios                    |
| `franchises_2000_onward.csv`  | Same shortlist for releases from 2000 onward                                    |
| `standalones_all_years.csv`   | Top five standalone films with usable ratios                                    |
| `standalones_2000_onward.csv` | Same shortlist for releases from 2000 onward                                    |
| `actors_min_2_films.csv`      | First-billed actors with at least two usable film ratios                        |
| `actors_min_3_films.csv`      | First-billed actors with at least three usable film ratios                      |
| `directors_min_2_films.csv`   | Directors with at least two usable film ratios                                  |
| `directors_min_3_films.csv`   | Directors with at least three usable film ratios                                |

CSV tables are written to a temporary file beside their destination and replaced
only after that table finishes writing; failed writes remove the temporary file
and preserve the previous destination. This protects each file individually,
not the nine-file set as one transaction.

Revenue-to-budget ratios are calculated only when both values are positive.
The comparison's `franchise_film_median` counts each usable film once. Its
`franchise_equal_weight_median` first calculates each collection's median, then
takes the median of those collection medians, giving each collection one value.
The comparison includes every collection with a usable ratio; the bundle
shortlist separately requires at least three usable films per release window.
This avoids ranking a bundle on just one or two observed films and limits the
recommendation to collections meeting that coverage rule.

Franchise membership follows TMDb collection membership. These ratios describe
reported revenue relative to production budget; they do not measure net profit.

## Supporting genre analysis

The [TMDb data profiling notebook](data_profile/tmdb_data_profile.ipynb)
compares genres across all years, before 2000, and from 2000 onward.
It reports median box-office revenue and median revenue per dollar of
production budget. A genre needs at least five films with positive
reported revenue in a period to receive a revenue rank.

Fantasy led on median revenue overall and from 2000 onward. Adventure
led before 2000. Genre groups can overlap. In this sample, Animation
and Family contained the same 17 films.

Run the notebook after preparing the cache and validated IDs. Its optional live
spot-checks are disabled by default, so a top-to-bottom run uses local data
without TMDb calls. To intentionally perform live spot-checks, set
`RUN_LIVE_SPOT_CHECKS = True` in that section and configure your local API key.
The nine CSVs in `data/analysis/` come from the main licensing analysis.

## Offline verification

After installing the pinned dependencies, run from the repository root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

The [regression checks](tests/README.md) use mocked HTTP responses and waits,
temporary inputs and databases, and versioned synthetic shortlist fixtures.
They need no API key, local candidate list, or cache. They cover import safety,
ID normalization, retries and fatal-stop audit persistence, transform edge cases,
disabled notebook live checks, and all four shortlist changes plus unchanged
sections. They do not write the real cache or analysis outputs.

## Verified baseline

The original input has 127 rows: 117 distinct valid IDs, six duplicate rows,
three invalid entries, and one blank ID. The clean-clone test produced both
responses for 112 films (224 cached responses) and all nine analysis CSVs.

The remaining IDs returned HTTP 404 for both details and credits:
`8471293`, `9412887`, `8471294`, `9412888`, and `7733901`.
Live API results can change; use `data/cache/fetch_audit.csv` to explain any
difference from the 112-film baseline. Cached successful responses retain the
data acquired on their original fetch date.

## Performance test

The latest verification ran three cached analyses per dataset on 20 November
2026 using the project's virtual environment and a temporary project copy.
The laptop had an Intel Core i5-6300U and 7.87 GiB RAM, running Windows 10 Pro.

| Dataset | Films analyzed | Run 1 | Run 2 | Run 3 | Median |
|---|---:|---:|---:|---:|---:|
| Current TMDb cache | 112 of 117 validated IDs | 2.381 s | 2.558 s | 2.124 s | 2.381 s |
| Synthetic cache | 500 of 500 IDs | 3.598 s | 3.646 s | 3.154 s | 3.598 s |

With the virtual environment activated (or replace `python` with
`.\.venv\Scripts\python.exe`):

```powershell
python benchmarks/benchmark_analysis.py
python benchmarks/benchmark_500.py
```

Each run wrote nine CSVs. The timings include Python startup, reading the SQLite
cache, transformation, calculations, integrity checks, and CSV writes. They
exclude live TMDb requests and synthetic dataset setup. Every analysis process
was fresh; operating-system caches were not flushed or controlled.

The 500-film dataset repeats complete cached details and credits whose fetch
audit marks both endpoints successful, assigning each copy a unique test ID.
Its dataset and outputs remain in a temporary folder that is removed afterward.
It tests capacity for 500 records, rather than 500 independently fetched films.
Successful source IDs are deduplicated and sorted numerically before cycling;
JSON object keys are serialized in sorted order. Identical source records produce
the same 500 IDs and outputs even if audit rows or SQLite insertion order change.
No randomness is used, so no seed is needed; changed source content can still
change the synthetic data. See the [measurement report](measurement_report.md) for p95, worst-case observed
times, reproduction details, and limitations. No numeric runtime deadline was
specified in the brief.

## Repeat the local clone test

In an existing `lab2-clean-test` clone whose `origin` points to the local source
repository, first pull committed changes:

```powershell
git pull --ff-only origin
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Then run the canonical `run_pipeline.py` command above. Retain the clone's own `.env` and
original input. An existing cache tests cache reuse; a clone without a cache
tests fresh acquisition. Confirm 117 unique validated IDs, inspect the acquisition
audit and SQLite cache, and check that `data/analysis/` contains nine CSVs.

See [the data diagnosis](docs/data_diagnosis.md) and
[architecture decisions](decisions/) for more background.
