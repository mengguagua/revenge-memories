#!/usr/bin/env python3
"""Mechanical crop/scale/anchor registration of image-generated sprites; never paints anatomy."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'battle';out=B/'candidate-v1';out.mkdir(exist_ok=True);(B/'reviews').mkdir(exist_ok=True)
raw=Image.open(B/'source/battle-v1-generated.png').convert('RGBA')
scale=128/(774-190)
registration=[]
for frame,crop,hem in [(7,(124,188,504,776),(342,774)),(8,(1451,21,1839,776),(1678,774))]:
 im=raw.crop(crop);alpha=im.getchannel('A');removed=sum(0<a<=8 for a in alpha.getdata());im.putalpha(alpha.point(lambda a:0 if a<=8 else a))
 im.save(out/f'crop-{frame:03d}.png');size=tuple(round(v*scale)for v in im.size);im=im.resize(size,Image.Resampling.NEAREST)
 x=round(196-(hem[0]-crop[0])*scale);y=round(256-(hem[1]-crop[1])*scale)
 canvas=Image.new('RGBA',(320,256));canvas.alpha_composite(im,(x,y));canvas.save(out/f'frame-{frame:03d}.png',optimize=True)
 registration.append({'source_frame':frame,'raw':'source/battle-v1-generated.png','crop_global':crop,'scale_uniform':scale,'resampled_size':size,'paste':[x,y],'source_hood_top_y':128,'target_visible_robe_hem':[196,256],'raw_hood_top_y':190,'raw_visible_robe_hem':hem,'basis':'Visible continuous robe hem, not hidden feet or staff bounds. No positional clamp.','alpha_noise_threshold':8,'low_alpha_pixels_removed':removed,'alpha_bounds':canvas.getbbox(),'bytes':(out/f'frame-{frame:03d}.png').stat().st_size,'sha256':hashlib.sha256((out/f'frame-{frame:03d}.png').read_bytes()).hexdigest()})
(out/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(225,226,218))]:
 board=Image.new('RGBA',(688,624),bg+(255,));d=ImageDraw.Draw(board);fg=(232,240,242)if theme=='dark'else(35,44,48)
 d.text((24,14),'修女职业样板 · 原作7 / 8',font=font,fill=fg)
 d.text((24,326),'四倍像素首稿 · 衣装与姿势对照',font=font,fill=fg)
 for k,f in enumerate([7,8]):
  board.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+320*k,44))
  board.alpha_composite(Image.open(out/f'frame-{f:03d}.png').convert('RGBA'),(24+320*k,356))
 board.convert('RGB').save(B/f'reviews/battle-v1-original-vs-new-{theme}.png',optimize=True)
print(json.dumps(registration,indent=2))
