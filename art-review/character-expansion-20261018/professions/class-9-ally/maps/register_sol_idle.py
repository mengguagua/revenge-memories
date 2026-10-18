# -*- coding: utf-8 -*-
"""Split at measured transparent gaps, uniform register all three idle sprites."""
from pathlib import Path
from PIL import Image
import json
M=Path(__file__).resolve().parent;raw=Image.open(M/'source/sol-idle-v1-generated.png').convert('RGBA');edges=[0,844,1390,2170];recs=[]
# Equal thirds would cut first shield into the next sprite. Confirm full RGBA reassembly.
reassembled=Image.new('RGBA',raw.size)
for i in range(3):reassembled.paste(raw.crop((edges[i],0,edges[i+1],raw.height)),(edges[i],0))
assert raw.size==reassembled.size and raw.tobytes()==reassembled.tobytes()
for i in range(3):
 cell=(edges[i],0,edges[i+1],raw.height);im=raw.crop(cell);a=im.getchannel('A').point(lambda v:255 if v>=32 else 0);b=a.getbbox();head=82;scale=64/(b[3]-head);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);roi=([570,270,225][i],b[3]-10,im.width,b[3]);foot=a.crop(roi).getbbox();cx=(roi[0]+(foot[0]+foot[2])/2)*sm.width/im.width;dx=round(66-cx);bottom=sm.getchannel('A').point(lambda v:255 if v>4 else 0).getbbox()[3];dy=80-bottom;out=Image.new('RGBA',(96,96));out.alpha_composite(sm,(dx,dy));out.save(M/f'candidate-sol/idle-{i:03}.png',optimize=True)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<96 and 0<=y+dy<96)];assert max(outside,default=0)<=4
 recs.append({'revision':'sol','source_frame':i,'cell':cell,'cut_basis':'Measured transparent inter-sprite gaps; full original RGBA reconstructed exactly. Equal thirds rejected because shield crosses first boundary.','scale':scale,'translation':[dx,dy],'raw_chosen_sole_roi':roi,'source_selected_low_boot_target':[66,80],'registered_selected_low_boot':[cx+dx,bottom+dy],'visible_clipped_alpha_gt4':0,'cropped_alpha_max':max(outside,default=0),'note':'The higher boot has a few output pixels of silhouette variation; not every-joint exactness.'})
(M/'source/sol-idle-registration.json').write_text(json.dumps(recs,indent=2)+'\n')
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 out=Image.new('RGB',(288,192),bg)
 for i in range(3):
  a=Image.open(M/f'reference/idle-{i:03}.png').convert('RGBA').resize((96,96),Image.Resampling.NEAREST);b=Image.open(M/f'candidate-sol/idle-{i:03}.png');out.paste(a,(i*96,0),a);out.paste(b,(i*96,96),b)
 out.resize((864,576),Image.Resampling.NEAREST).save(M/f'reviews/sol-idle-{label}-3x.png',optimize=True)
print('Three static poses registered without cutting shield edges.')
