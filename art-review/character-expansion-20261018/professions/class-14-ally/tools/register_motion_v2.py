#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';O=B/'candidate-motion-v2';O.mkdir(exist_ok=True)
spec=[{'frame':1,'file':'run-1-2-3-v2-generated.png','crop':[0,0,620,848],'head_y':322,'foot':[493,806],'target_head_y':148,'target_foot':[226,256]}, {'frame':2,'file':'run-1-2-3-v2-generated.png','crop':[620,0,1250,848],'head_y':334,'foot':[946,794],'target_head_y':152,'target_foot':[194,256]}, {'frame':3,'file':'run-1-2-3-v2-generated.png','crop':[1250,0,1855,848],'head_y':330,'foot':[1724,807],'target_head_y':148,'target_foot':[214,256]}, {'frame':5,'file':'pose005-v2-generated.png','crop':[0,0,1168,1347],'head_y':452,'foot':[653,1267],'target_head_y':164,'target_foot':[190,256]}, {'frame':6,'file':'pose006-v2-generated.png','crop':[0,0,1261,1247],'head_y':358,'foot':[759,1150],'target_head_y':164,'target_foot':[192,256]}]
rr=[]
for s in spec:
 im=Image.open(B/'source'/s['file']).convert('RGBA').crop(s['crop']);im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(256-s['target_head_y'])/(s['foot'][1]-s['head_y']);sz=[round(v*sc) for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_foot'][i]-(s['foot'][i]-s['crop'][i])*sc) for i in range(2)];out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);dy=256-out.getbbox()[3];xy[1]+=dy;out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);out.save(O/f'frame-{s["frame"]:03d}.png');rr.append({**s,'scale':sc,'resized':sz,'paste':xy,'alpha_bounds':out.getbbox(),'baseline_rounding_adjustment':dy})
(O/'registration.json').write_text(json.dumps(rr,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 im=Image.new('RGBA',(1648,624),bg+(255,));d=ImageDraw.Draw(im);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'村民剑士 · 原作1 / 2 / 3 / 5 / 6',font=font,fill=fg);d.text((24,326),'四倍像素动作修订 · 刀尖、握点与原脚相',font=font,fill=fg)
 for k,f in enumerate([1,2,3,5,6]):
  im.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));im.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 im.convert('RGB').save(B/f'reviews/motion-v2-original-vs-new-{th}.png',optimize=True)
print(rr)
