#!/usr/bin/env python3
"""Review-only cavalry battle palettes and profile-local flying lance overrides."""
import colorsys
import json
import statistics
from PIL import Image
from revise_cavalry_map import ROOT, digest, signature
from revise_enemy_cavalry_map import PALETTE, recolor

REVISION = 'cavalry-battle-lance-colors-v1-20261021'
OUT = ROOT/REVISION
MAPPINGS = {side:ROOT/f'professions/class-1-{side}/battle/frame_mapping.json' for side in ['ally','enemy']}
EFFECTS = {'ally':'5660a52a5bb041','enemy':'native-d48324673775fc'}
FACE = {0:(175,121,195,137),1:(161,124,183,140),2:(157,124,179,140),3:(159,124,181,140),
        4:(182,124,201,140),5:(168,124,184,140),6:(141,118,165,133),7:(133,118,155,133),
        9:(111,121,131,137),16:(111,121,131,137),17:(105,124,123,139),19:(110,124,131,139)}


def create():
    OUT.mkdir(exist_ok=True);baseline=OUT/'baseline.json'
    if not baseline.exists():
        data=json.loads((ROOT/'demos/gallery-data.json').read_text());maps={side:json.loads(p.read_text()) for side,p in MAPPINGS.items()}
        sources={}
        for side,m in maps.items():
            for p in m['frame_mapping'].values():
                path=(MAPPINGS[side].parent/p).resolve();sources[path.relative_to(ROOT).as_posix()]=digest(path)
            ep=ROOT/data['effects'][EFFECTS[side]]['path'];sources[ep.relative_to(ROOT).as_posix()]=digest(ep)
        baseline.write_text(json.dumps({'mappings':maps,'effects':{side:data['effects'][key] for side,key in EFFECTS.items()},
            'sources':sources,'digests':{a['id']:a['contentDigest'] for a in data['actions']},
            'timelines':{a['id']:signature(a) for a in data['actions']},
            'map_mappings':{side:digest(ROOT/f'professions/class-1-{side}/maps/frame_mapping.json') for side in maps},
            'rules_sha256':digest(ROOT.parents[1]/'actual/data/legacy/rules_full.json')},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());mappings=before['mappings'];assets=[]
    def save(image,name,purpose):
        p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);image.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),'bytes':p.stat().st_size,
            'sha256':digest(p),'visible_colors':len({p[:3] for p in image.getdata() if p[3]})})
        return '../../../'+p.relative_to(ROOT).as_posix()
    # Sample the actual allied held weapon above the rider's head.
    held=Image.open((MAPPINGS['ally'].parent/mappings['ally']['frame_mapping']['17']).resolve()).convert('RGBA')
    samples={'wood':[],'metal':[]}
    for y in range(92,110):
        for x in range(held.width):
            r,g,b,a=held.getpixel((x,y));h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            if a<201:continue
            if .055<h<.18 and .20<s<.85 and v>.25:samples['wood'].append((r,g,b))
            elif s<.22 and v>.4:samples['metal'].append((r,g,b))
    sampled={k:tuple(int(statistics.median(p[i] for p in ps)) for i in range(3)) for k,ps in samples.items()}
    wood_highlight=tuple(sorted(p[i] for p in samples['wood'])[int(.75*(len(samples['wood'])-1))] for i in range(3))
    lance_palettes={'ally':{'shaft':wood_highlight,'head':sampled['metal'],'tip':(225,228,223),'collar':(123,128,135),'butt':(159,115,60)},
                    'enemy':{'shaft':(66,91,131),'head':(158,173,194),'tip':(214,220,228),'collar':(69,64,100),'butt':(139,125,169)}}
    for side in ['ally','enemy']:
        old=Image.open(ROOT/before['effects'][side]['path']).convert('RGBA');new=old.copy();p=lance_palettes[side]
        for y in range(old.height):
            for x in range(old.width):
                rgba=old.getpixel((x,y))
                if not rgba[3]:continue
                role='shaft' if 40<=x<=60 else 'butt' if x>=61 else 'collar' if x==36 and y==13 else 'tip' if x<=28 else 'head'
                new.putpixel((x,y),(*p[role],rgba[3]))
        path=save(new,f'{side}/flying-lance.png',side+' cavalry flying lance / color replacement only')
        m=mappings[side];m.setdefault('effect_overrides',{})[EFFECTS[side]]=path
        m.update(revision=REVISION,status='review_candidate',runtime_integrated=False,
            review_note='友方飞行投枪恢复手持武器的木色枪杆与金属枪头；敌方人物、战马和投枪统一蓝紫色。原动作、轨迹与命中时序保持，仅更新对照页。')
    # Enemy battle poses keep every original pixel position and alpha value.
    enemy=mappings['enemy'];records=[];order=enemy['output_atlas_frame_order'];atlas=Image.new('RGBA',(320*len(order),256))
    for key,path in list(enemy['frame_mapping'].items()):
        f=int(key);source=(MAPPINGS['enemy'].parent/path).resolve();old=Image.open(source).convert('RGBA');new=old.copy();box=FACE[f]
        for y in range(old.height):
            for x in range(old.width):
                r,g,b,a=old.getpixel((x,y))
                if a:new.putpixel((x,y),(*recolor((r,g,b),box[0]<=x<box[2] and box[1]<=y<box[3]),a))
        target=save(new,f'enemy/body/frame-{f:03}.png','enemy cavalry battle body / accepted map blue-violet palette; original alpha and geometry')
        enemy['frame_mapping'][key]=target
        records.append({'frame':f,'source':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'path':target,
            'face_mask':list(box),'size':list(new.size),'bytes':assets[-1]['bytes'],'sha256':assets[-1]['sha256']})
        if f in order:atlas.alpha_composite(new,(order.index(f)*320,0))
    enemy['output_atlas']=save(atlas,'enemy/body-atlas.png','offline multi-pose review atlas; not a single runtime character image')
    enemy.update(body_review_records=records,palette=PALETTE,art_mode='existing battle art; exact-geometry sixteen-color blue-violet recolor; profile-local lance override')
    enemy['previous_batches']=enemy.get('batches',[])
    enemy['batches']=[{'id':'本轮敌方战斗配色','frames':order,'status':'pending_user_visual_acceptance',
        'review':'../../../'+REVISION+'/enemy-poses-dark.png'}]
    for side,m in mappings.items():MAPPINGS[side].write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    data=json.loads((ROOT/'demos/gallery-data.json').read_text());rules=json.loads((ROOT.parents[1]/'actual/data/legacy/rules_full.json').read_text())
    contracts=[]
    for a in data['actions']:
        if a['profile'] in ['professions-class-1-ally-battle','professions-class-1-enemy-battle'] and 'javelin' in a['key']:
            first=next(i for i,f in enumerate(a['frames']) if f['effects'])
            contracts.append({'actor_id':'ally-cavalry' if '-ally-' in a['profile'] else 'enemy-cavalry','class_id':1,
                'existing_card_item_ids':[4,7],'action':a['key'],'effect':'one original flying lance; palette only',
                'release_tick_zero_based':first,'contact_tick_zero_based':a['contactTick'],'total_frames':len(a['frames']),
                'timing_and_gameplay_changed':False})
    (OUT/'action-contract.json').write_text(json.dumps({'rules_source':'actual/data/legacy/rules_full.json',
        'existing_items':[i for i in rules['items'] if i['id'] in [4,7]],'actions':contracts,
        'note':'Uses existing action paths only. No new hits, damage, weapon ability or unlocked effect.'},ensure_ascii=False,indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
        'enemy_palette':PALETTE,'lance_palettes':lance_palettes,'ally_held_weapon_color_source':{'frame':17,'box':[0,92,320,110],
        'samples':{k:len(v) for k,v in samples.items()},'median_rgb':sampled,'shaft_visible_highlight_rgb':wood_highlight},'assets':assets},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'enemy_body_frames':len(records),'local_lance_overrides':2},ensure_ascii=False))


if __name__=='__main__':create()
