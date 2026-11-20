# ADR-005: Require three observed films for the franchise shortlist and use both time windows to choose the first negotiation target

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

The candidate list covered 32 TMDb collections with usable ratios across all years and 24 from 2000 onward. Coverage varied by collection. Harry Potter had eight films in the sample, while Jaws had one. The single Jaws film had a ratio of 67.24×, the highest collection median if every collection qualifies.

## Decision

Require at least three films with usable revenue-to-budget ratios in the selected time window. Rank eligible collections by median ratio. Show the number of films and the lowest observed ratio alongside each result.

Keep the all-years shortlist as the historical ranking and use the 2000-onward results to check how much it depends on older films. Open negotiations with The Lord of the Rings because all three observed films qualify in both windows and its lowest observed ratio was 9.37×.

## Alternatives considered

### Alternative A: Allow collections with one observed film

- **How it would work:** Rank every collection with at least one usable ratio.
- **Why it is attractive:** A collection with limited coverage could still surface as a target.
- **Why rejected:** Jaws would rank first at 67.24× based on one film. That result gives Kwame little evidence about how other titles in a potential bundle performed.

### Alternative B: Choose the first negotiation target from the all-years ranking alone

- **How it would work:** Open negotiations with Star Wars because its six observed films had the highest median among eligible collections, at 13.40×.
- **Why it is attractive:** It uses all six observed films and recognizes the collection’s strong historical results.
- **Why rejected:** Four of those films were released before 2000. The two newer films had ratios of 5.41× and 7.52×. The Lord of the Rings had three films in the newer window, with a median of 11.73× and a lowest ratio of 9.37×.

## Consequences

- **What this buys:** Each shortlisted franchise has evidence from at least three films. The lowest observed ratio lets Kwame see the weaker end of each collection before negotiating a bundle.
- **What this costs:** A promising collection can miss the shortlist because too few of its films appear in the sample. Star Wars falls out of the 2000-onward shortlist under this rule because only two observed films qualify.
- **What it costs the client if I am wrong:** If the studio’s Star Wars offer includes the older hits and StreamVault expects them to drive more viewing than The Lord of the Rings, opening with The Lord of the Rings could delay a better deal.
- **What would make me revisit this:** The studio confirms a different set of titles from the ones analyzed, or projected streaming value and proposed fees change which bundle offers the better deal.

## What this survives

- **The list grows to 500 titles:** The pipeline recalculates collection medians, lowest ratios, and eligibility from the new list.
- **More films are added to a collection:** A previously excluded collection can qualify once three films have usable ratios in the window.
- **Kwame changes the release-year cutoff:** The same calculation can rerank the collections using the revised window.
