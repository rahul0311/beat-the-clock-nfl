# Beat the Clock

Beat the Clock is a Python tool for the NFL Big Data Bowl — NYU Edition that measures whether wide receivers (WR), tight ends (TE), and running backs (RB) get open *within the time their quarterback actually takes to throw*, using public 2021 Weeks 1–8 tracking and PFF data. For every short pass it builds the QB's typical release time from his **other** games, then checks whether each route runner reached a sustained 2-yard window in the short zone before that clock — turning raw tracking into a coverage-by-position openness map a coach can act on.
**The headline finding:** short-game separation is driven far more by coverage than by position. Against zone coverage, WRs reach an open window **92.8%** of resolved plays and TEs **86.9%**; against man coverage both fall sharply (WR **67.9%**, TE **69.3%**), while RBs rarely create a downfield short window in either look (**26.9–31.7%**) because their outlets sit at or behind the line. The WR > TE > RB ordering holds at 1.5, 2.0, and 2.5-yard definitions of "open," so it is not an artifact of one threshold.
A coach or analyst uses this to set quick-game expectations by coverage: against man, lean on scheme (motion, picks, play action) rather than expecting receivers to win one-on-one; against zone, the quick game opens up for both WRs and TEs. The tool ships as a self-contained dashboard with the headline chart, a throwing-time baseline, and three independently checked tracking replays.
These are descriptive associations on geometric space before the throw. Separation is **not** catch probability, coverage responsibility, or a ranking of receiver talent — a receiver can be wide open and the pass still fall incomplete (shown in the Brady → Evans replay).

## The football question

**Do receivers create sustained separation within the time their quarterback typically takes to throw — and does that depend more on position or on coverage?**

The intended audience is a coach or analyst reviewing how receiver movement fits the offense's throwing rhythm against a given coverage. The tool reports a coverage-by-position openness map, a throwing-time baseline, and actual-play replays; it does not recommend whom the QB should have targeted or infer what an unobserved route would have done.

## The headline: coverage decides who gets open

For each short pass, we estimate the QB's typical release time from his **other** games (the "clock"), then check whether each WR/TE/RB route runner reached a sustained 2-yard window in the 0–10 yard zone before that clock. The **resolved open-rate** below counts only plays the tracking runs long enough to judge (window observed vs. fully observed with no window); unresolved and no-reference cases are excluded from the rate and reported separately.

| Coverage | WR | TE | RB |
|---|---:|---:|---:|
| **Zone** | 92.8% (n=8,744) | 86.9% (n=3,421) | 31.7% (n=1,964) |
| **Man** | 67.9% (n=2,955) | 69.3% (n=1,132) | 26.9% (n=629) |

(n = resolved receiver–play observations, full 122-game season.) Against zone, receivers win space often; against man, both WRs and TEs drop roughly 20–25 points. RBs rarely create a downfield short window in either coverage because their outlets sit at or behind the line, outside this regional window by design.

### Sensitivity: does it survive a different definition of "open"?

The 2-yard cutoff is a modeling choice, so we re-ran the window at 1.5, 2.0, and 2.5 yards on a stated 40-game sample (8,245 short receiver–plays). The WR > TE > RB ordering holds at every threshold, so the ranking is robust, not an artifact of one cutoff.

| Position | 1.5 yd | 2.0 yd | 2.5 yd |
|---|---:|---:|---:|
| WR | 91.4% | 86.0% | 82.1% |
| TE | 84.1% | 79.7% | 73.9% |
| RB | 28.0% | 26.9% | 26.0% |

The zone-beats-man gap for both WR and TE also persists at every threshold. One fragile pattern did **not** survive and is deliberately not claimed: whether TE edges WR against man flips with the threshold (TE only leads at exactly 2.0 yd), so we report the coverage effect, not a within-man position winner.

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

## Work completed so far

- Downloaded all **122 per-game tracking files** and the four metadata files: games, players, plays, and PFF scouting data.
- Built and rerun a Python pipeline that joins player roles and play context, normalizes playing direction, measures tagged snap-to-release time, and calculates nearest-defender separation.
- Added explicit exclusion counts for non-attempts, penalties, missing or ambiguous events, and missing scrimmage-line metadata.
- Corrected target-name matching, including formats such as `Dj.Moore`, `Mi.Carter`, and compound surnames; ambiguous or unmatched targets remain missing.
- Corrected the scrimmage-line reference: the ball may already have moved toward the QB at the tagged snap, so the pipeline now uses play metadata.
- Independently checked three real plays against raw CSV rows, covering completed, incomplete, quick, and delayed short throws, and both playing directions.
- Passed **12 tests** covering measurement correctness, target matching, windows ending at observation, early-release censoring, insufficient reference samples, and exclusion of the evaluated game from the QB reference.
- Added the receiver-window view for **25,082 receiver–play observations**, including untargeted route runners, with explicit unknown cases and minimum/maximum ranges rather than a player-quality leaderboard.
- Added the **coverage-by-position openness map** (headline chart) and a **1.5 / 2.0 / 2.5-yard threshold sensitivity check** confirming the WR > TE > RB ordering is stable.
- Built a self-contained dashboard with the headline matchup chart, release-time charts, target-role comparisons, receiver/QB tables, three animated replays, and methods/exclusion notes.
- Created this public repository and opened the local project in Kiro with project context in `.kiro/steering/`.

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

- Account more fully for route responsibility and differences in observed receiving situations; the current method exposes early-release censoring rather than guessing missing routes.
- Extend the threshold sensitivity check (currently 40 games) and the coverage breakdown to the full season and to duration/depth parameters.
- Finish the public hosted output and final competition submission.

## Repository versus local prototype

The prototype includes the dashboard source, generated `docs/index.html`, corrected analysis, receiver-window comparison, coverage matchup, and tests. It is a working descriptive tool with provisional measurement choices. Generated bulk results and raw data are excluded from Git; the dashboard embeds its own analyzed values and three replay examples. Original pre-validation results are archived locally and must not be used for receiver conclusions.

The dashboard consists of `build_dashboard.py`, `dashboard.html`, and the generated [docs/index.html](docs/index.html); it embeds the analyzed data and Plotly runtime so it can open without external chart requests. Download/open that HTML file, or serve `docs/` locally using the [setup instructions](SETUP.md). The source analysis uses Python, pandas, and NumPy. Public hosting is pending.

## Assumptions and limitations

- “Short pass” is a description label, not a route classification or a precise air-yard measurement.
- The resolved open-rate excludes unresolved and no-reference plays; it is a rate among judgeable plays, not a share of all route runners. Coverage-family labels (man/zone) come from PFF.
- Time to throw is `(pass_forward frame − ball_snap frame) / 10`, using tagged events at the documented 10 Hz; rounded timestamp strings are not used as a finer clock.
- The retained sample excludes penalized plays, sacks, scrambles, and other non-attempts, as well as unusable event/line metadata; it is not every offensive play.
- Target-specific views exclude unmatched targets and positions outside WR/TE/RB. Matching is text-based and remains a limitation despite checks.
- Nearest-defender distance is not assigned coverage responsibility, a clear passing lane, or catch probability.
- We cannot infer the quarterback's intended reads, prove a missed throw, identify a checkdown from timing alone, or claim that play action causes the observed delay.
- The data is historical, from 2021 Weeks 1–8; results are not current player ratings.

[Setup instructions](SETUP.md) · [Measurement definition](ALIGNMENT.md) · [First-play validation notes](validation/README.md) · [Event dataset and documentation](https://github.com/ThompsonJamesBliss/nfl-big-data-bowl-regional-event-data)
