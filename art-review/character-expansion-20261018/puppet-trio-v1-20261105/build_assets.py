# coding: utf-8
"""Slice generated whole poses, register native pixels, keep sources outside delivery."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,subprocess,shutil
R=Path(__file__).resolve().parent;A=R/'assets';frames={};warnings=[]
def source(name):return Image.open(R/'source'/f'{name}-original.png').convert('RGBA')
def rawcell(name,cols,rows,i):
 im=source(name);x,y=i%cols,i//cols;rect=(round(x*im.width/cols),round(y*im.height/rows),round((x+1)*im.width/cols),round((y+1)*im.height/rows))
 if name=='owl-maps':
  # Measured whole alpha-component rectangles: generated wingbeats cross equal row lines.
  boxes=[[(60,41,334,195),(417,15,667,194),(758,42,1049,194),(1123,52,1394,199)],[(111,230,326,381),(452,208,669,372),(796,235,1030,369),(1152,253,1375,369)],[(52,408,339,542),(405,378,680,541),(755,408,1049,544),(1122,417,1389,549)],[(58,581,333,731),(416,552,670,730),(760,582,1049,729),(1125,593,1394,737)],[(111,763,326,910),(450,743,670,903),(796,769,1030,903),(1152,779,1378,904)],[(52,938,340,1070),(405,910,679,1071),(755,939,1047,1071),(1123,944,1389,1076)]]
  l,t,r,b=boxes[i//4][i%4];rect=(l-2,t-2,r+2,b+2)
 im=im.crop(rect)
 im.putalpha(im.getchannel('A').point(lambda v:255 if v>=160 else 0));b=im.getbbox()
 assert b,(name,i)
 if min(b[0],b[1],im.width-b[2],im.height-b[3])<2:warnings.append({'source':name,'cell':i,'bounds':b,'cell_size':im.size})
 return im.crop(b),rect,b
def factor(name,c,r,i,height):return height/rawcell(name,c,r,i)[0].height
def save(name,c,r,i,group,index,scale,size,baseline):
 im,rect,b=rawcell(name,c,r,i);w,h=max(1,round(im.width*scale)),max(1,round(im.height*scale))
 assert w<=size[0]-4 and h<=baseline-2,(group,index,(w,h),size,baseline)
 im=im.resize((w,h),Image.Resampling.NEAREST).quantize(colors=24,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
 out=Image.new('RGBA',size);at=((size[0]-w)//2,baseline-h);out.paste(im,at);path=A/f'{group}-{index:02}.png';out.save(path)
 entry={'id':index,'path':'assets/'+path.name,'pixels':list(size),'content':[at[0],at[1],w,h],'source':name,'source_cell':i,'source_crop':rect,'source_alpha_bounds':b}
 frames.setdefault(group,[]).append(entry);return out
# Complete battle drawings, never limb cutouts.
for key,size,base,body in [('cyclops',(80,80),72,36),('owl',(128,112),100,44)]:
 name=key+'-battle';scale=factor(name,4,4,0,body)
 if key=='owl':scale=min(scale,88/max(rawcell(name,4,4,i)[0].height for i in range(16)))
 for i in range(16):save(name,4,4,i,key+'-'+('intact' if i<8 else 'broken')+'-battle',i%8,scale,size,base)
for name,states in [('prometheus-battle-a-v2',['intact','fire-broken']),('prometheus-battle-b',['life-broken','both-broken'])]:
 scale=factor(name,4,4,0,56)
 for i in range(16):save(name,4,4,i,'prometheus-'+states[i//8]+'-battle',i%8,scale,(128,112),100)
# Map rows: down,right,up; left is a WHOLE mirror only for symmetric Cyclops/Owl.
for key in ['cyclops','owl']:
 name=key+'-maps';scale=factor(name,4,6,0,48);size=(96,80) if key=='owl' else (80,80)
 scale=min(scale,(size[0]-8)/max(rawcell(name,4,6,i)[0].width for i in range(24)),68/max(rawcell(name,4,6,i)[0].height for i in range(24)))
 for stateindex,state in enumerate(['intact','broken']):
  group=key+'-'+state+'-maps'
  for row,start in [(0,0),(1,4),(2,8)]:
   for phase in range(4):save(name,4,6,stateindex*12+row*4+phase,group,start+phase,scale,size,72)
  if key=='cyclops':
   frames[group]=[e for e in frames[group] if not 4<=e['id']<8]
   s=factor('cyclops-side-v2',4,2,0,48)
   for phase in range(4):save('cyclops-side-v2',4,2,stateindex*4+phase,group,4+phase,s,size,72)
  # Owl source row1 faces LEFT, verified against sensor hood and beak.
  for phase in range(4):
   entry=next(e for e in frames[group] if e['id']==4+phase);im=Image.open(R/entry['path'])
   if key=='owl':
    im.save(A/f'{group}-{12+phase:02}.png');im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);im.save(R/entry['path'])
   else:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);im.save(A/f'{group}-{12+phase:02}.png')
   copy=dict(entry);copy.update(id=12+phase,path=f'assets/{group}-{12+phase:02}.png',whole_mirror_of=4+phase);frames[group].append(copy)
for name,states in [('prometheus-maps-a',['intact','fire-broken']),('prometheus-maps-b',['life-broken','both-broken'])]:
 scale=factor(name,4,8,0,60);scale=min(scale,72/max(rawcell(name,4,8,i)[0].width for i in range(32)),68/max(rawcell(name,4,8,i)[0].height for i in range(32)))
 for si,state in enumerate(states):
  group='prometheus-'+state+'-maps'
  for row,start in [(0,0),(2,8)]:
   for phase in range(4):save(name,4,8,si*16+row*4+phase,group,start+phase,scale,(80,80),72)
  for direction,start,side_row in [('right',4,0),('left',12,1)]:
   idx=['intact','fire-broken','life-broken','both-broken'].index(state);s=factor('prometheus-sides-v2',4,8,idx*8,60);s=min(s,68/max(rawcell('prometheus-sides-v2',4,8,idx*8+side_row*4+j)[0].height for j in range(4)))
   for phase in range(4):save('prometheus-sides-v2',4,8,idx*8+side_row*4+phase,group,start+phase,s,(80,80),72)
# Bitmap FX; only cropping/native registration, no procedural drawing of effects.
fxnames=['violet-pulse','violet-hit','heal','boost','fire-bolt','fire-hit','revive','regen','physical-wave','core-break','dodge','smoke'];fx={}
for i,name in enumerate(fxnames):
 im,rect,b=rawcell('effects-v2',4,3,i);size=(32,48) if name=='revive' else (32,32);scale=min((size[0]-4)/im.width,(size[1]-4)/im.height)
 group='fx-'+name;save('effects-v2',4,3,i,group,0,scale,size,size[1]-1);fx[name]=frames.pop(group)[0]
# Reference soldier and hit timing already approved in the same gallery.
shutil.copyfile(R.parent/'water-monkey-v1-20261104/assets/soldier-reference.png',A/'soldier-reference.png')
shutil.copyfile(R.parent/'water-monkey-v1-20261104/assets/hit.ogg',A/'hit.ogg')
for group,entries in frames.items():
 entries.sort(key=lambda f:f['id']);first=Image.open(R/entries[0]['path']);ref=Image.new('RGBA',(first.width*len(entries),first.height))
 for i in range(len(entries)):ref.paste(first,(i*first.width,0))
 ref.save(A/f'{group}-reference.png')
# Native1x dark/light audit strips; no new artwork drawn by code.
for key in ['cyclops','owl','prometheus']:
 states=['intact','broken'] if key!='prometheus' else ['intact','fire-broken','life-broken','both-broken']
 bw,bh=Image.open(A/f'{key}-intact-battle-00.png').size;mw,mh=Image.open(A/f'{key}-intact-maps-00.png').size
 out=Image.new('RGBA',(max(bw*len(states),mw*4),bh+mh*len(states)),(29,44,54,255))
 for n,state in enumerate(states):
  out.alpha_composite(Image.open(A/f'{key}-{state}-battle-00.png'),(bw*n,0))
  for d,frame in enumerate([0,4,8,12]):out.alpha_composite(Image.open(A/f'{key}-{state}-maps-{frame:02}.png'),(mw*d,bh+mh*n))
 out.save(A/f'{key}-overview.png')
inventory=[]
for p in sorted(A.glob('*.png')):
 subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--strip','safe','--quiet',str(p)],check=True)
 im=Image.open(p);inventory.append({'path':'assets/'+p.name,'pixels':list(im.size),'bytes':p.stat().st_size,'colors':len(im.getcolors(1000000) or []),'use':'Review-only native pixel sprite, registration reference or bitmap FX','quality':'Whole generated poses, nearest registration, 24-color transparent native copies. Raw images kept offline.'})
(R/'asset-manifest.json').write_text(json.dumps({'status':'preview_only','frames':frames,'effects':fx,'images':inventory,'source_boundary_flags':warnings},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'groups':len(frames),'poses':sum(map(len,frames.values())),'images':len(inventory),'source_boundary_flags':warnings},ensure_ascii=False))
