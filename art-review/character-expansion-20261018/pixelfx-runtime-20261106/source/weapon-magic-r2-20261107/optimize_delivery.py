"""Lossless delivery optimization, with decoded-pixel equality for every PNG."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import hashlib,json,subprocess,time
import build_gallery as G

start=time.time();paths=[p for p in json.loads((G.OUT/'qa/referenced-images.json').read_text()) if p.startswith(('assets/fx/','assets/runtime/'))]
paths+= [str(p.relative_to(G.OUT)) for p in (G.OUT/'qa').glob('*-final.png')]
def pixels(p):
    with Image.open(p) as im:return im.size,hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
def optimize(relative):
    p=G.OUT/relative;before=p.stat().st_size;size,digest=pixels(p)
    r=subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--strip','safe','-t','1','--quiet',str(p)],capture_output=True,text=True)
    after_size,after_digest=pixels(p)
    return {'path':relative,'purpose':'approved comparison atlas' if '/approved/' in relative else 'PixelFX native effect atlas' if '/fx/' in relative else 'visual QA contact sheet' if relative.startswith('qa/') else 'actual-engine preview atlas','width':size[0],'height':size[1],'before_bytes':before,'bytes':p.stat().st_size,'lossless':size==after_size and digest==after_digest,'error':r.stderr.strip() if r.returncode else '',**({'quality_note':'Native resolution and exact original colors retained; multi-frame preview sheet.'} if p.stat().st_size>=200000 else {})}
rows=[]
with ThreadPoolExecutor(max_workers=4) as pool:
    for row in pool.map(optimize,paths):
        rows.append(row)
        if len(rows)%500==0:print('Optimized and verified',len(rows),'/',len(paths),flush=True)
report={'passed':all(r['lossless'] and not r['error'] for r in rows),'images':len(rows),'before_bytes':sum(r['before_bytes'] for r in rows),'after_bytes':sum(r['bytes'] for r in rows),'above_200kb':sum(r['bytes']>=200000 for r in rows),'elapsed_seconds':round(time.time()-start,2),'scope':'Only new R2 effect/runtime atlases and final QA sheets. Copied base assets are unchanged.', 'method':'oxipng -o 2 --strip safe; no alpha rewriting, resizing, quantization, or cropping. Every decoded RGBA hash compared before/after.','files':rows}
(G.OUT/'qa/image-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
raise SystemExit(0 if report['passed'] else 1)
