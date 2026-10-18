#!/usr/bin/env python3
"""Package independent native tactical maps and complete the isolated exemplar."""
from pathlib import Path
from PIL import Image
import json, hashlib, subprocess, sys
R=Path(__file__).resolve().parents[1]; E=R.parents[1]; M=R/'maps'; B=R/'battle'
status='complete_art_review_passed' if '--review-passed' in sys.argv else 'review_candidate'
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def info(p):
    im=Image.open(p);return {'path':str(p.relative_to(R)),'size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'alpha_bounds':im.convert('RGBA').getbbox()}
ref=json.loads((M/'reference/tactical-native-source.json').read_text())
regs=json.loads((M/'registration.json').read_text()); by={(r['kind'],r['slot']):r for r in regs}
native=[*sorted((M/'tactical-native-frames').glob('frame-*.png')),M/'frames/tactical-native-walk.png']
idle=[*sorted((M/'frames').glob('idle-*.png')),M/'deliverables/tactical-idle.png']
subprocess.run(['/opt/homebrew/bin/oxipng','-o','4','--strip','safe','--quiet',*map(str,native+idle)],check=True)
scenarios=[]
for kind in ['walk','idle']:
    aliases=list(range(8)) if kind=='walk' else [0,1,2,1,0,1]
    rows=[]
    for f,c in enumerate(aliases):
        local=f'tactical-native-frames/frame-{f:03d}.png' if kind=='walk' else f'frames/idle-{f:03d}.png'
        z=info(M/local);rows.append({'source_index':f,'output_index':f,'source_frame':f,'canonical_frame':c,'output_path':local,'path':local,'direction':ref['frame_mapping'][f]['direction'] if kind=='walk' else 'fixed','registration':by[(kind,c)],**{k:v for k,v in z.items() if k!='path'}})
    s={'id':'tactical-'+kind,'class_id':8,'source_side':'ally','character_id':'class-8-ally','display_name':'佣兵（职业样板）','source_atlas':'reference/tactical-native-original.png' if kind=='walk' else 'reference/original-idle.png','source_frame_size':[32,24] if kind=='walk' else [24,24],'source_anchor':[16,24] if kind=='walk' else [12,20],'output_atlas':'frames/tactical-native-walk.png' if kind=='walk' else 'deliverables/tactical-idle.png','output_frame_size':[128,96] if kind=='walk' else [96,96],'output_anchor':[64,96] if kind=='walk' else [48,80],'logical_render_scale':0.25,'frame_mapping':rows,'directions':ref['directions'] if kind=='walk' else {'all':[0,1,2,1]},'direction_mirror_x':{},'default_facing':'right' if kind=='walk' else 'fixed','timing':ref['timing'] if kind=='walk' else {'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]},'source_aliases':{str(i):c for i,c in enumerate(aliases)}}
    if kind=='walk':s.update({'source_audit':{'status':'verified_native_tactical','proof':'../../../source-input/corrected-tactical-walk/verification.json','overlay':'../../../source-input/corrected-tactical-walk/overlay.json','reference_key':'class-8-ally','local_reference':'reference/tactical-native-source.json','review':'Original native eight-slot and dark/light redraw boards inspected.'},'source_reference_label':'原作校正参考（战术移动）','native_actor_origin':ref['native_actor_origin'],'registration_note':'Eight independent native poses. No mirror aliases; facing labels do not authorize moving the sword to the other side.'})
    scenarios.append(s)
write(M/'frame_mapping.json',{'schema_version':1,'character_id':'class-8-ally','actor_id':'class-8-ally','display_name':'佣兵（职业样板）','class_id':8,'source_side':'ally','status':status,'runtime_integrated':False,'width_height_scale':4,'scenarios':scenarios,'source_note':'Native tactical walker from original CPU bank11:L0BB5B1, CHR26. Static idle is original CHR24/25/21 metatile cycle. No old village-OAM hybrid used.'})
errors=[]
for p in native+idle:
    im=Image.open(p)
    if im.mode!='RGBA':errors.append('alpha:'+str(p))
    if p.parent.name=='tactical-native-frames' and im.size!=(128,96):errors.append('walk-size:'+str(p))
    if p.name.startswith('idle-') and im.size!=(96,96):errors.append('idle-size:'+str(p))
original=Image.open(M/'reference/original-idle.png').convert('RGBA')
idle_proof=[]
for f,c in enumerate([0,1,2,1,0,1]):
    a=original.crop((24*f,0,24*(f+1),24));b=original.crop((24*c,0,24*(c+1),24));ok=a.size==b.size and a.tobytes()==b.tobytes();idle_proof.append({'frame':f,'canonical':c,'rgba_exact':ok})
    if not ok:errors.append('source-idle-alias:'+str(f))
mapqa={'status':status,'structural_pass':not errors,'errors':errors,'source_audit_status':'verified_native_tactical','native_walk_slots':8,'independent_walk_drawings':8,'mirror_aliases':[],'idle_independent_drawings':3,'idle_alias_proof':idle_proof,'source_proof':'../../../source-input/corrected-tactical-walk/verification.json','registration_basis':'Selected supporting boot/paired idle soles and hair top. This does not assert every joint or every visible foot pixel matches.','manual_checks':['Eight native directions/phase slots inspected; no artificial mirror applied.','Up head-side paired light pixels interpreted as ears/head edges, not a raised empty fist.','Right faces are mostly frontal; left faces turn left. Sword remains on original side.','Native3/6 support stride corrected locally to avoid moving head/body when foot registered.','Blade tips shortened near source hair-top height; hands and costume retained.','Both light and dark boards inspected; no game/browser run.'],'retained_differences':'Redrawn coat panels, projected blade silhouette and some individual foot/head residuals remain; selected registration marker is not strict skeletal equality.','runtime_integrated':False}
write(M/'qa-report.json',mapqa)
write(R/'source-inspection.json',{'source_class_id':8,'side':'ally','battle':['Short split cloth/armor panels below waist, not exposed upper thighs. No source shield; new single brass shoulder guard and short purple coat preserve separate limbs.','1 compact preparation,2 airborne transition,3 folded-leg windup,4/5 long leading leg and folded other leg,7 lowered recovery,16 upright sword.','Source7 shifted -1 native pixel is exact RGBA subset of6; only the remaining original arc is retained as source effect. Source8/15 exactly alias0.'],'map':['Original CPU tactical CHR26 uses eight independent poses; no mirror aliases.','Up0/1 rear sword on image-right; paired head-edge light pixels are not high fists. Empty arm merges into coat-side silhouette.','Right2/3 mostly frontal face, left6/7 leftward face; all right/down/left poses hold visible sword on image-left.','Static idle uses original three fixed-facing phases, upright sword with small inward grip/angle change.','Opaque black original pixels and white blade are both inspected with contrasting backgrounds.'],'known_redesign_differences':json.loads((B/'qa-report.json').read_text())['geometry_limit'],'source_proofs':['battle/reference/ally-enemy-source-comparison.json','battle/reference/slash-reuse-proof.json','maps/reference/tactical-native-source.json'],'identity_scope':'Profession exemplar only. Does not unlock Carlo equipment or abilities.'})
delivery=[*sorted((B/'frames').glob('*.png')),*sorted((B/'deliverables').glob('*.png')),*native,*idle]
inventory=[]
for p in sorted(R.rglob('*.png')):
    z=info(p);z['role']='delivery' if p in delivery else 'review_preview' if '/reviews/' in str(p) else 'raw_history_or_reference';z['size_note']='Losslessly optimized delivery; retain visual quality over soft reference size limits.' if p in delivery else 'Isolated original/history/review, not runtime-integrated.';inventory.append(z)
write(R/'image-inventory.json',{'count':len(inventory),'images':inventory})
write(R/'qa-report.json',{'status':status,'structural_pass':not errors,'errors':errors,'battle':json.loads((B/'qa-report.json').read_text()),'maps':mapqa,'battle_native_independent_poses':9,'battle_unique_generated_body_poses':8,'battle_required_source_frames':11,'bound_attack_programs':7,'map_walk_native_poses':8,'map_walk_independent_poses':8,'map_idle_independent_poses':3,'delivery_png_count':len(delivery),'largest_delivery_bytes':max(p.stat().st_size for p in delivery),'runtime_integrated':False,'browser_or_game_screenshot':'Not run; source/read-only and isolated image review only.'})
write(R/'manifest.json',{'id':'class-8-ally','display_name':'佣兵（职业样板）','status':status,'battle_mapping':'battle/frame_mapping.json','maps_mapping':'maps/frame_mapping.json','qa':'qa-report.json','inventory':'image-inventory.json','source_inspection':'source-inspection.json','generator':'Built-in image_gen; complete prompts, raw outputs and local iterations retained.','history':{'battle-keys-v1-v2':'Costume accepted; upright blade length locally corrected.','battle-motion-v1-v4':'Compact legs and hand/weapon projection corrected; original slash reused by exact proof.','maps-v1-v2':'Native eight slots; face orientation and blade-length corrections.','maps-native3-6-v3':'Only wide support legs edited to preserve head/body registration.','maps-native5-v3-v4':'Overextended v3 retained as history; selected v4 shifts only support boot/shin slightly while retaining knee, hip and other leg.'},'runtime_integrated':False})
(R/'README.md').write_text('# 佣兵职业样板（class8 / ally）\n\n战斗9个独立源姿势、8份新人体、11个源帧引用，7条当前可达攻击绑定。帧6按原证据复用帧7平移并叠加原剑弧。\n\n战术地图使用原CPU核准的CHR26八个独立方向步相，左右不镜像；另有3个固定朝向待机姿势。入口为 `battle/frame_mapping.json` 和 `maps/frame_mapping.json`。\n\n黑色低束发、深紫分片战衣、象牙领、小铜肩甲、苔灰腰带与深靴为独立设计。可见腿、手和衣摆分层辨认，不按同色统一当肢体。登记只约束选定靴/头参考点，不宣称所有关节逐像素一致；原衣料外轮廓与新刀残差详见QA。\n\n原始生成图、提示词、全部局部迭代均保留；透明4倍交付图已无损优化。仅隔离素材，没有修改或接入游戏。\n')
print(json.dumps({'status':status,'delivery_png_count':len(delivery),'errors':errors,'map_max_bytes':max(p.stat().st_size for p in native+idle)}))
