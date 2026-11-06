"""Prepare deterministic gzip companions for text assets; sources stay readable."""
from pathlib import Path
import gzip
import json
ROOT=Path(__file__).resolve().parents[1]
records=[]
for name in ['index.html','styles.css','app.js','content.js','robots.txt']:
    source=ROOT/name;raw=source.read_bytes();packed=gzip.compress(raw,compresslevel=9,mtime=0)
    (ROOT/(name+'.gz')).write_bytes(packed)
    assert gzip.decompress(packed)==raw
    records.append({'asset':name,'bytes':len(raw),'gzip_bytes':len(packed)})
(ROOT/'reports/text-compression.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps({'source_bytes':sum(r['bytes'] for r in records),'gzip_bytes':sum(r['gzip_bytes'] for r in records)}))
