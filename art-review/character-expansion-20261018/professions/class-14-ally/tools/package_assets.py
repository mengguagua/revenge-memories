#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];E=R.parents[1];B=R/'battle';M=R/'maps'
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def info(p):
 im=Image.open(p);return {'path':str(p.relative_to(R)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'alpha_bounds':im.convert('RGBA').getbbox()}
u=next(x for x in json.loads((E/'catalog/production-units.json').read_text())['units'] if x['id']=='class-14-ally');meta=json.loads((E/'source-input/original-motion/full-original-motion.json').read_text())['original_bodies']['14'];canon=u['unique_art_frames'];required=u['required_source_frames'];delivery=[*sorted((B/'frames').glob('*.png')),*sorted((B/'deliverables').glob('*.png')),*sorted((M/'frames').glob('*.png')),*sorted((M/'deliverables').glob('*.png'))]
subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe','--quiet',*[str(p)for p in delivery]],check=True)
regs=json.loads((B/'candidate-keys-v2/registration.json').read_text())+json.loads((B/'candidate-motion-v2/registration.json').read_text());byframe={r['frame']:r for r in regs};records=[]
for f in required:
 c=u['exact_pixel_aliases'][str(f)];record={'source_frame':f,'canonical_frame':c,**info(B/f'frames/frame-{f:03d}.png')}
 if c in byframe:record['registration']=byframe[c]
 if f==7:record['composition']={'body_frame':6,'original_arc':'reference/original-slash-only-007.png','shift':[0,0],'proof':'reference/slash-reuse-proof.json'}
 records.append(record)
write(B/'frame_mapping.json',{'schema_version':1,'character_id':'class-14-ally','display_name':'村民（职业样板）','original_class_id':14,'source_side':'ally','status':'complete_art_review_passed','runtime_integrated':False,'source_atlas':'../../../source-input/original-motion/class-14.png','source_frame_size':[80,64],'output_frame_size':[320,256],'source_anchor':[40,64],'output_anchor':[160,256],'source_columns':16,'source_oam_frame_count':16,'source_idle_frame':16,'source_frame_count':meta['frames'],'frame_mapping':{str(f):f'frames/frame-{f:03d}.png'for f in required},'canonical_frames':canon,'required_source_frames':required,'variant_keys':u['bound_action_keys'],'records':records,'output_atlas':'deliverables/battle-canonical.png','output_atlas_frame_order':canon,'external_effects':'Original external lightning effects remain separate. Frame7 source slash is isolated and composited behind the identical new frame6 body at original coordinates.','art_generator':'built-in image_gen','identity_scope':'Profession exemplar; does not grant Carlo or any named actor new equipment, card or ability.'})
reg=json.loads((M/'registration.json').read_text());byid={r['id']:r for r in reg};scenarios=[]
for typ,aliases,ss,os,sa,oa in [('walk',[0,1,0,1,0,1],[32,24],[128,96],[16,24],[64,96]),('idle',[0,1,2,1,0,1],[24,24],[96,96],[12,20],[48,80])]:
 rows=[]
 for f,c in enumerate(aliases):
  inf=info(M/f'frames/{typ}-{f:03d}.png');rows.append({'source_index':f,'output_index':f,'source_frame':f,'canonical_frame':c,'output_path':f'frames/{typ}-{f:03d}.png','path':f'frames/{typ}-{f:03d}.png','direction':'native-authored'if typ=='walk'else'fixed','registration':byid[f'{typ}-{c:03d}'],**{k:v for k,v in inf.items()if k!='path'}})
 scenarios.append({'id':'tactical-'+typ,'class_id':14,'source_side':'ally','character_id':'class-14-ally','display_name':'村民（职业样板）','source_atlas':f'reference/original-{typ}.png','source_frame_size':ss,'source_anchor':sa,'output_atlas':f'deliverables/tactical-{typ}.png','output_frame_size':os,'output_anchor':oa,'logical_render_scale':0.25,'frame_mapping':rows,'default_facing':'right'if typ=='walk'else'fixed','directions':{'down':[0,1],'up':[2,3],'right':[4,5],'left':[4,5]}if typ=='walk'else{'all':[0,1,2,1]},'direction_mirror_x':{'left':True}if typ=='walk'else{},'timing':{'native_fps':60.0988,'frame_ticks':16,'cycle_ticks':32,'move_ticks_per_tile':16,'phase':'continuous-clock'}if typ=='walk'else{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]},'source_aliases':{str(f):c for f,c in enumerate(aliases)}})
write(M/'frame_mapping.json',{'schema_version':1,'character_id':'class-14-ally','actor_id':'class-14-ally','display_name':'村民（职业样板）','class_id':14,'source_side':'ally','status':'complete_art_review_passed','runtime_integrated':False,'width_height_scale':4,'scenarios':scenarios,'source_note':'Two source walking phases from CHR26 sprite48, L0AA371/L0AA382. The right direction label is a program baseline, not an instruction to flip the source silhouette.'})
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',18)
for theme,bg in [('dark',(30,44,53)),('light',(229,230,220))]:
 board=Image.new('RGBA',(1648,1248),bg+(255,));d=ImageDraw.Draw(board);fg=(235,242,244)if theme=='dark'else(34,43,47)
 for group,fs in enumerate([canon[:5],canon[5:]]):
  y=group*624;d.text((24,y+14),'村民原作：'+ ' / '.join(map(str,fs)),font=font,fill=fg);d.text((24,y+326),'四倍像素修订：衣装重绘与原动作时序',font=font,fill=fg)
  for k,f in enumerate(fs):board.alpha_composite(Image.open(B/f'reference/original-{f:03d}.png').convert('RGBA'),(24+k*320,y+44));board.alpha_composite(Image.open(B/f'frames/frame-{f:03d}.png').convert('RGBA'),(24+k*320,y+356))
 board.convert('RGB').save(B/f'reviews/final-canonical-{theme}.png',optimize=True)
write(R/'source-inspection.json',{'source_class_id':14,'side':'ally','battle':['Short tunic with visibly separated legs and calf protection; no original shield/cape/skirt armor. New short vest, rolled sleeves and trousers preserve visible limb actions.','Frames1–3 high sword angled upper-left, three distinct running leg phases; frame4 upright sword to RIGHT of head; frame5 blade up-right, frame6 low close-in sword and bent high free arm.','Frame6 all2688 opaque 4x source pixels are exactly equal to frame7 at same XY; extra frame7 pixels are original slash only. Frame16/31 exactly alias0.'],'map':['CHR26 sprite48: two walking phases. Broad white below head in phase0 belongs to connected clothing silhouette, not a long shoulder sword. Independent right-side narrow tool follows source side and small movement.','Idle short blade moves from diagonal (4,7) to (6,12), to upright x6/7,y7..13, to inward upright x8,y7..13. The last blade remains visible; initial occluded interpretation was corrected after exact pixel review.','Original black pixels are opaque. Light backgrounds alone can hide white blades; final dark and light comparisons inspected.'],'known_redesign_differences':['Battle1–3 blade tips roughly10–18 output pixels left of originals; battle5 tip roughly11output pixels lower. Root accepted as new sword shaping, not strict pixel lock.','Battle5 visible boot centers about9/8 output pixels inward from source while same lunge phase; map idle far boot drawn at y80 versus native y76. Kept explicitly separate from anchor rounding accuracy.'],'source_aliases':{'walk':[0,1,0,1,0,1],'idle':[0,1,2,1,0,1]},'identity_scope':'Profession exemplar, not named-actor ability unlock.'})
inventory=[]
for p in sorted(R.rglob('*.png')):
 z=info(p);z['role']='delivery'if p in delivery else'review_preview'if'/reviews/'in str(p)else'raw_history_or_reference';z['size_note']='Losslessly optimized at native4x target; atlas may exceed soft50KB reference to preserve fine details.'if z['role']=='delivery'and z['bytes']>50000 else'Losslessly optimized delivery.'if z['role']=='delivery'else'Isolated raw/reference/history or review file; not game-integrated.';inventory.append(z)
write(R/'image-inventory.json',{'count':len(inventory),'images':inventory})
errors=[]
for p in delivery:
 if Image.open(p).mode!='RGBA':errors.append('not_RGBA:'+str(p.relative_to(R)))
for f in required:
 if Image.open(B/f'frames/frame-{f:03d}.png').size!=(320,256):errors.append('battle_size:'+str(f))
for typ in ['walk','idle']:
 for f in range(6):
  if Image.open(M/f'frames/{typ}-{f:03d}.png').size!=((128,96)if typ=='walk'else(96,96)):errors.append('map_size:'+typ+str(f))
for f in [16,31]:
 if Image.open(B/f'frames/frame-{f:03d}.png').tobytes()!=Image.open(B/'frames/frame-000.png').tobytes():errors.append('alias:'+str(f))
write(R/'qa-report.json',{'structural_pass':not errors,'errors':errors,'battle_native_independent_poses':9,'battle_unique_generated_body_poses':8,'battle_required_source_frames':11,'bound_attack_programs':7,'map_walk_independent_poses':2,'map_idle_independent_poses':3,'delivery_png_count':len(delivery),'largest_delivery_bytes':max(p.stat().st_size for p in delivery),'manual_checks':['Original clothing, visible blade/grip and body occlusion inspected.','Original/new full canonical dark/light boards inspected.','Map idle2 white vertical blade recovered after pixel-coordinate audit, not inferred absent from light board.','Raw stray semitransparent marks removed via imagegen targeted cleanup, raw history retained.','Chosen visible feet/paired boot anchors registered with uniform resampling, no weapon bbox centering or clamping.'],'source7_reuse_proof':json.loads((B/'reference/slash-reuse-proof.json').read_text()),'root_review':'Root accepted final battle keys/motion and final map dark/light boards.','geometry_limit':'Redrawn garment and weapon contours, some per-foot perspective offsets remain; see source-inspection known_redesign_differences. Anchor rounding is NOT a claim that every limb pixel matches.','browser_or_game_screenshot':'Not run; isolated art only; prior browser restriction honored.','runtime_integrated':False})
write(R/'manifest.json',{'id':'class-14-ally','display_name':'村民（职业样板）','status':'complete_art_review_passed','battle_mapping':'battle/frame_mapping.json','maps_mapping':'maps/frame_mapping.json','inventory':'image-inventory.json','qa':'qa-report.json','source_inspection':'source-inspection.json','history':{'battle-keys-v1':'Costume accepted; sword side/length/grip refined.','battle-keys-v2':'Selected0/4/32 local grip/sword corrections.','motion-v1':'Three running steps and two strikes; blade lengths/angles/stance refined.','motion-v2':'Selected1–3/5/6;7 source slash composited separately.','maps-v1':'Initial large-headed form and wrong down-pointing walking blade retained only as history.','maps-v2':'Head proportion and upright short-tool corrections; selected walk and idle0/1.','idle002-v3-v4':'Recovered visible inward native blade and cleaned generated gray smudges; selectedv4.'},'generator':'Built-in image_gen, all prompts and raw/history retained.','runtime_integrated':False})
(R/'README.md').write_text('''# 村民职业样板（class14 / ally）

战斗 9 个原生独立姿势（8 份新人体，斩击帧7复用6加原弧），11 个源帧引用；7 条当前可达攻击绑定。战术地图为 2 个行走步相、3 个待机姿势。原别名、原帧时序与外置雷电保持。

入口：`battle/frame_mapping.json`、`maps/frame_mapping.json`。所有图像只在本隔离目录，未修改或接入游戏。形象是职业样板，不给卡洛等角色新增能力。

原作短衣与可见腿部按层识别，新增卷袖衬衣、短皮背心、橙色腰巾、灰裤和布绑腿。地图待机第三相的白刃原本仍可见，已按 x8、y7–13 的原像素补回；深浅底均复核。

登记使用可见靴底与头高，统一比例缩放，不按刀尖居中。保留的新刀轮廓和少量脚部透视差异详见 `source-inspection.json`，不声称逐像素锁定。最终对照在 `battle/reviews/final-canonical-*.png`、`maps/reviews/map-original-vs-new-*.png`。提示词、原始生成稿和全部局部修订均保留。
''')
print(json.dumps({'delivery_png_count':len(delivery),'max_bytes':max(p.stat().st_size for p in delivery),'errors':errors,'battle':len(required),'map_canonical':5}))
