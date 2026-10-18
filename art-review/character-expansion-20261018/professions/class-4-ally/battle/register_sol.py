# -*- coding: utf-8 -*-
"""Register selected ImageGen art by uniform scale and whole-frame translation."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,sys
P=Path(__file__).resolve().parent;R=P.parent/'reference'
SPECS={
 0:dict(raw='sol-pose-000-v2-generated.png',crop=[0,0,1280,1280],scale=160/804,point=[587,1138],target=[160,256]),
 1:dict(raw='sol-gallop-123-v2-generated.png',crop=[0,0,724,724],scale=160/472,point=[590.5,669],target=[238,256]),
 2:dict(raw='sol-pose-002-v4-generated.png',crop=[0,0,1280,1280],scale=160/829,point=[535,1164],target=[158,256]),
 3:dict(raw='sol-pose-003-v4-generated.png',crop=[0,0,1280,1280],scale=160/797,point=[650,1117],target=[200,256]),
 4:dict(raw='sol-gallop-4589-v2-generated.png',crop=[0,0,688,572],scale=168/433,point=[407,516],target=[188,256]),
 5:dict(raw='sol-gallop-4589-v2-generated.png',crop=[688,0,1376,572],scale=160/418,point=[421,502],target=[204,244]),
 6:dict(raw='sol-keys-v3-generated.png',crop=[724,0,1448,724],scale=184/501,point=[530.7,665],target=[242,256]),
 7:dict(raw='sol-keys-v2-generated.png',crop=[1448,0,2172,724],scale=136/387,point=[646.5,625],target=[274,216]),
 8:dict(raw='sol-gallop-4589-v2-generated.png',crop=[0,572,688,1143],scale=160/466,point=[346,525],target=[160,256]),
 9:dict(raw='sol-gallop-4589-v2-generated.png',crop=[688,572,1376,1143],scale=160/466,point=[331.5,526],target=[162,256]),
 41:dict(raw='sol-javelin-v1-generated.png',crop=[0,0,972,808],scale=160/633,point=[517.5,767],target=[160,256]),
 43:dict(raw='sol-javelin-v1-generated.png',crop=[972,0,1945,808],scale=160/633,point=[441.5,767],target=[160,256]),
}
def register(f,s):
 im=Image.open(P/'source'/s['raw']).convert('RGBA').crop(s['crop']);a=im.getchannel('A');box=a.point(lambda v:255 if v>4 else 0).getbbox()
 # Crop only a large technical cell, never erase any visible transparency.
 scale=s['scale'];out=Image.new('RGBA',(320,256));offset=[round(s['target'][i]-s['point'][i]*scale)for i in range(2)]
 resized=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
 visible=resized.getchannel('A').point(lambda v:255 if v>4 else 0).getbbox()
 assert visible and visible[0]+offset[0]>=0 and visible[1]+offset[1]>=0 and visible[2]+offset[0]<=320 and visible[3]+offset[1]<=256,(f,visible,offset)
 out.alpha_composite(resized,offset);out.save(P/f'frames/frame-{f:03}.png',optimize=True)
 return dict(source_frame=f,author='sol',**s,offset=offset,raw_visible_bbox=box,output_visible_bbox=out.getbbox(),registration_scope='Selected visible sole point and body height; not a proof of all joints.')
if __name__=='__main__':
 records=[register(f,s)for f,s in SPECS.items()]
 (P/'source/sol-registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 for color,name in [('#eee8d8','light'),('#1d2932','dark')]:
  out=Image.new('RGB',(960,4*552),color);d=ImageDraw.Draw(out)
  for i,f in enumerate(SPECS):
   for yy,path in [(24,R/f'original-{f:03}.png'),(288,P/f'frames/frame-{f:03}.png')]:
    im=Image.open(path).convert('RGBA');im=im.resize((320,256),Image.Resampling.NEAREST);out.paste(im,((i%3)*320,(i//3)*552+yy),im)
   d.text(((i%3)*320+10,(i//3)*552+5),f'{f:03} original / sol',fill='white'if name=='dark'else'black')
  out.save(P/f'reviews/sol-keys-{name}.png',optimize=True)
 print('Registered',list(SPECS))
