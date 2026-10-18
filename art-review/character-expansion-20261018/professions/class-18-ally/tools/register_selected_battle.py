#!/usr/bin/env python3
"""Register selected generated sprite poses using visible hood and robe-hem landmarks."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'battle';out=B/'candidate-final';out.mkdir(exist_ok=True);(B/'reviews').mkdir(exist_ok=True)
selected=[{'frame':7,'raw':'battle-v4-pose007.png','crop':[60,78,982,1499],'hood_y':80,'hem':[584,1497]}, {'frame':8,'raw':'battle-v5-pose008.png','crop':[207,57,920,1555],'hood_y':381,'hem':[591.5,1553]}]
records=[]
for s in selected:
 raw=Image.open(B/'source'/s['raw']).convert('RGBA');crop=s['crop'];im=raw.crop(crop);alpha=im.getchannel('A');removed=sum(0<a<=8 for a in alpha.getdata());im.putalpha(alpha.point(lambda a:0 if a<=8 else a));im.save(out/f'crop-{s["frame"]:03d}.png')
 scale=128/(s['hem'][1]-s['hood_y']);size=tuple(round(v*scale)for v in im.size);im=im.resize(size,Image.Resampling.NEAREST)
 xy=[round(196-(s['hem'][0]-crop[0])*scale),round(256-(s['hem'][1]-crop[1])*scale)]
 canvas=Image.new('RGBA',(320,256));canvas.alpha_composite(im,xy);path=out/f'frame-{s["frame"]:03d}.png';canvas.save(path,optimize=True)
 records.append({**s,'uniform_scale':scale,'resampled_size':size,'paste':xy,'target_visible_hood_y':128,'target_visible_robe_hem':[196,256],'registration_basis':'Visible continuous robe hem and hood top; no hidden joint guess, no silhouette clamp.','alpha_noise_threshold':8,'low_alpha_pixels_removed':removed,'output_alpha_bounds':canvas.getbbox(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(out/'registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(225,226,218))]:
 board=Image.new('RGBA',(688,624),bg+(255,));d=ImageDraw.Draw(board);fg=(232,240,242)if theme=='dark'else(35,44,48)
 d.text((24,14),'修女职业样板 · 原作7 / 8',font=font,fill=fg)
 d.text((24,326),'四倍像素修正稿 · 保留原握持与举杖',font=font,fill=fg)
 for k,f in enumerate([7,8]):
  board.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+320*k,44))
  board.alpha_composite(Image.open(out/f'frame-{f:03d}.png').convert('RGBA'),(24+320*k,356))
 board.convert('RGB').save(B/f'reviews/battle-final-original-vs-new-{theme}.png',optimize=True)
print(json.dumps(records,indent=2))
