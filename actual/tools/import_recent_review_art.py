#!/usr/bin/env python3
"""Import the confirmed October 20–21 gallery snapshot, preserving other art."""
import copy, hashlib, json, shutil
from pathlib import Path
from PIL import Image

GAME=Path(__file__).resolve().parents[1]
REVIEW=GAME.parent/'art-review/character-expansion-20261018'
OUT=GAME/'assets/reviewed-animation-20261018'
REPORT=GAME/'reports/recent-art-20261021'
REV='confirmed-art-20261021'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
resource=lambda p:'res://'+p.relative_to(GAME).as_posix()

def visible_hash(im):
    im=im.convert('RGBA');im.putdata([p if p[3] else (0,0,0,0) for p in im.getdata()])
    return hashlib.sha256(im.tobytes()).hexdigest()

def main():
    REPORT.mkdir(parents=True,exist_ok=True);backup=REPORT/'before';backup.mkdir(exist_ok=True)
    runtime=GAME/'data/reviewed_animations.json'
    if not (backup/runtime.name).exists():shutil.copy2(runtime,backup/runtime.name)
    before=read(runtime);data=copy.deepcopy(before);g=read(REVIEW/'demos/gallery-data.json')
    ally=read(REVIEW/'source-input/original-motion/full-original-motion.json')
    ally['variants'].update(read(REVIEW/'source-input/corrected-ally-motion/overlay.json')['variants'])
    enemy=read(REVIEW/'source-input/enemy-motion/full-enemy-motion.json')
    selected=[p for p in g['profiles'] if any(d in (p.get('revision') or '') for d in ['20261020','20261021'])]
    assert len(selected)==22
    inventory=[];effect_inventory={};changed_variants=[];changed_maps=[];changed_battle=[]
    def effect(eid,meta,scope=None):
        key=(scope+'-'+eid) if scope else eid
        if key in effect_inventory:return key
        src=REVIEW/meta['path'];dst=OUT/'effects'/(key+'.png');dst.parent.mkdir(exist_ok=True)
        if dst.exists() and not (backup/dst.name).exists():shutil.copy2(dst,backup/dst.name)
        shutil.copy2(src,dst);im=Image.open(dst).convert('RGBA')
        density=im.width/meta['frame_size'][0]
        assert density==im.height/meta['frame_size'][1] and density in [1,4]
        m=copy.deepcopy(meta);m.update(path=resource(dst),frame_size=list(im.size),native_density=density,columns=1,source_effect_id=eid,art_revision=REV)
        data['sprites'][key]=m
        effect_inventory[key]={'id':key,'source':str(src.relative_to(REVIEW)),'path':resource(dst),'size':list(im.size),'bytes':dst.stat().st_size,'visible_hash':visible_hash(im)}
        return key
    for p in selected:
        pid=p['id'];cid=p['classId'];side=p['side'];key=cid+'_'+side;context=p['context']
        assert not p.get('frameErrors') and not p.get('sourceReviewPending')
        count=max(p['sourceFrameCount'],max(map(int,p['newFrames']))+1);columns=min(16,count);w,h=p['outputFrameSize']
        atlas=Image.new('RGBA',(columns*w,((count+columns-1)//columns)*h));hashes={}
        for slot,path in p['newFrames'].items():
            im=Image.open(REVIEW/path).convert('RGBA');assert im.size==(w,h)
            n=int(slot);atlas.paste(im,(n%columns*w,n//columns*h));hashes[slot]=visible_hash(im)
        target=OUT/(pid+'.png')
        if target.exists() and not (backup/target.name).exists():shutil.copy2(target,backup/target.name)
        atlas.save(target,optimize=True)
        art={'path':resource(target),'frame_size':[w,h],'frames':count,'columns':columns,'anchor':p['anchor'],
             'native_density':4,'reviewed_profile':pid,'source_oam_frame_count':p['sourceOamCutoff'],
             'oam_flip_origin_offset':p['flipOriginOffset'],'original_motion':True,'art_revision':p['revision']}
        item={'profile':pid,'key':key,'context':context,'revision':p['revision'],'path':resource(target),
              'size':list(atlas.size),'bytes':target.stat().st_size,'frame_hashes':hashes,'effect_aliases':{}}
        if context=='battle':
            actions=[a for a in g['actions'] if a['profile']==pid and a['kind']=='attack']
            art.update(reviewed_variants={},reviewed_class_id=int(cid),reviewed_side=side)
            source=enemy if side=='enemy' else ally
            for a in actions:
                assert a['ready'];original=source['variants'][a['key']];variant=copy.deepcopy(original)
                assert original['contact_tick']==a['contactTick'] and len(original['frames'])==len(a['frames'])
                rows=[]
                for n,row in enumerate(a.get('revisedFrames',a['frames'])):
                    r=copy.deepcopy(original['frames'][n]);r.update(copy.deepcopy(row));rows.append(r)
                rows+=copy.deepcopy(a.get('reviewTailFrames',[]))
                for row in rows:
                    assert str(row['frame']) in hashes,(pid,row['frame'])
                    effects=[]
                    for e in row.get('effects',[]):
                        eid=e['sprite']
                        if eid.startswith('review-slime-') and eid.endswith('-target-reference'):continue
                        if eid in p.get('revisedEffects',{}):
                            alias=effect(eid,p['revisedEffects'][eid],'reviewed-'+cid+'-'+side)
                            item['effect_aliases'][eid]=alias;e['sprite']=alias
                        elif eid.startswith('review-'):
                            effect(eid,g['effects'][eid])
                        elif eid not in data['sprites']:
                            effect(eid,g['effects'][eid])
                        if eid.startswith('review-slime-') and '-color-' not in eid:
                            e['bind_target']=True
                        effects.append(e)
                    row['effects']=effects
                variant.update(frames=rows,art_revision=p['revision'],source_frame_count=len(a['frames']),visual_tail_frames=len(a.get('reviewTailFrames',[])))
                runtime_key='reviewed/'+pid+'/'+a['key'];data['variants'][runtime_key]=variant
                art['reviewed_variants'][a['key']]=runtime_key;changed_variants.append(runtime_key)
            idle=next(a for a in g['actions'] if a['profile']==pid and a['key']=='idle')
            art['sequences']={'idle':[idle['frames'][0]['frame']]};data['battle'][key]=art;changed_battle.append(key)
        else:
            mapping=read(REVIEW/p['mapping']);scenario=next(s for s in mapping['scenarios'] if s['id']==context)
            art.update(tile_origin=[p['anchor'][0]-8,p['anchor'][1]-16],directions=copy.deepcopy(scenario['directions']),default_facing='right',static_facing=bool(scenario.get('static_facing',False)))
            if context=='tactical-walk':
                cycles={}
                for direction,order in scenario['directions'].items():
                    cycle=scenario.get('direction_preview_cycles',{}).get(direction,{})
                    indices=cycle.get('frames',order);ticks=cycle.get('frame_ticks',scenario.get('direction_frame_ticks',{}).get(direction,[scenario['timing']['frame_ticks']]*len(indices)))
                    cycles[direction]={'frames':indices,'ticks':ticks}
                art['direction_cycles']=cycles;art['native_move_ticks']=16
                art['directions']['side']=art['directions']['right']
            else:
                art.update(native_cycle=scenario['timing']['cycle_frames'],cycle_ticks=scenario['timing']['frame_ticks'],directions={d:[0,0] for d in ['up','down','left','right','side']})
            if p.get('mapShadow'):
                shadow=copy.deepcopy(p['mapShadow']);dst=OUT/(pid+'-shadow.png');shutil.copy2(REVIEW/shadow['path'],dst);shadow['path']=resource(dst);art['ground_shadow']=shadow
            data['maps'].setdefault(key,{})[context]=art;changed_maps.append([key,context])
        inventory.append(item)
    for key,value in before['battle'].items():
        if key not in changed_battle:assert data['battle'][key]==value
    for key,contexts in before['maps'].items():
        for context,value in contexts.items():
            if [key,context] not in changed_maps:assert data['maps'][key][context]==value
    assert all(data['variants'][k]==v for k,v in before['variants'].items() if k not in changed_variants)
    data.setdefault('map_revisions',{})[REV]={i['profile']:i['revision'] for i in inventory}
    runtime.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    for item in inventory+list(effect_inventory.values()):
        settings=(GAME/item['path'].removeprefix('res://')).with_suffix('.png.import')
        if settings.exists():
            settings.write_text(settings.read_text().replace('process/fix_alpha_border=true','process/fix_alpha_border=false'))
    report={'version':'0.10.1','revision':REV,'inventory':inventory,'effects':list(effect_inventory.values()),
            'map_profiles':len(changed_maps),'battle_profiles':len(changed_battle),'attack_variants':len(changed_variants),
            'unchanged_unselected_art_and_variants':True,'gameplay_contacts_preserved':True,
            'slime_target':'Runtime defender rendered directly; review-only target texture omitted; gel binds to defender origin.',
            'rules_and_save_data_modified':False}
    (REPORT/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['inventory','effects']},ensure_ascii=False))

if __name__=='__main__':main()
