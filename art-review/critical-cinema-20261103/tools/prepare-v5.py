import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];S=R/'source/revision5';A=json.loads((S/'assets-before.js').read_text().split('window.CinemaAssets=')[1].rstrip().rstrip(';'));OUT=R/'assets/v5';records=[]
def skin(im,top=None):
 a=np.array(im);ys,xs=np.where(a[:,:,3]>128);y0=int(ys.min())if top is None else top;h=ys.max()-y0+1;m=(a[:,:,0]>145)&(a[:,:,0]>a[:,:,1]*1.09)&(a[:,:,1]>a[:,:,2]*1.12)&(a[:,:,3]>180);m[:y0+3]=False;m[y0+int(h*.23):]=False;yy,xx=np.where(m)
 if not len(xx):raise ValueError('No face')
 # Isolate face from a trailing hand by selecting the uppermost occupied row band.
 ymin=yy.min();m[ymin+round(h*.14):]=False;yy,xx=np.where(m);return dict(face_width=float(np.quantile(xx,.95)-np.quantile(xx,.05)+1),face_x=float(np.median(xx)),head_top=y0)
refs={'hunapu':[('assets/hunapu-sword-0.png',0,134),('assets/v3/hunapu-strike-v3-1.png',0,168)],'eileen':[('assets/eileen-sword-0.png',0,177),('assets/eileen-sword-advanced-0.png',26,169)]}
for d in json.loads((S/'generation.json').read_text()):
 hero=d['key'].split('-')[0];p=Path(d['source_path']);shutil.copy2(p,S/(d['key']+'-source.png'));im=Image.open(p).convert('RGBA');w,h=im.size;cells=[]
 for row in range(2):
  rowim=im.crop((0,round(row*h/2),w,round((row+1)*h/2)));arr=np.array(rowim);mask=arr[:,:,3]>100
  # Label complete actors across each row, instead of assuming evenly spaced atlas cells.
  labels=np.zeros(mask.shape,dtype=np.int32);parent=[0];previous=[]
  def find(k):
   while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
   return k
  for yy,line in enumerate(mask):
   edges=np.diff(np.pad(line.astype(np.int8),(1,1)));starts=np.where(edges==1)[0];ends=np.where(edges==-1)[0];current=[]
   for xx,xx1 in zip(starts,ends):
    k=len(parent);parent.append(k);labels[yy,xx:xx1]=k
    for p0,p1,pk in previous:
     if p0<=xx1 and p1>=xx:parent[find(k)]=find(pk)
    current.append((xx,xx1,k))
   previous=current
  roots=np.array([find(k)for k in range(len(parent))]);labels=roots[labels];sizes=np.bincount(labels.ravel());sizes[0]=0;largest=np.argsort(sizes)[-4:];boxes=[]
  for k in largest:
   ys,xs=np.where(labels==k);boxes.append((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))
  for box in sorted(boxes,key=lambda b:b[0]):
   a=arr[box[1]:box[3],box[0]:box[2]].copy();a[a[:,:,3]<100,3]=0;cells.append(Image.fromarray(a))
 for stage in range(2):
  ref,top,bh=refs[hero][stage];refim=Image.open(R/ref).convert('RGBA');refmetric=skin(refim,top);refscale=137/bh;target_face=refmetric['face_width']*refscale
  values=[skin(c)for c in cells[stage*4:stage*4+4]];rawface=float(np.median([m['face_width']for m in values]));scale=target_face/rawface
  # Crouching lowers stature. Keep head scale from attack artwork instead of inflating a crouched body to standing height.
  maxh=max(c.height for c in cells[stage*4:stage*4+4]);standing_pixels=137;desired=max(standing_pixels*.84,min(standing_pixels*.96,maxh*scale));scale=desired/maxh
  for i in range(4):
   n=stage*4+i;c=cells[n];c=c.resize((round(c.width*scale/refscale),round(c.height*scale/refscale)),Image.Resampling.NEAREST);m=skin(c);p=OUT/f'{hero}-return-{n}.png';c.save(p,optimize=True)
   meta=dict(path=str(p.relative_to(R)),width=c.width,height=c.height,head_top=m['head_top'],body_anchor=m['face_x'],face_width=m['face_width'],body_height=bh,source_box=[0,0,c.width,c.height],source_cell=[0,0,c.width,c.height],pixel_scale=1,return_head_y=290-desired)
   A[hero+'-return']['frames'][n]=meta;records.append(dict(hero=hero,stage=stage,frame=n,path=meta['path'],width=c.width,height=c.height,bytes=p.stat().st_size,screen_head_top=meta['return_head_y'],reference_face_width=target_face,screen_face_width=m['face_width']*refscale,body_scale=refscale,full_sword_required=True,source=str((S/(d['key']+'-source.png')).relative_to(R))))
(R/'assets.js').write_text('window.CinemaForest=true;\nwindow.CinemaAssets='+json.dumps(A,ensure_ascii=False,separators=(',',':'))+';\n');(S/'return-registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(records))
# Artwork checks against dark and light surfaces at actual rendering scale.
canvas=Image.new('RGB',(1100,600),'#182c3c')
for row,hero in enumerate(['hunapu','eileen']):
 for stage in range(2):
  for i in range(4):
   n=stage*4+i;d=A[hero+'-return']['frames'][n];c=Image.open(R/d['path']);s=137/d['body_height'];c=c.resize((round(c.width*s*1.5),round(c.height*s*1.5)),Image.Resampling.NEAREST);canvas.paste(c,(i*270+12,(row*2+stage)*150),c)
canvas.save(R/'checks/v5/return-contact.png')
