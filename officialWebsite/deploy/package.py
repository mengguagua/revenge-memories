"""Allowlisted public release package; never includes sources or credentials."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import io
import json
import tarfile

ROOT=Path(__file__).resolve().parents[1]
release=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d-%H%M%S')
files=[ROOT/name for name in ['index.html','styles.css','app.js','content.js','robots.txt','sitemap.xml']]
files += [ROOT/(name+'.gz') for name in ['index.html','styles.css','app.js','content.js','robots.txt']]
files += sorted((ROOT/'assets').rglob('*'))
files=[p for p in files if p.is_file()]
for p in files:
    if p.is_symlink():raise SystemExit('Symlinks are not allowed in the public release')
manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files)
out=ROOT/'dist'/f'revenge-web-{release}.tar.gz';out.parent.mkdir(exist_ok=True)
with tarfile.open(out,'w:gz',compresslevel=6) as archive:
    for p in files:archive.add(p,arcname=p.relative_to(ROOT).as_posix(),recursive=False)
    raw=manifest.encode();info=tarfile.TarInfo('SHA256SUMS');info.size=len(raw);info.mode=0o644;archive.addfile(info,io.BytesIO(raw))
report={'release':release,'archive':str(out),'archive_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'archive_bytes':out.stat().st_size,'public_files':len(files),'public_bytes':sum(p.stat().st_size for p in files),'domain':'revenge-web.gaocc.cc'}
(ROOT/'reports/release-package.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
