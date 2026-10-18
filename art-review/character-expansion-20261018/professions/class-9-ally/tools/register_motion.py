#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';O=B/'candidate-motion-v1';O.mkdir(exist_ok=True);raw=Image.open(B/'source/motion-1-2-3-v1-generated.png').convert('RGBA')
spec=[{'frame':1,'crop':[0,0,700,754],'head_y':58,'feet':[409.5,648],'target_head_y':144,'target_feet':[202,256]}, {'frame':2,'crop':[700,0,1418,754],'head_y':59,'feet':[1384.5,648],'target_head_y':144,'target_feet':[236,248]}, {'frame':3,'crop':[1418,0,2087,754],'head_y':58,'feet':[1872,507],'target_head_y':144,'target_feet':[186,232]}];rr=[]
for s in spec:
 im=raw.crop(s['crop']);im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(s['target_feet'][1]-s['target_head_y'])/(s['feet'][1]-s['head_y']);sz=[round(v*sc) for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_feet'][i]-(s['feet'][i]-s['crop'][i])*sc)for i in range(2)];out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);out.save(O/f'frame-{s["frame"]:03d}.png');rr.append({**s,'scale':sc,'resized':sz,'paste':xy,'alpha_bounds':out.getbbox()})
(O/'registration.json').write_text(json.dumps(rr,indent=2)+'\n');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 im=Image.new('RGBA',(1008,624),bg+(255,));d=ImageDraw.Draw(im);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'剑士 · 原作1 / 2 / 3',font=font,fill=fg);d.text((24,326),'连续动作首稿 · 跑动 / 跨步 / 收腿',font=font,fill=fg)
 for k,f in enumerate([1,2,3]):
  im.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));im.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 im.convert('RGB').save(B/f'reviews/motion-1-2-3-v1-{th}.png',optimize=True)
print(rr)
