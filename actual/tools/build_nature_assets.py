#!/usr/bin/env python3
"""Prepare complete generated nature sprites; source objects are component-grouped.

The generator's rows are not equal height: fixed 4x4 cropping would cut trunks.
"""
from pathlib import Path
from collections import deque
import json,subprocess
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'source/natural-0.1.3/nature-sheet.png'
OUT=ROOT/'assets/nature';OUT.mkdir(parents=True,exist_ok=True)
REPORT=ROOT/'reports/natural-0.1.3';REPORT.mkdir(parents=True,exist_ok=True)
im=Image.open(SOURCE).convert('RGBA');w,h=im.size
alpha=im.getchannel('A');bits=bytearray(1 if a>32 else 0 for a in alpha.getdata());components=[]
for start in range(w*h):
 if not bits[start]:continue
 bits[start]=0;q=deque([start]);points=[]
 while q:
  p=q.popleft();points.append(p);x=p%w;y=p//w
  for dy in [-1,0,1]:
   for dx in [-1,0,1]:
    xx=x+dx;yy=y+dy
    if not(dx or dy) or not(0<=xx<w and 0<=yy<h):continue
    n=yy*w+xx
    if bits[n]:bits[n]=0;q.append(n)
 if len(points)>=8:
  box=(min(p%w for p in points),min(p//w for p in points),max(p%w for p in points)+1,max(p//w for p in points)+1)
  components.append((box,points))
centers=[h*v for v in [.18,.44,.71,.92]]
for _ in range(12):
 groups=[[] for _ in range(4)]
 for box,points in components:
  if len(points)<100:continue
  y=(box[1]+box[3])/2;groups[min(range(4),key=lambda k:abs(y-centers[k]))].append(y)
 centers=[sum(g)/len(g) if g else centers[i] for i,g in enumerate(groups)]
groups=[[] for _ in range(16)]
for box,points in components:
 row=min(range(4),key=lambda k:abs((box[1]+box[3])/2-centers[k]))
 col=min(range(4),key=lambda k:abs((box[0]+box[2])/2-(k+.5)*w/4))
 groups[row*4+col].append((box,points))
SPECS=[('pine_tall',24,32,'forest'),('pine_broad',32,32,'forest'),('pine_young',16,16,'forest'),('pine_pair',40,32,'forest'),
 ('snow_tall',24,32,'snow_forest'),('snow_broad',32,32,'snow_forest'),('snow_young',16,16,'snow_forest'),('snow_pair',40,32,'snow_forest'),
 ('peak_low',32,32,'rock'),('crag_tall',32,48,'rock'),('ridge_bent',48,32,'rock'),('outcrop',32,24,'rock'),
 ('brush',16,16,'understory'),('snow_boulder',16,16,'rock'),('stone_low',32,16,'rock'),('boulder',16,16,'rock')]
jobs=list(enumerate(SPECS))+[(0,('pine_small_a',16,16,'forest')),(1,('pine_small_b',16,16,'forest')),
 (4,('snow_small_a',16,16,'snow_forest')),(5,('snow_small_b',16,16,'snow_forest'))]
records=[];board=Image.new('RGB',(256,320),(27,39,43));draw=ImageDraw.Draw(board)
for i,(source_index,(name,nw,nh,kind)) in enumerate(jobs):
 group=groups[source_index]
 if not group:raise ValueError('Missing complete sprite '+name)
 box=(min(a[0][0] for a in group),min(a[0][1] for a in group),max(a[0][2] for a in group),max(a[0][3] for a in group))
 mask=Image.new('L',im.size);px=mask.load()
 for _,points in group:
  for p in points:px[p%w,p//w]=255
 obj=im.copy();obj.putalpha(Image.composite(alpha,Image.new('L',im.size),mask));obj=obj.crop(box)
 scale=min((nw-2)/obj.width,(nh-2)/obj.height);size=(max(1,round(obj.width*scale)),max(1,round(obj.height*scale)))
 obj=obj.resize(size,Image.Resampling.NEAREST)
 a=obj.getchannel('A').point(lambda p:255 if p>=96 else 0)
 obj=obj.convert('RGB').quantize(colors=24,dither=Image.Dither.NONE).convert('RGBA');obj.putalpha(a)
 canvas=Image.new('RGBA',(nw,nh));canvas.alpha_composite(obj,((nw-size[0])//2,nh-size[1]-1))
 path=OUT/(name+'.png');canvas.save(path,optimize=True)
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(path)],check=True)
 records.append({'key':name,'kind':kind,'path':'res://assets/nature/'+name+'.png','size':[nw,nh],'anchor':[nw//2,nh-2],
  'source_bbox':list(box),'source_components':len(group),'opaque_bbox':list(canvas.getbbox()),'bytes':path.stat().st_size,'whole_source':True})
 board.paste(canvas,(i%4*64+(64-nw)//2,i//4*64+3+(48-nh)//2),canvas);draw.text((i%4*64+4,i//4*64+51),name,fill=(220,220,200))
(OUT/'nature.json').write_text(json.dumps({'schema':1,'native_grid':16,'sprites':records,'source':'source/natural-0.1.3','mode':'built-in imagegen','sampling':'nearest; complete source components; no clipped silhouettes'},ensure_ascii=False,indent=2)+'\n')
board.save(REPORT/'nature-catalog.png',optimize=True)
print(json.dumps({'sprites':len(records),'source_size':[w,h],'row_centers':centers,'largest_sprite_bytes':max(r['bytes'] for r in records)}))
