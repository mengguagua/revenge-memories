# -*- coding: utf-8 -*-
"""Technical registration of existing ImageGen candidates; no artwork painting."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json
M=Path(__file__).resolve().parent;O=M/'candidate-sol';O.mkdir(exist_ok=True)
def mask(im,t=128):return im.getchannel('A').point(lambda v:255 if v>=t else 0)
# Helmet landmark and isolated grounded-hoof ROIs selected from each actual raw.
# Source foot targets follow own source; alpha identity with enemy7 is independently proved.
spec=[(0,'tactical-up-generated-v1.png',0,2,193,16,[470,790,550,825],[64,92]),(1,'tactical-up-generated-v1.png',1,2,211,20,[380,790,455,826],[70,96]),(2,'tactical-right-generated-v2.png',0,2,195,36,[174,790,260,820],[34,96]),(3,'tactical-right-generated-v2.png',1,2,204,36,[430,790,505,820],[70,96]),(4,'tactical-down-generated-v1.png',0,2,138,20,[448,820,528,855],[64,96]),(5,'tactical-down-generated-v1.png',1,2,149,24,[398,820,475,855],[66,96]),(8,'idle-generated-v1.png',0,3,112,19,[570,670,648,700],[62,80]),(9,'idle-generated-v1.png',1,3,112,19,[230,670,598,700],[52,80]),(10,'idle-generated-v1.png',2,3,112,19,[230,670,313,700],[42,80])]
records=[]
for f,name,i,n,head,targethead,roi,target in spec:
 raw=Image.open(M/'source'/name).convert('RGBA');cell=[raw.width*i//n,0,raw.width*(i+1)//n,raw.height];im=raw.crop(cell);a=mask(im);b=a.getbbox();scale=(target[1]-targethead)/(b[3]-head);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);fb=a.crop(roi).getbbox();cx=(roi[0]+(fb[0]+fb[2])/2)*sm.width/im.width;dx=round(target[0]-cx);bottom=mask(sm,5).getbbox()[3];dy=target[1]-bottom;size=(96,96)if f>=8 else(128,96);out=Image.new('RGBA',size);out.alpha_composite(sm,(dx,dy));out.save(O/f'frame-{f:03}.png',optimize=True)
 outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<size[0] and 0<=y+dy<size[1])]
 assert max(outside,default=0)<=4,(f,max(outside))
 records.append({'revision':'sol','slot':f,'raw':'source/'+name,'cell':cell,'raw_helmet_top':head,'target_helmet_top':targethead,'raw_grounded_hoof_roi':roi,'chosen_source_hoof_target':target,'chosen_registered_hoof':[cx+dx,bottom+dy],'uniform_scale':scale,'translation':[dx,dy],'visible_clipped_alpha_gt4':0,'cropped_alpha_max':max(outside,default=0),'status':'candidate_visual_review','limit':'Selected visible hoof/helmet registration only; not every joint or hoof equality.'})
for d,s in [(6,2),(7,3)]:
 a=Image.open(M/f'reference/tactical-native-{s:02}.png').convert('RGBA');b=Image.open(M/f'reference/tactical-native-{d:02}.png').convert('RGBA');c=ImageOps.mirror(a);assert c.size==b.size and c.tobytes()==b.tobytes();ImageOps.mirror(Image.open(O/f'frame-{s:03}.png')).save(O/f'frame-{d:03}.png',optimize=True);records.append({'revision':'sol','slot':d,'exact_full_rgba_mirror_of':s})
(M/'source/sol-registration.json').write_text(json.dumps(records,indent=2)+'\n')
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 out=Image.new('RGB',(512,384),bg)
 for f in range(8):
  x=f%4*128;y=f//4*192;a=Image.open(M/f'reference/tactical-native-{f:02}.png').convert('RGBA').resize((128,96),Image.Resampling.NEAREST);b=Image.open(O/f'frame-{f:03}.png');out.paste(a,(x,y),a);out.paste(b,(x,y+96),b)
 out.resize((1024,768),Image.Resampling.NEAREST).save(M/f'reviews/sol-native-{label}-2x.png',optimize=True)
 out=Image.new('RGB',(288,192),bg)
 for f in range(3):
  a=Image.open(M/f'reference/static-idle-{f:02}.png').convert('RGBA').resize((96,96),Image.Resampling.NEAREST);b=Image.open(O/f'frame-{f+8:03}.png');out.paste(a,(f*96,0),a);out.paste(b,(f*96,96),b)
 out.resize((864,576),Image.Resampling.NEAREST).save(M/f'reviews/sol-idle-{label}-3x.png',optimize=True)
print('Registered11 candidate source poses, no visible alpha clipping.')
