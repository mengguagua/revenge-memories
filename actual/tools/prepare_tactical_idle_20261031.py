from pathlib import Path
from PIL import Image
import json,subprocess,statistics
R=Path(__file__).resolve().parents[2];A=R/'actual/assets/tactical-readability-20261031';S=R/'source/tactical-readability-20261031'
im=Image.open(S/'healer-source.png');w,h=im.size; split_y=int(h*.55)
def sprite_bounds(tile):
 from collections import deque
 alpha=tile.convert('RGBA').getchannel('A');w,h=tile.size
 pending={y*w+x for y in range(h) for x in range(w) if alpha.getpixel((x,y))>=128};best=[]
 while pending:
  first=pending.pop();todo=deque([first]);component=[first]
  while todo:
   v=todo.popleft();x=v%w;y=v//w
   for n in ([v-1] if x else [])+([v+1] if x+1<w else [])+([v-w] if y else [])+([v+w] if y+1<h else []):
    if n in pending:pending.remove(n);todo.append(n);component.append(n)
  if len(component)>len(best):best=component
 xs=[v%w for v in best];ys=[v//w for v in best]
 return (max(0,min(xs)-3),max(0,min(ys)-3),min(w,max(xs)+4),min(h,max(ys)+4))
frames=[]
for i in range(4):
 crop=S/f'healer-cut-{i}.png';tile=im.crop((i%2*w//2,0 if i<2 else split_y,(i%2+1)*w//2,split_y if i<2 else h));tile.crop(sprite_bounds(tile)).save(crop)
 output=A/f'healer-frame-{i}.png'
 subprocess.run(['/opt/homebrew/bin/magick',str(crop),'-resize','60x60','-gravity','south','-background','none','-extent','96x96',str(output)],check=True)
 frames.append(output)
subprocess.run(['/opt/homebrew/bin/magick',*[str(p) for p in frames],'+append',str(A/'healer-idle.png')],check=True)
# Cut assembly only; all newly drawn character pixels come from imagegen.
for p in frames:p.unlink()
m=json.loads((R/'actual/data/animation_runtime/reviewed.json').read_text())['metadata']['maps']
left={'1_ally','1_enemy','2_ally','2_enemy','3_ally','4_ally','4_enemy','7_ally','7_enemy','15_ally','15_enemy','16_ally','17_ally','19_ally','20_ally','20_enemy','22_ally','22_enemy','13_ally','13_enemy'}
out={}
for key,contexts in m.items():
 if 'tactical-idle' not in contexts:continue
 art=contexts['tactical-idle'];override={}
 if key=='18_ally':
  override={'path':'res://assets/tactical-readability-20261031/healer-idle.png','frames':4,'columns':4,'native_cycle':[0,1,2,3],'cycle_ticks':[16,12,16,12]}
  art={**art,**override}
 image=Image.open(R/('actual/'+art['path'][6:])).convert('RGBA');fw,fh=art['frame_size'];poses=[];foot_x=[]
 for i in range(art['frames']):
  tile=image.crop((i%art['columns']*fw,i//art['columns']*fh,i%art['columns']*fw+fw,i//art['columns']*fh+fh));alpha=tile.getchannel('A').point(lambda a:255 if a>=48 else 0);box=alpha.getbbox()
  if not box:poses.append({'bottom':fh,'bounds':[0,0,fw,fh]});continue
  ys=range(max(box[1],box[3]-12),box[3]);xs=[x for y in ys for x in range(box[0],box[2]) if alpha.getpixel((x,y))]
  foot_x.append(statistics.median(xs));poses.append({'bottom':box[3],'bounds':list(box)})
 out[key]={'path':art['path'],'source_facing':'left' if key in left else 'right','foot_x':round(statistics.median(foot_x),2),'poses':poses,'override':override}
(R/'actual/data/tactical_idle_20261031.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Aligned',len(out),'idle profiles')
