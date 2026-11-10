"""Audit one play directly from CSV rows without using the bulk-analysis pipeline."""
import argparse
import csv
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re


def read_csv(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def inspect(data_dir, game_id, play_id):
    players = {p['nflId']: p for p in read_csv(data_dir / 'players.csv')}
    play = next(p for p in read_csv(data_dir / 'plays.csv')
                if p['gameId'] == game_id and p['playId'] == play_id)
    game = next(g for g in read_csv(data_dir / 'games.csv') if g['gameId'] == game_id)
    scouting = [p for p in read_csv(data_dir / 'pffScoutingData.csv')
                if p['gameId'] == game_id and p['playId'] == play_id]
    rows = [p for p in read_csv(data_dir / 'tracking' / ('tracking_' + game_id + '.csv'))
            if p['playId'] == play_id]
    role = {p['nflId']: p['pff_role'] for p in scouting}
    tagged = defaultdict(set)
    for row in rows:
        if row['event'] != 'None':
            tagged[row['event']].add(int(row['frameId']))
    assert len(tagged['ball_snap']) == len(tagged['pass_forward']) == 1
    snap, release = next(iter(tagged['ball_snap'])), next(iter(tagged['pass_forward']))
    assert release > snap
    direction = rows[0]['playDirection']
    assert all(p['playDirection'] == direction for p in rows)
    raw_los = float(play['absoluteYardlineNumber'])
    los = 120 - raw_los if direction == 'left' else raw_los
    # Cross-check the scrimmage line against team and yardline metadata.
    expected_los = 10 + (float(play['yardlineNumber']) if play['yardlineSide'] == play['possessionTeam']
                         else 100 - float(play['yardlineNumber']))
    assert abs(los - expected_los) < .01
    qb_ids = [p['nflId'] for p in scouting if p['pff_role'] == 'Pass']
    assert len(qb_ids) == 1
    qb_id = qb_ids[0]
    name_match = re.search(r'\bpass (?:incomplete )?(?:short|deep) (?:left|middle|right) to ([A-Za-z.\x27-]+)', play['playDescription'])
    if not name_match:
        raise ValueError('Play has no unambiguous named target; choose another validation example.')
    abbreviation = name_match.group(1)
    target_matches = []
    for pid, r in role.items():
        if r != 'Pass Route':
            continue
        pieces = players[pid]['displayName'].split()
        if (pieces[0][0] + '.' + pieces[-1]).lower() == abbreviation.lower():
            target_matches.append(pid)
    assert len(target_matches) == 1, (abbreviation, target_matches)
    target_id = target_matches[0]
    frames = []
    snapshots = defaultdict(list)
    for row in rows:
        if snap <= int(row['frameId']) <= release:
            snapshots[int(row['frameId'])].append(row)
    for fid, frame in sorted(snapshots.items()):
        assert len(frame) == 23 and len({p['nflId'] for p in frame}) == 23
        assert Counter(p['team'] for p in frame) == Counter({play['possessionTeam']: 11, play['defensiveTeam']: 11, 'football': 1})
        target = next(p for p in frame if p['nflId'] == target_id)
        defenders = [p for p in frame if p['team'] == play['defensiveTeam']]
        nearest = min(defenders, key=lambda p: math.hypot(float(p['x']) - float(target['x']), float(p['y']) - float(target['y'])))
        distance = math.hypot(float(nearest['x']) - float(target['x']), float(nearest['y']) - float(target['y']))
        people = []
        for p in frame:
            x, y = float(p['x']), float(p['y'])
            if direction == 'left':
                x, y = 120 - x, 53.3 - y
            pid = p['nflId']
            people.append(dict(id=int(pid) if pid != 'NA' else 0, name=players.get(pid, {}).get('displayName', 'Ball'),
                               position=players.get(pid, {}).get('officialPosition', 'Ball'), role=role.get(pid, 'Ball'),
                               team=p['team'], number=p['jerseyNumber'], depth=round(x - los, 3), width=round(y, 3)))
        frames.append(dict(frame=fid, t=round((fid - snap) / 10, 3),
                           event=next((p['event'] for p in frame if p['event'] != 'None'), None),
                           rawTime=frame[0]['time'], separation=round(distance, 6),
                           nearestDefender=players[nearest['nflId']]['displayName'], nearestDefenderId=int(nearest['nflId']),
                           targetDepth=next(p['depth'] for p in people if p['id'] == int(target_id)), players=people))
    assert [f['frame'] for f in frames] == list(range(snap, release + 1))
    # Rotation must preserve Euclidean distance. This checks both axes and units.
    for f in frames:
        a = next(p for p in f['players'] if p['id'] == int(target_id))
        b = next(p for p in f['players'] if p['id'] == f['nearestDefenderId'])
        assert abs(math.hypot(a['depth'] - b['depth'], a['width'] - b['width']) - f['separation']) < 1e-5
    return dict(gameId=game_id, playId=play_id, date=game['gameDate'], description=play['playDescription'],
                offense=play['possessionTeam'], defense=play['defensiveTeam'], quarter=int(play['quarter']),
                clock=play['gameClock'], down=int(play['down']), yardsToGo=int(play['yardsToGo']),
                coverage=play['pff_passCoverage'], coverageType=play['pff_passCoverageType'], result=play['passResult'],
                playYards=int(play['playResult']), qb=players[qb_id]['displayName'], qbId=int(qb_id),
                target=players[target_id]['displayName'], targetId=int(target_id), targetPosition=players[target_id]['officialPosition'],
                snapFrame=snap, releaseFrame=release, timeToThrow=(release - snap) / 10,
                normalizedLineOfScrimmage=los, events={k: sorted(v) for k, v in tagged.items()},
                autoReleaseOffsetSeconds=(next(iter(tagged['autoevent_passforward'])) - snap) / 10 if len(tagged['autoevent_passforward']) == 1 else None,
                pressureCredited=any(p[k] == '1' for p in scouting for k in ('pff_hurry', 'pff_hit', 'pff_sack')),
                checks=['23 objects each frame: 11 offense, 11 defense, 1 ball',
                        'No missing or duplicate snap-to-release frames',
                        'One PFF passer; named target matches a PFF route runner',
                        'Metadata scrimmage line agrees with team and yardline',
                        'Left/right coordinate rotation preserves separation distances'], frames=frames)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--game-id', default='2021090900')
    parser.add_argument('--play-id', default='187')
    parser.add_argument('--output', type=Path, default=Path('validation/play-187.json'))
    args = parser.parse_args()
    result = inspect(args.data_dir, args.game_id, args.play_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'frames'}, indent=2))
