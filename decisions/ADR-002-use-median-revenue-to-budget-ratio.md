# ADR-002: Compare typical film performance using the median revenue-to-budget ratio

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

Kwame needs to compare films made on different production budgets.
Reported box-office revenue shows how much a film grossed, but a larger
gross can come from a much larger budget. The 112 analyzed films have
revenue-to-budget ratios ranging from 1.13× to 70.49×, so a few unusually
high ratios can also influence the group average.

## Decision

I divide reported box-office revenue by reported production budget in
nominal dollars and calculate a ratio only when both values are positive.
I keep valid extreme ratios and use the median of the individual film
ratios as the primary measure in both release windows.

## Alternatives considered

### Alternative A: Compare reported box-office revenue alone

- **How it would work:** Compare the median reported gross for franchise
  and standalone films without dividing by production budget.
- **Why it is attractive:** It shows which group typically generated more
  ticket revenue in absolute dollars.
- **Why rejected:** It does not answer how much ticket revenue films
  generated per dollar of production budget, which is the comparison
  used to screen licensing candidates.

### Alternative B: Compare the arithmetic mean of film ratios

- **How it would work:** Add the usable ratios in each group and divide
  by the number of films, giving each film one observation.
- **Why it is attractive:** High-performing titles have more influence,
  which is useful if Kwame wants to assess breakout potential.
- **Why rejected:** Ratios such as 70.49× for Star Wars and 67.24× for
  Jaws can pull the mean away from the middle film. The median better
  represents typical performance in this sample.

| Release window | Franchise mean | Standalone mean | Mean gap | Franchise median | Standalone median | Median gap |
| -------------- | -------------: | --------------: | -------: | ---------------: | ----------------: | ---------: |
| All years      |         8.540× |          8.284× |  +0.256× |           5.624× |            3.845× |    +1.779× |
| 2000 onward    |         5.411× |          4.901× |  +0.510× |           5.052× |            3.845× |    +1.207× |

The gap is the franchise result minus the standalone result. Franchises
lead in both windows using either statistic. The mean narrows the lead
from 1.779× to 0.256× across all years and from 1.207× to 0.510× from
2000 onward.

## Consequences

- **What this buys:** Kwame gets a comparison in reported ticket revenue
  per dollar of production budget. All 112 acquired films had positive
  budget and revenue, so all 112 contributed a usable ratio.
- **What this costs:** A zero or missing financial value leaves the film
  unscored. The figures use nominal dollars, and older grosses may
  include re-release revenue. The cached data does not identify which
  titles received re-release revenue or how much.
- **What it costs the client if I am wrong:** Kwame could overpay if he
  reads a high ratio as profit or as a forecast of streaming demand.
  The ratio uses production budget and theatrical gross. A licensing
  price needs separate evidence about rights, fees, and viewing value.
- **What would make me revisit this:** If Kwame prioritizes breakout
  titles, report the mean alongside the median. If reliable licensing
  costs and streaming forecasts become available, use them to reassess
  the shortlist and price ceilings.

## What this survives

- **A few films have unusually high ratios.** The median keeps those
  films in the analysis while limiting their influence on the result.
- **One franchise contributes more films than others.** Giving each
  franchise one median still puts franchises ahead in both windows.
  The franchise results are 5.73× across all years and 4.39× from 2000
  onward, compared with the standalone median of 3.84× in each window.
