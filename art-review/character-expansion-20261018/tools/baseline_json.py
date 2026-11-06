"""Read art baselines stored as lossless .json.gz archives.

Callers may keep their .json paths; existing uncompressed revisions still work.
Existence checks include the archive so preparation never replaces a frozen base.
"""

import gzip
import json
from pathlib import Path


def baseline_exists(path):
    path = Path(path)
    return path.exists() or path.with_suffix(path.suffix + '.gz').exists()


def read_baseline(path):
    path = Path(path)
    if not path.exists():
        path = path.with_suffix(path.suffix + '.gz')
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as source:
        return json.load(source)


def write_baseline(path, data):
    """Create new preparation snapshots compressed, without replacing a baseline."""
    path = Path(path)
    if baseline_exists(path):
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    archive = path.with_suffix(path.suffix + '.gz')
    with archive.open('xb') as target:
        with gzip.GzipFile(filename='', mode='wb', fileobj=target, mtime=0) as output:
            output.write((json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
