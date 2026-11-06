#!/usr/bin/env python3
"""Register both Eileen designs to her frozen personal-map and class11 programs."""
import argparse,copy,json,math,colorsys,os
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFilter
from build_gallery import ROOT,file_hash
from export_gallery import font
from prepare_eileen_complete import REV,OUT,SRC,write
from import_spellsword_complete import native_face
import import_knight_redraw_v3 as helper
import import_sniper_complete as io

HEX=['172638','31445d','3976b5','e4e1c8','dda77d','89516d','9e4247','bd9d68','a7d7e5']
C=[tuple(bytes.fromhex(h))for h in HEX]
NAVY,INDIGO,BLUE,IVORY,SKIN,MAGENTA,HAIR,BRASS,ICE=C
io.OUT=OUT
REG=[];STABLE=[]
def box(points):return[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1]
def center(b):return[(b[0]+b[2])/2,(b[1]+b[3])/2]
@lru_cache(maxsize=150000)
def material(rgb):
 h,s,v=colorsys.rgb_to_hsv(*(x/255 for x in rgb))
 if s>.24 and(h<.045 or h>.965)and rgb[0]>rgb[1]*1.3:return HAIR
 return min(C,key=lambda c:sum((a-b)**2 for a,b in zip(c,rgb)))
def quant(im):
 q=Image.new('RGBA',im.size);data=[]
 for p in im.getdata():
  fringe=p[2]>200 and p[0]<80 and p[1]<160
  data.append((*material(p[:3]),255)if p[3]>=240 and not fringe else(0,0,0,0))
 q.putdata(data);return q
def clean(im,label):
 pts=[(x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]]
 groups=helper.parts(pts)
 if not groups:return im
 removed=0
 for group in groups[1:]:
  if len(group)>20:continue
  for xy in group:im.putpixel(xy,(0,0,0,0));removed+=1
 return im
def face(im):
 groups=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*SKIN,255))
 candidates=[]
 for g in groups:
  b=box(g);w,h=b[2]-b[0],b[3]-b[1]
  if len(g)>25 and .55<w/h<2.1 and h<im.height*.35:candidates.append(g)
 assert candidates,'No face candidate'
 hair=Image.new('L',im.size)
 hair_groups=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255))
 for xy in max(hair_groups,key=len):hair.putpixel(xy,255)
 hair=hair.filter(ImageFilter.MaxFilter(13))
 upper=[g for g in candidates if center(box(g))[1]<im.height*.72]
 g=max(upper or candidates,key=lambda g:sum(hair.getpixel(xy)>0 for xy in g)+math.sqrt(len(g)))
 return center(box(g)),box(g)
@lru_cache(maxsize=32)
def figures(name,cols,rows):
 raw=quant(Image.open(SRC/name).convert('RGBA'));out=[]
 # A raised hand can reach over a nominal grid gutter. Extract connected
 # figures before sorting; never cut a complete arm at a cell boundary.
 groups=helper.parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3])
 groups=[g for g in groups if len(g)>1000]
 assert len(groups)==cols*rows,(name,'figure count',len(groups),cols*rows)
 groups.sort(key=lambda g:center(box(g))[1]);ordered=[]
 for n in range(0,len(groups),cols):ordered.extend(sorted(groups[n:n+cols],key=lambda g:center(box(g))[0]))
 for i,g in enumerate(ordered):
  b=box(g);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:im.putpixel((x-b[0],y-b[1]),raw.getpixel((x,y)))
  out.append((im,{'source':name,'cell':i,'source_visible_bounds':b,'source_opaque_pixels':len(g),'source_sha256':file_hash(SRC/name),'complete_connected_figure':True}))
 return out
def register(fig,size,target,floor,label,back=False,scale_override=None):
 im,meta=fig
 if back:
  pts=max(helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255)),key=len)
  first=min(y for x,y in pts);b=box([(x,y)for x,y in pts if y<first+im.height*.10]);p=[(b[0]+b[2])/2,b[1]+(b[2]-b[0])*.55];fb=[b[0],b[1],b[2],round(p[1]+4)]
 else:p,fb=face(im)
 scale=min((floor-target[1])/max(1,im.height-p[1]),target[0]/max(1,p[0]),(size[0]-target[0])/max(1,im.width-p[0]),target[1]/max(1,p[1]))
 if scale_override is not None:scale=min(scale,scale_override)
 dims=[max(1,round(im.width*scale)),max(1,round(im.height*scale))]
 small=im.resize(dims,Image.Resampling.NEAREST);at=[round(target[0]-p[0]*dims[0]/im.width),round(target[1]-p[1]*dims[1]/im.height)]
 assert at[0]>=0 and at[1]>=0 and at[0]+dims[0]<=size[0]and at[1]+dims[1]<=size[1],(label,dims,at,size)
 q=Image.new('RGBA',size);q.alpha_composite(small,tuple(at));q=clean(q,label)
 record={**meta,'label':label,'source_face':p,'face_box':fb,'target_face':target,'uniform_scale':scale,'scaled_size':dims,'translation':at,'clipped_pixels':0}
 REG.append(record);return q
def same_upper(poses,ids,seam,label):
 for i in ids[1:]:poses[i].paste(poses[ids[0]].crop((0,0,poses[i].width,seam)),(0,0))
 STABLE.append({'label':label,'frames':ids,'fixed_upper_region':[0,0,poses[ids[0]].width,seam]})
def mirrored_legs(im,seam,axis):
 lower=im.crop((0,seam,im.width,im.height));out=Image.new('RGBA',lower.size)
 if axis is None:
  b=lower.getbbox();axis=(b[0]+b[2])/2
 # Keep the lower-body envelope fixed while exchanging the two leg phases;
 # the adjacent coat hem follows, and the hands/weapon remain untouched.
 for y in range(lower.height):
  for x in range(lower.width):
   if lower.getpixel((x,y))[3]:
    xx=round(axis*2-1-x)
    if 0<=xx<lower.width:out.putpixel((xx,y),lower.getpixel((x,y)))
 q=im.copy();q.paste(out,(0,seam));return q
def maps(form):
 storyfig=figures('story-master.png',3,4);off=0 if form=='base'else 6
 story={i:register(storyfig[off+i],(128,96),[64,46],95,f'{form}-story-{i}',back=i in[2,3])for i in range(6)}
 for ids in [[0,1],[2,3]]:
  story[ids[1]]=mirrored_legs(story[ids[0]],77,None)
  STABLE.append({'label':f'{form} story opposed forward/back leg phases','frames':ids,'fixed_upper_region':[0,0,128,77],'lower_body_only_mirrored':True,'horizontal_lower_bounds_fixed':True})
 same_upper(story,[4,5],76,form+' story side upper body fixed')
 raw=figures(form+'-map-master.png',3,3)
 idle={i:register(raw[i],(96,96),[43,34],80,f'{form}-idle-{i}')for i in range(3)}
 # Keep the head, torso and BOTH legs from the same idle body. The holding
 # arm and sword remain outside the fixed region and move together.
 for i in [1,2]:
  idle[i].paste(idle[0].crop((37,27,96,96)),(37,27));idle[i].paste(idle[0].crop((0,60,96,96)),(0,60))
 STABLE.append({'label':form+' idle head torso and both legs fixed','frames':[0,1,2],'fixed_regions':[[37,27,96,96],[0,60,96,96]],'arm_and_sword_move_together':True})
 walk={}
 for index,cell,target in [(0,3,[56,46]),(1,4,[56,46]),(2,5,[70,46]),(3,6,[70,46]),(4,7,[64,46]),(5,8,[64,46])]:walk[index]=register(raw[cell],(128,96),target,95,f'{form}-walk-{index}',back=index in[0,1])
 for ids,axis in [([0,1],56),([4,5],64)]:
  walk[ids[1]]=mirrored_legs(walk[ids[0]],74,None)
  STABLE.append({'label':form+' tactical forward/back opposed legs','frames':ids,'fixed_upper_region':[0,0,128,74],'lower_body_only_mirrored':True,'horizontal_lower_bounds_fixed':True})
 same_upper(walk,[2,3],70,form+' tactical side arms fixed')
 walk[6]=walk[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);walk[7]=walk[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 return {'story':story,'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}
def battle(form):
 audit=json.loads((OUT/'source-audit.json').read_text());poses={}
 for n,ids in enumerate(audit['battle_batches'][:3]):
  raw=figures(f'{form}-battle-{n:02}-master.png',3,4)
  for i,fig in zip(ids,raw):
   original=Image.open(SRC/f'base-battle-{i:03}.png').convert('RGBA')
   poses[i]=register(fig,(320,288),[v*4 for v in native_face(i)],original.getbbox()[3],f'{form}-battle-{i}')
 raw=figures('casting-alpha-master.png',5,2);off=0 if form=='base'else 5
 for i,fig in zip(audit['battle_batches'][3],raw[off:off+5]):
  original=Image.open(SRC/f'base-battle-{i:03}.png').convert('RGBA');poses[i]=register(fig,(320,288),[v*4 for v in native_face(i)],original.getbbox()[3],f'{form}-battle-{i}')
 # Preserve the already corrected stable air poses; no rapid leg swapping.
 for ids,seam in [([2,3,4,5,6,7],112),([8,9],112),([25,26],184),([27,28],184)]:
  for i in ids[1:]:poses[i].paste(poses[ids[0]].crop((0,seam,320,288)),(0,seam))
  STABLE.append({'label':form+' stable airborne pelvis legs','frames':ids,'fixed_lower_region':[0,seam,320,288]})
 # Skin below the pelvis belongs to the reference's old bare thighs. Both
 # Eileen costumes use cloth leggings; retain every pixel and its silhouette.
 for i,im in poses.items():
  fp=[v*4 for v in native_face(i)]
  skin=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*SKIN,255))
  for group in skin:
   b=box(group)
   if len(group)>=65 and b[3]-b[1]>=8 and center(b)[1]>fp[1]+24:
    for xy in group:im.putpixel(xy,(*INDIGO,255))
 # Material components can join a different upper-body pixel in adjacent
 # poses. Reapply the shared lower plate after material classification too.
 for ids,seam in [([2,3,4,5,6,7],112),([8,9],112),([25,26],184),([27,28],184)]:
  for i in ids[1:]:poses[i].paste(poses[ids[0]].crop((0,seam,320,288)),(0,seam))
 # One exact native slash arc remains a separate visual, not an extra hit.
 arc=Image.open(ROOT/'spellsword-complete-v1-20261023/original-slash-arc.png').convert('RGBA');poses[19].alpha_composite(arc)
 for group in audit['battle_groups']:
  for i in group[1:]:poses[i]=poses[group[0]].copy()
 return poses
def asset(im,name,purpose):
 io.save(im,name,purpose);return OUT/name
def rel(path,parent):return os.path.relpath(path,parent)
def atlas(poses,size,path):
 q=Image.new('RGBA',(size[0]*len(poses),size[1]));order=sorted(poses)
 for n,i in enumerate(order):q.alpha_composite(poses[i],(n*size[0],0))
 return asset(q,path,'complete original slot order'),order
def board(entries,name,title,cols=4):
 cw,ch=360,330
 for light in[False,True]:
  q=Image.new('RGB',(cw*cols,52+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(q);fg=NAVY if light else(235,243,242);dr.text((q.width//2,25),title,anchor='mm',font=font(21),fill=fg)
  for n,(label,im)in enumerate(entries):
   if im.height<100:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
   x=n%cols*cw+(cw-im.width)//2;y=52+n//cols*ch;q.paste(im,(x,y),im);dr.text((n%cols*cw+cw//2,y+ch-18),label,anchor='mm',font=font(16),fill=fg)
  asset(q,f'{name}-{"light"if light else"dark"}.png','offline pose board, measured centered captions')
def build(publish=False):
 baseline=json.loads((OUT/'baseline.json').read_text());drafts={};contracts=[]
 for form,folder,job in [('base','eileen','女魔剑士'),('promoted','eileen-promoted','引光剑使')]:
  mp=maps(form);bp=battle(form);parent=ROOT/folder
  note='艾琳画像一致性：深红波浪刘海与低位松辫，象牙白海披肩、靛蓝与紫红旅行服、黄铜罗盘扣；头发纯色。'+('女魔剑士复用已完成职业的动作、冰蓝长剑和稳定跳跃骨架，按画像统一人物身份。'if form=='base'else'引光剑使独立长衣、白色护肩与黄铜细节设计，银白剑只改变外观，不表示提前获得引光剑或新增能力。')+'剧情与大地图共用同一套素材。'
  for kind,poses in {**mp,'battle':bp}.items():
   for i,im in poses.items():asset(im,f'{form}/{kind}/frame-{i:03}.png','generated identity pose, registered to native anchor and palette')
  board([(k+' '+str(i),im)for k,p in mp.items()for i,im in p.items()if k!='tactical-idle'or i<3],f'{form}-maps','艾琳 · '+job+' · 剧情与战斗地图')
  board([(str(i),im)for i,im in bp.items()],f'{form}-battle','艾琳 · '+job+' · 战斗姿势')
  mm={'schema_version':1,'character_id':'eileen','actor_id':'eileen','class_id':11,'source_side':'ally','display_name':'艾琳','display_class_name':job,'revision':REV,'status':'review_candidate','runtime_integrated':False,'palette':HEX,'review_note':note,'scenarios':[]}
  if form=='promoted':mm['hero_profession']='light_guide'
  for context in ['story','world','tactical-walk','tactical-idle']:
   kind='story'if context in['story','world']else context;poses=mp[kind];size=[96,96]if kind=='tactical-idle'else[128,96]
   if kind=='story':
    s={'id':context,'source_atlas':rel(SRC/'original-personal-map.png',parent/'maps'),'source_frame_size':[32,24],'source_anchor':[16,24],'output_frame_size':size,'output_anchor':[64,96],'logical_render_scale':.25,'directions':{'down':[0,1],'up':[2,3],'right':[4,5],'left':[4,5]},'direction_mirror_x':{'left':True},'timing':{'native_fps':60.0988,'frame_ticks':16,'phase':'continuous-clock'},'source_audit':{'status':'verified_native_personal','source_character_id':2}}
   else:
    old=next(s for s in baseline['maps']['scenarios']if s['id']==kind);s=copy.deepcopy(old)
    for field in ['source_atlas','motion_review']:
     if field in s:s[field]=rel((ROOT/'professions/class-11-ally/maps'/s[field]).resolve(),parent/'maps')
    for field,value in s.get('source_audit',{}).items():
     if isinstance(value,str)and value.startswith('../'):s['source_audit'][field]=rel((ROOT/'professions/class-11-ally/maps'/value).resolve(),parent/'maps')
   s.update(id=context,revision=REV,display_name='艾琳',review_note=note,frame_mapping=[],motion_review=rel(OUT/'README.md',parent/'maps'))
   s['ground_shadow']={'path':'hunapu-story-shadow-20261018/story-shadow.png'if kind=='story'else'gold-knight-walk-v3-20261020/ground-shadow.png','size':[11,3]if kind=='story'else[10,1.5],'offset':[0,-1]if kind!='tactical-idle'else[0,-2],'alpha':.38 if kind=='story'else .30}
   for i,im in sorted(poses.items()):
    p=OUT/f'{form}/{kind}/frame-{i:03}.png';value=rel(p,parent/'maps');s['frame_mapping'].append({'source_index':i,'source_frame':i,'output_index':i,'path':value,'output_path':value,'size':size,'bytes':p.stat().st_size,'sha256':file_hash(p)})
   p,_=atlas(poses,size,f'{form}/{kind}-atlas.png');s['output_atlas']=rel(p,parent/'maps');mm['scenarios'].append(s)
  keys=[]
  for a in baseline['actions']:
   if a['kind']!='attack':continue
   item=int(a['key'].split('_item_')[1].split('_')[0])if '_item_'in a['key']else None
   if item is not None and item not in[23,24,25,26,27,40]:continue
   keys.append(a['key']);contracts.append({'form':form,'actor_id':'eileen','character_id':2,'hero_profession':'light_guide'if form=='promoted'else None,'action':a['key'],'item_id':item,'native_ticks':len(a['frames']),'contact_tick':a['contactTick'],'original_actor_schedule_kept':True,'unlock_condition':'equipment-gated sword'if item is None else'initial fire spell'if item==23 else'original character2 learning table; not granted by art','additional_resolutions':0})
  bm=copy.deepcopy(baseline['battle_mapping'])
  for field,value in bm.items():
   if isinstance(value,str)and value.startswith('../'):bm[field]=rel((ROOT/'professions/class-11-ally/battle'/value).resolve(),parent/'battle')
  bm.update(character_id='eileen',display_name='艾琳',display_class_name=job,revision=REV,review_note=note,variant_keys=keys,frame_mapping={str(i):rel(OUT/f'{form}/battle/frame-{i:03}.png',parent/'battle')for i in bp},review_timeline=rel(OUT/'battle-motion.json',parent/'battle'),qa_report=rel(OUT/'verification.json',parent/'battle'),batches=[{'id':'艾琳专属完整战斗姿势','review':rel(OUT/f'{form}-battle-light.png',parent/'battle'),'status':'review_candidate'}])
  if form=='promoted':bm['hero_profession']='light_guide'
  p,order=atlas(bp,[320,288],f'{form}/battle-atlas.png');bm.update(output_atlas=rel(p,parent/'battle'),output_atlas_order=order)
  drafts[folder]={'maps':mm,'battle':bm}
  if publish:
   write(parent/'maps/frame_mapping.json',mm);write(parent/'battle/frame_mapping.json',bm);write(parent/'manifest.json',{'id':folder,'actor_id':'eileen','class_id':11,'display_class_name':job,'hero_profession':bm.get('hero_profession'),'revision':REV,'runtime_integrated':False,'status':'review_candidate','review_record':rel(OUT/'README.md',parent)})
 timeline=copy.deepcopy(baseline['review_timeline']);timeline.update(revision=REV,effects={},runtime_integrated=False);write(OUT/'battle-motion.json',timeline)
 write(OUT/'mapping-drafts.json',drafts);write(OUT/'action-effect-mapping.json',{'revision':REV,'actions':contracts,'spell_learning':{'initial':[23],'5':[26],'8':[24],'9':[40],'15':[27],'20':[25]},'advanced_trait':'existing offensive spell cost reduction only','personal_weapon_unlock':'current story_armaments item17 and inventory condition, not pre-equipped','new_effects':0,'runtime_integrated':False})
 write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':io.ASSETS,'registrations':REG,'stability_contracts':STABLE,'world_reuses_story':True,'battle_base_reuses_class11_choreography':True,'independent_promoted_design':True,'hair_material':'9e4247','runtime_integrated':False})
 print(json.dumps({'published':publish,'assets':len(io.ASSETS),'battle_slots_per_form':len(bp),'attack_variants_per_form':len(keys)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--inspect',action='store_true');a=p.parse_args()
 if a.inspect:
  for name,cols,rows in [('story-master.png',3,4),('base-map-master.png',3,3),('promoted-map-master.png',3,3),('casting-alpha-master.png',5,2)]:
   print(name,[(None if f is None else(f[0].size,face(f[0])[0]if i not in[2,3,8,9]or name!='story-master.png'else'back'))for i,f in enumerate(figures(name,cols,rows))],flush=True)
 else:build(a.publish)
