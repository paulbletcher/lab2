# ADR-001: Use TMDb collection membership to classify films

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

Kwame needs to compare franchise bundles with standalone films. The
candidate list supplies film IDs, so the pipeline needs a rule Adjoa
can apply to the 112 analyzed films and rerun when the list grows to
about 500 titles.

## Decision

I classify a film as franchise when its TMDb `collection_id` is present
and as standalone for this analysis when it is missing. I group franchise
films by `collection_id` to build the bundle shortlist.

## Alternatives considered

### Alternative A: Classify films manually

- **How it would work:** Review each candidate for sequels, reboots, and
  spin-offs, then maintain a film-to-franchise mapping.
- **Why it is attractive:** Manual review can catch franchise films that
  TMDb leaves unlinked.
- **Why rejected:** Adjoa would have to review each new title and maintain
  consistent rules for borderline cases. The collection ID gives the
  pipeline a rule it can apply directly on every run.

### Alternative B: Group films by title similarity

- **How it would work:** Normalize film titles and group those that share
  a name or title prefix.
- **Why it is attractive:** The pipeline could apply the rule using titles
  already present in the movie records.
- **Why rejected:** A shared title can group unrelated films, and sequels
  with different titles can end up in separate groups.

## Consequences

- **What this buys:** The same cached TMDb records produce the same
  groups on every run. The rule gives 96 franchise films and 16 standalones
  across all years, and 63 franchise films and 8 standalones from 2000 onward.
- **What this costs:** The classification depends on TMDb linking films
  correctly. The candidate list can also cover only part of a collection.
  For example, the analysis includes one film from the Jaws collection.
- **What it costs the client if I am wrong:** One unlinked franchise film
  would make up one of the eight titles in the 2000-onward standalone
  group. Moving it could shift both medians and change how strongly the
  data supports prioritizing bundles. Kwame could also price a studio
  offer using ratios from films the offer excludes.
- **What would make me revisit this:** If a review of the 16 standalones
  confirms an unlinked franchise film, record the evidence and rerun both
  release windows with the corrected classification. If the studio offers
  a different set of titles, reassess the bundle using the offered films
  before setting a price ceiling.

## What this survives

- **The candidate list grows to about 500 titles.** Adjoa can rerun the
  same rule on all acquired records without maintaining a manual mapping.
- **Different films share a title.** The pipeline uses collection IDs
  for grouping, so a shared title alone cannot merge two collections.
