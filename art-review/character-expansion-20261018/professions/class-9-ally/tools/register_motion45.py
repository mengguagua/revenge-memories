from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
R=Path(__file__).resolve().parents[1];B=R/'battle';O=B/'candidate-motion45-v3';O.mkdir(exist_ok=True)
spec=[{'frame':4,'raw':'source/pose004-v3-generated.png','head_y':981,'feet':[314.5,1851],'target_head_y':136,'target_feet':[140,244]},{'frame':5,'raw':'source/pose005-v3-generated.png','head_y':450,'feet':[92.5,1337],'target_head_y':128,'target_feet':[148,240]}];rr=[]
for s in spec:
 im=Image.open(B/s['raw']).convert('RGBA');im.putalpha(im.getchannel('A').point(lambda a:0 if a<=8 else a));sc=(s['target_feet'][1]-s['target_head_y'])/(s['feet'][1]-s['head_y']);sz=[round(v*sc)for v in im.size];im=im.resize(sz,Image.Resampling.NEAREST);xy=[round(s['target_feet'][i]-s['feet'][i]*sc)for i in range(2)];out=Image.new('RGBA',(320,256));out.alpha_composite(im,xy);out.save(O/f'frame-{s["frame"]:03d}.png');rr.append({**s,'scale':sc,'resized':sz,'paste':xy,'alpha_bounds':out.getbbox()})
(O/'registration.json').write_text(json.dumps(rr,indent=2)+'\n');font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for th,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 im=Image.new('RGBA',(688,624),bg+(255,));d=ImageDraw.Draw(im);fg=(235,242,244)if th=='dark'else(34,43,47);d.text((24,14),'剑士 · 原作4 / 5',font=font,fill=fg);d.text((24,326),'旋身稿 v3 · 高举剑 / 盾前交叉',font=font,fill=fg)
 for k,f in enumerate([4,5]):
  im.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,44));im.alpha_composite(Image.open(O/f'frame-{f:03d}.png').convert('RGBA'),(24+k*320,356))
 im.convert('RGB').save(B/f'reviews/motion-4-5-v3-{th}.png',optimize=True)
print(rr)
