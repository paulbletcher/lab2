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
   later runs; failed requests are retried. HTTP 401, 403, or 429 stops the batch.
   Other request failures are recorded in the audit, so inspect it even when the
   script exits successfully.
3. **Analyze:** reads the validated IDs and cached responses, flattens movie and
   credit data, and writes nine CSV tables under `data/analysis/`.

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

| CSV | Contents |
| --- | --- |
| `comparison.csv` | Franchise and standalone comparison for all years and releases from 2000 onward |
| `franchises_all_years.csv` | Top three collections with at least three usable film ratios |
| `franchises_2000_onward.csv` | Same shortlist for releases from 2000 onward |
| `standalones_all_years.csv` | Top five standalone films with usable ratios |
| `standalones_2000_onward.csv` | Same shortlist for releases from 2000 onward |
| `actors_min_2_films.csv` | First-billed actors with at least two usable film ratios |
| `actors_min_3_films.csv` | First-billed actors with at least three usable film ratios |
| `directors_min_2_films.csv` | Directors with at least two usable film ratios |
| `directors_min_3_films.csv` | Directors with at least three usable film ratios |

Revenue-to-budget ratios are calculated only when both values are positive.
Franchise membership follows TMDb collection membership. These ratios describe
reported revenue relative to production budget; they do not measure net profit.

## Verified baseline

The original input has 127 rows: 117 distinct valid IDs, six duplicate rows,
three invalid entries, and one blank ID. The clean-clone test produced both
responses for 112 films (224 cached responses) and all nine analysis CSVs.

The remaining IDs returned HTTP 404 for both details and credits:
`8471293`, `9412887`, `8471294`, `9412888`, and `7733901`.
Live API results can change; use `data/cache/fetch_audit.csv` to explain any
difference from the 112-film baseline. Cached successful responses retain the
data acquired on their original fetch date.

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
