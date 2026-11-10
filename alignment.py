"""Describe observed separation windows relative to an out-of-game QB clock.

Unobserved time is reported explicitly. This is not a receiver-quality ranking,
a counterfactual prediction, a catch model, or a claim about QB reads.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


MIN_REFERENCE_ATTEMPTS = 20


def classify_window(windows, clock, release, complete_tracking=True, min_window=.3):
    """Separate observed evidence from right-censoring and missing references."""
    if clock is None or not np.isfinite(clock):
        return 'no_reference'
    cutoff = min(float(clock), float(release))
    if any(min(float(end), cutoff) - float(start) >= min_window - 1e-7
           for start, end in windows):
        return 'window_observed'
    if complete_tracking and release >= clock - 1e-7:
        return 'no_window_observed'
    return 'unresolved'


def add_alignment(plays, routes, min_reference=MIN_REFERENCE_ATTEMPTS, min_window=.3):
    """Use other games only; fall back explicitly when a QB/context cell is sparse."""
    short = plays.loc[plays.depth.eq('short')].copy()
    lookups = {}
    for game_id in short.gameId.unique():
        other_games = short.loc[short.gameId.ne(game_id)]
        context = other_games.groupby(['qbId', 'playAction', 'coverageType']).ttt.agg(['count', 'median'])
        action = other_games.groupby(['qbId', 'playAction']).ttt.agg(['count', 'median'])
        quarterback = other_games.groupby('qbId').ttt.agg(['count', 'median'])
        lookups[game_id] = (context.to_dict('index'), action.to_dict('index'), quarterback.to_dict('index'))
    references = []
    for row in short.itertuples():
        context, action, quarterback = lookups[row.gameId]
        choices = [('QB + play action + coverage', context.get((row.qbId, row.playAction, row.coverageType))),
                   ('QB + play action', action.get((row.qbId, row.playAction))),
                   ('QB overall', quarterback.get(row.qbId))]
        selected = next(((name, cell) for name, cell in choices if cell and cell['count'] >= min_reference), None)
        references.append(dict(gameId=row.gameId, playId=row.playId,
                               clock=float(selected[1]['median']) if selected else None,
                               referenceCount=int(selected[1]['count']) if selected else 0,
                               referenceLevel=selected[0] if selected else 'Insufficient other-game attempts'))
    ref = pd.DataFrame(references)
    sample = routes.loc[routes.passDepth.eq('short')].merge(ref, on=['gameId', 'playId'], how='left', validate='many_to_one')
    assert not sample.duplicated(['gameId', 'playId', 'nflId']).any()
    sample['alignmentStatus'] = [classify_window(json.loads(row.windowsJson), row.clock, row.ttt,
                                                complete_tracking=row.validFrameShare >= .999 and row.continuousTracking,
                                                min_window=min_window)
                                 for row in sample.itertuples()]
    # Use one play once for reference audit, not once per receiver.
    audit = dict(routeObservations=len(sample), plays=len(ref), minimumOtherGameAttempts=min_reference,
                 referenceLevels=ref.referenceLevel.value_counts().to_dict(),
                 statuses=sample.alignmentStatus.value_counts().to_dict())
    return sample, audit


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--results', type=Path, default=Path('results/corrected'))
    a = p.parse_args()
    settings = json.loads((a.results / 'report.json').read_text())['settings']
    sample, audit = add_alignment(pd.read_csv(a.results / 'plays_analyzed.csv'), pd.read_csv(a.results / 'receiver_windows.csv'),
                                  min_window=settings['minimumWindowSeconds'])
    sample.to_csv(a.results / 'alignment.csv', index=False)
    (a.results / 'alignment-audit.json').write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))
