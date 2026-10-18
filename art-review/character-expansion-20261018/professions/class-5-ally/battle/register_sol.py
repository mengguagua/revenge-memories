# -*- coding: utf-8 -*-
"""Native5 registration: crop at actual gaps, isotropic resize, whole-sprite XY only."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
B=Path(__file__).resolve().parent;P=B.parent;O=B/'candidate-sol';O.mkdir(exist_ok=True)
def mask(im,t=128):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
configs=[(1,'sol-poses-1-2-v3-generated.png',[0,0,750,1024],[216,384],28),(2,'sol-poses-1-2-v3-generated.png',[750,0,1536,1024],[196,376],51),(4,'sol-poses-4-5-v2-generated.png',0,[204,384],61),(5,'sol-poses-4-5-v2-generated.png',1,[216,380],32),(6,'sol-pose-006-v1-generated.png',None,[212,384],27),(49,'sol-pose-049-v2-generated.png',None,[212,384],27),(50,'sol-pose-050-v1-generated.png',None,[212,384],27)]
recs=[]
for f,name,cell,target,top in configs:
 raw=Image.open(B/'source'/name).convert('RGBA')
 if isinstance(cell,int):cell=[raw.width*cell//2,0,raw.width*(cell+1)//2,raw.height]
 if cell is None:cell=[0,0,*raw.size]
 im=raw.crop(cell);a=mask(im,32);b=a.getbbox();scale=(target[1]-top*4)/(b[3]-b[1]);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);sole=a.crop((0,b[3]-10,im.width,b[3])).getbbox();cx=(sole[0]+sole[2])/2*sm.width/im.width;dx=round(target[0]-cx);bottom=mask(sm,5).getbbox()[3];dy=target[1]-bottom;out=Image.new('RGBA',(384,544));out.alpha_composite(sm,(dx,dy));out.save(O/f'frame-{f:03}.png',optimize=True)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<384 and 0<=y+dy<544)];assert max(outside,default=0)<=4,(f,max(outside))
 recs.append({'revision':'sol','frame':f,'raw':'source/'+name,'cell':cell,'source_top_y':top*4,'scale':scale,'translation':[dx,dy],'source_primary_hoof_target':target,'registered_primary_hoof':[cx+dx,bottom+dy],'visible_clipped_alpha_gt4':0,'cropped_alpha_max':max(outside,default=0),'status':'candidate_for_visual_review','limit':'Own native5 near-forehoof and visible top registration; not every hoof/joint proof.'})
(B/'source/sol-registration.json').write_text(json.dumps(recs,indent=2)+'\n')
canonical=[0,1,2,3,4,5,6,7,49,50]
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 out=Image.new('RGB',(384*5,544*4),bg);d=ImageDraw.Draw(out)
 for i,f in enumerate(canonical):
  x=i%5*384;y=i//5*1088;old=Image.open(P/f'reference/battle-{f:03}-native.png').convert('RGBA').resize((384,544),Image.Resampling.NEAREST);new=Image.open((B/'frames'if f in[0,3,7]else O)/f'frame-{f:03}.png');out.paste(old,(x,y),old);out.paste(new,(x,y+544),new);d.text((x+8,y+8),f'{f:03} original | sol below',fill='white'if label=='dark'else'black')
 out.save(B/f'reviews/sol-all-{label}.png',optimize=True)
print('Registered7 new candidates;0/3/7 unchanged')
