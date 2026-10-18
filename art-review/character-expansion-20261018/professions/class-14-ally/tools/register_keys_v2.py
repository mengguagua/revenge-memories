#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';O=B/'candidate-keys-v2';O.mkdir(exist_ok=True)
spec=[{'frame':0,'file':'pose000-v2-generated.png','head_y':104,'feet':[743,1286],'target_head_y':132,'target_feet':[198,256]}, {'frame':4,'file':'pose004-v3-generated.png','head_y':811,'feet':[457,1648],'target_head_y':152,'target_feet':[192,256]}, {'frame':32,'file':'pose032-v4-generated.png','head_y':1050,'feet':[382,2122],'target_head_y':132,'target_feet':[198,256]}]
rr=[]
for s in spec:
 im=Image.open(B/'source'/s['file']).convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(256-s['target_head_y'])/(s['feet'][1]-s['head_y']);sz=[round(v*sc) for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_feet'][i]-s['feet'][i]*sc) for i in range(2)];out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);dy=256-out.getbbox()[3];xy[1]+=dy;out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);out.save(O/f'frame-{s["frame"]:03d}.png');rr.append({**s,'scale':sc,'resized':sz,'paste':xy,'alpha_bounds':out.getbbox(),'baseline_rounding_adjustment':dy})
(O/'registration.json').write_text(json.dumps(rr,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 im=Image.new('RGBA',(1008,624),bg+(255,));d=ImageDraw.Draw(im);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'村民剑士 · 原作0 / 4 / 32',font=font,fill=fg);d.text((24,326),'四倍像素关键稿 · 局部握点与剑长修订',font=font,fill=fg)
 for k,f in enumerate([0,4,32]):
  im.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));im.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 im.convert('RGB').save(B/f'reviews/keys-v2-original-vs-new-{th}.png',optimize=True)
 print(th)
print(rr)
