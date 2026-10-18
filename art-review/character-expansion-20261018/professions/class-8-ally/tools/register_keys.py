#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';O=B/'candidate-keys-v1';O.mkdir(exist_ok=True);raw=Image.open(B/'source/keys-v1-generated.png').convert('RGBA')
spec=[{'frame':0,'crop':[0,300,520,950],'head_y':367,'feet':[350,885],'target_head_y':136,'target_feet':[202,256]}, {'frame':7,'crop':[520,300,1100,950],'head_y':400,'feet':[872,887],'target_head_y':144,'target_feet':[202,256]}, {'frame':16,'crop':[1100,0,1567,950],'head_y':367,'feet':[1409,887],'target_head_y':136,'target_feet':[202,256]}];rr=[]
for s in spec:
 im=raw.crop(s['crop']);im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(256-s['target_head_y'])/(s['feet'][1]-s['head_y']);sz=[round(v*sc) for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_feet'][i]-(s['feet'][i]-s['crop'][i])*sc)for i in range(2)];out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);dy=256-out.getbbox()[3];xy[1]+=dy;out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);out.save(O/f'frame-{s["frame"]:03d}.png');rr.append({**s,'scale':sc,'resized':sz,'paste':xy,'alpha_bounds':out.getbbox(),'baseline_rounding_adjustment':dy})
(O/'registration.json').write_text(json.dumps(rr,indent=2)+'\n');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 im=Image.new('RGBA',(1008,624),bg+(255,));d=ImageDraw.Draw(im);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'我方佣兵 · 原作0 / 7 / 16',font=font,fill=fg);d.text((24,326),'关键稿 · 深紫分片战衣与单肩护甲',font=font,fill=fg)
 for k,f in enumerate([0,7,16]):
  im.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));im.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 im.convert('RGB').save(B/f'reviews/keys-v1-original-vs-new-{th}.png',optimize=True)
print(rr)
