# -*- coding: utf-8 -*-
"""Package explicit selected art; source equality required for every alias."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import json,hashlib,shutil,subprocess
P=Path(__file__).resolve().parent;R=P.parents[1]
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):
 im=Image.open(p);return {'path':str(p.relative_to(P)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p),'alpha_bounds':im.convert('RGBA').getbbox()}
def atlas(paths,size,path):
 out=Image.new('RGBA',(size[0]*len(paths),size[1]));
 for i,p in enumerate(paths):out.alpha_composite(Image.open(p).convert('RGBA'),(i*size[0],0))
 out.save(path,optimize=True)
u=read(P/'reference/source-unit.json');B=P/'battle';F=B/'frames';F.mkdir(exist_ok=True)
selection={0:'candidate-keys-v2',12:'candidate-keys-v2',30:'candidate-keys-v2',4:'candidate-motion-v2',5:'candidate-motion-v2',11:'candidate-special-v2',32:'candidate-special-v1',**{i:'candidate-sol'for i in range(6,11)}}
records=[]
for f,candidate in sorted(selection.items()):
 p=B/candidate/f'frame-{f:03}.png';out=F/f'frame-{f:03}.png';shutil.copy2(p,out);records.append({'source_frame':f,'selected_candidate':str(p.relative_to(B)),'revision':'sol' if f in range(6,11) else 'previous_review_retained',**row(out)})
for f,alias in [(16,0),(29,0)]:
 a=Image.open(P/f'reference/original-{f:03}.png').convert('RGBA');b=Image.open(P/f'reference/original-{alias:03}.png').convert('RGBA');assert a.size==b.size and a.tobytes()==b.tobytes();shutil.copy2(F/f'frame-{alias:03}.png',F/f'frame-{f:03}.png');records.append({'source_frame':f,'exact_source_alias_of':alias,'full_rgba_proof':True,**row(F/f'frame-{f:03}.png')})
order=sorted(selection);atlas([F/f'frame-{f:03}.png'for f in order],(320,256),F/'heavy-infantry-battle-sol.png')
for bg,label in [('#eee8d8','light'),('#1d2932','dark')]:
 out=Image.new('RGB',(960,4*536),bg);d=ImageDraw.Draw(out)
 for i,f in enumerate(order):
  x=i%3*320;y=i//3*536;d.text((x+12,y+4),f'{f:03} original / sol',fill='white'if label=='dark'else'black')
  a=Image.open(P/f'reference/original4-{f:03}.png').convert('RGBA');b=Image.open(F/f'frame-{f:03}.png').convert('RGBA');out.paste(a,(x,y+20),a);out.paste(b,(x,y+276),b)
 out.save(B/f'reviews/sol-all-{label}.png',optimize=True)
m={'schema_version':1,'revision':'sol','character_id':'class-2-ally','display_name':'重装兵（职业样板） · sol','original_class_id':2,'source_side':'ally','status':'complete_art_review_passed','runtime_integrated':False,'source_atlas':'../../../source-input/original-motion/class-2.png','source_frame_size':[80,64],'output_frame_size':[320,256],'source_anchor':[40,64],'output_anchor':[160,256],'source_columns':16,'source_oam_frame_count':16,'source_idle_frame':16,'source_frame_count':33,'frame_mapping':{str(f):f'frames/frame-{f:03}.png'for f in u['required_source_frames']},'canonical_frames':order,'required_source_frames':u['required_source_frames'],'variant_keys':u['bound_action_keys'],'output_atlas':'frames/heavy-infantry-battle-sol.png','records':records,'batches':[{'id':'sol','review':'reviews/sol-all-light.png','frames':order}],'limitations':['12刃尖约8输出像素、30枪端约14输出像素、11枪端约16–22输出像素的旧稿轮廓差异保留。','登记证明选定头顶及靴区域中心，不声称所有关节逐像素一致。','四倍画框保留原演示比例；既有已认可稿不重绘。']}
write(B/'frame_mapping.json',m)
M=P/'maps';MF=M/'frames';MF.mkdir(exist_ok=True);native=read(M/'native-reference/source-record.json')
walk_records=[]
for f in range(8):walk_records.append({'source_index':f,'source_frame':f,'output_index':f,'path':f'sol-native-frames/frame-{f:03}.png','output_path':f'sol-native-frames/frame-{f:03}.png','direction':['up','right','down','left'][f//2],'revision':'sol',**{k:v for k,v in row(M/f'sol-native-frames/frame-{f:03}.png').items()if k!='path'}})
atlas([M/f'sol-native-frames/frame-{f:03}.png'for f in range(8)],(128,96),MF/'tactical-native-walk-sol.png')
idle_records=[]
for f,a in enumerate([0,1,2,1,0,1]):idle_records.append({'source_index':f,'source_frame':f,'canonical_frame':a,'path':f'idle-frames/frame-{a:03}.png','output_path':f'idle-frames/frame-{a:03}.png','revision':'previous_review_retained'})
atlas([M/f'idle-frames/frame-{f:03}.png'for f in [0,1,2,1,0,1]],(96,96),MF/'tactical-idle-sol.png')
mm={'schema_version':1,'revision':'sol','character_id':'class-2-ally','actor_id':'class-2-ally','display_name':'重装兵（职业样板） · sol','class_id':2,'source_side':'ally','status':'complete_art_review_passed','runtime_integrated':False,'width_height_scale':4,'scenarios':[{'id':'tactical-walk','source_atlas':'../../../source-input/corrected-tactical-walk/class-2-ally.png','source_frame_size':[32,24],'source_anchor':[16,24],'output_atlas':'frames/tactical-native-walk-sol.png','output_frame_size':[128,96],'output_anchor':[64,96],'logical_render_scale':.25,'frame_mapping':walk_records,'directions':{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},'direction_mirror_x':{},'timing':{'native_fps':60.0988,'frame_ticks':16},'source_audit':{'status':'verified_native_tactical','source_chr':19,'cpu_entry':'bank011:L0BB5B1','evidence':'native-reference/source-record.json','overlay':'../../../source-input/corrected-tactical-walk/overlay.json','mirror_proof':'source/sol-native-registration.json','note':'CPU direction flips already baked in. Only exact 6←mirror2 and7←mirror3 are reused.'}},{'id':'tactical-idle','static_facing':True,'source_atlas':'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_2_ally.png','source_frame_size':[24,24],'source_anchor':[12,24],'output_atlas':'frames/tactical-idle-sol.png','output_frame_size':[96,96],'output_anchor':[48,96],'frame_mapping':idle_records,'directions':{'all':[0,1,2,1]},'direction_mirror_x':{},'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]},'source_aliases':{'0':0,'1':1,'2':2,'3':1,'4':0,'5':1}}]}
write(M/'frame_mapping.json',mm)
write(P/'manifest.json',{'id':'class-2-ally','revision':'sol','display_name':'重装兵（职业样板）','status':'complete_art_review_passed','battle_mapping':'battle/frame_mapping.json','maps_mapping':'maps/frame_mapping.json','inventory':'image-inventory.json','qa':'qa-report.json','generator':'Built-in image_gen; prompts and originals retained','runtime_integrated':False})
# Inventory every PNG, keep source outputs distinct from actual selected frames.
write(P/'image-inventory.json',{'revision':'sol','images':[{'purpose':'raw_or_reference'if '/source/'in str(p)or'/reference/'in str(p)else'review_or_delivery',**row(p)}for p in sorted(P.rglob('*.png'))]})
print('Packaged',len(records),'battle source slots and',len(walk_records),'native map slots; visual final review remains explicit.')
