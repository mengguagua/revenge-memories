"""Add preview-only water palette metadata. Original runtime textures are copied, never edited."""
from pathlib import Path
import json,math,bisect,base64,shutil,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[2]
data=json.loads((ROOT/'data.js').read_text().split(' = ',1)[1].rstrip(';\n'))
water=next(c for c in data['cases'] if c['key']=='water')
capture=json.loads((ROOT/'source/captures/water/capture.json').read_text())
art=json.loads((PROJECT/'actual/data/mechanical_puppets_art.json').read_text())
times=[f['t'] for f in capture['frames']]
source_frames=art['variants']['cannon']['frames']
sprite_keys=sorted({e['sprite'] for f in source_frames for e in f.get('effects',[])})
folder=ROOT/'assets/water-reference';folder.mkdir(exist_ok=True)
textures={};source_records=[]
for key in sprite_keys:
 spec=art['effects'][key];source=PROJECT/'actual'/spec['path'].replace('res://','');target=folder/source.name
 shutil.copy2(source,target)
 textures[key]=str(target.relative_to(ROOT))
 source_records.append({'runtime_source':str(source.relative_to(PROJECT)),'preview_copy':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'size':list(Image.open(source).size),'bytes':target.stat().st_size})
rows=[]
for n in range(len(water['timeline'])):
 t=min(n/60,water['duration']);i=max(0,bisect.bisect_right(times,t)-1);tick=capture['frames'][i]['tick'];bounds=[]
 if 0<=tick<len(source_frames):
  for effect in source_frames[tick].get('effects',[]):
   spec=art['effects'][effect['sprite']];progress=(176-float(effect['position'][0]))/112
   x=capture['actor_origin'][0]+(capture['target_origin'][0]-capture['actor_origin'][0])*progress
   y=effect['position'][1]+capture['actor_origin'][1]-128
   w,h=spec['logical_frame_size'];ax,ay=spec['anchor']
   bounds.append({'texture':textures[effect['sprite']],'x':math.floor(x-ax+.5),'y':math.floor(y-ay+.5),'w':w,'h':h,'flip':not effect.get('flip',False)})
 rows.append(bounds)
water['waterTint']={'palette':['#1f3642','#2e4d59','#466a76','#638b95','#88abb0','#b0cace','#d1dfdf'],'frames':rows,'textures':sorted(set(textures.values())),'name':'灰青水色'}
water['treatment']='原水弹与命中水光改为低饱和灰青色，再衔接已认可的 PixelFX 水冠、水滴与短波纹。'
data['defaultCase']='water'
# Data URLs keep Canvas pixel reads usable when index.html is opened directly as file://.
data['embeddedImages']={p:'data:image/png;base64,'+base64.b64encode((ROOT/p).read_bytes()).decode() for p in water['atlases']+water['waterTint']['textures']+[data['effects'][water['effect']]['path']]}
(ROOT/'data.js').write_text('window.PIXELFX_PREVIEW = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
manifest=json.loads((ROOT/'asset-manifest.json').read_text())
manifest=[x for x in manifest if not x['path'].startswith('assets/water-reference/')]
for p in sorted(folder.glob('*.png')):manifest.append({'path':str(p.relative_to(ROOT)),'purpose':'unchanged source water texture, used as a preview-only alpha mask','dimensions':list(Image.open(p).size),'bytes':p.stat().st_size})
(ROOT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(ROOT/'source/water-tint-20261107/sources.json').write_text(json.dumps({'sources':source_records,'palette':water['waterTint']['palette'],'treatment':water['treatment'],'scope':'Candidate only; original game sources and left reference remain unchanged.'},ensure_ascii=False,indent=2))
print('Water palette metadata:',len(rows),'delivery frames,',len(textures),'source textures; data bytes:',(ROOT/'data.js').stat().st_size)
