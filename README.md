# Beat the Clock

Beat the Clock is a Python project for the NFL Big Data Bowl — NYU Edition, exploring how quarterback throwing time relates to receiving opportunities for wide receivers (WR), tight ends (TE), and running backs (RB).
The current tool compares sustained receiver separation windows with a quarterback's typical short-pass release time estimated from other games, and includes throwing-time distributions and three actual tracking replays.
It uses the event's public 2021 Weeks 1–8 tracking and PFF data, measuring snap-to-release time from tagged events and identifying short passes from play-description labels rather than total yards gained.
Initial descriptive results show a median release time of 2.5 seconds without play action versus 3.1 seconds with play action, illustrating why one average throwing clock can hide different receiving situations.
The receiver-timing view distinguishes observed windows from fully observed no-window cases and unresolved observations; its provisional geometric definitions do not establish receiver quality, a safe throw, catch probability, or a causal finding.

## The football question

**Do receivers create sustained separation within the time their quarterback typically takes to throw in comparable situations?**

The intended audience is a coach or analyst reviewing how receiver movement fits the offense's throwing rhythm. The current version adds a descriptive alignment measurement to the throwing-time baseline and actual-play replays; it does not recommend whom the QB should have targeted or infer what an unobserved route would have done.

## Work completed so far

- Downloaded all **122 per-game tracking files** and the four metadata files: games, players, plays, and PFF scouting data.
- Built and rerun a Python pipeline that joins player roles and play context, normalizes playing direction, measures tagged snap-to-release time, and calculates nearest-defender separation.
- Added explicit exclusion counts for non-attempts, penalties, missing or ambiguous events, and missing scrimmage-line metadata.
- Corrected target-name matching, including formats such as `Dj.Moore`, `Mi.Carter`, and compound surnames; ambiguous or unmatched targets remain missing.
- Corrected the scrimmage-line reference: the ball may already have moved toward the QB at the tagged snap, so the pipeline now uses play metadata.
- Independently checked three real plays against raw CSV rows, covering completed, incomplete, quick, and delayed short throws, and both playing directions.
- Passed **12 tests** covering measurement correctness, target matching, windows ending at observation, early-release censoring, insufficient reference samples, and exclusion of the evaluated game from the QB reference.
- Built a self-contained dashboard with release-time charts, target-role comparisons, receiver/QB tables, three animated replays, and methods/exclusion notes.
- Browser-checked the filters and all three replays; checked one filtered result against Python calculations.
- Added the receiver-window view for **25,082 receiver–play observations**, including untargeted route runners, with explicit unknown cases and minimum/maximum ranges rather than a player-quality leaderboard.
- Created this public repository and opened the local project in Kiro with project context in `.kiro/steering/`.

## Current descriptive results

The corrected local run retains **6,889 pass attempts**, including **5,436 short-labeled attempts**, from 8,557 tracked plays across 122 games.

| Measurement | Observed value |
|---|---:|
| Mean short-pass release time | 2.78 seconds |
| Median short-pass release time | 2.60 seconds |
| Short passes released at least 3 seconds after the snap | 1,742 / 5,436 (32.0%) |
| Median without play action | 2.50 seconds; 4,286 attempts |
| Median with play action | 3.10 seconds; 1,150 attempts |
| Short-pass targets matched to a unique WR/TE/RB | 5,204 / 5,436 (95.7%) |

Play action means a fake handoff before the pass. Its timing difference is descriptive: formation, route assignment, coverage, quarterback, and game situation also vary between groups. The three-second cutoff summarizes the distribution; it is not an established definition of a quick pass or a checkdown.

## Real plays checked

All three examples are from Dallas at Tampa Bay on September 9, 2021, and are labeled short passes against Cover-3 zone.

| Play ID | Quarterback → target | Tagged release time | Outcome |
|---|---|---:|---|
| 187 | Dak Prescott → Dalton Schultz (TE) | 2.2 seconds | Complete, 5 total yards |
| 1425 | Dak Prescott → Blake Jarwin (TE) | 5.6 seconds | Complete, 6 total yards |
| 434 | Tom Brady → Mike Evans (WR) | 1.7 seconds | Incomplete |

The checks confirm 11 offensive players, 11 defenders, and the ball in each inspected frame, continuous snap-to-release frames, named targets, coordinate normalization, and agreement with bulk-pipeline measurements. In play 187, automatic and tagged release markers differ by **0.2 seconds**; that annotation uncertainty is retained rather than hidden. Evans has approximately **6.02 yards** of nearest-defender separation at tagged release in play 434, yet the pass is incomplete—an example of why distance alone does not predict a successful catch.

## Receiver windows within the QB clock

For each short-pass play, the reference is the QB's median short-pass release time in **other games**, with at least 20 attempts in the reference group. Matching first uses QB + play action + coverage family, then explicitly falls back to QB + play action or QB overall if necessary. If none has enough attempts, the reference remains unavailable. Because other games can occur later in the season, this is a historical descriptive comparison, not a live forecast.

A provisional window requires at least 2 yards from the nearest defender for at least 0.3 seconds, between 0 and 10 yards beyond the starting line and at least 0.5 seconds after the snap. A window must be observed before both the reference clock and the actual release. If release ends the observation early without a qualifying window, the case remains unknown. Behind-line and deep-route duties can fall outside this definition, so comparisons remain descriptive.

| Status across all receiver–play observations | Count |
|---|---:|
| Window observed before the reference clock | 15,609 |
| No qualifying window, continuously observed through the clock | 4,498 |
| Unresolved because observation ends early or has missing tracking | 3,921 |
| Insufficient other-game QB reference | 1,054 |

For example, Dallas WRs have 297 observed windows, 47 fully observed no-window cases, and 46 unresolved cases across 390 observations. The dashboard displays the resulting 76.2–87.9% possible range instead of counting every unknown as failure; this is a missing-observation range, not a confidence interval or a fair ranking of receiver skill. See [the measurement definition](ALIGNMENT.md).

## What is still unfinished

- Assess sensitivity of the provisional distance, duration, and depth thresholds before making stronger football claims.
- Account more fully for route responsibility and differences in observed receiving situations; the current method exposes early-release censoring rather than guessing missing routes.
- Check whether patterns hold within quarterback, coverage, receiving role, and other context rather than relying on pooled averages.
- Select a defensible original insight and refine the dashboard around it.
- Finish the public hosted output and final competition submission.

## Repository versus local prototype

The prototype includes the dashboard source, generated `docs/index.html`, corrected analysis, receiver-window comparison, and tests. It is a working descriptive tool with provisional measurement choices, not the final competition submission. Generated bulk results and raw data are excluded from Git; the dashboard embeds its own analyzed values and three replay examples. Original pre-validation results are archived locally and must not be used for receiver conclusions.

The dashboard consists of `build_dashboard.py`, `dashboard.html`, and the generated [docs/index.html](docs/index.html); it embeds the analyzed data and Plotly runtime so it can open without external chart requests. Download/open that HTML file, or serve `docs/` locally using the [setup instructions](SETUP.md). The source analysis uses Python, pandas, and NumPy. The project is open in Kiro with current context in its steering folder; public hosting is still pending.

## Assumptions and limitations

- “Short pass” is a description label, not a route classification or a precise air-yard measurement.
- Time to throw is `(pass_forward frame − ball_snap frame) / 10`, using tagged events at the documented 10 Hz; rounded timestamp strings are not used as a finer clock.
- The retained sample excludes penalized plays, sacks, scrambles, and other non-attempts, as well as unusable event/line metadata; it is not every offensive play.
- Target-specific views exclude unmatched targets and positions outside WR/TE/RB. Matching is text-based and remains a limitation despite checks.
- Nearest-defender distance is not assigned coverage responsibility, a clear passing lane, or catch probability.
- We cannot infer the quarterback's intended reads, prove a missed throw, identify a checkdown from timing alone, or claim that play action causes the observed delay.
- The data is historical, from 2021 Weeks 1–8; results are not current player ratings.

[Setup instructions](SETUP.md) · [First-play validation notes](validation/README.md) · [Event dataset and documentation](https://github.com/ThompsonJamesBliss/nfl-big-data-bowl-regional-event-data)
