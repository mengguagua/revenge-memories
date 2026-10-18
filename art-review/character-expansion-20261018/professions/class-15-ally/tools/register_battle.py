#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
R=Path(__file__).resolve().parents[1];B=R/'battle';out=B/'candidate-v1';out.mkdir(exist_ok=True);(B/'reviews').mkdir(exist_ok=True)
i=Image.open(B/'source/battle-v1-generated.png').convert('RGBA')
spec=[{'frame':0,'crop':[173,94,478,691],'raw_top':96,'raw_feet':[317.5,688],'target_top':108,'target_feet':[196,256]}, {'frame':1,'crop':[727,71,1447,692],'raw_top':73,'raw_feet':[1114.5,689],'target_top':100,'target_feet':[200,256]}, {'frame':2,'crop':[1601,122,2075,692],'raw_top':124,'raw_feet':[1853.5,689],'target_top':108,'target_feet':[186,256]}]
records=[]
for s in spec:
 q=i.crop(s['crop']);q.putalpha(q.getchannel('A').point(lambda a:0 if a<=8 else a));q.save(out/f'crop-{s["frame"]:03d}.png');scale=(256-s['target_top'])/(s['raw_feet'][1]-s['raw_top']);size=tuple(round(v*scale)for v in q.size);q=q.resize(size,Image.Resampling.NEAREST);xy=[round(s['target_feet'][j]-(s['raw_feet'][j]-s['crop'][j])*scale)for j in range(2)];c=Image.new('RGBA',(320,256));c.alpha_composite(q,xy);f=out/f'frame-{s["frame"]:03d}.png';c.save(f,optimize=True);records.append({**s,'uniform_scale':scale,'resampled_size':size,'paste':xy,'alpha_bounds':c.getbbox(),'source':'source/battle-v1-generated.png','bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'basis':'Visible supporting boot / paired visible boots, excluding cape bounds. No clamp.'})
(out/'registration.json').write_text(json.dumps(records,indent=2)+'\n');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 o=Image.new('RGBA',(1008,624),bg+(255,));d=ImageDraw.Draw(o);fg=(234,241,243)if theme=='dark'else(34,43,47);d.text((24,14),'我方男魔道士 · 原作0 / 1 / 2',font=font,fill=fg);d.text((24,326),'四倍像素首稿 · 敞披风与可见支撑腿',font=font,fill=fg)
 for k,f in enumerate([0,1,2]):
  o.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));o.alpha_composite(Image.open(out/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 o.convert('RGB').save(B/f'reviews/battle-v1-original-vs-new-{theme}.png',optimize=True)
print(json.dumps(records,indent=2))
