# coding: utf-8
"""Pack complete ImageGen poses and composite an exact crop of live F25 tiles; no game writes."""
from pathlib import Path
from PIL import Image, ImageEnhance
from functools import lru_cache
import json, shutil, subprocess, math
R=Path(__file__).resolve().parent; A=R/'assets';ROOT=R.parents[2];V1=R.parent/'puppet-trio-v1-20261105';frames={};effects={};source_evidence={}
OLD=json.loads((V1/'asset-manifest.json').read_text())
@lru_cache(None)
def source(name):return Image.open(R/'source'/f'{name}.png').convert('RGBA')
@lru_cache(None)
def components(name,c,r):
 im=source(name);w,h=im.size;mask=bytearray(im.getchannel('A').point(lambda p:1 if p>=165 else 0).tobytes());found=[]
 for seed in range(w*h):
  if not mask[seed]:continue
  mask[seed]=0;stack=[seed];l=w;t=h;rr=0;b=0;n=0
  while stack:
   p=stack.pop();y,x=divmod(p,w);n+=1;l=min(l,x);rr=max(rr,x);t=min(t,y);b=max(b,y)
   for d in (-1,1,-w,w,-w-1,-w+1,w-1,w+1):
    k=p+d
    if 0<=k<w*h and mask[k] and abs(k%w-x)<=1:mask[k]=0;stack.append(k)
  if n>500:found.append((n,(l,t,rr+1,b+1)))
 found=sorted(found,reverse=True)[:c*r];assert len(found)==c*r,(name,len(found),c*r)
 found.sort(key=lambda a:(a[1][1]+a[1][3])/2)
 ordered=[]
 for y in range(r):ordered.extend(sorted(found[y*c:(y+1)*c],key=lambda a:(a[1][0]+a[1][2])/2))
 rects=[b for _,b in ordered];source_evidence[name]={'rects':rects,'size':list(im.size),'touching_source_edge':[i for i,(l,t,rr,b) in enumerate(rects) if l==0 or t==0 or rr==w or b==h]};return rects
@lru_cache(None)
def raw(name,c,r,i):
 l,t,rr,b=components(name,c,r)[i];im=source(name).crop((max(0,l-2),max(0,t-2),min(source(name).width,rr+2),min(source(name).height,b+2)));im.putalpha(im.getchannel('A').point(lambda p:255 if p>=165 else 0));return im.crop(im.getbbox())
def flat(im):return im.quantize(colors=24,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
def registered(im,scale,size,baseline):
 w,h=max(1,round(im.width*scale)),max(1,round(im.height*scale));assert w<=size[0]-4 and h<=baseline-2,(im.size,(w,h),size,baseline)
 tile=Image.new('RGBA',size);im=flat(im.resize((w,h),Image.Resampling.NEAREST));tile.paste(im,((size[0]-w)//2,baseline-h));return tile

def add(group,index,im,src,cell=None):
 path=A/f'{group}-{index:02}.png';im.save(path);box=im.getbbox();frames.setdefault(group,[]).append({'id':index,'path':'assets/'+path.name,'pixels':list(im.size),'content':[box[0],box[1],box[2]-box[0],box[3]-box[1]],'source':src,'source_cell':cell});return im

def copy(group,idx):
 e=next(f for f in OLD['frames'][group] if f['id']==idx);return add(group,idx,Image.open(V1/e['path']).convert('RGBA'),'V1 '+e['path'],idx)

for si,state in enumerate(['intact','broken']):
 battle=f'cyclops-{state}-battle';g=f'cyclops-{state}-maps';name='cyclops-idle-rear'
 for i in range(8):copy(battle,i)
 for i in [0,1,2,3,4,5,6,7,12,13,14,15]:copy(g,i)
 s=48/raw(name,4,4,0).height
 for k in range(4):add(g,8+k,registered(raw(name,4,4,si*8+4+k),s,(80,80),72),name,si*8+4+k)
 for k in range(4):add(g,16+k,registered(raw(name,4,4,si*8+k),s,(80,80),72),name,si*8+k)

name='owl-battle';s=44/raw(name,5,4,0).height;s=min(s,92/max(raw(name,5,4,i).height for i in range(20)),120/max(raw(name,5,4,i).width for i in range(20)))
for si,state in enumerate(['intact','broken']):
 for i in range(10):add(f'owl-{state}-battle',i,registered(raw(name,5,4,si*10+i),s,(128,112),100),name,si*10+i)
name='owl-maps';s=48/raw(name,4,6,0).height;s=min(s,68/max(raw(name,4,6,i).height for i in range(24)),88/max(raw(name,4,6,i).width for i in range(24)))
for si,state in enumerate(['intact','broken']):
 g=f'owl-{state}-maps'
 for i in range(12):add(g,i,registered(raw(name,4,6,si*12+i),s,(96,80),72),name,si*12+i)
 for i in range(4):
  im=Image.open(A/f'{g}-{4+i:02}.png').convert('RGBA');add(g,12+i,im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),'whole mirror '+name,si*12+4+i)

states=['intact','fire-broken','life-broken','both-broken']
for j,state in enumerate(states):
 bi='boss-battle-a-framed' if j<2 else 'boss-battle-b';b0=(j%2)*8;s=66/raw(bi,4,4,0).height
 # No kneeling/fallen pose is exported for the boss. Final defeat stays upright then explodes.
 for i in range(6):add(f'prometheus-{state}-battle',i,registered(raw(bi,4,4,b0+i),s,(128,112),100),bi,b0+i)
 ma='boss-maps-a' if j<2 else 'boss-maps-b';d0=(j%2)*16;side='boss-right-back';g=f'prometheus-{state}-maps'
 for d in range(4):
  name,first=(ma,d0+d*4) if d in (0,3) else (side,j*8+(d-1)*4)
  scale=min(62/raw(name,4,8,first).height,68/max(raw(name,4,8,first+i).height for i in range(4)),74/max(raw(name,4,8,first+i).width for i in range(4)))
  for i in range(4):add(g,d*4+i,registered(raw(name,4,8,first+i),scale,(80,80),72),name,first+i)

for k in ['violet-pulse','violet-hit','heal','revive','regen','core-break','dodge','smoke']:
 e=dict(OLD['effects'][k]);shutil.copy2(V1/e['path'],R/e['path']);effects[k]=e

def fx_src(name,c,r,i):
 im=source(name);x,y=i%c,i//c
 # Measured gutters for this wide sheet keep the long jet's full nozzle.
 if name=='vfx-muted':
  borders=[0,448,895,1350,im.width] if y==0 else [0,520,895,1350,im.width]
  rect=(borders[x],round(y*im.height/r),borders[x+1],round((y+1)*im.height/r))
 else:rect=(round(x*im.width/c),round(y*im.height/r),round((x+1)*im.width/c),round((y+1)*im.height/r))
 im=im.crop(rect);im.putalpha(im.getchannel('A').point(lambda p:255 if p>=155 else 0));return im.crop(im.getbbox())

def fx_save(k,im,size,src,cell=None,align='center'):
 w,h=size;s=min((w-4)/im.width,(h-4)/im.height);im=flat(im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST));out=Image.new('RGBA',size);x=w-im.width-2 if align=='right' else (w-im.width)//2;out.paste(im,(x,(h-im.height)//2));path=A/f'fx-{k}.png';out.save(path);effects[k]={'path':'assets/'+path.name,'pixels':list(size),'source':src,'source_cell':cell};return out

vfx=[('flame-embers',0,(142,60)),('flame-crest',1,(142,86)),('flame-stream',2,(134,68)),('flame-ignite',3,(57,30)),('jet-main',4,(76,31)),('jet-small',5,(46,23)),('physical-wave',6,(64,58)),('talon-slash',7,(51,52))]
for k,i,size in vfx:fx_save(k,fx_src('vfx-muted',4,2,i),size,'vfx-muted',i,align='right' if k.startswith('flame') else 'center')
jet=fx_src('vfx-muted',4,2,4).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
for key,ang in [('jet-climb',-29),('jet-dive',36)]:fx_save(key,jet.rotate(ang,resample=Image.Resampling.NEAREST,expand=True),(74,62),'vfx-muted; whole plume registration',4)
for i,(key,size) in enumerate([('blast-flash',(58,58)),('blast-peak',(108,116)),('blast-debris',(106,114)),('blast-smoke',(104,108))]):fx_save(key,fx_src('explosion',4,1,i),size,'explosion',i)

# Actual game's enemy spearman; native4x sheet registered into a 2x tile-sized preview canvas.
idle=json.loads((ROOT/'actual/data/tactical_idle_20261031.json').read_text())['6_enemy'];path=ROOT/'actual'/idle['path'][6:];src=Image.open(path).convert('RGBA');piece=src.crop((0,0,96,96)).resize((48,48),Image.Resampling.NEAREST);out=Image.new('RGBA',(64,64));out.paste(piece,(round(32-idle['foot_x']/2),60-idle['poses'][0]['bottom']//2));out.save(A/'ally-map.png')
shutil.copy2(V1/'assets/soldier-reference.png',A/'soldier-reference.png');shutil.copy2(V1/'assets/hit.ogg',A/'hit.ogg')
# F25's current render layers and map tint; only crop 8x5 tiles, no terrain substitution or stage edits.
stage=json.loads((ROOT/'actual/data/stages/F25.json').read_text());atlas=Image.open(ROOT/'actual'/stage['art_atlas'][6:]).convert('RGBA');x0,y0=14,6;cols=stage['art_columns'];out=Image.new('RGBA',(128,80));tint=stage['map_tint']
for layer in stage['art_layers']:
 for y in range(y0,y0+5):
  for x in range(x0,x0+8):
   i=layer[y][x]
   if i is None or i<0:continue
   u,v=i%cols*16,i//cols*16;tile=atlas.crop((u,v,u+16,v+16));bands=tile.split();tile=Image.merge('RGBA',tuple(b.point(lambda p,j=j:round(p*tint[j])) for j,b in enumerate(bands)));out.alpha_composite(tile,((x-x0)*16,(y-y0)*16))
out.resize((256,160),Image.Resampling.NEAREST).save(A/'healing-ground-f25.png')
# Bake the preview palette into PNGs so mobile displays need no Canvas color filter.
def grade(path,saturation):
 im=Image.open(path).convert('RGBA');band=im.getchannel('A')
 im=ImageEnhance.Color(im).enhance(saturation);im.putalpha(band);im.save(path)
for group in frames.values():
 for f in group:grade(R/f['path'],.72)
for e in effects.values():grade(R/e['path'],.82)
for g,f in frames.items():f.sort(key=lambda x:x['id'])
M={'status':'preview_v2','frames':frames,'effects':effects,'source_evidence':source_evidence,'baked_palette':{'character_saturation':.72,'effect_saturation':.82},'map_reference':{'stage':'F25','tile_rect':[14,6,8,5],'scale':2,'atlas':stage['art_atlas'],'source':'actual/data/stages/F25.json','map_tint':tint,'companion':idle['path'],'companion_frame':0},'images':[]}
(R/'asset-manifest.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'groups':len(frames),'poses':sum(map(len,frames.values())),'fx':len(effects),'source_edges':{k:v['touching_source_edge'] for k,v in source_evidence.items() if v['touching_source_edge']}},ensure_ascii=False))
