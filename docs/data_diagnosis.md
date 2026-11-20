## Acquisition coverage

**Finding.** TMDb returned HTTP 404 for the movie details request for
five of the 117 validated IDs. These five IDs were excluded, leaving
112 films in the analysis (95.7% of validated IDs).

| TMDb ID   | Movie details outcome |
| --------- | --------------------- |
| `8471293` | HTTP 404              |
| `9412887` | HTTP 404              |
| `8471294` | HTTP 404              |
| `9412888` | HTTP 404              |
| `7733901` | HTTP 404              |

**How it was detected.** I filtered `data/cache/fetch_audit.csv` for
requests that did not succeed and checked the status for each ID.

**Impact on the recommendation.** Without movie details, I could not
classify these five films or calculate their revenue-to-budget ratios.
I cannot tell whether including them would widen or narrow the gap
between franchises and standalones.

**Reconciliation.** Of the 127 input rows, 1 was blank, 3 failed ID
validation, and 6 were duplicates. Of the 117 distinct IDs requested,
5 had unavailable movie details and 112 entered the analysis.

## Findings ranked by impact on the licensing decision

| Rank | Finding                                                           | How I detected it                                                                  | Impact on the decision                                                                                                                                                        |
| ---- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | The franchise shortlist is sensitive to the release-year cutoff.  | I reranked franchises using only films released from 2000 onward.                  | Star Wars led across all years. The Lord of the Rings led from 2000 onward. Franchises still had the higher median in both windows.                                           |
| 2    | Some collections are represented by very few films.               | I counted the candidate films with usable ratios in each collection. Jaws had one. | Its 67.24× ratio reflects one film. I required at least three films with usable ratios for the main franchise shortlist. The studio’s actual bundle still needs confirmation. |
| 3    | Five validated IDs had unavailable movie details.                 | I checked HTTP outcomes in the acquisition audit.                                  | The analysis covers 112 of 117 validated IDs. The effect of the five excluded films on the comparison is unknown.                                                             |
| 4    | The input contained a blank row, malformed IDs, and repeated IDs. | I checked for blanks, positive-integer IDs, and repeat occurrences.                | Four rows could not be used as supplied. Removing six repeat occurrences prevented those films from being counted twice.                                                      |
