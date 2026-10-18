#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'maps';out=M/'frames';out.mkdir(exist_ok=True);(M/'deliverables').mkdir(exist_ok=True);(M/'reviews').mkdir(exist_ok=True)
selected=[
 {'id':'walk-000','raw':'map-v2-walk.png','crop':[237,108,717,831],'hood_y':110,'landmark':[462,829],'target':[68,96],'target_hood_y':32,'size':[128,96],'kind':'visible planted shoe pair'},
 {'id':'walk-001','raw':'map-v2-walk.png','crop':[964,108,1532,831],'hood_y':110,'landmark':[1104.5,829],'target':[50,96],'target_hood_y':32,'size':[128,96],'kind':'visible rear planted shoe; front shoe remains lifted'},
 {'id':'idle-000','raw':'map-v3-idle-reach.png','crop':[60,47,712,894],'hood_y':49,'landmark':[461.5,891],'target':[56,80],'target_hood_y':16,'size':[96,96],'kind':'continuous main robe hem, excludes staff base'},
 {'id':'idle-002','raw':'map-v3-idle-reach.png','crop':[923,71,1605,895],'hood_y':73,'landmark':[1361,892],'target':[56,80],'target_hood_y':16,'size':[96,96],'kind':'continuous main robe hem, excludes staff base'}]
records=[]
for s in selected:
 i=Image.open(M/'source'/s['raw']).convert('RGBA').crop(s['crop']);a=i.getchannel('A');i.putalpha(a.point(lambda v:0 if v<=8 else v));i.save(out/(s['id']+'-crop.png'))
 scale=(s['target'][1]-s['target_hood_y'])/(s['landmark'][1]-s['hood_y']);i=i.resize(tuple(round(v*scale)for v in i.size),Image.Resampling.NEAREST)
 xy=[round(s['target'][j]-(s['landmark'][j]-s['crop'][j])*scale)for j in range(2)];c=Image.new('RGBA',s['size']);c.alpha_composite(i,xy);path=out/(s['id']+'.png');c.save(path,optimize=True)
 records.append({**s,'scale_uniform':scale,'paste':xy,'resampled_size':list(i.size),'registered_landmark':[xy[j]+(s['landmark'][j]-s['crop'][j])*scale for j in range(2)],'alpha_bounds':c.getbbox(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'clamp_applied':False})
for typ,aliases,sz in [('walk',[0,1,0,1,0,1],(128,96)),('idle',[0,0,2,0,0,0],(96,96))]:
 atlas=Image.new('RGBA',(sz[0]*6,sz[1]))
 for f,canonical in enumerate(aliases):
  i=Image.open(out/f'{typ}-{canonical:03d}.png').convert('RGBA');i.save(out/f'{typ}-{f:03d}.png',optimize=True);atlas.alpha_composite(i,(f*sz[0],0))
 atlas.save(M/f'deliverables/tactical-{typ}.png',optimize=True)
 if typ=='walk':
  for f in [0,1]:Image.open(out/f'walk-{f:03d}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(out/f'walk-left-{f:03d}.png',optimize=True)
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(230,229,219))]:
 board=Image.new('RGBA',(640,324),bg+(255,));d=ImageDraw.Draw(board);fg=(235,242,244)if theme=='dark'else(38,43,43)
 d.text((24,16),'原作：通用步相 0 / 1 · 修女待机 0 / 2',font=font,fill=fg);d.text((24,174),'四倍像素：过步 / 跨步 · 原杖姿待机',font=font,fill=fg)
 for k,(typ,f)in enumerate([('walk',0),('walk',1),('idle',0),('idle',2)]):
  old=Image.open(M/f'reference/original-{typ}-{f:03d}.png').convert('RGBA');new=Image.open(out/f'{typ}-{f:03d}.png').convert('RGBA');x=24+k*152
  board.alpha_composite(old,(x,50));board.alpha_composite(new,(x,208))
 board.convert('RGB').save(M/f'reviews/map-original-vs-new-{theme}.png',optimize=True)
(M/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(records,indent=2))
