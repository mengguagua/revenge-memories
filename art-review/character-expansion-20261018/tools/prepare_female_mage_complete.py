#!/usr/bin/env python3
"""Freeze native female-mage poses and programs for the art review."""
import json,math,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,pack_frame
from export_gallery import font
REV='female-mage-complete-v1-20261023';OUT=ROOT/REV;SRC=OUT/'source'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 SRC.mkdir(parents=True,exist_ok=True)
 baseline={'gallery':json.loads((ROOT/'demos/gallery-data.json').read_text()),'source_bodies':{},'variants':{}}
 audit=[]
 for side in ['ally','enemy']:
  d=json.loads((ROOT/('source-input/original-motion/full-original-motion.json' if side=='ally' else 'source-input/enemy-motion/full-enemy-motion.json')).read_text())
  if side=='ally':d['variants'].update(json.loads((ROOT/'source-input/corrected-ally-motion/overlay.json').read_text())['variants'])
  vs={k:v for k,v in d['variants'].items() if str(v.get('source_class_id'))=='16'}
  baseline['source_bodies'][side]=d['original_bodies']['16'];baseline['variants'][side]=vs
  used=sorted({f['frame'] for v in vs.values() for f in v['frames']});print(side,'variants',len(vs),'used',used,flush=True)
  for kind,rel,size,ids,scale,cols in [
   ('idle',f'source-input/legacy-assets/assets/original/graphics/map_units/class_16_{side}.png',(24,24),list(range(6)),12,3),
   ('walk',f'source-input/corrected-tactical-walk/class-16-{side}.png',(32,24),list(range(8)),12,4),
   ('battle','source-input/'+('original-motion/class-16.png'if side=='ally'else'enemy-motion/class-16-enemy.png'),(80,64),used,6,3)]:
   p=ROOT/rel;im=Image.open(p).convert('RGBA');ncols=im.width//size[0];cw,ch=size[0]*scale,size[1]*scale
   q=Image.new('RGBA',(cw*cols,ch*math.ceil(len(ids)/cols)))
   guide=Image.new('RGB',(cw*cols,(ch+32)*math.ceil(len(ids)/cols)),(32,45,53));dr=ImageDraw.Draw(guide)
   hashes={}
   for n,i in enumerate(ids):
    c=im.crop((i%ncols*size[0],i//ncols*size[1],i%ncols*size[0]+size[0],i//ncols*size[1]+size[1]));c.save(SRC/f'native-{side}-{kind}-{i:03}.png',optimize=True);large=c.resize((cw,ch),Image.Resampling.NEAREST)
    q.alpha_composite(large,(n%cols*cw,n//cols*ch));guide.paste(large,(n%cols*cw,n//cols*(ch+32)),large)
    dr.text((n%cols*cw+cw//2,n//cols*(ch+32)+ch+16),f'{kind} {i}',font=font(18),fill=(240,240,224),anchor='mm');hashes[i]=hashlib.sha256(c.tobytes()).hexdigest()
   q.save(SRC/f'target-{side}-{kind}.png',optimize=True);guide.save(SRC/f'native-{side}-{kind}-guide.png',optimize=True)
   audit.append({'side':side,'kind':kind,'path':rel,'sha256':file_hash(p),'slots':ids,'slot_pixel_hashes':hashes})
 if not(OUT/'baseline.json').exists():write(OUT/'baseline.json',baseline)
 write(OUT/'source-audit.json',{'revision':REV,'sources':audit,'native_programs':{s:{k:{'frames':len(v['frames']),'contact':v['contact_tick'],'program':v['source_program_address'],'poses':sorted({f['frame']for f in v['frames']})}for k,v in vv.items()}for s,vv in baseline['variants'].items()}})
 # Approved archer colors and proportions, for style only.
 m=json.loads((ROOT/'professions/class-12-ally/maps/frame_mapping.json').read_text());mp=ROOT/'professions/class-12-ally/maps';q=Image.new('RGB',(1000,400),(32,45,53))
 for n,s in enumerate(m['scenarios']):
  im=Image.open((mp/s['frame_mapping'][0]['output_path']).resolve()).convert('RGBA');im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);q.paste(im,(n*360,45),im)
 q.save(SRC/'approved-archer-colors.png',optimize=True)
if __name__=='__main__':main()
