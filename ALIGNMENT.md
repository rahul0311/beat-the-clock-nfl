# Receiver windows within a quarterback's throwing clock

## Question and audience

For a coach or analyst: do observed receiver routes create sustained geometric space before the QB's usual short-pass release time in similar situations?

This is a descriptive review tool. It is not a catch model, a fair ranking of receiver talent, a measure of intended route success, or a claim that the quarterback missed an available throw.

## Reference clock

For each retained short-labeled pass, compute a median release-time reference using short-labeled passes from **other games**. The complete current game is excluded, including all its other plays.

Choose the narrowest reference with at least 20 attempts:

1. Same QB, play-action flag, and coverage family.
2. Same QB and play-action flag.
3. Same QB overall.

If none qualifies, leave the clock unknown. Store the reference sample count and fallback level. Other games can occur before or after the evaluated game, so this is a historical comparison, not a chronological prediction or an on-field forecasting system. All reference attempts are thrown passes; sacks and scrambles are not assigned invented throwing times.

## Window definition

An observed WR/TE/RB route runner has a qualifying window when all of these hold:

- Nearest of all 11 defenders is at least 2 yards away.
- Receiver is 0–10 yards beyond the metadata line of scrimmage.
- At least 0.5 seconds have elapsed since tagged snap.
- The conditions persist over at least 0.3 seconds of contiguous observed intervals.
- At least 0.3 seconds of that window occur before both actual release and the reference clock.

The duration uses observed 0.1-second intervals and never extends beyond release. Missing intervals break windows. These thresholds are provisional choices, not an established football definition of openness. Initial PFF route runners are included whether targeted or not; a named WR/TE/RB target initially assigned to block is also included. Deep routes and routes behind the line can be disadvantaged by this regional definition, so the default view compares one QB and one roster position and does not sort by supposed quality.

## Four evidence states

| State | Meaning |
|---|---|
| Window observed | A qualifying window is actually seen before the clock; this can be established even if the throw ends earlier than the clock. |
| No window observed | Tracking is continuous through the reference clock, but no qualifying window is seen. This is not equivalent to failure to execute an assigned route. |
| Unresolved | No qualifying window is yet seen, and release ends observation early or tracking is incomplete. |
| No reference | Fewer than 20 suitable other-game attempts are available at every fallback level. |

No future route is extrapolated. A receiver with no observed window before an early throw is not classified as having failed to open.

## Displayed range

For a filtered receiver sample of `N` observations, let `H` be observed windows and `U` unresolved plus no-reference cases:

- Minimum observed share: `H / N`.
- Maximum share if every unresolved case qualified: `(H + U) / N`.

This is a display of unresolved evidence, not a confidence interval, a causal estimate, or a prediction of what players would do if the QB waited. It does not adjust away different route responsibilities or sample selection. Even non-overlapping ranges do not establish differences in receiver talent.

## Validation and outputs

`tests/test_alignment.py` checks early-release handling, enough observed duration before the cutoff, complete versus missing tracking, missing references, and exclusion of the whole current game from the reference. The measurement suite also checks target matching and contiguous-window calculations. Twelve tests currently pass.

`build_dashboard.py` joins the computed alignment data to the dashboard and writes ignored `results/corrected/alignment.csv` and `alignment-audit.json`. The audit records reference fallback levels by play and evidence-state counts by receiver–play observation. One pass with several receivers contributes several observations; these are not independent play counts.
