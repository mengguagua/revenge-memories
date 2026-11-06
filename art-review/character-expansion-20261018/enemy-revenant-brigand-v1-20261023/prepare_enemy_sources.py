#!/usr/bin/env python3
"""Read frozen native art/timelines; write only this review candidate's sources."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib,json,collections
BASE=Path(__file__).resolve().parent
ROOT=BASE.parent
REPO=ROOT.parents[1]
OUT=BASE/'source'
FPS=60.0988

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def frame(atlas,n,size,columns):
 w,h=size;x=n%columns*w;y=n//columns*h
 return atlas.crop((x,y,x+w,y+h))
def board(images,labels,path,cols=6,scale=3):
 w=max(i.width for i in images)*scale+24;h=max(i.height for i in images)*scale+42
 image=Image.new('RGB',(cols*w,((len(images)+cols-1)//cols)*h),'#202735');d=ImageDraw.Draw(image)
 for n,(im,label) in enumerate(zip(images,labels)):
  x=n%cols*w;y=n//cols*h;up=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
  image.paste(up,(x+12,y+24),up);d.text((x+12,y+5),label,fill='#f3eedd')
 image.save(path,optimize=True)
 return {'path':str(path.relative_to(BASE)),'size':list(image.size),'bytes':path.stat().st_size}
def rle(frames):
 rows=[]
 for i,f in enumerate(frames):
  state={'frame':f['frame'],'flip':f.get('flip',False)}
  if rows and rows[-1]['state']==state:rows[-1]['end_tick']=i;rows[-1]['ticks']+=1
  else:rows.append({'start_tick':i,'end_tick':i,'ticks':1,'state':state})
 return rows
motion_path=ROOT/'source-input/enemy-motion/full-enemy-motion.json'
walk_path=ROOT/'source-input/corrected-tactical-walk/overlay.json'
legacy_path=REPO/'actual/data/legacy/graphics.json'
effects_path=REPO/'actual/data/legacy/full_animation_effects.json'
motion=read(motion_path);walking=read(walk_path);legacy=read(legacy_path);effects=read(effects_path)
audit={'runtime_integrated':False,'scope':'Read-only original enemy class11/14 sources, timings, poses and exact aliases; no shared gallery or runtime writes','native_fps':FPS,'source_files':[{'path':str(p.relative_to(REPO)),'sha256':sha(p)}for p in [motion_path,walk_path,legacy_path,effects_path,ROOT/'tools/build_gallery.py']],'classes':{},'boards':[]}
for cid,name,folder in [(11,'蚀躯','revenant'),(14,'断路匪','brigand')]:
 body=motion['original_bodies'][str(cid)]
 variants={k:v for k,v in motion['variants'].items() if int(v['source_class_id'])==cid and v.get('source_side')=='enemy'}
 walk=walking['records'][f'class-{cid}-enemy'].copy();walk['status']='verified_native_tactical'
 oldmap=legacy['map_units'][f'class_{cid}_enemy']
 idle_atlas=ROOT/'source-input/legacy-assets/assets/original/graphics/map_units'/f'class_{cid}_enemy.png'
 walk_atlas=ROOT/'source-input/corrected-tactical-walk'/walk['source_atlas']
 battle_atlas=ROOT/body['path']
 sources={'idle':idle_atlas,'walk':walk_atlas,'battle':battle_atlas}
 specs={'idle':([24,24],6,list(range(6))),'walk':(walk['source_frame_size'],8,list(range(8))),'battle':(body['frame_size'],body['columns'],body['required_source_frames'])}
 extracts={};images={};records={}
 folder_out=BASE/folder/'source';folder_out.mkdir(parents=True,exist_ok=True)
 for kind,p in sources.items():
  size,cols,indices=specs[kind];im=Image.open(p).convert('RGBA');images[kind]={};records[kind]=[]
  for n in indices:
   cut=frame(im,n,size,cols);images[kind][n]=cut
   target=folder_out/f'native-{kind}-{n:03}.png';cut.save(target,optimize=True)
   records[kind].append({'frame':n,'path':str(target.relative_to(BASE)),'size':list(cut.size),'alpha_bounds':cut.getbbox(),'rgba_sha256':hashlib.sha256(cut.tobytes()).hexdigest(),'bytes':target.stat().st_size})
 # Canonical atlas coordinates, never individually auto-centered for the painter.
 for kind,indices in [('idle',[0,1,2]),('walk',list(range(8))),('battle',body['unique_art_frames'])]:
  labels=[f'{name if False else folder} {kind} {n}'+(f' {walk["frame_mapping"][n]["direction"]} P{walk["frame_mapping"][n]["phase"]}' if kind=='walk' else '') for n in indices]
  audit['boards'].append(board([images[kind][n]for n in indices],labels,OUT/f'class-{cid}-{kind}-board.png',cols=4 if kind=='walk' else 6,scale=5 if kind in ['idle','walk']else 3))
 alias_proofs=[]
 for key,value in body['exact_pixel_aliases'].items():
  if int(key)!=int(value):
   valid=images['battle'][int(key)].tobytes()==images['battle'][int(value)].tobytes()
   assert valid
   alias_proofs.append({'source':int(key),'canonical':int(value),'rgba_exact':valid})
 summaries={}
 for key,v in variants.items():
  frames=v['frames'];summaries[key]={'ticks':len(frames),'seconds':len(frames)/float(v.get('native_fps',FPS)),'contact_tick':v.get('contact_tick'),'contact_seconds':v.get('contact_tick',0)/FPS,'source_program_id':v.get('source_program_id'),'unique_frames':sorted({f['frame']for f in frames}),'rle_frame_holds':rle(frames),'offset_range':[[min(f.get('offset',[0,0])[i]for f in frames),max(f.get('offset',[0,0])[i]for f in frames)]for i in range(2)],'frame_rows_sha256':hashlib.sha256(json.dumps(frames,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
 scenarios=[{'id':'tactical-idle','source_atlas':str(idle_atlas.relative_to(ROOT)),'source_frame_size':[24,24],'source_anchor':[12,20],'source_frame_count':6,'required_drawn_frames':[0,1,2],'static_facing':True,'directions':{'all':[0,1,2,1]},'timing':{'native_fps':FPS,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8],'cycle_ticks':44}}, {'id':'tactical-walk','source_atlas':str(walk_atlas.relative_to(ROOT)),'source_frame_size':walk['source_frame_size'],'source_anchor':walk['source_anchor'],'source_frame_count':8,'required_drawn_frames':list(range(8)),'directions':{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},'direction_mirror_x':{},'timing':{'native_fps':FPS,'frame_ticks':16,'cycle_ticks':32},'source_audit':walk}]
 record={'class_id':cid,'source_side':'enemy','name_zh':name,'body':body,'source_battle_graphic':legacy['battle'][f'class_{cid}_enemy'],'variants':variants,'variant_summaries':summaries,'source_legacy_effect_variants':{k:v for k,v in effects['variants'].items() if int(v.get('source_class_id',0))==cid and v.get('source_side')=='enemy'},'map_scenarios':scenarios,'frame_extracts':records,'exact_alias_verification':alias_proofs,'gallery_source_flip_rule':'enemy XOR frame.flip; OAM frame < source_oam_frame_count adds [16,0] to rendered origin; keep source anchor and original frame offsets; never infer extra shake from bounding box','idle_reaction_ticks':{'idle':60,'miss':round(.45*FPS),'hit':28,'exit':32},'notes':['Original battle idle is background frame; attack OAM and background frames can occupy different atlas x registration. Preserve anchors and OAM correction rather than normalizing all drawing bounding boxes.','Map walk source is native corrected tactical 8-slot atlas, not legacy six-pose idle atlas.','Idle display uses slots0,1,2,1 at14,8,14,8 ticks; no invented vertical bob.']}
 # Original BG upload duplicates the OAM idle at -16 logical X.
 shifted=Image.new('RGBA',images['battle'][body['unique_art_frames'][0]].size)
 first=33 if cid==11 else 8;bg=83 if cid==11 else 24
 shifted.alpha_composite(images['battle'][first],(-16,0))
 assert shifted.tobytes()==images['battle'][bg].tobytes()
 record['registered_pixel_aliases']=[{'source_frame':bg,'drawn_frame':first,'logical_translation':[-16,0],'rgba_exact':True}]
 record['newly_drawn_battle_frames']=[n for n in body['unique_art_frames'] if n not in ([47,49,83] if cid==11 else [24])]
 if cid==11:
  effect=images['battle'][47].copy()
  for y in range(effect.height):
   for x in range(effect.width):
    px=images['battle'][48].getpixel((x,y))
    if px[3]:
     assert effect.getpixel((x,y))==px
     effect.putpixel((x,y),(0,0,0,0))
  effect_path=folder_out/'native-claw-arc-047.png';effect.save(effect_path,optimize=True)
  record['native_effect_alias']={'source_frame':47,'body_frame':48,'effect_path':str(effect_path.relative_to(BASE)),'effect_pixels':sum(p[3]>0 for p in effect.getdata()),'body_rgba_exact':True}
  record['native_blank_frames']=[49]
 audit['classes'][str(cid)]=record
 write(folder_out/'native-baseline.json',record)
write(OUT/'native-baseline.json',audit)
print('Prepared', str(OUT/'native-baseline.json'))
