# ADR-001: Cache each TMDb response in one SQLite file

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

The validated list contained 117 movie IDs. For each ID, the extraction script requests movie details and credits separately. The 112 films with both responses account for 224 successful responses. Adjoa will rerun the analysis on her laptop, and next year’s candidate list could grow to about 500 titles.

## Decision

In `pipeline/extract.py`, store successful responses in `data/cache/tmdb.sqlite`. Each row in the `responses` table stores the movie ID, endpoint, raw JSON, and UTC fetch timestamp. The movie ID and endpoint together identify one response.

Before calling TMDb, look for that movie ID and endpoint in SQLite. If the response is present, read it from the cache. If it is missing, request it and save the successful response immediately. If details succeed but credits fail, the next run can reuse the details and retry the credits. `run_analysis.py` reads the saved responses directly.

## Alternatives considered

### Alternative A: Store the fetched data in a second CSV

- **How it would work:** Store one row per movie with separate columns for details and credits. Those columns could hold the original JSON, or the responses could be flattened into individual fields.
- **Why it is attractive:** It uses the same familiar file format as `validated_ids.csv`. A flattened version would be easy to inspect in a spreadsheet.
- **Why rejected:** Flattening at this stage would require choosing which fields to keep before profiling was complete. A CSV with raw JSON would preserve the nested fields, but updating only the credits for a movie would require extra logic to locate and rewrite its row. SQLite lets the extractor save that response independently using the movie ID and endpoint.

## Consequences

- **What this buys:** With the current cache, a rerun can reuse 224 responses for the 112 films with both endpoints saved. The extractor may still request responses for unresolved IDs. The analysis runner can regenerate its output from SQLite without calling TMDb.
- **What this costs:** A cache hit uses the saved response even if TMDb has since updated it. The `fetched_at` timestamp records when the response was collected. The current lookup has no automatic expiry.
- **What it costs the client if I am wrong:** If an old budget or revenue figure changes enough to move a title into or out of the top five standalones or top three franchises, Kwame could enter negotiations with an outdated priority list.
- **What would make me revisit this:** If a fresh spot-check changes a shortlist position or the franchise-versus-standalone recommendation, add an explicit refresh option and rerun the affected analysis with updated responses.

## What this survives

- **A request fails halfway through a movie:** If details were saved before credits failed, the next run can reuse the details.
- **The list grows to 500 titles:** Existing IDs can reuse their saved responses. Each new ID adds up to two successful responses to the same file.
- **The analysis needs a field omitted from the first transform:** The original JSON is available to transform again.
