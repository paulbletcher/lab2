# ADR-005: Exclude unavailable and unusable records and test their effect on the recommendation

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

The input CSV contained 127 rows. One ID was blank, three failed TMDb
ID validation, and six were repeated numeric IDs. That left 117 distinct
valid IDs. Five returned HTTP 404 for both movie details and credits,
leaving 112 films for analysis.

One rejected ID, `tt0468569`, is the IMDb ID for The Dark Knight.
The same film was already included as TMDb ID `155`, so rejecting the
IMDb-format row did not reduce film coverage.

## Decision

I exclude blank and invalid IDs, count each valid TMDb ID once, and
exclude films whose details are unavailable. I record these outcomes
in the input and fetch audits, leave films with missing or non-positive
budget or revenue unscored, and test how the five missing films could
affect the recommendation.

## Alternatives considered

### Alternative A: Fill in missing ratios with a group median

- **How it would work:** Assign each missing film to a group and give
  it the observed median ratio for that group.
- **Why it is attractive:** All 117 valid IDs would contribute to the
  comparison.
- **Why rejected:** The five missing films have unverified collection
  membership, release dates, budgets, and grosses. Assigning a group
  and its median would build the observed result into the missing rows
  and hide how much those records could change the comparison.

### Alternative B: Suspend the recommendation until all 117 films are available

- **How it would work:** Hold the shortlist and memo until all five
  failed records can be resolved.
- **Why it is attractive:** Kwame would have coverage for every
  validated candidate ID.
- **Why rejected:** The 112 acquired films support a provisional
  recommendation. The scenario check identifies a tested scenario in which the leading group changes.

## Consequences

- **What this buys:** The analysis covers 112 of 117 validated IDs
  (95.7%), and every acquired film has a usable ratio. Counting the
  six repeated numeric rows again changed some medians but left the
  leading group the same in both windows.
- **What this costs:** The five unavailable films contribute no
  observed ratios. The tested scenarios assume all five are standalones
  and assign each the lowest or highest observed standalone ratio in
  the relevant window. The later window also assumes all five films
  were released on or after 2000-01-01. Their actual attributes remain
  unknown.
- **What it costs the client if I am wrong:** Kwame could give bundles
  too much priority in the later window. In the high-ratio scenario,
  the standalone median rises from 3.845× to 5.244× and overtakes the
  franchise median of 5.052×. The observed later-window standalone
  group has only eight films.
- **What would make me revisit this:** If any of the five IDs is
  corrected or its details become available, check its release date,
  collection membership, budget, and revenue. Rerun both windows
  with the recovered records and update the memo if the leading group
  or the shortlist changes.

## What this survives

- **All five missing films are low-ratio standalones.** Franchises
  lead in both tested windows.
- **All five missing films are high-ratio standalones.** Franchises
  still lead across all years, at 5.624× versus 5.244×. Standalones
  lead in the 2000-onward scenario, at 5.244× versus 5.052×.
