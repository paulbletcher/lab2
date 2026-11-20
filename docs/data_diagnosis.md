# Supporting data diagnosis

The submission-format account is [Data findings](../data_findings.md).
This document retains the detailed local evidence and sensitivity results.

## Acquisition coverage

**Finding.** TMDb returned HTTP 404 for both the movie details and credits requests for five of the 117 validated IDs. I excluded those five IDs, leaving 112 films in the analysis (95.7% of validated IDs).

| TMDb ID   | Movie details and credits outcome |
| --------- | --------------------------------- |
| `8471293` | HTTP 404                          |
| `9412887` | HTTP 404                          |
| `8471294` | HTTP 404                          |
| `9412888` | HTTP 404                          |
| `7733901` | HTTP 404                          |

**How it was detected.** I filtered `data/cache/fetch_audit.csv` for
requests that did not succeed and checked the status for each ID.

**Impact on the recommendation.** Without movie details, I could not
classify these five films or calculate their revenue-to-budget ratios.
Their actual effect is unknown. The measured scenarios below show how the
comparison changes under explicit assumptions about their group, ratios,
and release dates; they do not recover the missing records.

**Reconciliation.** Of the 127 input rows, 1 was blank, 3 failed ID
validation, and 6 were duplicates. Of the 117 distinct IDs requested,
5 had unavailable movie details and 112 entered the analysis.

I checked all 112 acquired films for distinct TMDb IDs sharing a normalized title and release year. The check found zero candidate duplicate groups. I also matched the rejected IMDb ID tt0468569 to The Dark Knight, already included as TMDb ID 155. Rejecting that row therefore did not reduce film coverage. It remains one of the three invalid-format rows in the input audit because the input expects TMDb IDs.

## Findings ranked by impact on the licensing decision

Ranks follow F-01 through F-05 in [Data findings](../data_findings.md).

| Rank | Finding                                                           | How I detected it                                                                  | Impact on the decision                                                                                                                                                        |
| ---- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Five validated IDs had unavailable movie details.                 | I checked the fetch audit and ran low/high standalone-ratio scenarios.             | The high-ratio scenario reverses the 2000-onward lead if all five missing films are standalone and meet the cutoff. Their actual attributes remain unknown.                   |
| 2    | The franchise shortlist is sensitive to the release-year cutoff.  | I reranked franchises using only films released from 2000 onward.                  | Star Wars led across all years. The Lord of the Rings led from 2000 onward. Franchises still had the higher median in both windows.                                           |
| 3    | Some collections are represented by very few films.               | I counted the candidate films with usable ratios in each collection. Jaws had one. | Its 67.24× ratio reflects one film. I required at least three films with usable ratios for the main franchise shortlist. The studio’s actual bundle still needs confirmation. |
| 4    | High ratios and historical reporting affect the apparent advantage. | I reviewed the financial-quality checks, extreme ratios, and mean-versus-median comparison. | Eight ratios exceed 20 times budget. Franchises lead under both means and medians, but the gap changes. Figures have no inflation adjustment, and grosses can include re-releases. |
| 5    | The input contained a blank row, malformed IDs, and repeated IDs. | I checked for blanks, positive-integer IDs, and repeat occurrences.                | Four rows could not be used as supplied. Removing six repeat occurrences prevented those films from being counted twice.                                                      |

## Sensitivity to missing records and repeated rows

I ran the notebook's new sensitivity cells against the local SQLite cache,
validated IDs, `fetch_audit.csv`, and `id_audit.csv`. The 112 cached films reproduce
the pipeline's movie data and `flatten_movie_details()` calculations. Franchise
medians here weight each film equally, rather than each collection. All-years
coverage is 96 franchise films and 16 standalones; from 2000 onward it is 63 and 8.
Ratios are usable only when both budget and revenue are positive.

Each missing-record scenario adds five hypothetical standalones to the observed
sample, with every added ratio equal to the lowest or highest usable standalone
ratio observed **in that window**. The all-years inputs are 1.133659 and 32.416667;
the 2000-onward inputs are 1.642246 and 14.469742. For the later window, **all five
hypothetical films are assumed to meet the 2000 release cutoff**. Their franchise
membership, financial values, and release dates are unknown, so these are scenarios
under stated assumptions, not estimates of the missing films or universal bounds.
The missing-record and repeated-row scenarios are separate tests.

The gap below is franchise minus standalone median. Values are rounded to three
decimals after calculation using the full ratios; a positive gap favors franchises.

| Release window | Scenario                             | Franchise median | Standalone median |    Gap | Leader     |
| -------------- | ------------------------------------ | ---------------: | ----------------: | -----: | ---------- |
| All years      | Baseline                             |            5.624 |             3.845 | +1.779 | Franchise  |
| All years      | Five missing: low standalone ratio   |            5.624 |             2.742 | +2.882 | Franchise  |
| All years      | Five missing: high standalone ratio  |            5.624 |             5.244 | +0.380 | Franchise  |
| All years      | Count six numeric repeats again      |            5.721 |             3.239 | +2.483 | Franchise  |
| 2000 onward    | Baseline                             |            5.052 |             3.845 | +1.207 | Franchise  |
| 2000 onward    | Five missing: low standalone ratio   |            5.052 |             2.742 | +2.310 | Franchise  |
| 2000 onward    | Five missing: high standalone ratio  |            5.052 |             5.244 | -0.192 | Standalone |
| 2000 onward    | Count eligible numeric repeats again |            5.062 |             3.845 | +1.217 | Franchise  |

Neither missing-record scenario changes the all-years leader. In the later
window, the low-ratio scenario preserves the franchise lead, while the high-ratio
scenario reverses it: standalones lead by 0.192. Five additions have more influence
on the eight observed recent standalones than on the 16-film all-years sample.

The six repeated numeric rows come from audit source lines 43, 60, 90, 91, 94,
and 102: `603` (The Matrix), `278` (The Shawshank Redemption), `1891` (The Empire
Strikes Back), `155` (The Dark Knight), `550` (Fight Club), and `680` (Pulp Fiction).
I applied the validator's whitespace trimming, positive-integer rule, and removal
of leading zeros before matching IDs. Each repeat adds one copy of the actual
cached film, retaining its group and release date. The rejected IMDb-format row
`tt0468569` is outside this test; it is not counted as a seventh numeric repeat.

Across all years, three extra franchise rows and three extra standalone rows
raise the franchise median by **0.097406** and lower the standalone median by
**0.606312**. Only The Dark Knight's repeated row meets the 2000 cutoff; it raises
the recent franchise median by **0.010022**, with **0.000000** change for standalones.
Neither duplicate scenario changes the leader. Counting repeated rows would
weight those films more heavily without adding any new movie coverage, supporting
the pipeline's decision to deduplicate.

For Kwame, the observed medians support prioritizing franchise discussions, but
the recent advantage is conditional on incomplete coverage and a small standalone
sample. He should assess individual titles, bundle terms, licensing costs, and
expected streaming demand before deciding; the high recent scenario shows why
the missing records could matter.

## Financial values and unusually high ratios

The new cells rechecked the notebook's financial-quality observations against
all **112** acquired films:

| Check                           | Films affected |
| ------------------------------- | -------------: |
| Budget missing or non-numeric   |              0 |
| Budget is zero                  |              0 |
| Revenue missing or non-numeric  |              0 |
| Revenue is zero                 |              0 |
| Negative budget                 |              0 |
| Negative revenue                |              0 |
| Release date missing or invalid |              0 |

All **112** films have usable revenue-to-budget ratios; none is excluded by these
financial checks. As an explicit review threshold, **8** films have ratios above
20 times budget. The five highest cached ratios are Star Wars (**70.491**),
Jaws (**67.236**), The Godfather (**40.844**), The Good, the Bad and the Ugly
(**32.417**), and The Empire Strikes Back (**29.911**). High ratios alone do not
establish data errors, so these records remain in the median calculations.

The reported figures have **no inflation adjustment**, and grosses can include
re-releases. The local cache does not establish which films' grosses include
re-release revenue or how much, so no film-specific re-release claim is made.
These are reported box-office revenues relative to production budgets, not net
profit or expected streaming returns.

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
