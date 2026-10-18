from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';O=B/'candidate-recovery-v3';O.mkdir(exist_ok=True)
spec=[{'frame':8,'head_y':252,'feet':[859.5,768],'target_head_y':172,'target_feet':[196,256]},{'frame':9,'head_y':252,'feet':[691.5,770],'target_head_y':172,'target_feet':[196,256]},{'frame':10,'head_y':502,'feet':[846,1160],'target_head_y':176,'target_feet':[180,256]},{'frame':11,'head_y':328,'feet':[492.5,830],'target_head_y':176,'target_feet':[180,256]}];rr=[]
for s in spec:
 name=f'source/recovery-{s["frame"]:03d}-v3-cut.png' if s['frame'] in [8,9] else ('source/pose010-v3-generated.png' if s['frame']==10 else 'source/recovery-011-v2-cut.png');im=Image.open(B/name).convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(s['target_feet'][1]-s['target_head_y'])/(s['feet'][1]-s['head_y']);sz=[round(v*sc)for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_feet'][i]-s['feet'][i]*sc)for i in range(2)];out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);out.save(O/f'frame-{s["frame"]:03d}.png');rr.append({**s,'scale':sc,'resized':sz,'paste':xy,'alpha_bounds':out.getbbox()})
(O/'registration.json').write_text(json.dumps(rr,indent=2)+'\n');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 im=Image.new('RGBA',(1328,624),bg+(255,));d=ImageDraw.Draw(im);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'剑士 · 原作8 / 9 / 10 / 11',font=font,fill=fg);d.text((24,326),'收势稿 v3 · 左高右低 / 双低靴',font=font,fill=fg)
 for k,f in enumerate([8,9,10,11]):
  im.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));im.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 im.convert('RGB').save(B/f'reviews/recovery-8-11-v3-{th}.png',optimize=True)
print(rr)
