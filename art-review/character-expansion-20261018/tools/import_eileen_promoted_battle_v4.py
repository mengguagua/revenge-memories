#!/usr/bin/env python3
"""Whole promoted battle poses, anatomical head scale, shared crouch and held sword."""
import argparse,copy,json,math,os
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,relative
from export_gallery import font
from import_eileen_complete import quant,box,center,C,NAVY,INDIGO,HAIR,SKIN,IVORY,BRASS
from import_knight_redraw_v3 import parts
from import_spellsword_complete import native_face
import import_sniper_complete as io
REV='eileen-promoted-battle-v4-20261024';OUT=ROOT/REV;SRC=OUT/'source';MAPPING=ROOT/'eileen-promoted/battle/frame_mapping.json';io.OUT=OUT;REG=[]
POINTS=[[89,165.5],[91,149.5],[88,156.5],[104,159.5],[108.5,153.5],[113,169],[63,156],[205.5,64]]
TARGETS={12:[47.5,20],13:[45,28],14:[45,44],15:[45.5,45]}

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def closest_skin(im,point):
 groups=[g for g in parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*SKIN,255))if len(g)>20];return min(groups,key=lambda g:sum((center(box(g))[j]-point[j])**2 for j in range(2)))
def landmarks(im,point):
 fb=box(closest_skin(im,point));candidates=[]
 for g in parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*HAIR,255)):
  b=box(g)
  if b[0]<=point[0]<b[2]and b[1]<=point[1]<b[3]:candidates.append(g)
 assert candidates,('no skull at anatomical face',point)
 skull=max(candidates,key=len);top=box(skull)[1];return fb,fb[3]-top,skull
def material_groups(im,point,skull,crouch=False,min_skin_area=0):
 # Preserve the generated shapes while assigning trouser/boot material;
 # the prompt's few peach knee gaps and red boot panels are not bare legs.
 skull=set(skull)
 for color in [SKIN,HAIR]:
  for g in parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*color,255)):
   if color==SKIN and len(g)<min_skin_area:continue
   b=box(g);cx,cy=center(b)
   leg=(cx>point[0]+90 and cy>point[1]+50)if crouch else(cy>point[1]+55 and b[1]>point[1]+30)
   if leg and not any(xy in skull for xy in g):
    for xy in g:im.putpixel(xy,(*INDIGO,255))
 return im
def register(im,point,label,target,floor=None,crouch=False,meta=None):
 im=im.copy();fb,height,skull=landmarks(im,point);material_groups(im,point,skull,crouch,350 if(meta or{}).get('source','').startswith('raw-')else 0)
 for y in range(fb[1],fb[3]):
  for x in range(fb[0],fb[2]):
   if im.getpixel((x,y))==(*IVORY,255):im.putpixel((x,y),(*BRASS,255))
 scale=30/height;dims=[round(v*scale)for v in im.size];at=[round(target[j]-point[j]*dims[j]/im.size[j])for j in range(2)]
 if floor is not None:at[1]=floor-dims[1]
 assert all(at[j]>=0 and at[j]+dims[j]<=(320,288)[j]for j in range(2)),(label,at,dims,point,height)
 small=im.resize(dims,Image.Resampling.NEAREST);q=Image.new('RGBA',(320,288));q.alpha_composite(small,tuple(at))
 assert sum(v[3]>0 for v in small.getdata())==sum(v[3]>0 for v in q.getdata()),label
 rec={**(meta or{}),'label':label,'anatomical_face':point,'face_box':fb,'skull_crown_y':box(skull)[1],'anatomical_head_height':height,'target_head_height':30,'scale':scale,'dimensions':dims,'translation':at,'target_face':target,'registered_face':[at[j]+point[j]*dims[j]/im.size[j]for j in range(2)],'whole_pose':True,'body_splices':0,'clipped_pixels':0};REG.append(rec);return q,rec
def new_figures():
 q=quant(Image.open(SRC/'pose-master.png').convert('RGBA'));groups=[g for g in parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3])if len(g)>1000];assert len(groups)==8;groups.sort(key=lambda g:center(box(g))[1]);groups=sorted(groups[:4],key=lambda g:box(g)[0])+sorted(groups[4:],key=lambda g:box(g)[0]);out=[]
 for n,g in enumerate(groups):
  b=box(g);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
  for x,y in g:im.putpixel((x-b[0],y-b[1]),q.getpixel((x,y)))
  out.append((im,{'source':'pose-master.png','cell':n,'source_bounds':b,'source_sha256':file_hash(SRC/'pose-master.png')}))
 return out
def sword(poses,registration):
 raw=quant(Image.open(SRC/'sword-hand-master.png').convert('RGBA'));g=max(parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3]),key=len);b=box(g);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
 for x,y in g:im.putpixel((x-b[0],y-b[1]),raw.getpixel((x,y)))
 im=im.rotate(-14,resample=Image.Resampling.NEAREST,expand=True);im=im.crop(im.getbbox());hand=max(parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==(*SKIN,255)),key=len);grip=center(box(hand));tip=max(((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]),key=lambda p:p[0]+p[1]);scale=75/math.dist(grip,tip);dims=[round(v*scale)for v in im.size]
 # Native retreat 11 shares the rear-hand carry of 31 and 23. Register to
 # the physical closed rear hand in the complete newly normalized body.
 target=[registration['translation'][j]+[161.5,149][j]*registration['dimensions'][j]/[229,301][j]for j in range(2)];at=[round(target[j]-grip[j]*dims[j]/im.size[j])for j in range(2)];small=im.resize(dims,Image.Resampling.NEAREST);layer=Image.new('RGBA',(320,288));assert all(at[j]>=0 and at[j]+dims[j]<=layer.size[j]for j in range(2));layer.alpha_composite(small,tuple(at));poses[11].alpha_composite(layer);io.save(layer,'layers/retreat-sword-hand.png','simple promoted silver sword continuously held in the rear hand, blade down-right');return {'source_sha256':file_hash(SRC/'sword-hand-master.png'),'target_grip':target,'rotation':-14,'hand_to_tip_length':75,'scale':scale,'dimensions':dims,'translation':at,'same_rear_hand_as_adjacent_poses':True}

def main(publish=False):
 baseline=json.loads((OUT/'baseline.json').read_text());m=copy.deepcopy(baseline['mapping']);poses={int(i):Image.open((MAPPING.parent/path).resolve()).convert('RGBA')for i,path in m['frame_mapping'].items()};raw=new_figures()
 for n,i in enumerate([2,8,10,12,13,14,15]):
  im,meta=raw[n];target=[v*4 for v in TARGETS.get(i,native_face(i))];poses[i],_=register(im,POINTS[n],str(i),target,meta=meta)
 crouch,creg=register(raw[7][0],POINTS[7],'whole crouch',[176,200],floor=257,crouch=True,meta=raw[7][1]);io.save(crouch,'layers/crouch-body.png','one intact promoted coat/head/knees/boots/support hands, not sliced across cloth')
 # Reuse Eileen's separately drawn braid layers: hair identity is shared
 # between her two costumes, while the promoted body remains independent.
 cfig=raw[7][0];fb=creg['face_box'];hair=parts((x,y)for y in range(cfig.height)for x in range(cfig.width)if cfig.getpixel((x,y))==(*HAIR,255));stubs=[g for g in hair if len(g)>80 and box(g)[0]>fb[2]+20 and box(g)[3]<fb[3]+20];stub=max(stubs,key=len);root=center(box(stub));target_root=[round(creg['translation'][j]+root[j]*creg['dimensions'][j]/cfig.size[j])for j in range(2)];shift=[target_root[0]-204,target_root[1]-196];hair_phases=[]
 for n in range(3):
  source=Image.open(ROOT/f'eileen-crouch-sword-v4-20261024/layers/hair-{n}.png').convert('RGBA');layer=Image.new('RGBA',(320,288));layer.alpha_composite(source,tuple(shift));assert sum(v[3]>0 for v in source.getdata())==sum(v[3]>0 for v in layer.getdata());hair_phases.append(layer);io.save(layer,f'layers/crouch-hair-{n}.png','Eileen braid layer placed behind one complete promoted crouch body')
 for i,phase in {16:0,22:0,17:1,18:2,19:0}.items():
  q=hair_phases[phase].copy();q.alpha_composite(crouch)
  if i==19:q.alpha_composite(Image.open(ROOT/'spellsword-complete-v1-20261023/original-slash-arc.png').convert('RGBA'))
  poses[i]=q
 # Complete existing drawings for launch/retreat; no lower-body patching.
 points={11:[39.5,58],20:[101,53.5],23:[77,55],24:[71,62.5],25:[158,62],27:[157,63],29:[155.5,62],30:[73,56.5],31:[80.5,58.5]};r11=None
 for i,point in points.items():
  im=Image.open(SRC/f'raw-{i:03}.png').convert('RGBA');poses[i],rec=register(im,point,str(i),[v*4 for v in native_face(i)],meta={'source':f'raw-{i:03}.png','source_sha256':file_hash(SRC/f'raw-{i:03}.png')})
  if i==11:r11=rec
 io.save(poses[11],'layers/retreat-body-without-sword.png','complete normalized retreat body before independent weapon registration');weapon=sword(poses,r11)
 aliases={3:2,4:2,5:2,6:2,7:2,9:8,21:20,26:25,28:27,32:29}
 for i,base in aliases.items():poses[i]=poses[base].copy()
 changed=list(range(2,33))
 for i in changed:io.save(poses[i],f'battle/frame-{i:03}.png','whole promoted battle pose, consistent head size and stable phase, weapon present')
 atlas=Image.new('RGBA',(320*len(poses),288));order=sorted(poses)
 for n,i in enumerate(order):atlas.alpha_composite(poses[i],(n*320,0))
 io.save(atlas,'battle-atlas.png','complete current promoted battle frame atlas')
 for light in [False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=NAVY if light else(235,243,242);q=Image.new('RGB',(360*4,330*math.ceil(len(order)/4)),bg);dr=ImageDraw.Draw(q)
  for n,i in enumerate(order):
   x=n%4*360+20;y=n//4*330;q.paste(poses[i],(x,y),poses[i]);dr.text((n%4*360+180,y+306),str(i),anchor='mm',font=font(18),fill=fg)
  q.save(OUT/f'battle-current-{"light"if light else"dark"}.png',optimize=True)
 m.update(revision=REV,review_note='引光剑使普通攻击：以真实面部和独立头颅标定空中体型，排除举剑手和上扬头发；每个空中阶段完整姿势保持。蹲地共用一个完整长衣／双腿／撑地手，仅松辫运动。回位11补齐后侧握剑手与银白剑。保留原帧序、跳跃轨迹、节奏、特效和第129帧唯一结算。',qa_report=os.path.relpath(OUT/'verification.json',MAPPING.parent),output_atlas=os.path.relpath(OUT/'battle-atlas.png',MAPPING.parent),output_atlas_order=order,batches=[{'id':'完整体型与落地持剑修正','review':os.path.relpath(OUT/'battle-current-light.png',MAPPING.parent),'status':'review_candidate'}])
 for i in changed:m['frame_mapping'][str(i)]=os.path.relpath(OUT/f'battle/frame-{i:03}.png',MAPPING.parent)
 write(OUT/'mapping-draft.json',m);write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'registrations':REG,'aliases':aliases,'changed_slots':changed,'whole_crouch_body_shared':True,'crouch_hair_registration':{'source_root':root,'target_root':target_root,'shift_from_existing_layers':shift},'weapon_registration':weapon,'body_splice_count':0,'runtime_integrated':False})
 if publish:write(MAPPING,m)
 print(json.dumps({'published':publish,'changed_slots':len(changed),'head_registrations':REG,'weapon':weapon}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
