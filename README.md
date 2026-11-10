# Beat the Clock

Beat the Clock is a Python dashboard that checks whether NFL wide receivers create a sustained separation window on short passes before their quarterback's usual throw time, using 2021 Weeks 1–8 tracking and PFF data (122 games). A window means at least 2 yards from every defender, 0–10 yards past the line of scrimmage, for at least 0.3 seconds, before the QB's median short-pass release time taken from his *other* games. Among resolved WR route observations, a window was measured on **93% against zone coverage (8,744 resolved of 9,733)** versus **68% against man coverage (2,955 resolved of 4,035)**; counting every unresolved case as no or yes gives ranges of 83–94% for zone and 50–77% for man, so the gap holds even under the most favourable assumption for man. A coach or analyst can use this to plan quick-game answers for man-heavy opponents, and real-play replays show exactly what the measurement sees on the field. This is a descriptive association on geometric space before the throw, not catch probability, receiver talent, or proof that coverage alone causes the gap.

**Live dashboard:** https://rahul0311.github.io/beat-the-clock-nfl/ · **Screenshot:** [docs/overview.png](docs/overview.png)

## Methods
- Time to throw = (tagged `pass_forward` frame − tagged `ball_snap` frame) / 10. Coordinates are normalized so every offense moves the same direction.
- Short passes come from play-description labels (5,436 attempts), not yards gained. Coverage (man/zone) comes from PFF.
- Each WR route runner on a short pass is checked, targeted or not. One pass with three WRs gives three observations.
- Each route is sorted into: window measured, no window while tracking ran through the QB's usual time, or unknown (the ball was thrown before that time, tracking was missing, or the QB had fewer than 20 other-game attempts). See [ALIGNMENT.md](ALIGNMENT.md).
- 12 unit tests cover timing, target matching, windows, censoring, and the other-game reference. Three replays were checked by hand against raw CSV rows.

## Sensitivity
Re-running the window at 1.5, 2.0, and 2.5 yards keeps zone well above man for resolved WR routes. **This check covers only the first 40 games (Weeks 1–3)**, not Weeks 4–8.

## Limitations
- Percentages are among resolved observations. Unknown cases are shown, not dropped silently.
- Man and zone plays also differ in down, distance, opponent, and QB. This analysis does not adjust for those.
- RBs and TEs are excluded from the headline. The 0–10 yard window leaves out behind-the-line outlets, so low RB numbers reflect the definition, not receiving ability.
- Nearest-defender distance is not the assigned coverage defender, a clear throwing lane, or catch probability. Evans is 6 yards clear on one replay and the pass is incomplete.
- Data is 2021 Weeks 1–8 only.

## Run it
See [SETUP.md](SETUP.md). In short: `python download_data.py`, `python analyze.py --out-dir results/corrected`, `python build_dashboard.py`, then open `docs/index.html`.
