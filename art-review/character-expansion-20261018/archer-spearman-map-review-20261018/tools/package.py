"""Publish only the four review mappings; never write runtime assets or packages."""
from pathlib import Path
from PIL import Image
import copy, hashlib, json, os, subprocess

V=Path(__file__).resolve().parents[1]; R=V.parent
KEYS=['class-12-ally','class-12-enemy','class-6-ally','class-6-enemy']
REV='archer-spearman-map-20261018'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def rel(p,base):return os.path.relpath(p,base)
protected=V/'other-mappings-baseline.json'
if not protected.exists():
    dump(protected,{str(p.relative_to(R)):sha(p) for p in R.glob('**/frame_mapping.json') if p.parent.parent.name not in KEYS})
inventory=[]
for key in KEYS:
    base=R/'professions'/key/'maps'; O=V/'deliverables'/key
    old=json.loads((V/'reference'/f'{key}-mapping-before.json').read_text())
    role='archer' if '12' in key else 'spear'
    palette=['#172638','#3976B5' if key.endswith('ally') else '#AE5148','#E4E1C8','#DDA77D']
    notes={
      'archer':{'tactical-walk':'头、身体、双臂和弓箭固定，仅腿脚交替。', 'tactical-idle':'身体、头部、腿脚与拉弦手固定，仅持弓手臂和弓箭上下运动。'},
      'spear':{'tactical-walk':'头部固定，完整手臂、腿脚和长枪按原两步交替；下裙甲仍为衣甲。', 'tactical-idle':'头、身体、腿脚和空手臂固定，仅持枪手臂和长枪运动。'}
    }[role]
    new={k:copy.deepcopy(old[k]) for k in ['schema_version','class_id','source_side','actor_id','character_id','display_name','width_height_scale'] if k in old}
    new.update(revision=REV,status='awaiting_user_review',runtime_integrated=False,
      art_mode='Built-in ImageGen; technical crop/registration, four-color remap, separate fixed/moving layers, native mirrors, lossless PNG.',
      review_note='本轮双方弓箭手／枪兵地图样板，四种不透明色、连续脚下投影；等待用户验收。',
      qa_report=rel(V/'verification.json',base),source_originals_unchanged=True,
      palette=palette,scenarios=[])
    for before in old['scenarios']:
        context=before['id']; kind='walk' if context=='tactical-walk' else 'idle'; count=8 if kind=='walk' else 6
        keep=['id','class_id','source_side','character_id','display_name','source_atlas','source_frame_size','source_anchor','source_columns','source_frame_count','output_frame_size','output_anchor','logical_render_scale','directions','direction_mirror_x','default_facing','static_facing','timing','idle','native_alias_groups','source_audit','original_source_path','proven_mirror_pairs','mirror_note','exact_mirror_aliases']
        s={k:copy.deepcopy(before[k]) for k in keep if k in before}
        frames=[]
        for i in range(count):
            p=O/f'{kind}-{i:02}.png'; image=Image.open(p).convert('RGBA')
            subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',str(p)],check=True)
            record={'source_index':i,'output_index':i,'path':rel(p,base),'output_path':rel(p,base),'size':list(image.size),'bytes':p.stat().st_size,'sha256':sha(p),'visible_bounds':list(image.getbbox()),'art_revision':REV,'generated_source':rel(V/'source'/f'{key}-generated.png',base),'construction':'fixed generated body plus moving generated parts; native frame timing/aliases'}
            prior=before['frame_mapping'][i]
            for field in ['native_cpu_frame','source_frame','direction','source_visible_bounds']:
                if field in prior:record[field]=copy.deepcopy(prior[field])
            frames.append(record)
            inventory.append({'path':str(p.relative_to(R)),'purpose':new['display_name']+' '+context,'dimensions':list(image.size),'bytes':p.stat().st_size,'sha256':sha(p)})
        size=s['output_frame_size']; atlas=Image.new('RGBA',(size[0]*count,size[1]))
        for i in range(count):atlas.paste(Image.open(O/f'{kind}-{i:02}.png'),(size[0]*i,0))
        atlaspath=O/f'{kind}-atlas.png';atlas.save(atlaspath,optimize=True)
        subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',str(atlaspath)],check=True)
        inventory.append({'path':str(atlaspath.relative_to(R)),'purpose':context+' atlas','dimensions':list(atlas.size),'bytes':atlaspath.stat().st_size,'sha256':sha(atlaspath)})
        shadow={'path':'hunapu-story-shadow-20261018/story-shadow.png','size':[11,3],'offset':[-2 if role=='spear' and kind=='idle' else 0,-1],'alpha':.38,'kind':'continuous_fixed_ground_projection','source':'Reuse accepted protagonist continuous shadow; separate fixed ground layer beneath every foot phase.'}
        s.update(frame_mapping=frames,output_atlas=rel(atlaspath,base),output_atlas_bytes=atlaspath.stat().st_size,
          revision=REV,review_note=notes[context],preview_ground='map-motion-review-v3/reference/grounds/tactical-M11.png',ground_shadow=shadow,
          motion_review={'reference':str((V/'native-motion-diff.json').relative_to(R)), 'fixed_and_moving_parts':notes[context]},
          adaptation_note=notes[context]+' 保留原作方向、源帧别名与时序；蓝／红阵营识别，简洁四色。')
        new['scenarios'].append(s)
    if key.endswith('ally'):
        idle=next(s for s in new['scenarios'] if s['id']=='tactical-idle')
        story=copy.deepcopy(idle)
        story.update(id='story',source_atlas=rel(V/'reference'/f'{key}-tactical-idle-00.png',base),source_columns=1,source_frame_count=1,
          output_atlas=idle['frame_mapping'][0]['output_path'],output_atlas_bytes=idle['frame_mapping'][0]['bytes'],
          frame_mapping=[copy.deepcopy(idle['frame_mapping'][0])],directions={'all':[0]},direction_mirror_x={},
          static_pose_preview=True,static_facing=True,timing={'native_fps':60.0988,'preview_hold_ticks':60},
          preview_ground='map-motion-review-v3/reference/grounds/story-P00-cobble.png',reference_label='原作职业待机',
          reference_provenance='Native tactical idle slot 0 shown for identity comparison, not an independent original story animation.',
          review_note='按用户本轮范围，仅静止形象，与战斗待机首帧使用同一张图片。',
          action_note='本轮不制作剧情四向行走。',adaptation_note='友军剧情形象直接复用本轮战斗待机首帧。')
        for k in ['idle','native_alias_groups','source_audit','motion_review','original_source_path']:story.pop(k,None)
        new['scenarios'].append(story)
    dump(base/'frame_mapping.json',new)
dump(V/'image-inventory.json',inventory)
print({'published_review_mappings':KEYS,'sprite_frames':56,'friendly_story_static':2,'runtime_integrated':False})
