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

## Build and view the current dashboard

To view the included self-contained prototype without downloading the dataset:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Open `http://127.0.0.1:8765/`. The included HTML embeds the analysis values, Plotly runtime, and three checked replays; no external chart requests are needed.

To regenerate it from source after installing dependencies and obtaining the data:

```bash
python analyze.py --data-dir data --out-dir results/corrected
python inspect_play.py --data-dir data --play-id 187 --output validation/play-187.json
python inspect_play.py --data-dir data --play-id 1425 --output validation/play-1425.json
python inspect_play.py --data-dir data --play-id 434 --output validation/play-434.json
python -m unittest discover -s tests -v
python build_dashboard.py --results results/corrected --output docs/index.html
```

Current stage: the dashboard includes the throwing-time baseline, receiver-window alignment, and three checked replays. Twelve tests pass. `build_dashboard.py` calls `alignment.py` to construct other-game QB clocks and explicit unresolved cases; it writes ignored `alignment.csv` and `alignment-audit.json` beside the corrected results. See [ALIGNMENT.md](ALIGNMENT.md) for definitions and limitations. Remaining work includes threshold/context sensitivity, final story selection, hosting, and submission. Original bulk outputs are archived under ignored `results/before-validation/` and must not be used for receiver conclusions.
