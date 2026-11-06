#!/usr/bin/env python3
"""Freeze class11 ally source only; enemy is excluded by user instruction."""
from baseline_json import baseline_exists,write_baseline
import json,math,hashlib,shutil
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,pack_frame
from export_gallery import font
REV='spellsword-complete-v1-20261023';OUT=ROOT/REV;SRC=OUT/'source'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sheet(ids,kind,name,cols=3,scale=6):
 ims=[Image.open(SRC/f'native-{kind}-{i:03}.png').convert('RGBA')for i in ids];w,h=ims[0].size;cw,ch=w*scale,h*scale;q=Image.new('RGBA',(cw*cols,ch*math.ceil(len(ids)/cols)))
 for n,im in enumerate(ims):q.alpha_composite(im.resize((cw,ch),Image.Resampling.NEAREST),(n%cols*cw,n//cols*ch))
 q.save(SRC/name,optimize=True)
def main():
 SRC.mkdir(parents=True,exist_ok=True);motion=json.loads((ROOT/'source-input/original-motion/full-original-motion.json').read_text());motion['variants'].update(json.loads((ROOT/'source-input/corrected-ally-motion/overlay.json').read_text())['variants']);vs={k:v for k,v in motion['variants'].items()if str(v.get('source_class_id'))=='11'};body=motion['original_bodies']['11'];used=sorted({50,*[f['frame']for v in vs.values()for f in v['frames']]})
 if not baseline_exists(OUT/'baseline.json'):write_baseline(OUT/'baseline.json',{'gallery':json.loads((ROOT/'demos/gallery-data.json').read_text()),'body':body,'variants':vs,'enemy_excluded_by_user':True})
 sources=[];aliases={}
 for kind,rel,size,ids,scale,cols in [('idle','source-input/legacy-assets/assets/original/graphics/map_units/class_11_ally.png',(24,24),list(range(6)),10,3),('walk','source-input/corrected-tactical-walk/class-11-ally.png',(32,24),list(range(8)),10,4),('battle','source-input/original-motion/class-11.png',tuple(body['frame_size']),used,4,4)]:
  p=ROOT/rel;atlas=Image.open(p).convert('RGBA');nc=atlas.width//size[0];cw,ch=size[0]*scale,size[1]*scale+28;q=Image.new('RGB',(cw*cols,40+ch*math.ceil(len(ids)/cols)),(32,45,53));dr=ImageDraw.Draw(q);dr.text((q.width//2,20),'class11 ally '+kind,anchor='mm',font=font(18),fill=(240,240,224));seen={}
  for n,i in enumerate(ids):
   im=atlas.crop((i%nc*size[0],i//nc*size[1],i%nc*size[0]+size[0],i//nc*size[1]+size[1]));im.save(SRC/f'native-{kind}-{i:03}.png',optimize=True);digest=hashlib.sha256(im.tobytes()).hexdigest();aliases[kind,i]=seen.setdefault(digest,i);large=im.resize((size[0]*scale,size[1]*scale),Image.Resampling.NEAREST);x=n%cols*cw;y=40+n//cols*ch;q.paste(large,(x,y),large);dr.text((x+cw//2,y+ch-14),str(i),anchor='mm',font=font(16),fill=(240,240,224))
  q.save(SRC/f'native-{kind}-all.png',optimize=True);sources.append({'path':rel,'sha256':file_hash(p),'kind':kind,'slots':ids})
 sheet([0,1,2],'idle','target-idle.png',3,14);sheet([0,1,2,3,4,5],'walk','target-walk.png',3,14)
 ids=[i for i in used if aliases['battle',i]==i]
 for n in range(0,len(ids),6):sheet(ids[n:n+6],'battle',f'target-battle-{n//6:02}.png',3,6)
 shutil.copyfile(ROOT/'female-mage-complete-v1-20261023/ally-maps-light.png',SRC/'approved-female-mage-maps.png');shutil.copyfile(ROOT/'female-mage-complete-v1-20261023/source/battle-master.png',SRC/'approved-female-mage-design.png')
 write(OUT/'source-audit.json',{'revision':REV,'sources':sources,'required_battle_slots':used,'exact_aliases':{k:{str(i):j for(kk,i),j in aliases.items()if kk==k}for k in ['idle','walk','battle']},'unique_battle_slots':ids,'variants':{k:{'ticks':len(v['frames']),'contact':v['contact_tick'],'program':v['source_program_address'],'frames':sorted({f['frame']for f in v['frames']})}for k,v in vs.items()},'enemy_excluded_by_user':True})
 print(json.dumps({'variants':len(vs),'required_battle_slots':len(used),'unique_battle_slots':ids}),flush=True)
if __name__=='__main__':main()
