# Lab 2: TMDb movie pipeline

Validate movie IDs, acquire movie details and credits from TMDb, cache the raw
responses in SQLite, and compare franchise and standalone films using revenue
relative to budget. The analysis also summarizes first-billed actors and directors.

## Setup

Run these commands in PowerShell from the repository root. The pipeline has been
tested with Python 3.14. Each clone should use its own virtual environment.

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

## Run the pipeline

Run each stage in order from the repository root, checking its result before
continuing:

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
   not cached and are requested again on a later run. Importing
   `pipeline.extract` does not start acquisition.
3. **Analyze:** `python run_analysis.py` reads the validated IDs and cached
   responses, transforms them, computes the analysis, checks integrity, and
   calls the loader to write nine CSV tables under `data/analysis/`.

To run the full workflow with the current Python environment:

```powershell
python run_pipeline.py
```

The runner uses the existing validation and extraction scripts, reuses successful
SQLite responses, and retries failed requests. Input ID validation is a prerequisite
for acquisition in this project. The lecture's extract → validate → transform →
check → load responsibilities live in these modules:

| Stage     | Location and responsibility                                                                                                                                                                        |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Extract   | `pipeline/extract.py`: TMDb acquisition, response ID validation, SQLite cache, and fetch audit                                                                                                     |
| Validate  | `pipeline/validate.py`: normalize and validate input IDs, remove duplicates, reconcile input counts, and write input audits                                                                        |
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

Revenue-to-budget ratios are calculated only when both values are positive.
Franchise membership follows TMDb collection membership. These ratios describe
reported revenue relative to production budget; they do not measure net profit.

## Supporting genre analysis

The [TMDb data profiling notebook](data%20profile/tmdb_data_profile.ipynb)
compares genres across all years, before 2000, and from 2000 onward.
It reports median box-office revenue and median revenue per dollar of
production budget. A genre needs at least five films with positive
reported revenue in a period to receive a revenue rank.

Fantasy led on median revenue overall and from 2000 onward. Adventure
led before 2000. Genre groups can overlap. In this sample, Animation
and Family contained the same 17 films.

Run the notebook's `Genre analysis` section after preparing the cache
and validated IDs. The nine CSVs in `data/analysis/` come from the
main licensing analysis.

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

I ran the cached analysis three times per dataset on 20 November 2026,
from the repository root using the project's virtual environment.

| Dataset            |           Films analyzed |   Run 1 |   Run 2 |   Run 3 |  Median |
| ------------------ | -----------------------: | ------: | ------: | ------: | ------: |
| Current TMDb cache | 112 of 117 validated IDs | 3.579 s | 1.619 s | 1.868 s | 1.868 s |
| Synthetic cache    |           500 of 500 IDs | 2.524 s | 2.614 s | 2.612 s | 2.612 s |

With the virtual environment activated (or replace `python` with
`.\.venv\Scripts\python.exe`):

```powershell
python benchmarks/benchmark_analysis.py
python benchmarks/benchmark_500.py
```

The timings include Python startup, reading the SQLite cache, transforming
the data, calculating the results, running integrity checks, and writing
the CSVs. They exclude live TMDb requests and synthetic data setup.

Both benchmarks wrote nine CSVs in each of their three runs. The 500-film
dataset repeats complete cached film records (details and credits) whose
fetch audit marks both endpoints successful, assigning each copy a unique
test ID. Its dataset and outputs stay inside a temporary project folder,
which is removed when the benchmark finishes. Its median was 2.612 seconds.
This demonstrates that the cached analysis can process 500 film records.
A first run that fetches data from TMDb will also depend on network and
API response times.

## Repeat the local clone test

In an existing `lab2-clean-test` clone whose `origin` points to the local source
repository, first pull committed changes:

```powershell
git pull --ff-only origin
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Then run the three pipeline commands above. Retain the clone's own `.env` and
original input. An existing cache tests cache reuse; a clone without a cache
tests fresh acquisition. Confirm 117 unique validated IDs, inspect the acquisition
audit and SQLite cache, and check that `data/analysis/` contains nine CSVs.

See [the data diagnosis](docs/data_diagnosis.md) and
[architecture decisions](docs/adrs/) for more background.
