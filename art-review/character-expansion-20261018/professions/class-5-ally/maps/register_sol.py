# -*- coding: utf-8 -*-
"""Own native5 body landmarks; original21..23 ground projection kept separate."""
from pathlib import Path
from PIL import Image,ImageOps
import json
M=Path(__file__).resolve().parent;P=M.parent;O=M/'sol-frames';O.mkdir(exist_ok=True);(M/'reviews').mkdir(exist_ok=True);(M/'frames').mkdir(exist_ok=True)
def mask(i,t=128):return i.getchannel('A').point(lambda v:255 if v>=t else 0)
def bounds(i,roi):
 b=mask(i,32).crop(roi).getbbox();assert b is not None,roi;return[b[0]+roi[0],b[1]+roi[1],b[2]+roi[0],b[3]+roi[1]]
# ROI isolates visible body hoof; excludes blade, feathers and detached source shadow.
spec=[(0,'sol-native-up-v2-generated.png',0,172,8,[490,610,740,690],[70,84]),(1,'sol-native-up-v2-generated.png',1,172,8,[360,610,650,690],[66,80]),(2,'sol-native-right-v3-generated.png',0,130,0,[580,570,750,645],[64,68]),(3,'sol-native-right-v3-generated.png',1,130,0,[210,570,460,645],[26,68]),(4,'sol-native-down-v2-generated.png',0,146,4,[525,450,750,615],[66,72]),(5,'sol-native-down-v2-generated.png',1,130,0,[360,480,650,665],[62,80])]
records=[]
for f,name,i,head,sourcehead,roi,target in spec:
 raw=Image.open(M/'source'/name).convert('RGBA');cell=[raw.width*i//2,0,raw.width*(i+1)//2,raw.height];im=raw.crop(cell);fb=bounds(im,roi);scale=(target[1]-sourcehead)/(fb[3]-head);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);rroi=[max(0,round(roi[0]*scale)),max(0,round(roi[1]*scale)),min(sm.width,round(roi[2]*scale)),min(sm.height,round(roi[3]*scale))];sb=bounds(sm,rroi);cx=(sb[0]+sb[2])/2;dx=round(target[0]-cx);dy=round(target[1]-sb[3]);out=Image.new('RGBA',(128,96));out.alpha_composite(sm,(dx,dy));outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<128 and 0<=y+dy<96)];assert max(outside,default=0)<=4,(f,max(outside))
 # Exact original detached ground projection, not used to register anatomy.
 native=Image.open(P/f'reference/native-walk-{f:02}.png').convert('RGBA');projection=native.crop((0,21,32,24)).resize((128,12),Image.Resampling.NEAREST);out.alpha_composite(projection,(0,84));out.save(O/f'frame-{f:03}.png',optimize=True)
 records.append({'revision':'sol','slot':f,'raw':'source/'+name,'cell':cell,'raw_helmet_top':head,'source_helmet_top':sourcehead,'raw_body_hoof_roi':roi,'uniform_scale':scale,'translation':[dx,dy],'source_visible_body_hoof_target':target,'registered_body_hoof':[cx+dx,sb[3]+dy],'maximum_cropped_alpha':max(outside,default=0),'visible_clipped_alpha_gt4':0,'projection':'Own original native rows21..23, nearest4x atoutputy84; body tail pixel row20 preserved.','note':'Registration describes selected visible body landmark only, not every joint.'})
for d,s in[(6,2),(7,3)]:
 a=Image.open(P/f'reference/native-walk-{s:02}.png').convert('RGBA');b=Image.open(P/f'reference/native-walk-{d:02}.png').convert('RGBA');c=ImageOps.mirror(a);assert c.size==b.size and c.tobytes()==b.tobytes();ImageOps.mirror(Image.open(O/f'frame-{s:03}.png')).save(O/f'frame-{d:03}.png',optimize=True);records.append({'slot':d,'exact_full_rgba_mirror_of':s,'revision':'sol'})
# Static cells use measured transparent gaps instead of equal thirds.
raw=Image.open(M/'source/sol-idle-three-v1-generated.png').convert('RGBA');edges=[0,770,1434,2172];re=Image.new('RGBA',raw.size)
for i in range(3):re.paste(raw.crop((edges[i],0,edges[i+1],raw.height)),(edges[i],0))
assert re.tobytes()==raw.tobytes()
for i,(target,roi)in enumerate([([28,80],[210,590,350,660]),([42,80],[130,590,620,665]),([56,80],[420,590,630,665])]):
 cell=[edges[i],0,edges[i+1],raw.height];im=raw.crop(cell);fb=bounds(im,roi);head=148;scale=64/(fb[3]-head);sm=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);rroi=[max(0,round(roi[0]*scale)),max(0,round(roi[1]*scale)),min(sm.width,round(roi[2]*scale)),min(sm.height,round(roi[3]*scale))];sb=bounds(sm,rroi);cx=(sb[0]+sb[2])/2;dx=round(target[0]-cx);dy=target[1]-sb[3];out=Image.new('RGBA',(96,96));out.alpha_composite(sm,(dx,dy));outside=[sm.getpixel((x,y))[3]for y in range(sm.height)for x in range(sm.width)if not(0<=x+dx<96 and 0<=y+dy<96)];assert max(outside,default=0)<=4,(i,'idle',max(outside));out.save(O/f'idle-{i:03}.png',optimize=True);records.append({'kind':'idle','slot':i,'revision':'sol','raw':'source/sol-idle-three-v1-generated.png','cell':cell,'raw_hoof_roi':roi,'uniform_scale':scale,'translation':[dx,dy],'selected_source_hoof_target':target,'registered_hoof':[cx+dx,sb[3]+dy],'maximum_cropped_alpha':max(outside,default=0),'split_complete_rgba_reassembly':True})
(M/'source/sol-registration.json').write_text(json.dumps(records,indent=2)+'\n')
for bg,label in[('#eee8d8','light'),('#1d2932','dark')]:
 board=Image.new('RGB',(512,384),bg)
 for f in range(8):
  x=f%4*128;y=f//4*192;a=Image.open(P/f'reference/native-walk-{f:02}.png').convert('RGBA').resize((128,96),Image.Resampling.NEAREST);b=Image.open(O/f'frame-{f:03}.png');board.paste(a,(x,y),a);board.paste(b,(x,y+96),b)
 board.resize((1024,768),Image.Resampling.NEAREST).save(M/f'reviews/sol-native-{label}-2x.png',optimize=True)
 native=Image.open(P/'reference/class-5-idle-source-atlas.png').convert('RGBA');board=Image.new('RGB',(288,192),bg)
 for f in range(3):
  a=native.crop((f*24,0,(f+1)*24,24)).resize((96,96),Image.Resampling.NEAREST);b=Image.open(O/f'idle-{f:03}.png');board.paste(a,(f*96,0),a);board.paste(b,(f*96,96),b)
 board.resize((864,576),Image.Resampling.NEAREST).save(M/f'reviews/sol-idle-{label}-3x.png',optimize=True)
print('Native5 maps:8walk/3idle, exact original projection and mirrors.')
