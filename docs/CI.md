# CI & contribution workflow

## Local CI

`scripts/ci` mirrors `.github/workflows/ci.yml` exactly so failures are
reproduced in ~0.7s instead of push-and-wait.

```bash
scripts/ci          # lint + format check + tests (full run)
scripts/ci lint     # ruff check only
scripts/ci format   # ruff format --check only
scripts/ci test     # pytest only
scripts/ci fix      # ruff check --fix + ruff format (mutating)
```

First run creates `.venv` and installs `requirements_test.txt`.

## Pre-push checklist

Before pushing commits intended for a pull request, **in this order**:

1. **Confirm the target PR is still open.**

   ```bash
   gh pr view <N> --json state,headRefOid
   ```

   If it reports `"state": "MERGED"`, do **not** push to that branch —
   commits would be stranded (no CI runs, content never reaches `main`).
   Branch off the current `HEAD` and open a new PR instead.

2. **Run local CI and require a clean pass.**

   ```bash
   bash scripts/ci
   ```

   Only push if it ends with `==> OK`.

3. Push, then verify remote checks were triggered:

   ```bash
   gh run list --branch <branch> --limit 3
   ```

## What local CI does *not* cover

`scripts/ci` runs ruff + pytest only. It does **not** run hassfest or the
HACS action. Entity `device_class` / `state_class` / unit-of-measurement
combinations and manifest/translation validity are only checked by the
**Validate** workflow remotely (`home-assistant/actions/hassfest` +
`hacs/action`). After changing any of those, watch the Validate run on the
PR — a green `scripts/ci` is necessary but not sufficient.
