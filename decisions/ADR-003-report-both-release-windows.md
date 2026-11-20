# ADR-003: Report all-years and 2000-onward results side by side

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Paul Bletcher, analyst

## Context

The brief requires both release windows. Yaw questions how much weight to
give pre-2000 box-office figures. The all-years comparison covers 112
films, and the 2000-onward comparison covers 71. The release cutoff changes
which collections have enough scored films to qualify for the shortlist.

## Decision

I report results for all analyzed release years and for films released on
or after 2000-01-01. I apply the same scoring and ranking rules in both
windows and call out any change that affects the licensing recommendation.

## Alternatives considered

### Alternative A: Report all years only

- **How it would work:** Compare groups and rank bundles using all 112
  analyzed films.
- **Why it is attractive:** It uses the full sample, including all 16
  standalones and six scored Star Wars films.
- **Why rejected:** Star Wars ranks first in this window, but four of its
  six scored films predate 2000. With two eligible films from 2000 onward,
  it falls below the three-film minimum. Reporting only the full sample
  would hide that change from Kwame.

### Alternative B: Report 2000 onward only

- **How it would work:** Apply the release cutoff before calculating
  group medians and ranking bundles.
- **Why it is attractive:** It answers Yaw's question directly by showing
  how films released from 2000 onward compare.
- **Why rejected:** It drops 41 analyzed films, including eight standalones.
  Kwame would lose the full-sample comparison and the evidence that
  Star Wars leads when earlier releases are included.

## Consequences

- **What this buys:** Kwame can see which conclusions hold across both
  windows and which depend on the cutoff.

| Release window | Franchise median | Standalone median | Top three eligible bundles                      |
| -------------- | ---------------: | ----------------: | ----------------------------------------------- |
| All years      | 5.62× (96 films) |  3.84× (16 films) | Star Wars, The Lord of the Rings, Indiana Jones |
| 2000 onward    | 5.05× (63 films) |   3.84× (8 films) | The Lord of the Rings, Ice Age, The Avengers    |

- **What this costs:** The 2000-onward result has only eight observed
  standalones. In the tested scenario where all five missing films were
  high-performing standalones released from 2000 onward, the combined standalone group’s median rose to 5.24× and overtook the franchise median of 5.05×.
- **What it costs the client if I am wrong:** Kwame could negotiate for
  Star Wars first based on the all-years ranking while giving too little
  weight to its limited coverage in the 2000-onward sample. He could
  also pass over worthwhile older titles if he relied only on the
  later window.
- **What would make me revisit this:** If the studio limits an offer to
  a specific set of titles or release period, rerank the offered films
  using those terms. If the five missing records become available, rerun
  both comparisons and check whether either recommendation changes.

## What this survives

- **Yaw asks to exclude pre-2000 releases.** Franchise films still lead
  on the observed median, and the 2000-onward shortlist is available
  for negotiation.
- **The top-ranked bundle changes with the cutoff.** The Lord of the
  Rings qualifies in both windows, ranking second across all years
  and first from 2000 onward. That makes it the first bundle to discuss
  when Kwame wants a candidate supported by both views.
