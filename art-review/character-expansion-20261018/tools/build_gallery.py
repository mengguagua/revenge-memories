#!/usr/bin/env python3
"""Build the offline review gallery from explicit art mappings; never mutate game data."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, math, re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FPS = 60.0988
SPELL_NAMES={23:'火球',24:'雷电',25:'诸神黄昏',26:'圣光',27:'风刃',28:'箭雨',29:'光环',30:'盖亚',31:'多拉',32:'史莱姆',33:'死亡',34:'美杜莎',35:'恢复',36:'全体恢复',37:'召唤',38:'眼光',39:'眼球',40:'恢复',41:'远程恢复',42:'吸血',43:'传送',44:'全体恢复',45:'幻影',46:'驱邪',47:'无法攻击'}

def read(path):
    return json.loads(path.read_text())

def relative(path):
    return path.resolve().relative_to(ROOT).as_posix()

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def matched_export(path, digest):
    metadata=path.with_suffix('.json')
    return path.is_file() and metadata.is_file() and read(metadata).get('contentDigest')==digest

def close_camera(profile, action):
    """One stable camera size per action, large enough for both complete source and redraw silhouettes."""
    bounds=[];w,h=profile['sourceFrameSize'];atlas=Image.open(ROOT/profile['sourceAtlas']).convert('RGBA')
    seen=set()
    for row in action['frames']:
        f=row['frame'];flip=(profile.get('side')=='enemy')!=row.get('flip',False)
        state=(f,flip)
        if state in seen:continue
        seen.add(state);column=profile['sourceColumns'];x=f%column*w;y=f//column*h
        images=[(atlas.crop((x,y,x+w,y+h)),1,1)]
        if str(f)in profile['newFrames']:
            redraw=Image.open(ROOT/profile['newFrames'][str(f)]).convert('RGBA')
            images.append((redraw,w/redraw.width,h/redraw.height))
        correction=profile['flipOriginOffset']if flip and f<profile['sourceOamCutoff']else[0,0]
        for image,sx,sy in images:
            box=image.getbbox()
            if not box:continue
            box=[box[0]*sx,box[1]*sy,box[2]*sx,box[3]*sy]
            if flip:box=[w-box[2],box[1],w-box[0],box[3]]
            bounds.append([box[0]-profile['anchor'][0]+correction[0],box[1]-profile['anchor'][1]+correction[1],box[2]-profile['anchor'][0]+correction[0],box[3]-profile['anchor'][1]+correction[1]])
    for row in action.get('revisedFrames', []):
        f=row['frame']
        if str(f) not in profile['newFrames']:continue
        image=Image.open(ROOT/profile['newFrames'][str(f)]).convert('RGBA');box=image.getbbox()
        if not box:continue
        sx=w/image.width;sy=h/image.height
        box=[box[0]*sx,box[1]*sy,box[2]*sx,box[3]*sy]
        flip=(profile.get('side')=='enemy')!=row.get('flip',False)
        if flip:box=[w-box[2],box[1],w-box[0],box[3]]
        correction=profile['flipOriginOffset']if flip and f<profile['sourceOamCutoff']else[0,0]
        bounds.append([box[0]-profile['anchor'][0]+correction[0],box[1]-profile['anchor'][1]+correction[1],box[2]-profile['anchor'][0]+correction[0],box[3]-profile['anchor'][1]+correction[1]])
    if not bounds:return {'offset':[-72,-84],'size':[144,112]}
    union=[min(b[0]for b in bounds),min(b[1]for b in bounds),max(b[2]for b in bounds),max(b[3]for b in bounds)]
    width=max(144,math.ceil((union[2]-union[0]+24)/8)*8);height=max(112,math.ceil((union[3]-union[1]+24)/8)*8)
    return {'offset':[math.floor((union[0]+union[2]-width)/2),math.floor((union[1]+union[3]-height)/2)],'size':[width,height],'bodyBoundsUnion':union,'padding':12}

def title(key):
    spell=re.search(r'_item_(\d+)',key)
    name = ('进阶普通攻击' if key.endswith('_promoted') else '必杀攻击' if key.endswith('_critical')
            else SPELL_NAMES.get(int(spell.group(1)),'法术 '+spell.group(1))if spell
            else '雷剑' if '_levin' in key else '投枪'if'_javelin'in key
            else '圣弓攻击'if'_silver_bow'in key else '弓箭攻击' if '_bow' in key
            else '光束'if'_beam'in key else '眼光'if'_eye'in key else '普通攻击')
    if '_far_ally' in key: name += ' · 我方远距'
    elif '_far_enemy' in key: name += ' · 敌方远距'
    elif '_ally_' in key: name += ' · 近距'
    if '_vs_heavy' in key: name += ' · 重甲目标'
    return name

def pack_frame(row):
    return {k: row[k] for k in ['frame', 'offset', 'flip', 'effects', 'alpha', 'tint', 'shake'] if k in row}

def reactions(idle):
    def row(**extra):
        return {'frame': idle, 'offset': [0, 0], 'flip': False, 'effects': [], **extra}
    shakes = [3, 1, 2, 1, 3, 1, 2, 4, 2, 1, 0]
    return [
        ('idle', '战斗待机', [row() for _ in range(60)], '原待机姿势，展示 60 帧。'),
        ('miss', '未命中 · 待机反应', [row() for _ in range(round(.45 * FPS))], '沿用现行未命中反馈：待机停留约 0.45 秒。'),
        ('hit', '受击反馈', [row(shake=shakes[i] if i < len(shakes) else 0,
          tint=.35 if int(i / FPS * 30) % 2 == 0 else 1) for i in range(28)],
          '按 1 点扣血时长展示位移与闪烁；实际停留随伤害数值变化。未新增受击姿势。'),
        ('exit', '战败退场', [row(alpha=1 - (i // 8 + 1) / 4) for i in range(32)],
          '原待机姿势分四级淡出，每级 8 帧。')]

def safe_path(base, value):
    path = (base / value).resolve()
    path.relative_to(ROOT)
    return path

def apply_class_display_names(profiles, classes, overrides):
    """Use approved campaign labels while preserving source IDs and enemy forms."""
    source_classes={str(row['class_id']):row for row in classes['classes']}
    for profile in profiles:
        cid=str(profile['classId']);enemy=profile.get('side')=='enemy'
        name_key='enemy_name_zh' if enemy else 'name_zh'
        new_name=overrides.get(cid,{}).get(name_key)
        if not new_name:continue
        source=source_classes[cid]
        old_name=source['enemy_source_name'] if enemy else source['name']
        profile['actorName']=profile['actorName'].replace(old_name,new_name)
        profile['className']=new_name
        profile['reviewNote']=profile.get('reviewNote','').replace(old_name,new_name)
        profile['sourceClassName']=old_name
        profile['displayNameRevision']='profession-names-20261020'

def map_bundle(mapping_path, mapping, actors, class_names, enemy_names):
    profiles, actions = [], []
    actor_id = mapping.get('actor_id', str(mapping.get('character_id', mapping_path.parent.parent.name)))
    if 'class_id'not in mapping:raise ValueError('Map mapping requires explicit class_id: '+str(mapping_path))
    cid = str(mapping['class_id']);side=mapping.get('source_side','ally')
    names = {'story':'剧情地图','world':'大地图','tactical-walk':'战斗地图 · 行走','tactical-idle':'战斗地图 · 待机'}
    direction_names = {'down':'向下','up':'向上','right':'向右','left':'向左','side':'侧向'}
    for scenario in mapping['scenarios']:
        context = scenario['id']; pid = relative(mapping_path.parent).replace('/','-') + '-' + context
        source = safe_path(mapping_path.parent, scenario['source_atlas'])
        source_size = scenario['source_frame_size']; source_atlas_size = list(Image.open(source).size)
        if mapping.get('revision')=='sol' and context in ['tactical-walk','tactical-idle']:
            expected_count=8 if context=='tactical-walk' else 6
            if source_atlas_size!=[source_size[0]*expected_count,source_size[1]]:
                raise ValueError('Native map source atlas dimensions do not match: '+str(source))
        columns = source_atlas_size[0] // source_size[0]
        frames, errors = {}, {}
        for record in scenario['frame_mapping']:
            index = str(record['source_index'])
            try:
                asset=safe_path(mapping_path.parent,record.get('output_path',record['path']))
                with Image.open(asset) as image:
                    if list(image.size)!=scenario['output_frame_size']: raise ValueError('Unexpected frame size')
                frames[index]=relative(asset)
            except Exception as error: errors[index]=str(error)
        profiles.append({'id':pid,'actor':actor_id,'actorName':scenario.get('display_name',mapping.get('display_name',actors.get(actor_id,actor_id))),'classId':cid,
          'className':mapping.get('display_class_name',(enemy_names if side=='enemy'else class_names).get(cid,cid)),
          'context':context,'contextName':names.get(context,context),'side':side,'source_side':side,
          'mapping':relative(mapping_path),'mappingStatus':scenario.get('status',mapping.get('status','review_candidate')),'revision':scenario.get('revision',mapping.get('revision')),'modifiedBy':scenario.get('modified_by',mapping.get('modified_by')),'reviewNote':scenario.get('review_note',mapping.get('review_note','')),'mapGround':scenario.get('preview_ground'),'mapShadow':scenario.get('ground_shadow'),'motionReview':scenario.get('motion_review'),'sourceAtlas':relative(source),
          'sourceFrameSize':source_size,'sourceAtlasSize':source_atlas_size,'sourceColumns':columns,
          'sourceFrameCount':columns*(source_atlas_size[1]//source_size[1]),'anchor':scenario['source_anchor'],
          'sourceOamCutoff':0,'flipOriginOffset':[0,0],'outputFrameSize':scenario['output_frame_size'],
          'newFrames':frames,'frameErrors':errors,'sourceReviewPending': context=='tactical-walk' and scenario.get('source_audit',{}).get('status')!='verified_native_tactical','sourceReviewNote':'参考来源复核中：旧参考混用了场景动作表与图块银行，暂停作为战斗地图对照。','links':[{'label':'四倍重绘图集','href':relative(safe_path(mapping_path.parent,scenario['output_atlas']))}]})
        timing=scenario['timing'];fps=timing.get('native_fps',FPS)
        def append(key,name,rows,kind,note,video=True,reference_label=None):
            actions.append({'id':pid+'--'+key,'profile':pid,'key':key,'name':name,'context':context,
              'kind':kind,'fps':fps,'origin':[32,36],'contactTick':None,'frames':rows,'notes':note,
              'viewport':[0,0,64,48],'defaultVideo':video})
            if reference_label or scenario.get('reference_label'):
                actions[-1]['referenceLabel']=reference_label or scenario['reference_label']
            if scenario.get('action_note'): actions[-1]['notes']+=' '+scenario['action_note']
        if scenario.get('static_pose_preview',False):
            rows=[{'frame':0,'offset':[0,0],'flip':False,'effects':[]}for _ in range(60)]
            append('idle-pose','剧情地图 · 待机形象',rows,'map_idle','静止形象复用战斗待机首帧；本轮仅检查剧情形象。')
        elif scenario.get('static_facing',False) or context=='tactical-idle':
            order=timing['cycle_frames'];ticks=timing['frame_ticks'];rows=[]
            for _ in range(2):
                for f,n in zip(order,ticks): rows.extend({'frame':f,'offset':[0,0],'flip':False,'effects':[]}for _ in range(n))
            append('idle-cycle','战斗地图 · 原待机循环',rows,'map_idle','固定朝向，保留原待机 14／8／14／8 帧节奏。')
        else:
            n=int(timing.get('frame_ticks',16))
            for direction,order in scenario['directions'].items():
                flip=bool(scenario.get('direction_mirror_x',{}).get(direction,False));rows=[]
                ticks=scenario.get('direction_frame_ticks',{}).get(direction,[n]*len(order))
                if len(ticks)!=len(order) or any(not isinstance(t,int) or t<=0 for t in ticks):
                    raise ValueError('Invalid per-direction frame timing: '+pid+' '+direction)
                repeats=scenario.get('direction_cycle_repeats',{}).get(direction,3)
                if not isinstance(repeats,int) or repeats<=0:
                    raise ValueError('Invalid per-direction cycle count: '+pid+' '+direction)
                for _ in range(repeats):
                    for f,count in zip(order,ticks):rows.extend({'frame':f,'offset':[0,0],'flip':flip,'effects':[]}for _ in range(count))
                label=direction_names.get(direction,direction)
                reference_label=scenario.get('direction_reference_labels',{}).get(direction)
                note=scenario.get('direction_action_notes',{}).get(direction,'原地审查步态；每个腿姿势保持 16 帧，两姿势循环，共展示三个循环。')
                append('walk-'+direction,'行走 · '+label,rows,'map_walk',note,reference_label=reference_label)
                append('idle-'+direction,'静止 · '+label,[{'frame':order[0],'offset':[0,0],'flip':flip,'effects':[]}for _ in range(32)],'map_idle','停止行走时保持当前方向的第一个姿势。',False,reference_label=reference_label)
    return profiles, actions

def build():
    motion = read(ROOT / 'source-input/original-motion/full-original-motion.json')
    effects = read(ROOT / 'source-input/effects.json')
    corrected_path=ROOT/'source-input/corrected-ally-motion/overlay.json'
    corrected=read(corrected_path)if corrected_path.exists()else{}
    if corrected:
        if file_hash(ROOT/corrected['base_frozen_motion'])!=corrected['base_sha256']:
            raise ValueError('Corrected-reference overlay does not match the unchanged frozen source')
        motion['variants'].update(corrected['variants'])
        effects.update(corrected.get('sprites',{}))
    enemy_path=ROOT/'source-input/enemy-motion/full-enemy-motion.json'
    enemy_motion=read(enemy_path)if enemy_path.exists()else None
    if enemy_motion: effects.update(enemy_motion.get('sprites',{}))
    audit = read(ROOT / 'catalog/hunapu-action-catalog.json')
    classes = read(ROOT / 'catalog/class-catalog.json')
    actor_catalog = read(ROOT / 'catalog/actor-story-map-catalog.json')
    actors = {r['id']: r['name'] for r in actor_catalog['actors']}
    class_names = {str(r['class_id']): r['name'] for r in classes['classes']}
    enemy_names = {str(r['class_id']): r['enemy_source_name'] for r in classes['classes']}
    profiles, actions, issues = [], [], []
    for mapping_path in sorted(ROOT.glob('**/frame_mapping.json')):
        if 'source-input' in mapping_path.parts: continue
        mapping = read(mapping_path)
        if 'scenarios' in mapping:
            map_profiles,map_actions=map_bundle(mapping_path,mapping,actors,class_names,enemy_names)
            profiles.extend(map_profiles);actions.extend(map_actions);continue
        if 'original_class_id' not in mapping or 'frame_mapping' not in mapping: continue
        cid = str(mapping['original_class_id'])
        side=mapping.get('source_side','ally')
        selected_motion=enemy_motion if side=='enemy'else motion
        if not selected_motion or cid not in selected_motion['original_bodies']:
            issues.append({'path': relative(mapping_path), 'error': 'Unknown original_class_id'}); continue
        body = selected_motion['original_bodies'][cid]
        profile_id = relative(mapping_path.parent).replace('/', '-')
        actor_id = mapping.get('character_id', profile_id)
        source = ROOT/body['path']if side=='enemy'else ROOT / 'source-input/original-motion' / Path(body['path']).name
        source_size = body['frame_size']
        frames, frame_errors = {}, {}
        expected = mapping.get('output_frame_size', [v * 4 for v in source_size])
        for key, value in mapping['frame_mapping'].items():
            try:
                asset = safe_path(mapping_path.parent, value)
                if not asset.is_file(): raise ValueError('missing file')
                with Image.open(asset) as image:
                    if list(image.size) != expected: raise ValueError('incorrect frame dimensions: ' + str(image.size))
                frames[str(key)] = relative(asset)
            except Exception as error:
                frame_errors[str(key)] = str(error)
        art_aliases=corrected.get('art_aliases',{}).get(cid,{})if side=='ally'else{}
        for key,record in art_aliases.items():
            representative=str(record['mapped_art_frame'])
            if key not in frames and representative in frames:frames[key]=frames[representative]
        original_size = list(Image.open(source).size)
        revised_effects = {}
        for effect_key, asset_path in mapping.get('effect_overrides', {}).items():
            if effect_key not in effects: raise ValueError('Unknown revised effect: '+effect_key)
            asset = safe_path(mapping_path.parent, asset_path)
            if not asset.is_file(): raise ValueError('Missing revised effect: '+str(asset))
            revised_effects[effect_key] = {**effects[effect_key], 'path':relative(asset)}
        profile = {'id': profile_id, 'actor': actor_id, 'actorName': mapping.get('display_name',actors.get(actor_id,actor_id)),
          'classId': cid, 'className': mapping.get('display_class_name',(enemy_names if side=='enemy'else class_names).get(cid,cid)), 'context': 'battle', 'contextName': '战斗场景', 'side':side,
          'mapping': relative(mapping_path), 'mappingStatus': mapping.get('status', 'unknown'), 'revision':mapping.get('revision'), 'modifiedBy':mapping.get('modified_by'), 'reviewNote':mapping.get('review_note',''),
          'sourceAtlas': relative(source), 'sourceFrameSize': source_size, 'sourceAtlasSize': original_size,
          'sourceColumns': body.get('columns', 16), 'sourceFrameCount': body['frames'],
          'anchor': body['anchor'], 'sourceOamCutoff': body['source_oam_frame_count'],
          'flipOriginOffset': [16, 0], 'outputFrameSize': expected, 'newFrames': frames,
          'frameErrors': frame_errors, 'referenceArtAliases':art_aliases, 'links': []}
        if revised_effects: profile['revisedEffects'] = revised_effects
        review_timeline = read(safe_path(mapping_path.parent,mapping['review_timeline'])) if mapping.get('review_timeline') else {}
        for effect_key,meta in review_timeline.get('effects',{}).items():
            if effect_key in effects:raise ValueError('Review effect ID collision: '+effect_key)
            asset=safe_path(mapping_path.parent,meta['path'])
            if not asset.is_file():raise ValueError('Missing review effect: '+str(asset))
            effects[effect_key]={**meta,'path':relative(asset)}
        for batch in mapping.get('batches', []):
            if batch.get('review'):
                f = safe_path(mapping_path.parent, batch['review'])
                if f.exists(): profile['links'].append({'label': batch['id'] + ' 姿势对照', 'href': relative(f)})
        profiles.append(profile)
        if actor_id == 'hunapu': keys = [r['key'] for r in audit['compiled_attack_variants']]
        else: keys = mapping.get('variant_keys', [k for k,v in selected_motion['variants'].items() if str(v['source_class_id']) == cid])
        for key in keys:
            if key not in selected_motion['variants']:
                issues.append({'profile': profile_id, 'variant': key, 'error': 'Missing frozen timeline'}); continue
            variant = selected_motion['variants'][key]
            action = {'id': profile_id + '--' + key, 'profile': profile_id, 'key': key, 'name': title(key),
              'context': 'battle', 'kind': 'attack', 'fps': variant.get('native_fps', FPS),
              'origin': variant['actor_origin'], 'contactTick': variant.get('contact_tick'),
              'frames': [pack_frame(row) for row in variant['frames']], 'notes': '原时序、位移和外置效果同步保留。',
              'defaultVideo': variant.get('formation') == 'near' and not key.endswith('_vs_heavy')}
            if side=='ally'and key in corrected.get('variants',{}):
                action['referenceLabel']=corrected['label']
                action['notes']='原作校正参考：弓箭从原生持弓姿势开始，去除旧提取中的9像素残留剑片。动作时序、位移和外置效果不变。新满弓图复用已完成稿。'
                action['referenceEvidence']='source-input/corrected-ally-motion/selector-audit.json'
            if key in review_timeline.get('actions',{}):
                revision=review_timeline['actions'][key]
                base_hash=hashlib.sha256(json.dumps(action['frames'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
                if revision['source_frames_sha256']!=base_hash:raise ValueError('Review timeline source changed: '+key)
                if len(revision['frames'])!=len(action['frames']):raise ValueError('Review timeline length mismatch: '+key)
                action['revisedFrames']=revision['frames']
                action['notes']=revision['note']
            actions.append(action)
        reaction_idle=int(mapping.get('source_idle_frame',body['sequences']['idle'][0]))
        reaction_origin=next((selected_motion['variants'][key]['actor_origin']for key in keys
          if key in selected_motion['variants']and selected_motion['variants'][key].get('formation')=='near'),[64 if side=='enemy'else 176,128])
        for key,name,rows,note in reactions(reaction_idle):
            actions.append({'id': profile_id + '--reaction-' + key, 'profile': profile_id, 'key': key,
              'name': name, 'context': 'battle', 'kind': 'reaction', 'fps': FPS, 'origin': reaction_origin,
              'contactTick': None, 'frames': rows, 'notes': note, 'defaultVideo': True})
    # Optional context bundles make additional map/class catalogs independent of this builder.
    for bundle_path in sorted(ROOT.glob('**/gallery_bundle.json')):
        bundle = read(bundle_path)
        for profile in bundle.get('profiles', []):
            profile = dict(profile)
            profile.setdefault('contextName', '地图')
            profile.setdefault('sourceOamCutoff', 0); profile.setdefault('flipOriginOffset', [0,0])
            profile.setdefault('links', []); profile.setdefault('mappingStatus', 'review_candidate')
            profiles.append(profile)
        actions.extend(bundle.get('actions', []))
    # Same complete confirmed display labels as docs2 / the running game. Frozen
    # source catalogs and art mappings retain their original provenance names.
    display_names=read(ROOT.parents[1]/'actual/data/class_names.json')
    apply_class_display_names(profiles,classes,display_names)
    profile_lookup = {p['id']:p for p in profiles}
    effect_bounds = {}
    for action in actions:
        profile = profile_lookup[action['profile']]
        if profile.get('displayNameRevision'):
            action['notes']=action['notes'].replace(profile['sourceClassName'],profile['className'])
        source_needed = sorted(set(row['frame'] for row in action['frames']))
        render_rows=action['frames']+action.get('revisedFrames',[])
        needed = sorted(set(row['frame'] for row in render_rows))
        missing = [i for i in needed if str(i) not in profile['newFrames']]
        effect_ids = sorted(set(effect['sprite'] for row in render_rows for effect in row.get('effects', [])))
        missing_effects = [key for key in effect_ids if key not in effects or not (ROOT / effects[key]['path']).is_file()]
        action.update(neededFrames=needed, missingFrames=missing, effectIds=effect_ids, missingEffects=missing_effects,
          ready=not missing and not missing_effects and not profile.get('sourceReviewPending'), sourceReviewPending=bool(profile.get('sourceReviewPending')), duration=len(action['frames']) / action['fps'])
        if action['sourceReviewPending']:action['notes']=profile['sourceReviewNote']
        if profile.get('revision'):
            action['revision']=profile['revision']
            action['modifiedBy']=profile.get('modifiedBy')
            action['notes']+=' 本次修改记录：'+profile['revision']+'。 '+('修改人：'+profile['modifiedBy']+'。 'if profile.get('modifiedBy')else'')+profile.get('reviewNote','')
        if action['context']=='battle':action['closeCamera']=close_camera(profile,action)
        if action['context']=='battle' and effect_ids:
            # Include complete frozen effect textures, even when their top lies beyond the native field.
            minimum_y=-32
            for row in render_rows:
                for effect in row.get('effects',[]):
                    meta=effects[effect['sprite']]
                    minimum_y=min(minimum_y,effect['position'][1]-meta['anchor'][1]+(meta.get('flip_origin_offset',[0,0])[1]if effect.get('flip')else 0))
            if minimum_y < -32:action['viewport']=[-16,minimum_y-16,288,144-(minimum_y-16)]
            # Some wide spells continue beyond either side of the native field.
            # Keep earlier framing when sufficient; expand only for real visible pixels.
            view=action.get('viewport',[-16,-32,288,176])
            left,top,right,bottom=view[0],view[1],view[0]+view[2],view[1]+view[3]
            for row in render_rows:
                for effect in row.get('effects',[]):
                    key=effect['sprite'];meta=effects[key]
                    if key not in effect_bounds:
                        with Image.open(ROOT/meta['path']) as im:
                            box=im.convert('RGBA').getbbox()
                            effect_bounds[key]=None if not box else [box[0]*meta['frame_size'][0]/im.width,box[1]*meta['frame_size'][1]/im.height,box[2]*meta['frame_size'][0]/im.width,box[3]*meta['frame_size'][1]/im.height]
                    box=effect_bounds[key]
                    if box is None:continue
                    box=list(box);at=[effect['position'][i]-meta['anchor'][i]for i in range(2)]
                    if effect.get('flip'):
                        box=[meta['frame_size'][0]-box[2],box[1],meta['frame_size'][0]-box[0],box[3]]
                        at=[at[i]+meta.get('flip_origin_offset',[0,0])[i]for i in range(2)]
                    x0,y0,x1,y1=box[0]+at[0],box[1]+at[1],box[2]+at[0],box[3]+at[1]
                    if x0<left:left=math.floor(x0-8)
                    if y0<top:top=math.floor(y0-8)
                    if x1>right:right=math.ceil(x1+8)
                    if y1>bottom:bottom=math.ceil(y1+8)
            expanded=[left,top,right-left,bottom-top]
            if expanded!=view:action['viewport']=expanded
        resources=[profile['sourceAtlas']]+[profile['newFrames'][str(f)]for f in needed if str(f)in profile['newFrames']]+[effects[k]['path']for k in effect_ids if k in effects]
        resources += [profile['revisedEffects'][k]['path']for k in effect_ids if k in profile.get('revisedEffects',{})]
        if profile.get('mapGround'): resources.append(profile['mapGround'])
        if profile.get('mapShadow'): resources.append(profile['mapShadow']['path'])
        resource_hashes={path:file_hash(ROOT/path)for path in sorted(set(resources))if(ROOT/path).exists()}
        signature={'frames':action['frames'],'origin':action['origin'],'viewport':action.get('viewport',[-16,-32,288,176]),'closeCamera':action.get('closeCamera'),'anchor':profile['anchor'],'side':profile.get('side','ally'),'resources':resource_hashes,'render_version':3}
        if action.get('revisedFrames'):signature['revised_frames']=action['revisedFrames']
        if profile.get('revisedEffects'):
            signature['revised_effects']={k:profile['revisedEffects'][k]for k in effect_ids if k in profile['revisedEffects']}
        if profile.get('mapGround'): signature['map_ground_revision']=1
        if profile.get('mapShadow'): signature['map_shadow']=profile['mapShadow']
        if profile.get('revision')=='sol':
            signature['sol_render_version']=1
            signature['labels']=[profile['actorName'],action['name'],action.get('referenceLabel','原作')]
        elif profile.get('revision') in ['archer-spearman-map-20261018','archer-bow-v2-20261018','archer-arms-step-v3-20261018','archer-down-hand-v4-20261018']:
            signature['centered_labels_version']=1
            signature['labels']=[profile['actorName'],action['name'],action.get('referenceLabel','原作')]
        if profile.get('displayNameRevision'):
            signature['display_name_revision']=profile['displayNameRevision']
            signature['labels']=[profile['actorName'],action['name'],action.get('referenceLabel','原作')]
        action['contentDigest']=hashlib.sha256(json.dumps(signature,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        video = ROOT / 'demos/videos' / (action['id'] + '.mp4')
        action['video'] = relative(video) if matched_export(video,action['contentDigest']) and action['ready'] else None
        close_video = ROOT / 'demos/videos' / (action['id'] + '--close.mp4')
        action['closeVideo'] = relative(close_video) if matched_export(close_video,action['contentDigest']) and action['ready'] else None
        screenshot = ROOT / 'demos/stills' / (action['id'] + '.png')
        action['still'] = relative(screenshot) if matched_export(screenshot,action['contentDigest']) and action['ready'] else None
        for i in source_needed:
            if not 0 <= i < profile['sourceFrameCount']: issues.append({'action':action['id'],'error':'Source frame out of range','frame':i})
        if action['contactTick'] is not None and not 0 <= action['contactTick'] < len(action['frames']):
            issues.append({'action':action['id'],'error':'Invalid contact tick'})
    result = {'schema':1, 'builtAt':datetime.now(timezone.utc).isoformat(), 'title':'角色重绘 · 全动作对照',
      'sourceRevision':motion['source_revision'], 'profiles':profiles, 'actions':actions, 'effects':effects,
      'viewport':[-16,-32,288,176], 'summary':{'profiles':len(profiles),'actions':len(actions),
        'ready':sum(a['ready'] for a in actions),'pending':sum(not a['ready'] for a in actions)},
      'validation':{'structuralIssues':issues,'browserVisualInspection':'not performed; file URL access was denied by the environment, and no alternate server/browser was attempted'},
      'referenceCorrections':{'label':corrected.get('label'),'note':corrected.get('reference_note'),'keys':list(corrected.get('variants',{}))},
      'policy':'素材齐备表示能完整播放；男主、弓箭手和本轮已验收枪兵地图均已接入测试包；其余未验收素材保持审核状态。缺图不回退为旧美术。'}
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n')
    demos=ROOT/'demos';demos.mkdir(exist_ok=True)
    (demos/'gallery-data.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    (demos/'build-report.json').write_text(json.dumps({'builtAt':result['builtAt'],'summary':result['summary'],
      'validation':result['validation'],'actions':[{k:a[k] for k in ['id','name','ready','missingFrames','missingEffects','duration']} for a in actions]},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['summary'],ensure_ascii=False))
    if issues: print(json.dumps(issues,ensure_ascii=False))
    return result

if __name__ == '__main__':
    build()
