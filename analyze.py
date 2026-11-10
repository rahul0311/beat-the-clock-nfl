"""Reproducible release-timing and pre-release receiver-separation analysis.

No learned catch probability, inferred route labels, or estimated time of pressure.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd


def pass_depth(description):
    match = re.search(r'\bpass (?:incomplete )?(short|deep)\b', description, re.I)
    return match.group(1).lower() if match else 'unclassified'


def alias(name):
    parts = name.split()
    if len(parts) < 2:
        return ''
    if parts[-1].lower().strip('.') in ('jr', 'sr', 'ii', 'iii', 'iv', 'v'):
        parts = parts[:-1]
    last = ''.join(parts[1:])
    return re.sub(r'[^a-z]', '', (parts[0][0] + last).lower())


def identify_target(description, route_ids, players):
    # Descriptions include D.Schultz, Dj.Moore, Mi.Carter, and A.St. Brown.
    match = re.search(r'\b(?:to|intended for)\s+([A-Za-z]+(?:\.[A-Za-z]+)*)\.((?:St\.\s+)?[A-Za-z][A-Za-z.\x27-]*)', description)
    if not match:
        return None
    prefix = re.sub(r'[^a-z]', '', match.group(1).lower())
    family = re.sub(r'[^a-z]', '', match.group(2).lower())
    hits = []
    for pid in route_ids:
        parts = players.get(pid, {}).get('displayName', '').split()
        if len(parts) < 2:
            continue
        if parts[-1].lower().strip('.') in ('jr', 'sr', 'ii', 'iii', 'iv', 'v'):
            parts = parts[:-1]
        first = re.sub(r'[^a-z]', '', parts[0].lower())
        surname = re.sub(r'[^a-z]', '', ''.join(parts[1:]).lower())
        if first.startswith(prefix) and surname == family:
            hits.append(pid)
    return hits[0] if len(hits) == 1 else None


def separation_windows(times, mask, minimum=.3):
    """Durations use observed intervals, never extend beyond release or missing frames."""
    intervals = np.diff(times)
    valid = mask[:-1] & np.isclose(intervals, .1, atol=.001)
    windows = []
    start = None
    for i, good in enumerate(valid):
        if good and start is None:
            start = i
        if start is not None and (not good or i == len(valid) - 1):
            end = i if not good else i + 1
            duration = float(times[end] - times[start])
            if duration + 1e-7 >= minimum:
                windows.append([round(float(times[start]), 3), round(float(times[end]), 3)])
            start = None
    return windows


def safe_records(df):
    return json.loads(df.to_json(orient='records', double_precision=5))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--out-dir', type=Path, default=Path('results'))
    parser.add_argument('--separation', type=float, default=2.0)
    parser.add_argument('--min-window', type=float, default=.3)
    parser.add_argument('--max-games', type=int, default=122)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plays = pd.read_csv(args.data_dir / 'plays.csv')
    games = pd.read_csv(args.data_dir / 'games.csv')
    player_df = pd.read_csv(args.data_dir / 'players.csv')
    players = player_df.set_index('nflId').to_dict('index')
    scouting = pd.read_csv(args.data_dir / 'pffScoutingData.csv')
    play_lookup = plays.set_index(['gameId', 'playId']).to_dict('index')
    game_lookup = games.set_index('gameId').to_dict('index')
    scouting_lookup = {key: frame for key, frame in scouting.groupby(['gameId', 'playId'], sort=False)}
    audit = Counter()
    play_results, route_results, example_candidates = [], [], []
    files = sorted((args.data_dir / 'tracking').glob('tracking_*.csv'))[:args.max_games]
    manifest = {x['name']: x for x in json.loads((args.data_dir / 'tracking-manifest.json').read_text())}
    for file_index, path in enumerate(files):
        if path.name in manifest and path.stat().st_size != manifest[path.name]['size']:
            audit['partial_tracking_files_skipped'] += 1
            continue
        tracking = pd.read_csv(path, usecols=['gameId', 'playId', 'nflId', 'frameId', 'time', 'team', 'playDirection', 'x', 'y', 'event'])
        for (game_id, play_id), raw in tracking.groupby(['gameId', 'playId'], sort=False):
            audit['tracked_plays'] += 1
            meta = play_lookup.get((game_id, play_id))
            scout = scouting_lookup.get((game_id, play_id))
            if meta is None or scout is None:
                audit['missing_metadata'] += 1
                continue
            if meta['passResult'] not in ('C', 'I', 'IN'):
                audit['non_attempts_excluded'] += 1
                continue
            if any(pd.notna(meta.get('foulName' + str(i))) for i in (1, 2, 3)):
                audit['penalized_plays_excluded'] += 1
                continue
            if re.search(r'\bspike[sd]?\b', meta['playDescription'], re.I):
                audit['spikes_excluded'] += 1
                continue
            snap_frames = raw.loc[raw.event == 'ball_snap', 'frameId'].unique()
            if len(snap_frames) != 1:
                audit['missing_or_ambiguous_snap'] += 1
                continue
            snap = int(snap_frames[0])
            releases = raw.loc[(raw.event == 'pass_forward') & (raw.frameId >= snap), 'frameId'].unique()
            if len(releases) != 1:
                audit['missing_or_ambiguous_release'] += 1
                continue
            release = int(releases[0])
            ttt = (release - snap) / 10
            if not 0 < ttt <= 12:
                audit['invalid_release_time'] += 1
                continue
            qbs = scout.loc[scout.pff_role.str.lower() == 'pass', 'nflId'].unique()
            if len(qbs) != 1:
                audit['ambiguous_passer'] += 1
                continue
            qb_id = int(qbs[0])
            cut = raw.loc[raw.frameId.between(snap, release)].copy()
            left = cut.playDirection.eq('left')
            cut.loc[left, 'x'] = 120 - cut.loc[left, 'x']
            cut.loc[left, 'y'] = 53.3 - cut.loc[left, 'y']
            # The ball can already have moved toward the QB at the tagged snap.
            # Use the play metadata's scrimmage line instead of the ball position.
            absolute_los = meta.get('absoluteYardlineNumber')
            if pd.isna(absolute_los):
                audit['missing_scrimmage_line'] += 1
                continue
            direction = raw.playDirection.iloc[0]
            los = float(120 - absolute_los if direction == 'left' else absolute_los)
            receivers = [int(pid) for pid in scout.loc[scout.pff_role.str.lower() == 'pass route', 'nflId']
                         if players.get(int(pid), {}).get('officialPosition') in ('WR', 'TE', 'RB')]
            # A chip/block-assigned skill player can subsequently receive a pass.
            # Match the named target against skill players present, not just route roles.
            target_candidates = [int(pid) for pid in scout.nflId
                                 if players.get(int(pid), {}).get('officialPosition') in ('WR', 'TE', 'RB')]
            target = identify_target(meta['playDescription'], target_candidates, players)
            if target is not None and target not in receivers:
                receivers.append(target)
            depth = pass_depth(meta['playDescription'])
            pressure = bool(scout[['pff_hurry', 'pff_hit', 'pff_sack']].fillna(0).to_numpy().max() > 0)
            row = dict(gameId=int(game_id), playId=int(play_id), week=int(game_lookup[game_id]['week']),
                       team=meta['possessionTeam'], opponent=meta['defensiveTeam'],
                       qb=players.get(qb_id, {}).get('displayName', str(qb_id)), qbId=qb_id,
                       ttt=round(ttt, 3), depth=depth, coverage=meta['pff_passCoverage'],
                       coverageType=meta['pff_passCoverageType'], formation=meta['offenseFormation'],
                       dropBackType=meta['dropBackType'], playAction=bool(meta['pff_playAction'] == 1),
                       down=int(meta['down']), yardsToGo=int(meta['yardsToGo']), result=meta['passResult'],
                       pressure=pressure, targetId=target, target=players.get(target, {}).get('displayName'),
                       description=meta['playDescription'], snapFrame=snap, releaseFrame=release)
            play_results.append(row)
            times = np.array(sorted(cut.frameId.unique()))
            seconds = (times - snap) / 10
            defense = cut.loc[(cut.team == meta['defensiveTeam']) & cut.nflId.notna()]
            dx = defense.pivot(index='frameId', columns='nflId', values='x').reindex(times).to_numpy()
            dy = defense.pivot(index='frameId', columns='nflId', values='y').reindex(times).to_numpy()
            complete_defense = np.isfinite(dx).sum(axis=1) == 11
            play_routes = []
            for pid in receivers:
                receiver = cut.loc[cut.nflId == pid].set_index('frameId').reindex(times)
                rx, ry = receiver.x.to_numpy(), receiver.y.to_numpy()
                dist = np.sqrt((rx[:, None] - dx) ** 2 + (ry[:, None] - dy) ** 2)
                if dx.shape[1] == 0:
                    continue
                with np.errstate(all='ignore'):
                    sep = np.min(np.where(np.isnan(dist), np.inf, dist), axis=1)
                valid = complete_defense & np.isfinite(rx) & np.isfinite(ry)
                sep[~valid] = np.nan
                depth_yards = rx - los
                # This is a geometric short-area definition, not an inferred route type.
                eligible = valid & (depth_yards >= 0) & (depth_yards <= 10) & (seconds >= .5)
                windows = separation_windows(seconds, eligible & (sep >= args.separation), args.min_window)
                total = sum(b - a for a, b in windows)
                route_row = dict(gameId=int(game_id), playId=int(play_id), nflId=pid,
                                 receiver=players[pid]['displayName'], position=players[pid]['officialPosition'],
                                 qb=row['qb'], team=row['team'], coverage=row['coverage'], coverageType=row['coverageType'],
                                 passDepth=depth, ttt=ttt, targeted=pid == target,
                                 firstWindow=windows[0][0] if windows else None,
                                 windowSeconds=round(total, 3), hasWindow=bool(windows),
                                 windowsJson=json.dumps(windows, separators=(',', ':')),
                                 continuousTracking=bool(np.all(np.diff(times) == 1)),
                                 releaseSeparation=float(sep[-1]) if np.isfinite(sep[-1]) else None,
                                 releaseDepth=float(depth_yards[-1]) if np.isfinite(depth_yards[-1]) else None,
                                 validFrameShare=round(float(valid.mean()), 3))
                route_results.append(route_row)
                play_routes.append(dict(nflId=pid, name=players[pid]['displayName'], position=players[pid]['officialPosition'],
                                        windows=windows, separation=[round(float(s), 2) if np.isfinite(s) else None for s in sep]))
            if depth == 'short' and target is not None and audit['valid_attempts'] % 13 == 0:
                frames = []
                role_map = scout.set_index('nflId').pff_role.to_dict()
                for fid, frame in cut.groupby('frameId', sort=True):
                    frames.append(dict(t=round((int(fid) - snap) / 10, 2), players=[
                        dict(id=int(p.nflId) if pd.notna(p.nflId) else 0,
                             x=round(float(p.x - los), 2), y=round(float(p.y), 2),
                             team=str(p.team), role=role_map.get(p.nflId, 'Ball'),
                             name=players.get(int(p.nflId), {}).get('displayName', 'Ball') if pd.notna(p.nflId) else 'Ball')
                        for p in frame.itertuples()]))
                example_candidates.append(dict(**row, routes=play_routes, frames=frames))
            audit['valid_attempts'] += 1
        if (file_index + 1) % 10 == 0 or file_index == len(files) - 1:
            print(f'Analyzed {file_index + 1}/{len(files)} games; {len(play_results)} valid attempts', flush=True)

    p = pd.DataFrame(play_results)
    r = pd.DataFrame(route_results)
    if p.empty:
        raise RuntimeError('No valid pass attempts found. Inspect tracking data and event labels.')
    p.to_csv(args.out_dir / 'plays_analyzed.csv', index=False)
    r.to_csv(args.out_dir / 'receiver_windows.csv', index=False)
    # Include examples throughout the observed release-time range, not just successes.
    examples = []
    if example_candidates:
        ordered = sorted(example_candidates, key=lambda x: x['ttt'])
        selected = np.unique(np.linspace(0, len(ordered) - 1, min(24, len(ordered))).astype(int))
        examples = [ordered[i] for i in selected]
    report = dict(source='2021 NFL, Weeks 1–8; public NYU event dataset',
                  settings=dict(separationYards=args.separation, minimumWindowSeconds=args.min_window,
                                shortAreaDepth=[0, 10], earliestWindowSeconds=.5),
                  audit=dict(audit), games=int(p.gameId.nunique()),
                  plays=safe_records(p), routes=safe_records(r), examples=examples)
    # Pandas serializes missing values to null; examples may contain missing coverage.
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, (float, np.floating)) and not np.isfinite(value):
            return None
        return value
    (args.out_dir / 'report.json').write_text(json.dumps(clean(report), separators=(',', ':'), allow_nan=False))
    print('Audit:', dict(audit), flush=True)
    print(p.groupby('depth').ttt.agg(['count', 'mean', 'median']).round(3).to_string(), flush=True)
    print('Target resolution:', round(p.loc[p.depth.eq('short'), 'targetId'].notna().mean(), 3), flush=True)


if __name__ == '__main__':
    main()
