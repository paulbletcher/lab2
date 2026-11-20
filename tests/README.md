# Offline regression checks

Run from the repository root after installing `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

These checks require no API key, local input CSV, or TMDb cache. HTTP and retry
waits are mocked. Databases, validation inputs, snapshots, and reports are created
in temporary directories and cleaned up by the tests. The real analysis outputs
and cache are never written by this suite. No additional test package is needed.

- `test_acquisition.py` checks cache reuse, retries, `Retry-After`, immediate
  404/401/403 handling, exhausted 429, sanitized errors, atomic audit writes,
  complete audit coverage after a fatal stop, and cache reuse on resumption.
- `test_workflow.py` checks import safety, ID normalization from a different
  working directory, disabled notebook live requests, and the public shortlist
  `snapshot` and `compare` commands.
- `test_transforms.py` checks film/index alignment, absent collections, empty
  credits, tied billing order, and repeated/co-director credits.

## Synthetic shortlist fixtures

`fixtures/shortlists/baseline/` and `fixtures/shortlists/current/` contain the
minimal ID, title, and ratio columns consumed by the report. They are controlled
test inputs, not a new acquisition or revised recommendation. Only the current
all-years standalone fixture differs from its baseline:

| Title | Controlled change |
|---|---|
| Pulp Fiction | Ratio 26.74 to 27.00, retaining rank 2 |
| Spirited Away | Rank 4 to 3, retaining its ratio |
| SYNTHETIC Example Film | Added at rank 4 with ratio 14.00 |
| Schindler's List | Removed from its prior rank 3 |

The other three sections remain unchanged. The test verifies the exact output
rows and sections and checks that an existing report cannot be overwritten.
