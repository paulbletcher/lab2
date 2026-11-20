# ADR-004: Use the median revenue-to-budget ratio to compare typical film performance

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

The 112 analyzed films had revenue-to-budget ratios ranging from 1.13× to 70.49×. Star Wars reached 70.49× and Jaws reached 67.24×. A few values this high can pull up an arithmetic mean. The sample also contains franchises of different sizes. Harry Potter contributed eight films, while Jaws contributed one.

## Decision

Divide reported box-office revenue by reported production budget when both amounts are positive. Keep the observed extremes in the data. Use the median film ratio as the primary comparison across all years and from 2000 onward. As a sensitivity check, calculate one median per franchise and then take the median across franchises, so each collection contributes one number.

## Alternatives considered

### Alternative A: Compare the arithmetic mean

- **How it would work:** Sum the usable film ratios in each group and divide by the number of films.
- **Why it is attractive:** It gives breakout films more influence, which could be useful if Kwame’s priority is exceptional upside.
- **Why rejected:** The median better represents typical film performance because unusually high ratios, such as 70.49× for Star Wars and 67.24× for Jaws, have less influence on it.

#### Mean and median comparison

Both statistics use the same eligible films, with each film counted once.
The gap is the franchise result minus the standalone result.

| Release window | Franchise mean | Standalone mean | Mean gap | Franchise median | Standalone median | Median gap |
| -------------- | -------------: | --------------: | -------: | ---------------: | ----------------: | ---------: |
| All years      |         8.540× |          8.284× |  +0.256× |           5.624× |            3.845× |    +1.779× |
| 2000 onward    |         5.411× |          4.901× |  +0.510× |           5.052× |            3.845× |    +1.207× |

Franchises led in both release windows using either statistic. Using the
mean narrowed the franchise lead from 1.779× to 0.256× across all years
and from 1.207× to 0.510× from 2000 onward.

## Consequences

- **What this buys:** With each film counted once, franchises led across all years (5.62× versus 3.84×) and from 2000 onward (5.05× versus 3.84×). The lead also held when each franchise contributed one median, at 5.73× versus 3.84× across all years and 4.39× versus 3.84× from 2000 onward.
- **What this costs:** The median summarizes the middle and can hide weaker bundle entries. The franchise shortlist therefore includes the lowest observed ratio alongside the median. The 2000-onward standalone median is based on eight films.
- **What it costs the client if I am wrong:** Kwame could overlook a promising breakout title if he uses the median as his only screening measure. He could also overpay if he treats historical ticket sales as a forecast of streaming value.
- **What would make me revisit this:** If Kwame starts prioritizing
  breakout potential, report the mean alongside the median and show
  which titles account for the largest differences. Recalculate both
  measures when the candidate list expands and check whether the
  leading group changes.

## What this survives

- **The list grows to 500 titles:** Both comparisons recalculate from the expanded list. Film and collection counts show how much evidence supports each result.
- **One franchise supplies many more films than the others:** The equal-franchise check shows whether the conclusion holds when each collection contributes one median.
