"""Build a self-contained dashboard from corrected Python analysis outputs."""
import argparse
import json
from pathlib import Path

import pandas as pd
from plotly.offline import get_plotlyjs
from alignment import add_alignment


def build(results, data_dir, validation_dir, output):
    report = json.loads((results / 'report.json').read_text())
    plays = pd.read_csv(results / 'plays_analyzed.csv')
    routes = pd.read_csv(results / 'receiver_windows.csv')
    players = pd.read_csv(data_dir / 'players.csv').set_index('nflId')
    plays['position'] = plays.targetId.map(players.officialPosition).fillna('Unknown')
    targets = routes.loc[routes.targeted, ['gameId', 'playId', 'releaseSeparation', 'releaseDepth', 'firstWindow', 'windowSeconds']]
    assert not targets.duplicated(['gameId', 'playId']).any()
    joined = plays.merge(targets, on=['gameId', 'playId'], how='left', validate='one_to_one')
    short = joined.loc[joined.depth.eq('short')]
    assert len(short) > 0 and len(joined) == len(plays)
    summary = dict(attempts=len(plays), shortAttempts=len(short), games=int(plays.gameId.nunique()),
                   mean=float(short.ttt.mean()), median=float(short.ttt.median()),
                   atLeast3Seconds=int(short.ttt.ge(3).sum()),
                   atLeast4Seconds=int(short.ttt.ge(4).sum()),
                   namedTargets=int(short.targetId.notna().sum()),
                   roleClocks=json.loads(short.groupby(['position', 'playAction']).ttt.agg(['count', 'mean', 'median']).reset_index().to_json(orient='records')),
                   playActionClocks=json.loads(short.groupby('playAction').ttt.agg(['count', 'mean', 'median']).reset_index().to_json(orient='records')))
    alignment, alignment_audit = add_alignment(plays, routes, min_window=report['settings']['minimumWindowSeconds'])
    alignment.to_csv(results / 'alignment.csv', index=False)
    (results / 'alignment-audit.json').write_text(json.dumps(alignment_audit, indent=2))
    examples = [json.loads((validation_dir / ('play-' + str(pid) + '.json')).read_text()) for pid in [187, 1425, 434]]
    for ex in examples:
        row = joined.loc[joined.gameId.eq(int(ex['gameId'])) & joined.playId.eq(int(ex['playId']))].iloc[0]
        assert row.target == ex['target'] and row.ttt == ex['timeToThrow']
        assert abs(row.releaseSeparation - ex['frames'][-1]['separation']) < 1e-5
    columns = ['gameId', 'playId', 'qb', 'team', 'week', 'ttt', 'depth', 'coverage', 'coverageType', 'formation',
               'playAction', 'pressure', 'position', 'down', 'result', 'target', 'releaseSeparation',
               'releaseDepth', 'firstWindow', 'windowSeconds']
    alignment_columns = ['qb', 'team', 'receiver', 'position', 'coverageType', 'targeted', 'clock',
                         'referenceCount', 'referenceLevel', 'ttt', 'alignmentStatus']
    payload = dict(columns=columns, rows=json.loads(joined[columns].to_json(orient='values', double_precision=4)),
                   alignmentColumns=alignment_columns,
                   alignment=json.loads(alignment[alignment_columns].to_json(orient='values', double_precision=4)),
                   alignmentAudit=alignment_audit,
                   summary=summary, audit=report['audit'], examples=examples, settings=report['settings'])
    template = Path(__file__).with_name('dashboard.html').read_text()
    packed = json.dumps(payload, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')
    html = template.replace('<!--PLOTLY_RUNTIME-->', '<script>' + get_plotlyjs() + '</script>')
    html = html.replace('DASHBOARD_DATA_PLACEHOLDER', packed)
    assert 'DASHBOARD_DATA_PLACEHOLDER' not in html
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    (results / 'findings.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print('Dashboard:', output.resolve(), 'bytes:', output.stat().st_size)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--results', type=Path, default=Path('results/corrected'))
    p.add_argument('--data-dir', type=Path, default=Path('data'))
    p.add_argument('--validation-dir', type=Path, default=Path('validation'))
    p.add_argument('--output', type=Path, default=Path('docs/index.html'))
    a = p.parse_args()
    build(a.results, a.data_dir, a.validation_dir, a.output)
