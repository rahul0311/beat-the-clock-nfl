"""Build a self-contained dashboard from corrected Python analysis outputs."""
import argparse
import json
from pathlib import Path

import pandas as pd
from plotly.offline import get_plotlyjs
from alignment import add_alignment


POSITIONS = ['WR', 'TE', 'RB']


def resolved_rate(df):
    """Open-rate among plays the tracking resolves: window / (window + no-window)."""
    counts = df.alignmentStatus.value_counts()
    observed = int(counts.get('window_observed', 0))
    none = int(counts.get('no_window_observed', 0))
    total = observed + none
    return dict(open=observed, resolved=total, rate=(round(100 * observed / total, 1) if total else None))


def build_matchup(alignment, sensitivity_dirs=None, min_window=.3):
    """Coverage x position resolved open-rates, plus optional threshold sensitivity."""
    matchup = {coverage: {pos: resolved_rate(alignment[(alignment.position == pos) & (alignment.coverageType == coverage)])
                          for pos in POSITIONS}
               for coverage in ['Man', 'Zone']}
    overall = {pos: resolved_rate(alignment[alignment.position == pos]) for pos in POSITIONS}
    sensitivity = {}
    for label, directory in (sensitivity_dirs or {}).items():
        directory = Path(directory)
        if not (directory / 'plays_analyzed.csv').exists():
            continue
        settings = json.loads((directory / 'report.json').read_text())['settings']
        sample, _ = add_alignment(pd.read_csv(directory / 'plays_analyzed.csv'),
                                  pd.read_csv(directory / 'receiver_windows.csv'),
                                  min_window=settings['minimumWindowSeconds'])
        wr = sample[sample.position == 'WR']
        sensitivity[label] = dict(weeks=sorted(int(w) for w in pd.read_csv(directory / 'plays_analyzed.csv').week.unique()),
                                  games=int(sample.gameId.nunique()),
                                  **{coverage: resolved_rate(wr[wr.coverageType == coverage]) for coverage in ['Man', 'Zone']})
    return dict(matchup=matchup, overall=overall, sensitivity=sensitivity)


def build(results, data_dir, validation_dir, output, sensitivity_dirs=None):
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
    coverage_matchup = build_matchup(alignment, sensitivity_dirs=sensitivity_dirs,
                                     min_window=report['settings']['minimumWindowSeconds'])
    (results / 'coverage_matchup.json').write_text(json.dumps(coverage_matchup, indent=2))
    examples = [json.loads((validation_dir / ('play-' + str(pid) + '.json')).read_text()) for pid in [187, 1425, 434, 2871]]
    for ex in examples:
        row = joined.loc[joined.gameId.eq(int(ex['gameId'])) & joined.playId.eq(int(ex['playId']))].iloc[0]
        assert row.target == ex['target'] and row.ttt == ex['timeToThrow']
        assert abs(row.releaseSeparation - ex['frames'][-1]['separation']) < 1e-5
        # Attach the target's QB reference clock and measured windows so replays show the metric itself.
        match = alignment.loc[alignment.gameId.eq(int(ex['gameId'])) & alignment.playId.eq(int(ex['playId'])) & alignment.targeted]
        assert len(match) == 1
        ex['referenceClock'] = float(match.clock.iloc[0]) if pd.notna(match.clock.iloc[0]) else None
        ex['windows'] = json.loads(match.windowsJson.iloc[0])
        ex['alignmentStatus'] = match.alignmentStatus.iloc[0]
    columns = ['gameId', 'playId', 'qb', 'team', 'week', 'ttt', 'depth', 'coverage', 'coverageType', 'formation',
               'playAction', 'pressure', 'position', 'down', 'result', 'target', 'releaseSeparation',
               'releaseDepth', 'firstWindow', 'windowSeconds']
    alignment_columns = ['qb', 'team', 'receiver', 'position', 'coverageType', 'targeted', 'clock',
                         'referenceCount', 'referenceLevel', 'ttt', 'alignmentStatus']
    payload = dict(columns=columns, rows=json.loads(joined[columns].to_json(orient='values', double_precision=4)),
                   alignmentColumns=alignment_columns,
                   alignment=json.loads(alignment[alignment_columns].to_json(orient='values', double_precision=4)),
                   alignmentAudit=alignment_audit, coverageMatchup=coverage_matchup,
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
    sensitivity_dirs = {'1.5 yd': 'results/sens_15', '2.0 yd': 'results/sens_20', '2.5 yd': 'results/sens_25'}
    build(a.results, a.data_dir, a.validation_dir, a.output, sensitivity_dirs=sensitivity_dirs)
