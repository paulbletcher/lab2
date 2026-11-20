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
