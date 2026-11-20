# ADR-002: Exclude unresolved IDs from movie-level analysis and retain them in the audit

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

TMDb returned HTTP 404 for movie details for IDs `8471293`, `9412887`, `8471294`, `9412888`, and `7733901`. The requests are recorded in `data/cache/fetch_audit.csv`. This left 112 of 117 validated IDs available for movie-level analysis, or 95.7% coverage.

## Decision

Retain the unresolved IDs and their request outcomes in the acquisition audit. Leave them out of the licensing comparison because their collection, budget, and revenue fields are unavailable. When movie details are available and credits are missing, include the film in the movie-level comparison and omit it from the talent calculations that need those credits.

## Alternatives considered

### Alternative A: Search for replacement IDs

- **How it would work:** Obtain the intended titles and release years from the client or original source, then match them to TMDb records.
- **Why it is attractive:** A verified match could recover a missing title and improve coverage.
- **Why rejected:** The supplied list contains only IDs. Without a title or another identifier to verify a replacement, a lookup could add the wrong film.

## Consequences

- **What this buys:** The five exclusions can be traced back to specific requests. Every film in the comparison has a retrieved details record.
- **What this costs:** Five candidates remain unassessed. Their franchise membership and ratios are unknown.
- **What it costs the client if I am wrong:** A missing record could belong to a strong standalone or to a franchise with only two observed films. Recovering it could change the standalone shortlist or make that franchise eligible under the three-film rule. The available data cannot establish whether either change would happen.
- **What would make me revisit this:** A successful details response becomes available for any of the five IDs, or the client supplies enough information to verify a corrected ID.

## What this survives

- **The list grows to 500 titles:** The same audit tracks failures by ID and recalculates coverage from the new list.
- **Only credits are missing:** A film with available details still contributes to the licensing comparison.
