import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
class ndimage:
 @staticmethod
 def label(mask):
  labels=np.zeros(mask.shape,dtype=np.int32);parent=[0];previous=[]
  def find(a):
   while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
   return a
  for y,row in enumerate(mask):
   changes=np.diff(np.pad(row.astype(np.int8),(1,1)));starts=np.where(changes==1)[0];ends=np.where(changes==-1)[0];current=[]
   for a,b in zip(starts,ends):
    k=len(parent);parent.append(k);labels[y,a:b]=k
    for c,d,j in previous:
     if c<b and d>a:parent[find(k)]=find(j)
    current.append((a,b,k))
   previous=current
  roots=np.array([find(i) for i in range(len(parent))]);labels=roots[labels];return labels,len(parent)-1
 @staticmethod
 def binary_propagation(seed,mask):
  labels,n=ndimage.label(mask);keep=np.unique(labels[seed&mask]);keep=keep[keep>0];return np.isin(labels,keep)
 @staticmethod
 def binary_dilation(m,iterations=1):
  for _ in range(iterations):m=m|np.pad(m[1:],((0,1),(0,0)))|np.pad(m[:-1],((1,0),(0,0)))|np.pad(m[:,1:],((0,0),(0,1)))|np.pad(m[:,:-1],((0,0),(1,0)))
  return m
R=Path(__file__).resolve().parents[1]; src=R/'source/revision4'; out=R/'assets/v4';out.mkdir(exist_ok=True)
A=json.loads((src/'assets.js').read_text().split('window.CinemaAssets=')[1].rstrip().rstrip(';'))
# The manifest may wrap the sheets; use the actual in-browser manifest structure.
print('manifest keys',list(A)[:4])
def save(im,name):
 p=out/name;im.save(p,optimize=True);return str(p.relative_to(R))
def main_component(mask):
 labels,n=ndimage.label(mask);sizes=np.bincount(labels.ravel());sizes[0]=0;return labels,sizes,int(sizes.argmax())
def meta(im,path):
 a=np.array(im);ys,xs=np.where(a[:,:,3]>64);head=int(ys.min());
 # Face registration is local to the head, independent of braid/coat or sword.
 skin=(a[:,:,0]>135)&(a[:,:,0]>a[:,:,1]*1.10)&(a[:,:,1]>a[:,:,2]*1.12)&(a[:,:,3]>100)
 skin[:head+3]=False;skin[head+int((ys.max()-head)*.23):]=False
 sy,sx=np.where(skin);anchor=float(np.median(sx)) if len(sx) else im.width*.34
 return dict(path=path,width=im.width,height=im.height,body_anchor=anchor,head_top=head,body_height=169,source_box=[0,0,im.width,im.height],source_cell=[0,0,im.width,im.height],pixel_scale=1)
for d in json.loads((src/'generation.json').read_text()):
 p=Path(d['path']);shutil.copy2(p,src/(d['key']+'-source.png'));im=Image.open(p).convert('RGBA');w,h=im.size;frames=[]
 if d['kind']=='actor':
  cells=[]
  for i in range(4):
   c=im.crop((i*w//4,0,(i+1)*w//4,h));a=np.array(c);rgb=a[:,:,:3].astype(int)
   bg=(rgb.max(2)-rgb.min(2)<38)&(rgb.min(2)>105)|(a[:,:,3]<110)
   exterior=ndimage.binary_propagation(np.pad(np.ones((h-2,c.width-2),bool),1,constant_values=False)==False,mask=bg)
   a[exterior,3]=0;a[a[:,:,3]<110,3]=0
   labels,sizes,k=main_component(a[:,:,3]>80);keep=labels==k;a[~ndimage.binary_dilation(keep,iterations=1),3]=0
   c=Image.fromarray(a);b=c.getbbox();cells.append(c.crop(b))
  scale=169/max(c.height for c in cells)
  for i,c in enumerate(cells):
   c=c.resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.NEAREST);p=save(c,f'eileen-return-{i+4}.png');frames.append(meta(c,p))
  A['eileen-return']['frames'][4:8]=frames
 else:
  # Fixed cell canvas and fixed fire-core register preserve size while the painted tail changes.
  for i in range(4):
   c=im.crop((i*w//4,0,(i+1)*w//4,h));a=np.array(c);ys,xs=np.where((a[:,:,0]>210)&(a[:,:,1]>175)&(a[:,:,2]>120)&(a[:,:,3]>160));cx=int(np.median(xs));cy=int(np.median(ys));c=c.crop((cx-370,cy-130,cx+145,cy+130));c=c.resize((172,87),Image.Resampling.NEAREST);p=save(c,f'fire-flight-{i}.png');frames.append(dict(path=p,width=172,height=87,core_anchor=[123,43],reference_width=172))
  A['fire-flight']=dict(frames=frames)
# Remove detached neighbouring atlas fragments; retain approved main bust and original canvas geometry.
cleaned=[]
for key in ['magic-cutins','bow-cutins']:
 for i,d in enumerate(A[key]['frames']):
  im=Image.open(R/d['path']).convert('RGBA');a=np.array(im);labels,sizes,k=main_component(a[:,:,3]>40);ys,xs=np.where(labels==k);x0,x1=max(0,xs.min()-3),min(im.width,xs.max()+4);y0,y1=max(0,ys.min()-3),min(im.height,ys.max()+4)
  outside=np.ones(a.shape[:2],bool);outside[y0:y1,x0:x1]=False;removed=int(np.sum((a[:,:,3]>0)&outside));a[outside,3]=0
  if removed:
   d['path']=save(Image.fromarray(a),f'{key}-{i}.png');cleaned.append(dict(key=key,frame=i,removed_pixels=removed,main_bounds=[int(x0),int(y0),int(x1),int(y1)]))
(R/'assets.js').write_text('window.CinemaForest=true;\nwindow.CinemaAssets='+json.dumps(A,ensure_ascii=False,separators=(',',':'))+';\n')
(src/'asset-manifest.json').write_text(json.dumps(A,ensure_ascii=False,indent=2));(src/'cutin-cleaning.json').write_text(json.dumps(cleaned,indent=2));print('new return',frames,'cleaned',cleaned)
