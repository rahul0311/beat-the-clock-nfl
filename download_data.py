"""Download the public dataset linked in the NYU event brief."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

REPO = 'https://raw.githubusercontent.com/ThompsonJamesBliss/nfl-big-data-bowl-regional-event-data/main/'
API = 'https://api.github.com/repos/ThompsonJamesBliss/nfl-big-data-bowl-regional-event-data/contents/data/tracking'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--max-games', type=int, default=122)
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.data_dir / 'tracking-manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        with urllib.request.urlopen(API, timeout=60) as response:
            manifest = json.load(response)
        manifest_path.write_text(json.dumps(manifest, indent=2))

    def download(item):
        relative, url, expected = item
        dest = args.data_dir / relative
        if dest.exists() and (expected is None or dest.stat().st_size == expected):
            return relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        temporary = dest.with_suffix('.part')
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=90) as source, temporary.open('wb') as out:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                if expected is not None and temporary.stat().st_size != expected:
                    raise ValueError('File size mismatch: ' + relative)
                temporary.replace(dest)
                return relative
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)

    items = [(name, REPO + 'data/' + name, None) for name in
             ['games.csv', 'players.csv', 'plays.csv', 'pffScoutingData.csv']]
    items += [('tracking/' + x['name'], x['download_url'], x['size'])
              for x in sorted(manifest, key=lambda x: x['name'])[:args.max_games]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        for count, result in enumerate(executor.map(download, items), 1):
            if count % 10 == 0 or count == len(items):
                print(f'{count}/{len(items)} files ready: {result}', flush=True)
    print('Data ready in', args.data_dir.resolve(), flush=True)


if __name__ == '__main__':
    main()
