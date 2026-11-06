# coding: utf-8
"""Pack approved V2 art and new ImageGen whole poses at the measured scene scale."""
from pathlib import Path
from PIL import Image, ImageEnhance
from functools import lru_cache
import json, shutil
R=Path(__file__).resolve().parent;V2=R.parent/'puppet-trio-v2-20261105';A=R/'assets'
M=json.loads((V2/'asset-manifest.json').read_text());S={}
FACTORS={'cyclops-maps':.68,'cyclops-battle':.93,'owl-maps':.45,'owl-battle':.62,'prometheus-maps':.66,'prometheus-battle':.64}
states=['intact','fire-broken','life-broken','both-broken']
def open_rgba(p):return Image.open(p).convert('RGBA')
def pack(im,size,anchor,dx,dy,scale):
 w,h=map(lambda x:max(1,round(x*scale)),im.size);x,y=round(anchor[0]+dx*scale),round(anchor[1]+dy*scale)
 assert 2<=x and 2<=y and x+w<=size[0]-2 and y+h<=size[1]-2,(size,anchor,x,y,w,h)
 out=Image.new('RGBA',size);out.paste(im.resize((w,h),Image.Resampling.NEAREST),(x,y));return out
def record(out,path,i,src,cell):
 out.save(R/path);x,y,r,b=out.getbbox();return {'id':i,'path':path,'pixels':list(out.size),'content':[x,y,r-x,b-y],'source':src,'source_cell':cell}
for e in M['images']:
 p=e['path']
 if not p.endswith('-reference.png'):shutil.copy2(V2/p,R/p)
for n in ('soldier-reference.png','hit.ogg'):shutil.copy2(V2/'assets'/n,A/n)
for group,poses in M['frames'].items():
 unit=group.split('-')[0];scene=group.rsplit('-',1)[-1]
 scale=FACTORS[unit+'-'+scene]
 for j,old in enumerate(poses):
  f=old['path'];im=open_rgba(V2/f);b=im.getbbox();size=im.size;anchor=[size[0]//2,72 if scene=='maps' or unit=='cyclops' else 100]
  out=pack(im.crop(b),size,anchor,b[0]-anchor[0],b[1]-anchor[1],scale)
  poses[j]=record(out,f,j,'V2 '+f,j)
# Keep symmetric directional assets an exact whole-sprite mirror after scaling.
for unit in ('cyclops','owl'):
 for state in ('intact','broken'):
  poses=M['frames'][f'{unit}-{state}-maps']
  for i in range(4):
   f=poses[12+i]['path'];im=open_rgba(R/poses[4+i]['path']).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   poses[12+i]=record(im,f,12+i,'Mirror of '+poses[4+i]['path'],4+i)
@lru_cache(None)
def cells(name, columns=4, rows=4):
 im=open_rgba(R/'source'/f'{name}.png');w,h=im.size;items=[];boxes=[]
 for row in range(rows):
  for col in range(columns):
   x,y,l,b=round(w*col/columns),round(h*row/rows),round(w*(col+1)/columns),round(h*(row+1)/rows)
   q=im.crop((x,y,l,b));q.putalpha(q.getchannel('A').point(lambda p:255 if p>=170 else 0))
   box=q.getbbox();assert box and box[0]>=2 and box[1]>=2 and box[2]<=q.width-2 and box[3]<=q.height-2,(name,row,col,box,q.size)
   items.append(q.crop(box));boxes.append([x+box[0],y+box[1],x+box[2],y+box[3]])
 S[name]={'size':list(im.size),'rects':boxes,'touching_source_edge':[]}
 return items
def solid(q):
 alpha=q.getchannel('A')
 q=ImageEnhance.Color(q).enhance(.72);q.putalpha(alpha)
 return q.quantize(colors=24,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
def feet(q):
 # Median center of the lowest contact band, used only for quiet planted poses.
 points=[x for x in range(q.width) if any(q.getpixel((x,y))[3]>=128 for y in range(q.height-11,q.height))]
 return (min(points)+max(points)+1)/2
for name,scene,start,height in [('battle-sprint','battle',6,38),('map-left-refined','maps',12,40),('map-idle','maps',16,40)]:
 q=cells(name);scale=height/max(p.height for p in q)
 for row,state in enumerate(states):
  group=f'prometheus-{state}-{scene}';poses=M['frames'][group]
  size=tuple(poses[0]['pixels']);anchor=[size[0]//2,100 if scene=='battle' else 72]
  for col in range(4):
   i=start+col;idx=row*4+col;p=q[idx]
   x=-feet(p) if name=='map-idle' else -p.width/2
   lift=(2 if col in (1,3) else 0) if scene=='battle' else 0
   out=pack(solid(p),size,anchor,x,-p.height-lift/scale,scale)
   f=f'assets/{group}-{i:02}.png';e=record(out,f,i,name,idx)
   if i<len(poses):poses[i]=e
   else:assert i==len(poses);poses.append(e)
# Correct only the four south-facing map poses; keep earlier renderings for review.
front=cells('map-down-front')
passing=cells('map-down-right-support',2,2)
frames=[(row,col,'map-down-right-support',row,passing[row]) if col==3 else (row,col,'map-down-front',row*4+col,front[row*4+col]) for row in range(4) for col in range(4)]
scales={name:min(40/max(q.height for _,_,src,_,q in frames if src==name),37/max(q.width for _,_,src,_,q in frames if src==name)) for name in ('map-down-front','map-down-right-support')}
for row,col,source,cell,q in frames:
 group=f'prometheus-{states[row]}-maps';path=f'assets/{group}-down-r1-{col:02}.png'
 # The split anchor extends farther left than the bare hand; align the torso instead of the tool.
 out=pack(solid(q),(80,80),(40,72),-.55*q.width,-q.height,scales[source])
 M['frames'][group][col]=record(out,path,col,source,cell)
M.update(status='preview_v3',source_evidence=S,scale_from_v2=FACTORS,images=[])
(R/'asset-manifest.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n')
print('Repacked V3 whole poses:',sum(map(len,M['frames'].values())))
