# First real-play measurement check

## Example

- Game: Dallas at Tampa Bay, September 9, 2021 (`gameId=2021090900`).
- Play: `187`, first quarter, 12:23, second down with six yards to go.
- QB: Dak Prescott. Named target: Dalton Schultz (TE).
- Play description: short middle pass, completed for five total yards.
- PFF coverage: Cover-3 / Zone. No hurry, hit, or sack credited in this play's scouting rows.

`play-187.json` is an extracted, normalized copy of this play's snap-to-release tracking, produced by `inspect_play.py`. It contains every observed player/ball position for these 23 frames and the source event markers. It does not include the catch; the completion and total yardage come from the play metadata, not a reconstructed catch.

## Measurements verified against CSV rows

| Measurement | Observation |
|---|---|
| Tagged snap | Frame 6 |
| Tagged release | Frame 28 |
| Tagged time to throw | `(28 - 6) / 10 = 2.2 seconds` |
| Automatic release marker | Frame 26, or 2.0 seconds after snap |
| Target separation at tagged release | 1.780028 yards to Devin White |
| Target depth at tagged release | 5.06 yards beyond the metadata scrimmage line |
| Largest observed target separation before release | 3.12 yards at 1.1 seconds |

The release annotations disagree by 0.2 seconds. Report which marker is used rather than presenting either as an independently verified instant of ball release. Raw time strings on these rows are rounded to whole seconds, so frame differences at the documented 10 Hz are used for elapsed time.

Nearest defender changes from Shaquil Barrett to Devin White at 1.2 seconds. This is a nearest-distance calculation, not proof of coverage responsibility or a receiver-defender matchup. A completed pass with less than two yards of separation at release also illustrates why a separation cutoff cannot be interpreted as catch probability.

## Checks and fixes

The independent inspector checks 11 offensive players, 11 defenders, and the ball in every frame; no missing or duplicate frames; one PFF passer; a named target matching a PFF route runner; consistency of the scrimmage line with team/yardline metadata; and distance preservation after coordinate rotation. Its results agree with the corrected bulk pipeline for this play's target, throwing time, release separation, and receiver depth.

This check exposed and corrected two bulk-pipeline issues: an uppercase initial was stripped before target-name matching, and a moving snap-frame ball was being used instead of the play metadata's line of scrimmage. Original full-dataset outputs have been moved to ignored `results/before-validation/` and must not be used for receiver conclusions. A corrected first-game run resolves 61 of 66 short-pass targets; unresolved descriptions remain unmatched.

## Reproduce

```bash
python inspect_play.py --data-dir data --game-id 2021090900 --play-id 187 --output validation/play-187.json
python -m unittest discover -s tests -v
python analyze.py --data-dir data --max-games 1 --out-dir results/first-game
```

One verified play is a measurement check, not a player ranking or a general football finding. The next checks should cover a delayed short throw and an incomplete short pass, including plays moving in the opposite direction.
