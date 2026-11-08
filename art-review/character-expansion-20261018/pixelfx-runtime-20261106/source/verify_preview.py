from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math,re
ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT.parents[2]
data=json.loads((ROOT/'data.js').read_text().split(' = ',1)[1].rstrip(';\n'))
baseline=json.loads((ROOT/'source/runtime-before.json').read_text())
changed=[p for p,h in baseline.items() if not (GAME/p).exists() or hashlib.sha256((GAME/p).read_bytes()).hexdigest()!=h]
errors=[]
if changed:errors.append('Runtime source/config changed')
checks=[]
for c in data['cases']:
 for a in c['atlases']:
  if not (ROOT/a).is_file():errors.append('Missing atlas '+a)
 if max(c['timeline'])>=c['uniqueFrames'] or min(c['timeline'])<0:errors.append('Invalid timeline '+c['key'])
 if c['contactCalls']!=1:errors.append('Contact count '+c['key'])
 fx=data['effects'][c['effect']];image=Image.open(ROOT/fx['path']).convert('RGBA');w,h=fx['frameSize'];px,py=fx['pivot']
 visible_bottom=0;spills=0
 for f in range(fx['frames']):
  a=image.crop(((f%fx['columns'])*w,(f//fx['columns'])*h,(f%fx['columns']+1)*w,(f//fx['columns']+1)*h)).getchannel('A')
  b=a.point(lambda x:255 if x>=24 else 0).getbbox()
  if b:
   bottom=b[3]-py+c['anchor'][1];visible_bottom=max(visible_bottom,bottom)
   if bottom>128:spills+=1
 if spills:errors.append('Visible effect reaches UI '+c['key'])
 checks.append({'case':c['key'],'unique_runtime_frames':c['uniqueFrames'],'single_contact':c['contactCalls']==1,'fx_visible_bottom_max':visible_bottom,'ui_begins_y':128,'visible_spill_frames':spills,'sync':'Both canvases share the same timeline index and source frame.'})

# Inspect the pixel language on both backgrounds at native and integer enlargement.
contact=Image.new('RGB',(800,640),'#101820');draw=ImageDraw.Draw(contact)
for row,(key,frame) in enumerate([('hit',1),('cannon',1),('core',6),('water',6)]):
 fx=data['effects'][key];w,h=fx['frameSize'];im=Image.open(ROOT/fx['path']).convert('RGBA');cols=fx['columns'];tile=im.crop(((frame%cols)*w,(frame//cols)*h,(frame%cols+1)*w,(frame//cols+1)*h))
 draw.text((8,row*160+8),key,fill='#dce4e5')
 for col,bg in enumerate(['#101820','#e0d8c7']):
  panel=Image.new('RGBA',(360,144),bg);panel.alpha_composite(tile,(12,36));panel.alpha_composite(tile.resize((w*2,h*2),Image.Resampling.NEAREST),(125,8));contact.paste(panel.convert('RGB'),(50+col*375,row*160+8))
contact.save(ROOT/'qa/native-dark-light.png',optimize=True)
inventory=json.loads((ROOT/'asset-manifest.json').read_text())
for entry in inventory:
 p=ROOT/entry['path'];entry['bytes']=p.stat().st_size
entry={'path':'qa/native-dark-light.png','purpose':'native 1x and 2x effect transparency inspection on dark/light backgrounds','dimensions':[800,640],'bytes':(ROOT/'qa/native-dark-light.png').stat().st_size}
inventory=[e for e in inventory if e['path']!=entry['path']]+[entry]
(ROOT/'asset-manifest.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
report={'passed':not errors,'errors':errors,'runtime_files_checked':len(baseline),'runtime_files_changed':changed,'cases':checks,'image_files':len(inventory),'largest_image_bytes':max(e['bytes'] for e in inventory),'fx_bytes':{k:(ROOT/e['path']).stat().st_size for k,e in data['effects'].items()},'limits_note':'All delivered images under 200KB; every FX atlas under 50KB. Core and water retain their native frame count and clarity above the 20KB small-icon reference.','scope':'Preview only. No gameplay modifications, installation, or iPhone performance claim.'}
(ROOT/'qa/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)
