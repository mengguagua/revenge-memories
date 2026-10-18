#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';o=B/'candidate-keys-v1';o.mkdir(exist_ok=True);(B/'reviews').mkdir(exist_ok=True);raw=Image.open(B/'source/keys-v1-generated.png').convert('RGBA')
spec=[{'frame':0,'crop':[185,305,468,681],'head_y':307,'feet':[389,678],'target_head_y':132,'target_feet':[198,256]}, {'frame':4,'crop':[958,123,1269,679],'head_y':371,'feet':[1113,676],'target_head_y':152,'target_feet':[192,256]}, {'frame':32,'crop':[1722,30,1882,681],'head_y':307,'feet':[1801,678],'target_head_y':132,'target_feet':[198,256]}]
rr=[]
for s in spec:
 i=raw.crop(s['crop']);i.putalpha(i.getchannel('A').point(lambda v:0 if v<=8 else v));i.save(o/f'crop-{s["frame"]:03d}.png');sc=(256-s['target_head_y'])/(s['feet'][1]-s['head_y']);sz=tuple(round(v*sc)for v in i.size);i=i.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_feet'][j]-(s['feet'][j]-s['crop'][j])*sc)for j in range(2)];c=Image.new('RGBA',(320,256));c.alpha_composite(i,xy);dy=256-c.getbbox()[3];xy[1]+=dy;c=Image.new('RGBA',(320,256));c.alpha_composite(i,xy);c.save(o/f'frame-{s["frame"]:03d}.png',optimize=True);rr.append({**s,'uniform_scale':sc,'resampled_size':sz,'paste':xy,'alpha_bounds':c.getbbox(),'baseline_rounding_adjustment':dy,'basis':'Visible paired boot soles, not sword bounding box; no clamp.'})
(o/'registration.json').write_text(json.dumps(rr,indent=2)+'\n');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 im=Image.new('RGBA',(1008,624),bg+(255,));d=ImageDraw.Draw(im);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'村民剑士 · 原作0 / 4 / 32',font=font,fill=fg);d.text((24,326),'四倍像素关键稿 · 轻装短背心与布绑腿',font=font,fill=fg)
 for k,f in enumerate([0,4,32]):
  im.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));im.alpha_composite(Image.open(o/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 im.convert('RGB').save(B/f'reviews/keys-v1-original-vs-new-{th}.png',optimize=True)
print(json.dumps(rr,indent=2))
