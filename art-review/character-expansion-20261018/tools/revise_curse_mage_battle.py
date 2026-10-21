#!/usr/bin/env python3
"""Review-only caster recolor and spell choreography over frozen source timelines."""
from pathlib import Path
import copy, hashlib, json, math
from PIL import Image
from revise_curse_mage_idle import ROOT, PALETTE

REVISION = 'curse-mage-battle-v1-20261020'
OUT = ROOT / REVISION
FIRE = ['48fd24a19e14be', 'd628db09f2c7df', '947873207996af']
GROUND = {'411b4233ccc6b2', '9a12ea678bb2cc', 'c17516c5e4ad1c'}
BLUE_FIRE = [(40,48,86), (75,94,146), (167,182,211)]
SCALES = [.5, .65, .8, .95, 1.1, 1.2]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',',':')).encode()).hexdigest()


def load(path):
    return Image.open(path).convert('RGBA')


def visible_center(effect, effects):
    meta=effects[effect['sprite']];image=load(ROOT/meta['path']);box=image.getbbox()
    center=[(box[0]+box[2])/2*meta['frame_size'][0]/image.width,
            (box[1]+box[3])/2*meta['frame_size'][1]/image.height]
    if effect.get('flip'):center[0]=meta['frame_size'][0]-center[0]
    delta=meta.get('flip_origin_offset',[0,0]) if effect.get('flip') else [0,0]
    return [effect['position'][i]-meta['anchor'][i]+center[i]+delta[i]for i in range(2)]


def muted_robe(im):
    colors = [tuple(bytes.fromhex(PALETTE[k])) for k in ['outline','robe_shadow','robe_mid','robe_light']]
    result = im.copy()
    result.putdata([(*colors[0 if (l:=.2126*r+.7152*g+.0722*b)<30 else 1 if l<75 else 2 if l<145 else 3],a)
                    if a else (0,0,0,0) for r,g,b,a in im.getdata()])
    return result


def fire_color(im, side):
    if side=='ally':return im.copy()
    result=im.copy()
    result.putdata([(*BLUE_FIRE[0 if (l:=.2126*r+.7152*g+.0722*b)<125 else 1 if l<230 else 2],a)
                    if a else (0,0,0,0) for r,g,b,a in im.getdata()])
    return result


def save(path, im, inventory, purpose):
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),
                      'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'visible_bounds':list(im.getbbox()) if im.getbbox() else None})


def staff_pose(body, side, angle):
    # Reuse the existing cleric's cap and clean shaft texture, without the hand
    # or clothing pixels in its occluded grip region.
    source=load(ROOT/'professions/class-18-ally/battle/frames/frame-007.png')
    cap=source.crop((148,148,160,162));shaft=source.crop((150,162,156,178))
    staff=Image.new('RGBA',(16,112));staff.alpha_composite(cap,(2,0))
    for y in range(12,112,16):staff.alpha_composite(shaft,(5,y))
    if side=='enemy':staff=muted_robe(staff)
    grip=(90,84) if side=='enemy' else (158,122)
    layer=Image.new('RGBA',body.size);layer.alpha_composite(staff,(grip[0]-8,grip[1]-72))
    layer=layer.rotate(angle,resample=Image.Resampling.NEAREST,center=grip)
    # The original fingers and sleeve cover the shaft at the grip.
    layer.alpha_composite(body)
    return layer


def create():
    OUT.mkdir(exist_ok=True)
    data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'actions':{a['id']:{k:a.get(k)for k in ['frames','origin','fps','contactTick','viewport','closeCamera']}for a in data['actions']},
          'mappings':{side:json.loads((ROOT/f'professions/class-15-{side}/battle/frame_mapping.json').read_text())for side in ['enemy','ally']}},ensure_ascii=False,indent=2)+'\n')
    inventory=[];contracts=[]
    for side in ['enemy','ally']:
        profile=next(p for p in data['profiles']if p['id']==f'professions-class-15-{side}-battle')
        timeline={'revision':REVISION,'runtime_integrated':False,'effects':{},'actions':{}}
        effects=timeline['effects'];body_paths={}
        for f in ([0,4,5]if side=='enemy'else[0,1,2]):
            old=load(ROOT/f'professions/class-15-{side}/battle/frames/frame-{f:03}.png')
            image=muted_robe(old) if side=='enemy'else old
            if side=='enemy':
                path=OUT/f'{side}/body/frame-{f:03}.png';save(path,image,inventory,'enemy body / shared walking robe palette');body_paths[str(f)]=path.relative_to(ROOT).as_posix()
        raised=load(OUT/'enemy/body/frame-004.png') if side=='enemy'else load(ROOT/'professions/class-15-ally/battle/frames/frame-001.png')
        for f,angle in [(100,-34),(101,-17),(102,0)]:
            path=OUT/f'{side}/body/frame-{f:03}.png';save(path,staff_pose(raised,side,angle),inventory,'lightning / existing staff lifted in three angles');body_paths[str(f)]=path.relative_to(ROOT).as_posix()
        fire_ids={};flight_ids={};ground_ids={};rise_ids={}
        def add(key,image,frame_size,anchor,purpose,flip_offset=None):
            path=OUT/f'{side}/effects/{key}.png';save(path,image,inventory,purpose)
            eid=f'review-c15-{side}-{key}'
            effects[eid]={'path':'../../../'+path.relative_to(ROOT).as_posix(),'frame_size':frame_size,'frames':1,'anchor':anchor,'flip_origin_offset':flip_offset or [0,0]}
            return eid
        for phase,key in enumerate(FIRE):
            source=fire_color(load(ROOT/f'source-input/effects/{key}.png'),side)
            flame=source.crop(source.getbbox())
            for size,scale in enumerate(SCALES):
                cell=Image.new('RGBA',(48,48));part=flame.resize((max(1,round(flame.width*scale)),max(1,round(flame.height*scale))),Image.Resampling.NEAREST)
                cell.alpha_composite(part,(24-part.width//2,24-part.height//2))
                fire_ids[phase,size]=add(f'fire-grow-{phase}-{size}',cell.resize((192,192),Image.Resampling.NEAREST),[48,48],[24,24],'fireball / overhead growth and hold')
            for mode,target,angle,scale in [('ground',ground_ids,-90,.7),('rise',rise_ids,-45,.9)]:
                part=flame.rotate(angle,resample=Image.Resampling.NEAREST,expand=True)
                part=part.resize((round(part.width*scale),round(part.height*scale)),Image.Resampling.NEAREST)
                cell=Image.new('RGBA',(48,48));cell.alpha_composite(part,(24-part.width//2,24-part.height//2))
                target[phase]=add(f'ragnarok-{mode}-{phase}',cell.resize((192,192),Image.Resampling.NEAREST),[48,48],[24,24],f'ragnarok / {mode} flame')
        # Enemy fire and the later Ragnarok burst share a compact dark-blue
        # three-color ramp. Other spells and the source panel keep their art.
        used=set()
        for a in data['actions']:
            if a['profile']==profile['id'] and ('_item_23' in a['key'] or '_item_25' in a['key']):
                used.update(k for k in a['effectIds'] if not k.startswith('review-'))
        recolored={}
        if side=='enemy':
            for key in sorted(used):
                meta=data['effects'][key];eid=add('blue-'+key.removeprefix('native-'),fire_color(load(ROOT/meta['path']),side),meta['frame_size'],meta['anchor'],'enemy fire / original silhouette, dark blue ramp',meta.get('flip_origin_offset'))
                recolored[key]=eid
        for a in data['actions']:
            if a['profile']!=profile['id']:continue
            match=next((item for item in [23,24,25]if a['key'].split('_item_')[-1].split('_')[0]==str(item)),None) if '_item_'in a['key'] else None
            if match is None:continue
            rows=copy.deepcopy(a['frames']);events={}
            if match==23:
                start=next(i for i,row in enumerate(rows)if row.get('effects'))
                release=next(i for i,row in enumerate(rows)if i>start and row['frame']!=rows[start]['frame'])
                new_release=release+8;contact=a['contactTick']
                flight_end=max(i for i,row in enumerate(a['frames'][:contact+1]) if row.get('effects'))
                end_effect=next(e for row in reversed(rows[:contact+1])for e in row.get('effects',[]))
                direction=1 if end_effect['position'][0]>a['origin'][0]else -1
                overhead=[a['origin'][0],a['origin'][1]-51]
                for tick in range(start,new_release):
                    phase=((tick-start)//4)%3;size=min(5,(tick-start)//4)
                    rows[tick]['frame']=rows[start]['frame'];rows[tick]['effects']=[{'sprite':fire_ids[phase,size],'position':overhead,'flip':direction<0}]
                for tick in range(new_release,flight_end+1):
                    u=(tick-new_release)/max(1,flight_end-new_release)
                    old_index=min(flight_end,release+round(u*(flight_end-release)))
                    rows[tick]=copy.deepcopy(a['frames'][old_index])
                    if rows[tick].get('effects'):
                        e=rows[tick]['effects'][0];p=visible_center(e,data['effects'])
                        e['position']=[round(overhead[j]*(1-u)+p[j]*u)for j in range(2)]
                        e['sprite']=fire_ids[(tick//4)%3,5 if u<.4 else 4 if u<.7 else 3]
                events={'overhead_start':start,'original_release':release,'revised_release':new_release,'head_hold_added_ticks':8,'growth_scales':SCALES,'head_center':overhead,'last_visible_flight_tick':flight_end,'contact_tick_kept':contact}
                note='火球在头顶逐级蓄大并延长停留8帧，再释放；最后飞行段相应收紧，原总帧数、命中帧与单次结算保持。'
            elif match==24:
                start=next(i for i,row in enumerate(rows)if row.get('effects'))
                release=next(i for i,row in enumerate(rows)if i>start and row['frame']!=rows[start]['frame'])
                for tick in range(start,release):
                    rows[tick]['effects']=[];rows[tick]['frame']=100+min(2,(tick-start)//6)
                events={'staff_start':start,'staff_raise_steps':[100,101,102],'target_lightning_unchanged_from_tick':release,'contact_tick_kept':a['contactTick']}
                note='雷电起手去除施法者头顶电光，原抬手改为握杖、抬杖、举定三步；后续目标落雷与全部结算保持。'
            else:
                ground_ticks=[i for i,row in enumerate(rows)if any(e['sprite'].removeprefix('native-')in GROUND for e in row.get('effects',[]))]
                start=min(ground_ticks);ground_positions=[e['position'][0]for i in ground_ticks for e in rows[i]['effects']if e['sprite'].removeprefix('native-')in GROUND]
                direction=1 if sum(ground_positions)/len(ground_positions)>a['origin'][0]else -1
                end=start+82
                for tick in range(start,end):
                    revised=[]
                    for projectile in range(5):
                        age=tick-start-projectile*8
                        if not 0<=age<50:continue
                        phase=(age//3)%3
                        if age<22:
                            x=a['origin'][0]+direction*(16+age*80/21);y=123;sprite=ground_ids[phase]
                        else:
                            u=(age-22)/27;x=a['origin'][0]+direction*(96+u*58);y=123-u*76;sprite=rise_ids[phase]
                        revised.append({'sprite':sprite,'position':[round(x),round(y)],'flip':direction<0})
                    rows[tick]['effects']=revised
                events={'trajectory_start':start,'trajectory_end_exclusive':end,'projectiles':5,'stagger_ticks':8,'ground_ticks_each':22,'diagonal_ticks_each':28,'modified_motion_fraction':round(82/len(rows),4),'contact_tick_kept':a['contactTick']}
                note='诸神黄昏保留起手与后段爆发；约20%时段改为五枚火焰先贴地，再按8帧间隔逐枚斜上飞出。五枚仅为同次法术的视觉阶段，不新增命中或伤害。'
            if side=='enemy':
                for row in rows:
                    for e in row.get('effects',[]):e['sprite']=recolored.get(e['sprite'],e['sprite'])
            note+=('敌军火焰以暗蓝色为主。'if side=='enemy'and match!=24 else '友军火焰保持红色。'if match!=24 else '')
            timeline['actions'][a['key']]={'source_frames_sha256':digest(a['frames']),'frames':rows,'note':note,'events':events}
            contracts.append({'actor':profile['actor'],'side':side,'spell_id':match,'spell_name':{23:'火球',24:'雷电',25:'诸神黄昏'}[match],
                              'action':a['id'],'contact_tick':a['contactTick'],'total_ticks':len(rows),'events':events,'additional_hits':0})
        (OUT/f'{side}-motion.json').write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':'))+'\n')
        (OUT/f'{side}-body-paths.json').write_text(json.dumps(body_paths,ensure_ascii=False,indent=2)+'\n')
    for side in ['enemy','ally']:
        atlas=OUT/side/'body-atlas.png'
        if atlas.exists():save(atlas,load(atlas),inventory,'review body atlas / canonical and three staff poses')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'robe_palette':PALETTE,'enemy_fire_palette':BLUE_FIRE,'assets':inventory},ensure_ascii=False,indent=2)+'\n')
    (OUT/'spell-action-contract.json').write_text(json.dumps({'source':'actual/data/legacy/rules_full.json IDs23,24,25; docs2/完整游戏设定.md',
      'gameplay_modified':False,'contracts':contracts},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'assets':len(inventory),'spell_variants':len(contracts),'revision':REVISION},ensure_ascii=False))


if __name__=='__main__':create()
