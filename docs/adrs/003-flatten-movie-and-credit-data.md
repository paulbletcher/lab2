# ADR-003: Use one row per film for licensing and one row per film–director pair for director analysis

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

TMDb provides movie details, cast, and crew as nested responses. I inspected the responses and calculated sample ratios in the notebook before moving the reusable transformation rules into `pipeline/transform.py`. The 112 analyzed films produced 122 unique film–director pairs. Nine films had more than one director. All 112 films had a first-billed actor.

## Decision

Keep one row per film in the licensing table and extract the collection ID and name into that row. Keep a separate director table with one row per film ID and director ID. For actor analysis, select the cast member with the lowest available billing order.

Check that the actor join matches at most one actor row to each film. Check that each director credit matches one film while allowing multiple directors to share the same film.

## Alternatives considered

### Alternative A: Join every director into the main movie table

- **How it would work:** Use the joined film and director data as the input for both licensing and talent calculations.
- **Why it is attractive:** One table would contain both the financial fields and director credits.
- **Why rejected:** The join would turn 112 movie rows into 122 rows. The extra 10 rows would give films with co-directors more influence in the licensing comparison.

### Alternative B: Keep just one director per film

- **How it would work:** Pick one director for each movie and discard any additional director rows.
- **Why it is attractive:** The joined table would still have one row per movie.
- **Why rejected:** It would drop 10 valid director credits across nine films and could change who meets the minimum film count for the director ranking.

## Consequences

- **What this buys:** Each film counts once in the licensing comparison. The director analysis keeps all 122 distinct film–director pairs. The actor analysis has one first-billed actor for each of the 112 films.
- **What this costs:** The pipeline needs separate tables and join checks. First billing is a consistent rule, but it can leave out another performer who shares the lead.
- **What it costs the client if I am wrong:** If first billing misses a relevant co-lead, that performer may fall below the three-film minimum or miss the talent shortlist.
- **What would make me revisit this:** A credit spot-check shows that including a co-lead would change the talent shortlist, or a join changes the expected film or credit count.

## What this survives

- **A film has several directors:** All director credits remain available while the licensing comparison still counts the film once.
- **The list grows to 500 titles:** The same movie IDs, credit pairs, and join checks apply to the expanded data.
