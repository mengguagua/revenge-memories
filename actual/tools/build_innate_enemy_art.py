"""Slice generated body poses with component masks; preserve source sheets separately."""
import subprocess,re,json,shutil
from pathlib import Path
from PIL import Image
from collections import deque
M='/opt/homebrew/bin/magick'
root=Path(__file__).resolve().parents[1]; repo=root.parent
out=root/'assets/innate-enemies-20261023'; work=Path('/private/tmp/innate-enemy-art');work.mkdir(exist_ok=True)
sources={'21':('exec-13427fb7-37e5-41df-a246-48b2dc617c95.png',.40,24),'3':('exec-05c922d5-056f-4219-a24b-7eb6356e544e.png',.32,18),'5':('exec-43b759e0-4088-47b2-b114-29edb8b1506b.png',.32,18)}
art={};manifest=[]
def run(args):return subprocess.check_output([M,*map(str,args)],text=True)
for cid,(filename,scale,colors) in sources.items():
 src=Path('/Users/gcc/.codex/generated_images/01a1676d-d26b-7992-acd6-1335649650d5')/filename
 archive=repo/'art-review/enemy-deployment-20261023/source'/('class-'+cid+'-muted.png')
 if archive.exists():src=archive
 else:shutil.copy2(src,archive)
 image=Image.open(src).convert('RGBA');w,h=image.size;pixels=bytearray(v>12 for v in image.getchannel('A').getdata());components=[]
 for start in range(w*h):
  if not pixels[start]:continue
  pixels[start]=0;q=deque([start]);points=[]
  while q:
   n=q.popleft();points.append(n);x=n%w;y=n//w
   for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if 0<=nx<w and 0<=ny<h:
     k=ny*w+nx
     if pixels[k]:pixels[k]=0;q.append(k)
  if len(points)>10000:
   xs=[n%w for n in points];ys=[n//w for n in points]
   components.append(dict(id=len(components),w=max(xs)-min(xs)+1,h=max(ys)-min(ys)+1,x=min(xs),y=min(ys),cx=sum(xs)/len(xs),cy=sum(ys)/len(ys),points=points))
 assert len(components)==8,(cid,components)
 components.sort(key=lambda c:(int(c['cy']>440),c['cx']))
 frames=[]
 for i,c in enumerate(components):
  mask=work/f'{cid}-{i}-mask.png';frame=work/f'{cid}-{i}.png'
  data=bytearray(w*h)
  for n in c.pop('points'):data[n]=255
  Image.frombytes('L',(w,h),bytes(data)).save(mask)
  # Actual alpha is retained inside the isolated silhouette; adjacent poses never leak.
  run([src,mask,'-alpha','off','-compose','CopyOpacity','-composite','-compose','Over','-crop',f"{c['w']}x{c['h']}+{c['x']}+{c['y']}",'+repage','-filter','Point','-resize',f'{scale*100}%','-background','none','-gravity','south','-splice','0x32','-gravity','south','-extent','256x256',frame])
  frames.append(frame)
 atlas=out/f'class-{cid}-battle.png'
 run([*frames,'+append','+dither','-colors',colors,atlas])
 mapfile=out/f'class-{cid}-map.png'
 run([frames[0],'-trim','+repage','-filter','Point','-resize','56x48','-background','none','-gravity','south','-splice','0x8','-gravity','south','-extent','64x64','+dither','-colors',colors,mapfile])
 art[cid]={'path':'res://assets/innate-enemies-20261023/'+atlas.name,'frame_size':[256,256],'frames':8,'columns':8,'anchor':[64,112],'native_density':2,'default_facing':'right','sequences':{'idle':[0],'hit':[6]},'pose_map':{'idle':0,'prepare':4 if cid=='3' else 1,'release':5 if cid=='3' else 2,'recover':3,'bite_prepare':1 if cid=='3' else 4,'bite_contact':2 if cid=='3' else 5,'hurt':6,'empowered':7 if cid=='21' else 0},'map':{'path':'res://assets/innate-enemies-20261023/'+mapfile.name,'frame_size':[64,64],'frames':1,'native_density':2,'anchor':[16,28],'tile_origin':[8,16],'default_facing':'right','directions':{'up':[0,0],'down':[0,0],'side':[0,0]}}}
 files=[atlas,mapfile]
 if cid in ['3','5']:
  portrait=out/f'class-{cid}-portrait.png'
  run([frames[0],'-trim','+repage','-filter','Point','-resize','44x44','-background','none','-gravity','center','-extent','48x48','+dither','-colors',colors,portrait]);files.append(portrait)
 for p in files:
  subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--strip','safe','--quiet',str(p)],check=True)
  manifest.append({'file':str(p.relative_to(root)),'bytes':p.stat().st_size,'size':run(['identify','-format','%wx%h',p]),'palette_limit':colors,'use':'battle poses' if p==atlas else 'portrait' if 'portrait' in p.name else 'map icon','source':str(archive.relative_to(repo)),'pose_boxes':components if p==atlas else []})
(root/'data/innate_attack_art.json').write_text(json.dumps(art,ensure_ascii=False,indent=2)+'\n')
(root/'reports/enemy-deployment-20261023/art-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print([(x['file'],x['bytes']) for x in manifest])
