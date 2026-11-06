#!/usr/bin/env python3
"""Authored Dawn Warrior sprites, registered separately from the basic Warrior."""
import argparse,copy,colorsys,hashlib,json,math,os
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFilter,ImageOps
from import_knight_redraw_v3 import parts
from export_gallery import font
ROOT=Path(__file__).resolve().parents[1];REV='hunapu-dawn-complete-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source';MP=ROOT/'hunapu-promoted/maps/frame_mapping.json';BP=ROOT/'hunapu-promoted/battle/frame_mapping.json'
HEX=['172638','263c64','3976a8','a7d7e5','e4e5df','d7a27c','a6776a','205b96','b9c5d1','4366b9'];C=[tuple(bytes.fromhex(h))for h in HEX];NAVY,DEEP,BLUE,ICE,PALE,SKIN,SHADE,HAIR,SILVER,GEM=C
ASSETS=[];REG=[];CORES=[]
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def box(g):return[min(x for x,y in g),min(y for x,y in g),max(x for x,y in g)+1,max(y for x,y in g)+1]
def center(b):return[(b[0]+b[2])/2,(b[1]+b[3])/2]
@lru_cache(maxsize=500000)
def color(rgb):return min(C,key=lambda c:sum((a-b)**2 for a,b in zip(rgb,c)))
def quant(raw):
 q=Image.new('RGBA',raw.size);q.putdata([(*color(p[:3]),255)if p[3]>=235 and not(p[2]>210 and p[0]<55 and p[1]>150)else(0,0,0,0)for p in raw.getdata()]);return q
def save(im,name,purpose):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 if im.mode=='RGBA':
  colors=sorted(set(im.getdata()));assert len(colors)<=256;q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-len(colors)*3));lut={c:i for i,c in enumerate(colors)};q.putdata([lut[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
 else:q=im
 q.save(p,optimize=True);row={'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'purpose':purpose};ASSETS.append(row);return p
def warm(p):return p[3]and p[0]>110 and p[0]>p[1]*1.08 and p[1]>p[2]*1.06
def blue(p):
 if not p[3]:return False
 h,s,v=colorsys.rgb_to_hsv(*(n/255 for n in p[:3]));return .52<h<.73 and s>.32 and v>.40
def face(im):
 groups=parts((x,y)for y in range(im.height)for x in range(im.width)if blue(im.getpixel((x,y))));candidates=[]
 for g in groups:
  b=box(g);w,h=b[2]-b[0],b[3]-b[1]
  if len(g)<5 or not .5<w/h<2.2 or len(g)/(w*h)<.30:continue
  roi=[max(0,b[0]-round(w*.10)),max(0,b[1]+round(h*.20)),min(im.width,b[2]+round(w*.10)),min(im.height,b[3]+round(h*.65))]
  skin=[(x,y)for y in range(roi[1],roi[3])for x in range(roi[0],roi[2])if warm(im.getpixel((x,y)))]
  if not skin:continue
  groupskin=parts(skin);s=max(groupskin,key=len);candidates.append((len(s),s))
 assert candidates,'no hair-bounded face candidates';g=max(candidates,key=lambda c:c[0])[1];bb=box(g);return center(bb),bb
def art_face(im):
 # Authored gauntlets leave the face as the largest skin component. Measuring
 # the full cheek avoids mistaking a small hair gap or raised hand for a face.
 groups=parts((x,y)for y in range(im.height)for x in range(im.width)if warm(im.getpixel((x,y))))
 bb=box(max(groups,key=len));return center(bb),bb
def hairbox(im,fp=None):
 pts=[(x,y)for y in range(im.height)for x in range(im.width)if blue(im.getpixel((x,y)))and(fp is None or abs(x-fp[0])<im.height*.18 and fp[1]-im.height*.24<y<fp[1]+im.height*.04)]
 groups=parts(pts);assert groups
 if fp is None:groups=[g for g in groups if center(box(g))[1]<im.height*.42]or groups
 return box(max(groups,key=len))
@lru_cache(maxsize=None)
def figures(name,cols,rows):
 raw=quant(Image.open(SRC/name).convert('RGBA'));groups=parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3]);main=[g for g in groups if len(g)>600 and sum(warm(raw.getpixel(p))for p in g)>30];assert len(main)==cols*rows,(name,len(main),[len(g)for g in main]);main.sort(key=lambda g:center(box(g))[1]);ordered=[]
 for n in range(0,len(main),cols):ordered+=sorted(main[n:n+cols],key=lambda g:center(box(g))[0])
 labels={id(g):i for i,g in enumerate(ordered)};sets=[set(g)for g in ordered];centers=[center(box(g))for g in ordered]
 for g in groups:
  if id(g)in labels or len(g)<4:continue
  b=box(g);p=center(b);i=min(range(len(sets)),key=lambda i:sum((p[k]-centers[i][k])**2 for k in(0,1)))
  if sum((p[k]-centers[i][k])**2 for k in(0,1))<(max(raw.size)/max(cols,rows)*.85)**2:sets[i].update(g)
 out=[]
 for i,g in enumerate(sets):
  bb=box(g);im=Image.new('RGBA',(bb[2]-bb[0],bb[3]-bb[1]))
  for x,y in g:im.putpixel((x-bb[0],y-bb[1]),raw.getpixel((x,y)))
  im.save(SRC/(name.removesuffix('.png')+f'-figure-{i:02}.png'));out.append(im)
 return out
def solid_hair(im,fp=None,back=False):
 out=im.copy();fp=fp or(face(im)[0]if not back else None);hb=hairbox(im,fp);pad=max(2,round((hb[2]-hb[0])*.12));roi=(max(0,hb[0]-pad),max(0,hb[1]-pad),min(im.width,hb[2]+pad),min(im.height,hb[3]+pad))
 for y in range(roi[1],roi[3]):
  for x in range(roi[0],roi[2]):
   p=im.getpixel((x,y))
   if p[3]and p[:3]in[BLUE,DEEP,HAIR,GEM]:out.putpixel((x,y),(*HAIR,255))
 return out,hb
def place(im,size,scale,point,target,label,ground=None):
 q=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST);rat=[q.size[i]/im.size[i]for i in(0,1)];at=[round(target[i]-point[i]*rat[i])for i in(0,1)]
 if ground is not None:at[1]=ground-q.getbbox()[3]
 bb=q.getbbox();at[0]=min(max(at[0],-bb[0]),size[0]-bb[2]);at[1]=min(max(at[1],-bb[1]),size[1]-bb[3]);out=Image.new('RGBA',size);out.alpha_composite(q,at);count=lambda m:sum(p[3]>0 for p in m.getdata());assert count(out)==count(q),(label,'clipped authored pixels')
 REG.append({'label':label,'scale':scale,'source_landmark':point,'target_landmark':target,'translation':at,'registered_landmark':[at[i]+point[i]*rat[i]for i in(0,1)],'clipped_pixels':0,'registered_face_height':None,'source_size':list(im.size),'scaled_size':list(q.size)});return out
def battle():
 specs=[('sword-master.png',5,2,[31,32,33,34,35,36,37,38,39,40]),('critical-a-master.png',4,3,[0,1,2,3,8,9,10,11,12,13,14,15]),('critical-b-master.png',3,2,[16,17,18,19,20,21]),('bow-master.png',3,1,[125,126,127])];poses={}
 for name,cols,rows,ids in specs:
  for i,raw in zip(ids,figures(name,cols,rows)):
   old=Image.open(SRC/f'base-battle-{i:03}.png').convert('RGBA');target,oldface=face(old);fp,fb=art_face(raw);im,hb=solid_hair(raw,fp);ground=old.getbbox()[3]
   # The forearm overlaps the lower cheek in 19. Use its batch's complete
   # face height so the occluded cheek cannot enlarge the entire figure.
   physical_face_height=39 if i==19 else 55 if i==127 else fb[3]-fb[1]
   # Bow artwork uses a more open face; compare full head width as well as
   # cheek height. A shared floor prevents the full-draw pose from floating.
   face_pixels=16.5 if i in[125,126,127]else 18
   if i in[125,126,127]:ground=272;target[0]=188
   if i in[17,18,19,20,21]:ground=272
   scale=face_pixels/physical_face_height;air=i in[11,12,13,14,15,16];poses[i]=place(im,(320,288),scale,fp,target,f'battle-{i}',ground=None if air else ground);REG[-1].update(registered_face_height=physical_face_height*scale,reference_face_height=oldface[3]-oldface[1],raw_face_box=fb,raw_hair_box=hb,airborne_head_registration=air,occluded_cheek_registration=i in[19,127])
 # Raised invocation is a stable hold; tiny mantle differences must not rescale
 # the complete body repeatedly, so both neighboring source slots share it.
 poses[21]=poses[20].copy()
 for old,new in[(60,0),(90,0),(119,31),(133,17),(134,18),(135,19),(136,20),(137,21),(138,126)]:poses[old]=poses[new].copy()
 return poses
def fixed_head(im,ref,box_,label):
 out=im.copy();region=ref.crop(box_);material=Image.new('L',region.size);material.putdata([255 if p[3]and p[:3]in[HAIR,SKIN,SHADE]else 0 for p in region.getdata()]);mask=material.filter(ImageFilter.MaxFilter(3));mask.putdata([m if p[3]else 0 for m,p in zip(mask.getdata(),region.getdata())]);out.paste(region,box_[:2],mask);CORES.append({'label':label,'fixed_head_region':list(box_),'method':'semantic hair/face and one pixel outline mask; exclude old blade and gem'});return out
def maps():
 storyraw=figures('story-master.png',3,2);tact=figures('tactical-master.png',3,3);story={};idle={};walk={}
 def reg(raw,kind,i,back=False):
  fp=None if back else art_face(raw)[0];im,hb=solid_hair(raw,fp,back);point=[(hb[0]+hb[2])/2,(hb[1]+hb[3])/2];size=(96,96)if kind=='idle'else(128,96);ground=80 if kind=='idle'else 95;scale=64/(im.getbbox()[3]-hb[1]);return place(im,size,scale,point,[size[0]/2,33 if kind=='idle'else 48],kind+'-'+str(i),ground)
 for cell,i in enumerate([0,2,4,1,3,5]):story[i]=reg(storyraw[cell],'story',i,i in[2,3])
 for i in range(3):idle[i]=reg(tact[i],'idle',i)
 for cell,i in[(3,0),(6,1),(4,2),(7,3),(5,4),(8,5)]:walk[i]=reg(tact[cell],'walk',i,i in[0,1])
 # Keep roots/head and pelvis steady while retaining the authored opposite legs.
 for name,ims,groups,head,waist in [('story',story,[[0,1],[2,3],[4,5]],(43,29,85,60),(58,66,70,73)),('walk',walk,[[0,1],[2,3],[4,5]],(43,28,85,59),(59,66,70,72)),('idle',idle,[[0,1,2]],(29,14,67,47),(43,53,55,59))]:
  for group in groups:
   for i in group[1:]:
    ims[i]=fixed_head(ims[i],ims[group[0]],head,name+'-'+str(i));ims[i].paste(ims[group[0]].crop(waist),waist[:2])
    if name=='idle':ims[i].paste(ims[group[0]].crop((0,61,96,96)),(0,61))
    if name=='walk':ims[i].paste(ims[group[0]].crop((0,0,128,71)),(0,0))
 walk[6]=ImageOps.mirror(walk[2]);walk[7]=ImageOps.mirror(walk[3]);return{'story':story,'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}
def board(items,name,title,cols=4):
 for light in[False,True]:
  cw,ch=360,330;bg=(220,222,216)if light else(32,45,53);fg=NAVY if light else(235,243,242);q=Image.new('RGB',(cw*cols,52+ch*math.ceil(len(items)/cols)),bg);dr=ImageDraw.Draw(q);dr.text((q.width/2,26),title,font=font(21),anchor='mm',fill=fg)
  for n,(label,im)in enumerate(items):
   if im.height<100:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%cols*cw+(cw-im.width)//2;y=52+n//cols*ch;q.paste(im,(x,y),im);dr.text((n%cols*cw+cw/2,y+ch-18),label,font=font(16),anchor='mm',fill=fg)
  save(q,name+('-light.png'if light else'-dark.png'),'深浅背景全部动作姿势与内容安全区域检查')
def build(publish=False):
 m=maps();b=battle();oldmaps=json.loads((ROOT/'hunapu/maps/frame_mapping.json').read_text());oldbattle=json.loads((ROOT/'hunapu/battle/frame_mapping.json').read_text());srcgallery=json.loads((SRC/'base-gallery.json').read_text());note='胡纳普·破晓勇士独立进阶形象：延续战士蓝发与年轻面孔，浅蓝护甲、深蓝长靴与短披肩，减少咖啡色；银色镂空蓝脊长剑、圆形蓝护手及短蓝羽带。剧情与大地图复用；地图头腰固定，步态和肢体前后分明。强化单次挥斩、跃起重斩和稳定收势；弓为实际弓装备的独立场景。外观不授予守约剑、引霆剑或新的能力。'
 for kind,poses in{**m,'battle':b}.items():
  for i,im in poses.items():save(im,f'{kind}/frame-{i:03}.png','破晓勇士独立人物动作帧')
 board([(k+' '+str(i),im)for k,poses in m.items()for i,im in poses.items()if k!='tactical-idle'or i<3],'maps','胡纳普 · 破晓勇士 · 全地图姿势')
 board([(str(i),b[i])for i in[31,32,33,34,35,36,37,38,39,40]],'sword','破晓勇士 · 前冲、蓄力、单次挥斩',5)
 board([(str(i),b[i])for i in[0,1,2,3,8,9,10,11,12,13,14,15,16]],'critical','破晓勇士 · 跃起重斩',4)
 board([(str(i),b[i])for i in[17,18,19,20,21,125,126,127]],'equipment','破晓勇士 · 剑技姿势与持弓',4)
 rel=lambda p,parent:os.path.relpath(p,parent);mm={'schema_version':1,'character_id':1,'actor_id':'hunapu','class_id':21,'source_side':'ally','display_name':'胡纳普','display_class_name':'破晓勇士','hero_profession':'dawn_warrior','revision':REV,'status':'review_candidate','runtime_integrated':False,'palette':HEX,'review_note':note,'scenarios':[]}
 for context in['story','world','tactical-walk','tactical-idle']:
  s=copy.deepcopy(next(x for x in oldmaps['scenarios']if x['id']==context));kind='story'if context in['story','world']else context;poses=m[kind];size=[96,96]if kind=='tactical-idle'else[128,96];s.update(revision=REV,status='review_candidate',display_name='胡纳普',review_note=note,frame_mapping=[],motion_review=rel(OUT/'README.md',MP.parent))
  for field in['source_atlas']:
   s[field]=rel((ROOT/'hunapu/maps'/s[field]).resolve(),MP.parent)
  for field in['generated_sheet','fixed_layer_contract','preview_image']:
   s.pop(field,None)
  atlas=Image.new('RGBA',(size[0]*len(poses),size[1]))
  for i,im in sorted(poses.items()):
   path=OUT/kind/f'frame-{i:03}.png';v=rel(path,MP.parent);s['frame_mapping'].append({'source_index':i,'source_frame':i,'output_index':i,'path':v,'output_path':v,'size':size,'bytes':path.stat().st_size,'sha256':sha(path)});atlas.alpha_composite(im,(i*size[0],0))
  s['output_atlas']=rel(save(atlas,kind+'-atlas.png','原槽位地图图集'),MP.parent);mm['scenarios'].append(s)
 keys=[a['key']for a in srcgallery['actions']if a['kind']=='attack'and a['key']!='original_class_21_normal'];bm=copy.deepcopy(oldbattle)
 for k,v in bm.items():
  if isinstance(v,str)and v.startswith('../'):bm[k]=rel((ROOT/'hunapu/battle'/v).resolve(),BP.parent)
 bm.update(character_id='hunapu',display_name='胡纳普',display_class_name='破晓勇士',hero_profession='dawn_warrior',revision=REV,status='review_candidate',runtime_integrated=False,review_note=note,source_idle_frame=119,variant_keys=keys,frame_mapping={str(i):rel(OUT/'battle'/f'frame-{i:03}.png',BP.parent)for i in b},qa_report=rel(OUT/'verification.json',BP.parent),batches=[{'id':'剑、必杀与弓完整姿势','review':rel(OUT/'sword-light.png',BP.parent),'status':'review_candidate'}]);bm.pop('review_timeline',None)
 atlas=Image.new('RGBA',(320*len(b),288));order=sorted(b)
 for n,i in enumerate(order):atlas.alpha_composite(b[i],(n*320,0))
 bm.update(output_atlas=rel(save(atlas,'battle-atlas.png','全部新战斗姿势图集'),BP.parent),output_atlas_order=order)
 write(OUT/'mapping-drafts.json',{'maps':mm,'battle':bm});write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registrations':REG,'map_root_stability':CORES,'world_reuses_story':True,'runtime_integrated':False})
 if publish:
  write(MP,mm);write(BP,bm);write(MP.parent.parent/'manifest.json',{'id':'hunapu-promoted','actor_id':'hunapu','class_id':21,'hero_profession':'dawn_warrior','display_class_name':'破晓勇士','revision':REV,'runtime_integrated':False,'status':'review_candidate','review_record':rel(OUT/'README.md',MP.parent.parent)})
 print(json.dumps({'published':publish,'map_slots':20,'battle_slots':len(b),'native_attack_variants':len(keys),'assets':len(ASSETS)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();build(a.publish)
