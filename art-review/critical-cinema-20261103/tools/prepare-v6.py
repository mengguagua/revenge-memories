import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];S=R/'source/revision6';O=R/'assets/v6';A=json.loads((S/'assets-before.js').read_text().split('window.CinemaAssets=')[1].rstrip().rstrip(';'));records=[]
def actors(im):
 arr=np.array(im);mask=arr[:,:,3]>100;labels=np.zeros(mask.shape,dtype=np.int32);parent=[0];previous=[]
 def find(k):
  while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
  return k
 for yy,line in enumerate(mask):
  edge=np.diff(np.pad(line.astype(np.int8),(1,1)));starts=np.where(edge==1)[0];ends=np.where(edge==-1)[0];current=[]
  for x,x1 in zip(starts,ends):
   k=len(parent);parent.append(k);labels[yy,x:x1]=k
   for p0,p1,pk in previous:
    if p0<=x1 and p1>=x:parent[find(k)]=find(pk)
   current.append((x,x1,k))
  previous=current
 labels=np.array([find(k)for k in range(len(parent))])[labels];sizes=np.bincount(labels.ravel());sizes[0]=0;parts=[]
 for k in np.argsort(sizes)[-4:]:
  yy,xx=np.where(labels==k);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));a=arr[box[1]:box[3],box[0]:box[2]].copy();a[a[:,:,3]<100,3]=0;parts.append((box,Image.fromarray(a)))
 return sorted(parts,key=lambda p:p[0][0])
def head_anchor(im):
 a=np.array(im);skin=(a[:,:,0]>145)&(a[:,:,0]>a[:,:,1]*1.09)&(a[:,:,1]>a[:,:,2]*1.12)&(a[:,:,3]>150);skin[round(im.height*.30):]=False;y,x=np.where(skin)
 if not len(x):raise ValueError('No face registration')
 y0=y.min();skin[y0+round(im.height*.16):]=False;y,x=np.where(skin);return float(np.median(x)),int(np.where(a[:,:,3]>100)[0].min())
height={'hunapu-base':120,'hunapu-advanced':120,'eileen-base':125,'eileen-advanced':122}
for d in json.loads((S/'generation.json').read_text()):
 p=Path(d['source_path']);shutil.copy2(p,S/(d['key']+'-source.png'));im=Image.open(p).convert('RGBA');parts=actors(im);desired=height[d['key']];scale=desired/max(c.height for _,c in parts)
 for n,(box,c) in enumerate(parts):
  c=c.resize((round(c.width*scale),round(c.height*scale)),Image.Resampling.NEAREST);anchor,head=head_anchor(c);index=d['stage']*4+n;p=O/(d['key']+'-'+str(n)+'.png');c.save(p,optimize=True)
  f=dict(path=str(p.relative_to(R)),width=c.width,height=c.height,body_anchor=anchor,head_top=head,body_height=137,return_head_y=290-desired,source_box=list(box),source_cell=[0,0,im.width,im.height],pixel_scale=1/scale,identity_reference=d['refs'])
  A[d['asset']]['frames'][index]=f;records.append(dict(group=d['key'],frame=index,source_box=list(box),path=f['path'],width=c.width,height=c.height,bytes=p.stat().st_size,display_scale=1,stable_head_y=f['return_head_y'],identity_references=d['refs']))
(R/'assets.js').write_text('window.CinemaForest=true;\nwindow.CinemaAssets='+json.dumps(A,ensure_ascii=False,separators=(',',':'))+';\n');(S/'return-assets.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('PREPARED',len(records),'identity-specific return frames')
