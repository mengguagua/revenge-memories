#!/usr/bin/env python3
"""Freeze allied healer18 and saint17 native motion and art references."""
from baseline_json import baseline_exists,write_baseline
import json,math,hashlib
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
REV='healer-saint-complete-v1-20261023';OUT=ROOT/REV;SRC=OUT/'source'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 SRC.mkdir(parents=True,exist_ok=True);full=json.loads((ROOT/'source-input/original-motion/full-original-motion.json').read_text());full['variants'].update(json.loads((ROOT/'source-input/corrected-ally-motion/overlay.json').read_text())['variants']);b={'gallery':json.loads((ROOT/'demos/gallery-data.json').read_text()),'classes':{},'class_names':json.loads((ROOT.parents[1]/'actual/data/class_names.json').read_text())};audit=[]
 for c in[18,17]:
  body=full['original_bodies'][str(c)];vs={k:v for k,v in full['variants'].items()if str(v.get('source_class_id'))==str(c)};used=sorted({body['sequences']['idle'][0],*[f['frame']for v in vs.values()for f in v['frames']]});b['classes'][str(c)]={'body':body,'variants':vs};out=SRC/f'class-{c}';out.mkdir(exist_ok=True)
  for kind,rel,size,ids,cols,scale in [('idle',f'source-input/legacy-assets/assets/original/graphics/map_units/class_{c}_ally.png',(24,24),list(range(6)),3,12),('walk',f'source-input/corrected-tactical-walk/class-{c}-ally.png',(32,24),list(range(8)),4,10),('battle',f'source-input/original-motion/class-{c}.png',body['frame_size'],used,4,5)]:
   atlas=Image.open(ROOT/rel).convert('RGBA');nc=atlas.width//size[0];cw,ch=size[0]*scale,size[1]*scale;guide=Image.new('RGB',(cols*cw,(ch+32)*math.ceil(len(ids)/cols)),(32,45,53));dr=ImageDraw.Draw(guide);aliases={};seen={}
   for n,i in enumerate(ids):
    im=atlas.crop((i%nc*size[0],i//nc*size[1],i%nc*size[0]+size[0],i//nc*size[1]+size[1]));im.save(out/f'native-{kind}-{i:03}.png',optimize=True);h=hashlib.sha256(im.tobytes()).hexdigest();aliases[str(i)]=seen.setdefault(h,i);big=im.resize((cw,ch),Image.Resampling.NEAREST);x=n%cols*cw;y=n//cols*(ch+32);guide.paste(big,(x,y),big);dr.text((x+cw//2,y+ch+16),str(i),anchor='mm',font=font(18),fill=(235,240,226))
   guide.save(out/f'native-{kind}-guide.png',optimize=True);audit.append({'class':c,'kind':kind,'path':rel,'sha256':file_hash(ROOT/rel),'slots':ids,'aliases':aliases})
   targets=[(list(range(3)),3,'idle')]if kind=='idle'else[(list(range(6)),3,'walk')]if kind=='walk'else[(used[n:n+6],3,f'battle-{n//6}')for n in range(0,len(used),6)]
   for slots,cols2,label in targets:
    q=Image.new('RGBA',(cw*cols2,ch*math.ceil(len(slots)/cols2)))
    for n,i in enumerate(slots):q.alpha_composite(Image.open(out/f'native-{kind}-{i:03}.png').convert('RGBA').resize((cw,ch),Image.Resampling.NEAREST),(n%cols2*cw,n//cols2*ch))
    q.save(out/f'target-{label}.png',optimize=True)
  print(c,'variants',len(vs),'battle',used,flush=True)
 if not baseline_exists(OUT/'baseline.json'):write_baseline(OUT/'baseline.json',b)
 write(OUT/'source-audit.json',{'revision':REV,'sources':audit,'enemy_excluded':True})
if __name__=='__main__':main()
