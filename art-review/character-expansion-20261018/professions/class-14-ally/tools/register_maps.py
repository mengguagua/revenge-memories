#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
R=Path(__file__).resolve().parents[1];M=R/'maps';out=M/'frames';out.mkdir(exist_ok=True)
spec=[{'id':'walk-000','raw':'walk-v2-generated.png','crop':[280,90,820,880],'top':130,'feet':[551,825],'target_top':32,'target':[64,96],'size':[128,96]}, {'id':'walk-001','raw':'walk-v2-generated.png','crop':[950,90,1470,880],'top':140,'feet':[1348,844],'target_top':32,'target':[74,96],'size':[128,96]}, {'id':'idle-000','raw':'idle-v2-generated.png','crop':[90,160,560,710],'top':211,'feet':[361,668],'target_top':16,'target':[50,80],'size':[96,96]}, {'id':'idle-001','raw':'idle-v2-generated.png','crop':[740,160,1140,710],'top':211,'feet':[944,668],'target_top':16,'target':[50,80],'size':[96,96]}, {'id':'idle-002','raw':'idle002-v4-generated.png','crop':[0,0,1012,1554],'top':9,'feet':[506,1540],'target_top':16,'target':[50,80],'size':[96,96]}]
records=[]
for s in spec:
 i=Image.open(M/'source'/s['raw']).convert('RGBA').crop(s['crop']);i.putalpha(i.getchannel('A').point(lambda v:0 if v<=8 else v));scale=(s['target'][1]-s['target_top'])/(s['feet'][1]-s['top']);size=tuple(round(v*scale)for v in i.size);i=i.resize(size,Image.Resampling.NEAREST);xy=[round(s['target'][j]-(s['feet'][j]-s['crop'][j])*scale)for j in range(2)];c=Image.new('RGBA',s['size']);c.alpha_composite(i,xy);dy=s['target'][1]-c.getbbox()[3];xy[1]+=dy;c=Image.new('RGBA',s['size']);c.alpha_composite(i,xy);path=out/(s['id']+'.png');c.save(path,optimize=True);records.append({**s,'scale_uniform':scale,'resampled_size':size,'paste':xy,'alpha_bounds':c.getbbox(),'registered_landmark':[xy[j]+(s['feet'][j]-s['crop'][j])*scale for j in range(2)],'baseline_rounding_adjustment':dy,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'registration_basis':'Visible boot soles, not weapon bounding-box centering; no clamp.'})
for typ,aliases,sz in [('walk',[0,1,0,1,0,1],(128,96)),('idle',[0,1,2,1,0,1],(96,96))]:
 atlas=Image.new('RGBA',(6*sz[0],sz[1]))
 for f,cid in enumerate(aliases):
  q=Image.open(out/f'{typ}-{cid:03d}.png').convert('RGBA');q.save(out/f'{typ}-{f:03d}.png',optimize=True);atlas.alpha_composite(q,(f*sz[0],0))
 atlas.save(M/f'deliverables/tactical-{typ}.png',optimize=True)
 if typ=='walk':
  for f in [0,1]:Image.open(out/f'walk-{f:03d}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(out/f'walk-left-{f:03d}.png',optimize=True)
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 o=Image.new('RGBA',(792,324),bg+(255,));d=ImageDraw.Draw(o);fg=(235,242,244)if theme=='dark'else(34,43,47);d.text((24,16),'原作：行走 0 / 1 · 待机 0 / 1 / 2',font=font,fill=fg);d.text((24,174),'四倍像素：短刃和衣面分辨 · 原步相',font=font,fill=fg)
 for k,(typ,f)in enumerate([('walk',0),('walk',1),('idle',0),('idle',1),('idle',2)]):
  old=Image.open(M/f'reference/{typ}-{f:03d}-4x.png').convert('RGBA');new=Image.open(out/f'{typ}-{f:03d}.png').convert('RGBA');o.alpha_composite(old,(24+k*152,50));o.alpha_composite(new,(24+k*152,208))
 o.convert('RGB').save(M/f'reviews/map-original-vs-new-{theme}.png',optimize=True)
 o.convert('RGB').resize((2376,972),Image.Resampling.NEAREST).save(M/f'reviews/map-original-vs-new-{theme}-3x.png',optimize=True)
(M/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(records,indent=2))
