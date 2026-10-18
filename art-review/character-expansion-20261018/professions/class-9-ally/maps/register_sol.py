# -*- coding: utf-8 -*-
"""Register eight independent source slots. A candidate is not automatically selected."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
M=Path(__file__).resolve().parent;O=M/'candidate-sol';O.mkdir(exist_ok=True)
heads=[132,132,185,200,145,145,144,170];targets=[62,70,42,70,70,54,86,58]
records=[]
for f in range(8):
 d=['up','right','down','left'][f//2];name='sol-native-left-v1-generated.png'if d=='left'else f'native-{d}-v1-generated.png';name='sol-native-right-v2-generated.png'if f==2 else name;raw=Image.open(M/'source'/name).convert('RGBA');cell=[raw.width*(f%2)//2,0,raw.width*((f%2)+1)//2,raw.height];im=raw.crop(cell);a=im.getchannel('A').point(lambda v:255 if v>=32 else 0);b=a.getbbox();scale=64/(b[3]-heads[f]);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);ma=sm.getchannel('A').point(lambda v:255 if v>=32 else 0);bb=ma.getbbox();foot=a.crop((0,b[3]-8,im.width,b[3])).getbbox();cx=(foot[0]+foot[2])/2*sm.width/im.width;dx=round(targets[f]-cx);dy=96-sm.getchannel('A').point(lambda v:255 if v>4 else 0).getbbox()[3];out=Image.new('RGBA',(128,96));out.alpha_composite(sm,(dx,dy));out.save(O/f'frame-{f:03}.png',optimize=True)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<128 and 0<=y+dy<96)]
 records.append({'revision':'sol','source_slot':f,'raw':'source/'+name,'cell':cell,'scale':scale,'raw_hair_top':heads[f],'translation':[dx,dy],'selected_low_boot_center':[cx+dx,bb[3]+dy],'source_selected_low_boot_target':[targets[f],96],'visible_clipped_alpha_gt4':sum(v>4 for v in outside),'cropped_alpha_max':max(outside,default=0),'review':'candidate'})
(M/'source/sol-native-registration.json').write_text(json.dumps(records,indent=2)+'\n')
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 out=Image.new('RGB',(512,384),bg)
 for f in range(8):
  x=f%4*128;y=f//4*192;a=Image.open(M/f'reference/native-{f:03}.png').convert('RGBA').resize((128,96),Image.Resampling.NEAREST);b=Image.open(O/f'frame-{f:03}.png');out.paste(a,(x,y),a);out.paste(b,(x,y+96),b)
 out.resize((1024,768),Image.Resampling.NEAREST).save(M/f'reviews/sol-native-{label}-2x.png',optimize=True)
print(json.dumps(records))
