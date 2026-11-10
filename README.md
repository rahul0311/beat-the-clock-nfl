# Beat the Clock

Beat the Clock is a Python project for the NFL Big Data Bowl — NYU Edition, exploring how quarterback throwing time relates to receiving opportunities for wide receivers (WR), tight ends (TE), and running backs (RB).
The current working prototype compares short-pass release-time distributions, receiver separation at release, and three actual tracking replays, with filters for quarterback, coverage family, and target position.
It uses the event's public 2021 Weeks 1–8 tracking and PFF data, measuring snap-to-release time from tagged events and identifying short passes from play-description labels rather than total yards gained.
Initial descriptive results show a median release time of 2.5 seconds without play action versus 3.1 seconds with play action, illustrating why one average throwing clock can hide different receiving situations.
These associations are not player-quality ratings or causal findings, separation does not establish a safe throw or catch probability, and the planned receiver–quarterback timing-alignment metric is not yet complete.

## The football question

**Do receivers create sustained separation within the time their quarterback typically takes to throw in comparable situations?**

The intended audience is a coach or analyst reviewing how receiver movement fits the offense's throwing rhythm. The first version establishes the throwing-time baseline and lets users inspect spacing on actual plays; it does not yet answer the full alignment question or recommend whom the QB should have targeted.

## Work completed so far

- Downloaded all **122 per-game tracking files** and the four metadata files: games, players, plays, and PFF scouting data.
- Built and rerun a Python pipeline that joins player roles and play context, normalizes playing direction, measures tagged snap-to-release time, and calculates nearest-defender separation.
- Added explicit exclusion counts for non-attempts, penalties, missing or ambiguous events, and missing scrimmage-line metadata.
- Corrected target-name matching, including formats such as `Dj.Moore`, `Mi.Carter`, and compound surnames; ambiguous or unmatched targets remain missing.
- Corrected the scrimmage-line reference: the ball may already have moved toward the QB at the tagged snap, so the pipeline now uses play metadata.
- Independently checked three real plays against raw CSV rows, covering completed, incomplete, quick, and delayed short throws, and both playing directions.
- Passed **six measurement tests** covering name matching, ambiguous names, short-pass labels, missing frames, and windows ending at the last observation.
- Built a self-contained dashboard with release-time charts, target-role comparisons, receiver/QB tables, three animated replays, and methods/exclusion notes.
- Browser-checked the filters and all three replays; checked one filtered result against Python calculations.
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

## What is still unfinished

- Define and validate the central receiver–QB timing-alignment measurement across comparable situations.
- Account for route responsibility and observation ending when the ball is released; a receiver with no observed window is not automatically a poor performer.
- Check whether patterns hold within quarterback, coverage, receiving role, and other context rather than relying on pooled averages.
- Select a defensible original insight and refine the dashboard around it.
- Finish the public hosted output and final competition submission.

## Repository versus local prototype

The prototype includes the dashboard source, generated `docs/index.html`, corrected analysis, and measurement tests. It is a working descriptive baseline, not the completed timing-alignment feature or final competition submission. Generated bulk results and raw data are excluded from Git; the compact dashboard embeds its own analyzed values and three replay examples. Original pre-validation results are archived locally and must not be used for receiver conclusions.

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
