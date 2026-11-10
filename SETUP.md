# Setup and current status

## Run locally

Requires Python 3.9 or later. Run these commands from the repository folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python download_data.py --data-dir data
```

The download includes four metadata CSV files and 122 per-game tracking files (approximately 850 MB of tracking data). Raw data and generated exploratory results are excluded from Git.

## Experimental analysis

`analyze.py` is an initial exploration, not a validated model or final submission. It can generate play-level timing records and candidate receiver windows:

```bash
python analyze.py --data-dir data --out-dir results
```

It uses exact `ball_snap` and `pass_forward` events at 10 Hz, excludes penalized plays and non-attempts, and retains incomplete and intercepted pass attempts when event markers are available. Missing or ambiguous markers are reported in the audit rather than guessed. Receiver-target identity is inferred from abbreviated names in play descriptions and must be validated before using target-specific results.

The current candidate window definition is at least 2 yards from the nearest defender, sustained for at least 0.3 seconds, between 0 and 10 yards beyond the snap location and at least 0.5 seconds after the snap. These are provisional geometric choices, not established definitions of openness, route type, or catch probability. Windows stop at release; a receiver without an observed window may have a route that was cut off by an earlier throw. Raw window rates are not context-adjusted player rankings.

## Work sequence

1. Agree on the exact football question and intended audience.
2. Inspect actual plays and manually verify event timing, coordinates, roles, and target matching.
3. Agree on short-pass and receiver-window definitions; account for missing observations and differing route responsibilities.
4. Test a small, comparable sample and examine whether any pattern is meaningful.
5. Build the visualization around a validated finding and show sample sizes and limitations.
6. Verify a clean run, finalize the 3–5 sentence README, and prepare the public submission URL.

Current stage: initial exploration exists; manual measurement validation and question confirmation are next. No finished dashboard or final finding has been produced.
