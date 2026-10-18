#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
R=Path(__file__).resolve().parents[1];M=R/'maps';out=M/'frames';out.mkdir(exist_ok=True);(M/'reviews').mkdir(exist_ok=True);(M/'deliverables').mkdir(exist_ok=True)
spec=[{'id':'walk-000','raw':'map-v2-compact-walk.png','crop':[56,38,1037,1355],'top':40,'feet':[433,1352],'target_top':32,'target':[66,96],'size':[128,96]}, {'id':'idle-000','raw':'map-v4-idle000-span.png','crop':[61,54,1096,1334],'top':56,'feet':[619.5,1331],'target_top':16,'target':[50,80],'size':[96,96]}, {'id':'idle-001','raw':'map-v3-idle-sleeves.png','crop':[883,29,1356,712],'top':31,'feet':[1130.5,709],'target_top':16,'target':[48,80],'size':[96,96]}, {'id':'idle-002','raw':'map-v1-generated.png','crop':[1733,112,2094,648],'top':114,'feet':[1915.5,645],'target_top':16,'target':[48,80],'size':[96,96]}]
records=[]
for s in spec:
 i=Image.open(M/'source'/s['raw']).convert('RGBA').crop(s['crop']);i.putalpha(i.getchannel('A').point(lambda v:0 if v<=8 else v));i.save(out/(s['id']+'-crop.png'));scale=(s['target'][1]-s['target_top'])/(s['feet'][1]-s['top']);size=tuple(round(v*scale)for v in i.size);i=i.resize(size,Image.Resampling.NEAREST);xy=[round(s['target'][j]-(s['feet'][j]-s['crop'][j])*scale)for j in range(2)];c=Image.new('RGBA',s['size']);c.alpha_composite(i,xy);dy=s['target'][1]-c.getbbox()[3];xy[1]+=dy;c=Image.new('RGBA',s['size']);c.alpha_composite(i,xy);path=out/(s['id']+'.png');c.save(path,optimize=True);records.append({**s,'scale_uniform':scale,'resampled_size':size,'paste':xy,'alpha_bounds':c.getbbox(),'registered_landmark':[xy[j]+(s['feet'][j]-s['crop'][j])*scale for j in range(2)],'baseline_rounding_adjustment':dy,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'registration_basis':'Visible boots, no cape bounding-box centering or clamp.'})
q=Image.open(out/'walk-000.png').convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);c=Image.new('RGBA',(128,96));c.alpha_composite(q,(4,0));c.save(out/'walk-001.png',optimize=True)
records.append({'id':'walk-001','derived_from':'walk-000.png','transform':'horizontal mirror plus [4,0] output pixels','source_proof':'Native original-walk-15 frame1 RGBA exactly equals mirror(frame0)+[1,0] native px. OAM L0AA5E6 uses same tiles with attr43.'})
for typ,aliases,sz in [('walk',[0,1,0,1,0,1],(128,96)),('idle',[0,1,2,1,0,1],(96,96))]:
 atlas=Image.new('RGBA',(6*sz[0],sz[1]))
 for f,cid in enumerate(aliases):
  q=Image.open(out/f'{typ}-{cid:03d}.png').convert('RGBA');q.save(out/f'{typ}-{f:03d}.png',optimize=True);atlas.alpha_composite(q,(f*sz[0],0))
 atlas.save(M/f'deliverables/tactical-{typ}.png',optimize=True)
 if typ=='walk':
  for f in [0,1]:Image.open(out/f'walk-{f:03d}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(out/f'walk-left-{f:03d}.png',optimize=True)
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 o=Image.new('RGBA',(792,324),bg+(255,));d=ImageDraw.Draw(o);fg=(235,242,244)if theme=='dark'else(34,43,47);d.text((24,16),'原作：镜像步相 0 / 1 · 待机 0 / 1 / 2',font=font,fill=fg);d.text((24,174),'四倍像素：按原OAM整图镜像 · 原袖/手变化',font=font,fill=fg)
 for k,(typ,f)in enumerate([('walk',0),('walk',1),('idle',0),('idle',1),('idle',2)]):
  old=Image.open(M/f'reference/original-{typ}-{f:03d}.png').convert('RGBA');new=Image.open(out/f'{typ}-{f:03d}.png').convert('RGBA');o.alpha_composite(old,(24+k*152,50));o.alpha_composite(new,(24+k*152,208))
 o.convert('RGB').save(M/f'reviews/map-original-vs-new-{theme}.png',optimize=True)
(M/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(records,indent=2))
