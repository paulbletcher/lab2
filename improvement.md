# Improvement beyond the brief: Quarterly shortlist change report

## The problem it solves

Adjoa reruns the licensing analysis each quarter. Comparing four ranked tables
by hand makes it easy to miss a new candidate, a dropped title, a rank move, or
a changed revenue-to-budget ratio. Kwame needs to know which negotiation
priorities deserve another look.

## What I built

I built `shortlist_changes.py`. Its `snapshot` command saves the ranked franchise
and standalone shortlists for both release windows. Its `compare` command
compares two snapshots and writes a Markdown report showing entries, departures,
rank moves, and ratio changes, reported to two decimal places. It compares
matching release windows and preserves the original analysis outputs and cache.
The report identifies changes; it does not establish their causes.

### Verification with two synthetic snapshots

I copied the real shortlist and made controlled edits to test entries,
departures, rank moves, and ratio changes. I set _Pulp Fiction_ to 27.00×
to check that the report detects a ratio change even when the rank stays
at 2.

| Title                  | Change reported | Evidence                                 |
| ---------------------- | --------------- | ---------------------------------------- |
| Pulp Fiction           | Ratio changed   | 26.74× to 27.00×, still at rank 2        |
| Spirited Away          | Moved up        | Rank 4 to rank 3, still at 14.47×        |
| SYNTHETIC Example Film | Entered         | Rank 4 with a ratio of 14.00×            |
| Schindler’s List       | Dropped out     | Previously rank 3 with a ratio of 14.61× |

The `snapshot` and `compare` commands reported all four expected changes
in the all-years standalone shortlist. The other three shortlist
sections correctly reported no changes.

## What it is worth to Kwame and Adjoa

Adjoa can save one snapshot per quarter and generate the comparison with one
command, instead of inspecting four old and four new tables manually. Kwame
gets a short list of negotiation priorities to revisit. The acquisition audit
and candidate list provide separate evidence for investigating a change.
The synthetic test verifies all four change types and the unchanged case;
no time saving or financial return has been measured.

## What it cost

The improvement adds one script using only Python's standard library and stores
four CSVs per snapshot. It introduces no new package dependency. Adjoa must
retain the relevant snapshots and use a new destination and report filename
for each comparison because existing files are protected from overwrite.
Reports cover the ranked shortlists, not every acquired film; differences that
do not change the ratio rounded to two decimal places are not reported as
ratio changes. Analyst development time was not recorded.
