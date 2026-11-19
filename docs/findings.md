## Step 1: CSV ID validation

Verified locally using `explore/inspect_ids.ipynb` against `data/id_list.csv` (column: `tmdb_id`).

| Measure | Count |
| --- | ---: |
| Observed data rows | 127 |
| Blank or whitespace-only rows | 1 |
| Malformed nonblank rows | 3 |
| Extra duplicate valid rows | 6 |
| Distinct valid IDs | 117 |

Reconciliation passed: 127 = 1 + 3 + 6 + 117.

Validation strips surrounding whitespace, accepts only ASCII digits representing positive whole numbers, and removes leading zeros before counting duplicates. Extra duplicate rows exclude the first occurrence of each valid ID. Original values and row positions remain available in the notebook's working table.

Overlap between sources is a possible explanation for duplicates. The CSV has no source column, so their origin is unknown.

The original CSV was left unchanged. No API calls were made. Notebook outputs were cleared before saving.
