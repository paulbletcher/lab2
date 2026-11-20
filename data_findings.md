# Data findings — StreamVault

## Summary

The local input has 127 rows and produces 117 distinct valid numeric IDs.
Both requested responses are cached for 112 films; five IDs returned HTTP 404
for both endpoints. All 112 acquired films have usable positive budgets and
revenues. The observed franchise-film median exceeds the standalone median in
both release windows, but the missing-film high-ratio scenario reverses the
2000-onward comparison. The recent standalone sample contains only eight films.

Results use the same validated IDs and `flatten_movie_details()` calculations
as the pipeline. Source evidence is in the profiling notebook, input audit,
fetch audit, and SQLite cache. The detailed scenario account is retained in
[the supporting diagnosis](docs/data_diagnosis.md).

## Reconciliation

| Stage | Rows | Delta | Reason |
|---|---:|---:|---|
| Original candidate rows | 127 | — | Supplied input list |
| Nonblank rows | 126 | -1 | One blank ID |
| Valid numeric ID rows | 123 | -3 | Rejected `-1`, `tt0468569`, and `N/A` |
| Distinct validated IDs | 117 | -6 | Six repeated numeric ID occurrences |
| Acquired and analyzed films | 112 | -5 | Details and credits both returned HTTP 404 for five IDs |
| Films with usable ratios | 112 | 0 | Every acquired film has positive budget and revenue |

This reconciles 127 = 1 blank + 3 invalid + 6 repeat occurrences + 5 unavailable
records + 112 analyzed films. The cache holds 224 successful endpoint responses
for these films. The actor join retains 112 first-billed actor rows; the director
join retains 122 unique movie–director pairs, with nine films having co-directors.
These are relationships, not extra films.

## Findings, ranked by risk

### F-01: Missing records can reverse the recent comparison — Severity: High

- **What it is:** Five validated IDs have neither requested response: `8471293`, `9412887`, `8471294`, `9412888`, and `7733901`.
- **How I detected it:** Reconciled validated IDs, cached responses, and the fetch audit; both endpoints record HTTP 404 for each ID.
- **Scale:** Five of 117 validated films are unavailable; coverage is 95.7%. Only eight observed standalones meet the 2000 cutoff.
- **Effect on the client's number:** Assuming all five are recent standalones at the highest observed recent standalone ratio raises that group's median from 3.845 to 5.244, above the franchise median of 5.052.
- **What I did about it:** Excluded unavailable records from observed results, retained their audit outcomes, and ran separate low/high standalone-ratio scenarios in both windows. No values were imputed into the real dataset.
- **Residual risk:** Their actual groups, dates, and financial values remain unknown. The scenarios are conditional examples, not universal bounds or recovered observations.

### F-02: Release cutoff changes negotiation targets — Severity: High

- **What it is:** The all-years and 2000-onward windows have different eligible films and bundle rankings.
- **How I detected it:** Applied the release cutoff before grouping, required three usable films per collection, and reranked using the same rules.
- **Scale:** The later window retains 71 films: 63 franchise and eight standalone films; 41 films are outside it.
- **Effect on the client's number:** The franchise-film median falls from 5.624 to 5.052 while the standalone median remains 3.845. Star Wars leads the all-years bundle ranking but has only two eligible recent films; The Lord of the Rings leads the later ranking.
- **What I did about it:** Reported both windows side by side and recommended The Lord of the Rings as a candidate supported by both views.
- **Residual risk:** The cutoff is a sensitivity check, not an inflation correction. It changes sample composition as well as release period.

### F-03: Collection membership and partial bundles limit interpretation — Severity: High

- **What it is:** Collection links define franchise membership, and the candidate list may contain only part of a collection.
- **How I detected it:** Inspected nested collection fields and counted distinct candidate films per collection.
- **Scale:** There are 96 franchise films and 16 standalones across all years. Jaws is represented by one film, despite its 67.236 ratio.
- **Effect on the client's number:** A single strong film can make a sparsely represented collection look attractive. An unlinked film could also affect the small standalone group.
- **What I did about it:** Required at least three usable films for a bundle shortlist and showed the weakest observed ratio alongside the median. The Lord of the Rings has three observed films and a lowest ratio of 9.370.
- **Residual risk:** Collection links and the studio's actual offered titles have not been independently reconciled. A recommendation is conditional on the offered rights and films.

### F-04: High ratios and historical reporting affect the apparent advantage — Severity: Medium

- **What it is:** A few films have unusually high revenue-to-budget ratios; reported financial values have no inflation adjustment and grosses can include re-releases.
- **How I detected it:** Checked numeric and positive financial values, reviewed the five highest and lowest ratios, and compared arithmetic means with medians on the same baseline.
- **Scale:** Zero missing/non-numeric, zero, or negative budgets and revenues; zero invalid release dates among 112 films. Eight ratios exceed the explicit 20-times review threshold. The highest is 70.491.
- **Effect on the client's number:** Using means narrows the franchise lead to 0.256 across all years and 0.510 from 2000 onward, versus median gaps of 1.779 and 1.207. The leader remains franchise under both statistics.
- **What I did about it:** Retained valid extreme observations, used the median for a typical-film comparison, and reported the mean sensitivity. No film-specific re-release contribution was inferred.
- **Residual risk:** Reported gross divided by production budget is not net profit, licensing value, or a forecast of streaming demand; the cash flows and reporting periods are not independently verified.

### F-05: Repeated and malformed input rows distort film weights — Severity: Medium

- **What it is:** The input contains one blank, three invalid-format values, and six repeated numeric rows.
- **How I detected it:** Trimmed whitespace, accepted positive integers, removed leading zeros, identified repeat occurrences, and reconciled every input row in `id_audit.csv`.
- **Scale:** The repeats are `603`, `278`, `1891`, `155`, `550`, and `680`, at source lines 43, 60, 90, 91, 94, and 102. The rejected IMDb-format row `tt0468569` is excluded from the six-repeat scenario.
- **Effect on the client's number:** Counting the six repeats again changes all-years franchise and standalone medians by +0.097406 and -0.606312. Only the repeated `155` meets the 2000 cutoff: recent changes are +0.010022 and 0.000000. Neither window changes leader.
- **What I did about it:** Counted each valid normalized ID once. Separately inspected normalized titles and release years across all 112 films; found zero candidate duplicate groups with distinct IDs.
- **Residual risk:** Different editions or other identities may not be captured by title/year screening alone. Removing repeats changes weights rather than film coverage.

### Measured scenario results

The gap is franchise median minus standalone median. Scenarios are separate;
all calculations use unrounded ratios before displaying three decimals.

| Release window | Scenario | Franchise median | Standalone median | Gap | Leader |
|---|---|---:|---:|---:|---|
| All years | Baseline | 5.624 | 3.845 | +1.779 | Franchise |
| All years | Five missing: low standalone ratio | 5.624 | 2.742 | +2.882 | Franchise |
| All years | Five missing: high standalone ratio | 5.624 | 5.244 | +0.380 | Franchise |
| All years | Count six numeric repeats again | 5.721 | 3.239 | +2.483 | Franchise |
| 2000 onward | Baseline | 5.052 | 3.845 | +1.207 | Franchise |
| 2000 onward | Five missing: low standalone ratio | 5.052 | 2.742 | +2.310 | Franchise |
| 2000 onward | Five missing: high standalone ratio | 5.052 | 5.244 | -0.192 | Standalone |
| 2000 onward | Count eligible numeric repeats again | 5.062 | 3.845 | +1.217 | Franchise |

Each missing-film scenario assumes five additional standalones with usable
ratios. Each receives the observed window-specific standalone minimum or maximum:
1.133659 or 32.416667 across all years; 1.642246 or 14.469742 from 2000 onward.
For the later window, all five hypothetical films are explicitly assumed to
have release dates on or after 2000-01-01. Neither scenario changes the all-years
leader; only the high recent scenario reverses the observed lead.

## Looked wrong, is not wrong

| Apparent problem | Why it looks wrong | Why it is actually fine |
|---|---|---|
| Rejected `tt0468569` | It is a genuine film identifier | The input requires numeric TMDb IDs; the cached IMDb field matches The Dark Knight, already included as `155`, so film coverage is retained |
| Multiple director rows per film | A join can appear to duplicate films | Nine films have co-directors; 122 unique movie–director pairs are retained, while movie-level comparisons still use 112 films |
| Very high ratios | Star Wars and Jaws exceed 60 times budget | High ratios alone do not establish errors; positive cached amounts are retained, with medians and a mean sensitivity check |
| Identical Animation and Family summaries | It can look like duplicated aggregation | Both genre groups contain exactly the same 17 films in this candidate list; genre membership can overlap |

## Could not verify

The five missing films' attributes, completeness of collection links, exact
studio bundle contents, licensing fees, production-budget definitions, and
future streaming demand remain unverified. There is no inflation adjustment.
Grosses can include re-releases, but this cache does not establish which films
received them or the amounts. These gaps prevent a defensible absolute price
ceiling or a claim about streaming profit. I recommend conditional negotiations,
not committing the $14M solely on these historical ratios.

## Transform schema and coercion diagnosis

The details transform preserves movie row order and index. `collection_id` is
nullable `Int64`; `collection_name` is nullable pandas `string`. Missing IDs
mean standalone and force a missing name. Whitespace-only names become missing;
a missing name alone does not remove a present collection ID or change the group.
The current 112 cached records contain 96 collection objects and 16 null
collections, with no blank or missing names among the collection objects.

`flat_movies.attrs["financial_coercion"]` distinguishes original nulls from
non-null values that become missing during numeric conversion. The analysis
command logs both counts separately. For budget and revenue, the current cache
has **0 originally missing and 0 invalid non-null values**. No movie rows are
dropped by conversion; ratios still require positive budget and revenue.

Lead actor selection accepts nonnegative integer billing positions represented
as integers, integral floats, or numeric strings. Missing, boolean, nonnumeric,
nonfinite, negative, and fractional positions are excluded. Ties keep the first
cast entry. All 7,827 cached cast positions are integers, so this broader input
handling changes no current lead actor or analytical output.

The film-level franchise median counts each usable film once. The equal-weight
collection figure is the median of each collection's usable-film median, so each
collection contributes once. The latter includes collections with at least one
usable film; bundle shortlists require at least three usable films in the chosen
release window to limit rankings based on sparse evidence.
