#!/usr/bin/env python3
"""Check only the class14 candidate; optional isolated gallery, never export."""
import argparse,ast,json
from pathlib import Path
from PIL import Image
from build_gallery import pack_frame
from import_knight_redraw_v3 import parts
from import_enemy_brigand_v1 import ROOT,OUT,SRC,REV,COLORS,ACTOR,digest,write,pixel_count

def resolve(ref):
 p=(ROOT/'professions'/ACTOR/'battle'/ref).resolve()
 assert p.is_relative_to(OUT.resolve()),'candidate reference escaped its isolated directory'
 return p

def main(gallery=None):
 base=json.loads((SRC/'native-baseline.json').read_text());meta=json.loads((OUT/'asset-manifest.json').read_text());recipe=json.loads((OUT/'pose-inputs.json').read_text());drafts=json.loads((OUT/'mapping-drafts.json').read_text());checks=[];assets=[]
 def check(value,label):
  assert value,label
  checks.append(label)
 maps=drafts[f'professions/{ACTOR}/maps/frame_mapping.json'];battle=drafts[f'professions/{ACTOR}/battle/frame_mapping.json']
 check(set(drafts)=={f'professions/{ACTOR}/{kind}/frame_mapping.json'for kind in['maps','battle']},'only class14 mappings staged')
 check(maps['source_side']==battle['source_side']=='enemy','faction remains enemy')
 check(maps['class_id']==battle['original_class_id']==14,'class identity remains14')
 check(not maps['runtime_integrated']and not battle['runtime_integrated'],'review only; runtime not integrated')
 check(meta['source_pose_inputs_sha256']==digest(OUT/'pose-inputs.json'),'pose recipe matches generated assets')
 check(not recipe.get('pending_redraws'),'all requested pose repairs completed')
 check(battle['variant_keys']==list(base['variants']),'all original class14 variants retained')
 check(battle['source_frame_size']==[80,64]and battle['output_frame_size']==[320,256],'native body logical size and4x art size')
 check(battle['source_anchor']==[40,64]and battle['output_anchor']==[160,256],'native anchor unchanged')
 check(sorted(map(int,battle['frame_mapping']))==base['body']['required_source_frames'],'all required native battle slots present')
 for scenario in maps['scenarios']:
  original=next(s for s in base['map_scenarios']if s['id']==scenario['id']);walk=scenario['id']=='tactical-walk'
  check(scenario['timing']==original['timing'],scenario['id']+' exact native timing')
  check(scenario['directions']==original['directions'],scenario['id']+' native direction slot order')
  check(scenario.get('direction_mirror_x',{})==original.get('direction_mirror_x',{}),scenario['id']+' no extra direction mirror')
  ids=list(range(8 if walk else 6));check([r['source_index']for r in scenario['frame_mapping']]==ids,scenario['id']+' full native slot coverage')
  ims=[]
  for row in scenario['frame_mapping']:
   p=resolve(row['path']);im=Image.open(p).convert('RGBA');ims.append(im)
   check(list(im.size)==([128,96]if walk else[96,96]),p.name+' map size')
   check(digest(p)==row['sha256'],str(p)+' mapping hash')
  if not walk:
   for a,b in[(3,1),(4,0),(5,1)]:check(ims[a].tobytes()==ims[b].tobytes(),'native idle alias '+str(a))
  else:check(len({im.tobytes()for im in ims})==8,'all independent directional steps are drawn')
 for record in meta['assets']:
  p=ROOT/record['path'];check(p.is_relative_to(OUT),'asset stays within brigand directory')
  check(digest(p)==record['sha256'],'asset content hash '+record['path'])
  im=Image.open(p).convert('RGBA')
  if '/frame-' not in record['path']:continue
  check(set(im.getchannel('A').getdata())<={0,255},'clean binary transparency '+record['path'])
  colors={c[:3]for c in im.getdata()if c[3]};effect='battle/frame-014' in record['path']
  check(effect or colors<=set(COLORS),'approved six material colors '+record['path'])
  components=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3])
  check(len(components)==3 if effect else len(components)==1,'connected whole anatomy / two unchanged source effect islands '+record['path'])
  assets.append({'path':record['path'],'dimensions':list(im.size),'bytes':p.stat().st_size,'colors':len(colors),'components':len(components),'reference_size_met':p.stat().st_size<50000})
 def body(i):return Image.open(resolve(battle['frame_mapping'][str(i)])).convert('RGBA')
 shifted=Image.new('RGBA',(320,256));shifted.alpha_composite(body(8),(-64,0))
 check(shifted.tobytes()==body(24).tobytes()==body(31).tobytes(),'native background aliases retain exact -16 logical X')
 fx=Image.open(OUT/'native-slash-effect-014.png').convert('RGBA');check(pixel_count(fx)==77*16,'original77-pixel slash retained at4x')
 fx.alpha_composite(body(15));check(fx.tobytes()==body(14).tobytes(),'slash frame14 uses original effect and body15')
 for reg in meta['registration']:
  check(reg['clipped_pixels']==0,'no clipped source pose '+reg['label'])
  check(digest(SRC/reg['source'])==reg['source_sha256'],'source retained '+reg['label'])
 groups=[[f'idle-{i}'for i in range(3)]]+[[f'walk-{i}',f'walk-{i+1}']for i in[0,2,4,6]]
 registrations={r['label']:r for r in meta['registration']}
 for group in groups:
  rows=[registrations[k]for k in group]
  for key in ['target_head','target_hip']:
   check(all(r[key]==rows[0][key]for r in rows),'fixed '+key+' '+str(group))
  for key in ['head','hip']:
   for axis in[0,1]:check(max(r['actual_landmarks'][key][axis]for r in rows)-min(r['actual_landmarks'][key][axis]for r in rows)<=1.5,'registered '+key+' stability '+str(group))
 core_report=[]
 check(len(recipe['fixed_map_cores'])==5,'nonempty fixed core coverage for idle and all four directions')
 def drawn(label):
  kind,index=label.rsplit('-',1);return Image.open(OUT/('tactical-idle'if kind=='idle'else'tactical-walk')/f'frame-{int(index):03}.png').convert('RGBA')
 for group in recipe['fixed_map_cores']:
  first=drawn(group['poses'][0]);regions=[]
  for box,kind in zip(group['boxes'],group['purpose']):
   reference=first.crop(box);bounds=reference.getbbox()
   check(bool(bounds),'registered '+kind+' contains real pixels '+str(group['poses']))
   for label in group['poses'][1:]:check(drawn(label).crop(box).tobytes()==reference.tobytes(),'pixel-exact fixed '+kind+' '+label)
   regions.append({'kind':kind,'box':box,'actual_pixel_bounds':bounds,'head_size_difference':[0,0]if kind=='head_neck'else None,'centroid_drift_output_pixels':[0,0],'rgba_equal':True})
  core_report.append({'poses':group['poses'],'regions':regions,'whole_actor_translation':[0,0]})
 # Anatomical phase check: two different PNGs are insufficient. The grounded
 # boot crosses the fixed waist axis while the head/waist core does not move.
 supports={}
 for index in[0,1,4,5]:
  im=drawn('walk-'+str(index));bottom=im.getbbox()[3]-1;pts=[(x,y)for y in range(bottom-3,bottom+1)for x in range(im.width)if im.getpixel((x,y))[3]]
  center=sum(x+.5 for x,y in pts)/len(pts);width=max(x for x,y in pts)-min(x for x,y in pts)+1
  check(width>=7,'grounded boot has a real sole width '+str(index))
  supports[str(index)]={'sole_center_x':center,'bottom_y':bottom,'sole_width':width,'waist_axis_x':64,'side':'left'if center<64 else'right'}
 check(supports['0']['sole_center_x']<64<supports['1']['sole_center_x'],'back walk alternates grounded left and right boots')
 check(supports['4']['sole_center_x']>64>supports['5']['sole_center_x'],'front native slot4 right / slot5 left support order')
 check(supports['4']['sole_center_x']>=67 and supports['4']['sole_center_x']-supports['5']['sole_center_x']>=4,'front support leg has clear lateral separation with fixed upper body')
 # The original black silhouette includes a ground shadow. Its lowest row
 # is not an anatomical foot. Read the colored extended shin at y20..22.
 for index in[0,1,4,5]:
  original=Image.open(SRC/f'native-walk-{index:03}.png').convert('RGBA')
  shin=[(x,y)for y in range(20,23)for x in range(original.width)if original.getpixel((x,y))==(254,110,204,255)]
  check(bool(shin),'native colored shin evidence '+str(index))
  native_center=sum(x+.5 for x,y in shin)/len(shin);native_side='left'if native_center<16 else'right'
  supports[str(index)].update(native_shin_pixels=shin,native_shin_center_x=native_center,native_support_side=native_side,native_reference_sha256=digest(SRC/f'native-walk-{index:03}.png'))
  check(supports[str(index)]['side']==native_side,'new anatomy matches original source phase '+str(index))
 equipment=[]
 for group in meta['shared_equipment']:
  layer=Image.open(resolve(group['reference_path'])).convert('RGBA')
  for target in group['targets']:
   im=drawn(target['pose']);dx,dy=target['translation'];mismatches=sum(im.getpixel((x+dx,y+dy))!=layer.getpixel((x,y))for y in range(layer.height)for x in range(layer.width)if layer.getpixel((x,y))[3])
   check(mismatches==0,'rigid axe contour retained '+target['pose']);equipment.append({'pose':target['pose'],'reference':group['source'],'translation':target['translation'],'outline_changed_pixels':mismatches,'size_change':[0,0]})
 schedules=[]
 if gallery:
  data=json.loads(Path(gallery).read_text());actions=[a for a in data['actions']if a['profile'].startswith('professions-class-14-enemy-')]
  check(bool(actions),'isolated gallery contains class14 actions')
  for a in actions:
   check(a['ready'],'ready '+a['id']);check(not a.get('revisedFrames')and not a.get('reviewTailFrames'),'no timing rewrite '+a['id'])
   if a['kind']=='attack':
    v=base['variants'][a['key']];check(a['frames']==[pack_frame(r)for r in v['frames']],'original battle program frames/offsets/effects '+a['key']);check(a['fps']==v['native_fps']and a['contactTick']==v['contact_tick']and a['origin']==v['actor_origin'],'original FPS/contact/origin '+a['key']);schedules.append({'key':a['key'],'ticks':len(a['frames']),'contact_tick':a['contactTick']})
   elif a['kind']=='map_walk':
    first={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']];check([r['frame']for r in a['frames']]==[i for _ in range(3)for i in[first,first+1]for _ in range(16)],'original map walk rhythm '+a['id']);check(all(r['offset']==[0,0]and not r['flip']for r in a['frames']),'fixed original map origin '+a['id'])
   elif a['key']=='idle-cycle':check([r['frame']for r in a['frames']]==[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)],'original idle cycle')
 for script in['import_enemy_brigand_v1.py','verify_enemy_brigand_v1.py']:ast.parse((ROOT/'tools'/script).read_text())
 report={'status':'passed','checks':len(checks),'assets':assets,'native_schedules':schedules,'gallery_verified':bool(gallery),'native_timing_modified':False,'map_head_neck_hip_origins_fixed':True,'fixed_core_measurements':core_report,'axe_contour_measurements':equipment,'support_leg_measurements':supports,'runtime_integrated':False,'user_visual_acceptance':'pending'}
 write(OUT/'verification.json',report);print(json.dumps({'status':'passed','checks':len(checks),'gallery_verified':bool(gallery)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--gallery',type=Path);main(p.parse_args().gallery)
