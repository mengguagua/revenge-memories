#!/usr/bin/env python3
"""Share confirmed class15 spell visuals with class19, keeping its native actor rows."""
import copy,hashlib,json,re
from pathlib import Path
from build_gallery import ROOT,file_hash
from revise_curse_mage_battle import GROUND
from revise_slime_engulf import arrival_tick
REV='sage-shared-mage-spells-v3-20261023';OUT=ROOT/REV
COMMON=[23,24,25,26,27,28,29,31,32]

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def item(key):return int(re.search(r'_item_(\d+)',key).group(1))
def first_effect(rows):return next(i for i,f in enumerate(rows) if f['effects'])
def first_motion(rows):
    start=first_effect(rows);pos=rows[start]['effects'][0]['position']
    return next(i for i in range(start+1,len(rows)) if any(e['position']!=pos for e in rows[i]['effects']))
def first_sprite(rows,key):return next(i for i,f in enumerate(rows) if any(e['sprite']==key for e in f['effects']))
def first_group_motion(rows):
    start=first_effect(rows);positions=[e['position'] for e in rows[start]['effects']]
    return next(i for i in range(start+1,len(rows)) if [e['position'] for e in rows[i]['effects']]!=positions)

def stage_anchors(mage,sage,events):
    spell=item(sage['key']);ms=first_effect(mage['frames']);ss=first_effect(sage['frames']);pairs=[(ms,ss)];delta=sage['contactTick']-mage['contactTick']
    if spell==23:pairs.append((events['original_release'],first_motion(sage['frames'])))
    elif spell==24:pairs.append((events['target_lightning_unchanged_from_tick'],events['target_lightning_unchanged_from_tick']+delta))
    elif spell==25:pairs.append((events['trajectory_start'],next(i for i,f in enumerate(sage['frames']) if any(e['sprite'] in GROUND for e in f['effects']))))
    elif spell==26:pairs.append((first_group_motion(mage['frames']),first_group_motion(sage['frames'])))
    elif spell==27:
        pairs.append((events['spin_start'],first_sprite(sage['frames'],'44865a24d18d0f')))
        pairs.append((events['release_tick_kept'],first_motion(sage['frames'])))
    elif spell==29:
        pairs.append((events['full_ring_start'],first_sprite(sage['frames'],'e6b1ec951361a1')))
        pairs.append((events['release_tick_kept'],first_motion(sage['frames'])))
    elif spell==31:pairs.append((events['release_tick_kept'],first_motion(sage['frames'])))
    elif spell==32:pairs.append((events['attack_segment_start'],arrival_tick(sage['frames'])))
    pairs.append((mage['contactTick'],sage['contactTick']))
    pairs=sorted(set(pairs));assert all(a[0]<b[0] and a[1]<b[1] for a,b in zip(pairs,pairs[1:])),(sage['key'],pairs)
    return pairs

def source_tick(t,pairs):
    if t<pairs[0][1]:return None
    if t>=pairs[-1][1]:return pairs[-1][0]+t-pairs[-1][1]
    for (a,x),(b,y) in zip(pairs,pairs[1:]):
        if x<=t<y:return round(a+(t-x)*(b-a)/(y-x))
    raise ValueError(t)

def transfer(mage,sage,review):
    spell=item(sage['key']);rows=copy.deepcopy(sage['frames']);events=review['events'];contract={'mage_action':mage['id'],'sage_action':sage['id'],'spell_id':spell,'source_contact':mage['contactTick'],'sage_contact':sage['contactTick'],'native_actor_frames_kept':True,'additional_hits':0}
    if spell==28:
        replacements=events['full_arrow_replacements'];hits=0
        for row in rows:
            extra=[]
            for e in row['effects']:
                if e['sprite'] not in replacements:continue
                e['sprite']=replacements[e['sprite']];hits+=1
                if spell==28:
                    other=copy.deepcopy(e);other['position']=[e['position'][i]+events['additional_lane_offset'][i] for i in range(2)];extra.append(other)
            row['effects'].extend(extra)
        assert hits>0
        contract.update(mode='shared bitmap and identical approved draw recipe',replacement_effects=replacements,additional_lane_offset=events.get('additional_lane_offset'),replacement_events=hits)
    else:
        pairs=stage_anchors(mage,sage,events);template=mage.get('revisedFrames',mage['frames'])+mage.get('reviewTailFrames',[]);dx=[sage['origin'][i]-mage['origin'][i] for i in range(2)];indices=[]
        for t,row in enumerate(rows):
            n=source_tick(t,pairs);indices.append(n)
            if n is None:effects=[]
            elif n<len(template):effects=template[n]['effects']
            else:effects=template[-1]['effects'] if spell==32 else []
            row['effects']=copy.deepcopy(effects)
            for e in row['effects']:e['position']=[e['position'][i]+dx[i] for i in range(2)]
        contract.update(mode='shared complete effect sequence, aligned to own native spell stages',anchors=[{'mage_tick':a,'sage_tick':b} for a,b in pairs],template_ticks=len(template),source_tick_by_sage_frame=indices,origin_delta=dx,recovery_holds_target_reference=spell==32,tail_played_inside_native_recovery=True)
    note='与术法师同名法术共用已确认的素材、配色及效果阶段；蓄力、飞行和收尾按博学术师原施法阶段与结算对齐。博学术师人物动作、红宝珠法杖、总帧数与结算保持，不新增命中或能力。'
    return {'source_frames_sha256':sha(sage['frames']),'frames':rows,'note':note,'events':contract},contract

def main():
    OUT.mkdir(parents=True,exist_ok=True);data=json.loads((ROOT/'demos/gallery-data.json').read_text());mp=ROOT/'professions/class-15-ally/battle/frame_mapping.json';sp=ROOT/'professions/class-19-ally/battle/frame_mapping.json';mm=json.loads(mp.read_text());sm=json.loads(sp.read_text());timeline_path=(mp.parent/mm['review_timeline']).resolve();mt=json.loads(timeline_path.read_text());actions={a['key']:a for a in data['actions'] if a['context']=='battle' and a['profile'] in ['professions-class-15-ally-battle','professions-class-19-ally-battle']}
    if not (OUT/'baseline.json').exists():
        write(OUT/'baseline.json',{'action_facts':{a['id']:{'digest':a['contentDigest'],'frames_sha256':sha(a['frames']),'fps':a['fps'],'origin':a['origin'],'contact':a['contactTick'],'duration':a['duration']} for a in data['actions']},'sage_battle_mapping':sm,'sage_maps_sha256':file_hash(ROOT/'professions/class-19-ally/maps/frame_mapping.json'),'mage_mapping_path':str(mp.relative_to(ROOT)),'mage_mapping_sha256':file_hash(mp),'mage_timeline_path':str(timeline_path.relative_to(ROOT)),'mage_timeline_sha256':file_hash(timeline_path),'body_assets':{path:file_hash(ROOT/path) for p in data['profiles'] if p['id']=='professions-class-19-ally-battle' for path in p['newFrames'].values()}})
    baseline=json.loads((OUT/'baseline.json').read_text());assert file_hash(mp)==baseline['mage_mapping_sha256'] and file_hash(timeline_path)==baseline['mage_timeline_sha256']
    revised={};contracts=[]
    for sage in actions.values():
        if sage['profile']!='professions-class-19-ally-battle' or sage['kind']!='attack' or item(sage['key']) not in COMMON:continue
        mk=sage['key'].replace('class_19_','class_15_',1);mage=actions[mk];row,contract=transfer(mage,sage,mt['actions'][mk]);revised[sage['key']]=row;contracts.append(contract)
    assert len(revised)==54
    shared_ids=sorted({e['sprite'] for a in revised.values() for f in a['frames'] for e in f['effects']});assets=[]
    for eid in shared_ids:
        meta=data['effects'][eid];path=ROOT/meta['path'];assets.append({'effect_id':eid,'metadata':meta,'sha256':file_hash(path),'bytes':path.stat().st_size})
    # The mage timeline already registers these IDs globally. Reference the
    # exact same entries without duplicate IDs or copied image files.
    write(OUT/'shared-motion.json',{'revision':REV,'runtime_integrated':False,'effects':{},'shared_effect_source':baseline['mage_timeline_path'],'actions':revised})
    m=copy.deepcopy(baseline['sage_battle_mapping']);m.update(revision=REV,review_timeline='../../../'+REV+'/shared-motion.json',review_note='博学术师与术法师同名法术共用已确认特效：火球、雷电、诸神黄昏、圣光、风刃、箭雨、光环、鬼火、史莱姆。人物及红宝珠法杖保持；原施法阶段、总时长和结算不变。',qa_report='../../../'+REV+'/verification.json',shared_spell_source='class-15-ally',shared_spell_ids=COMMON);write(sp,m);write(OUT/'mapping-draft.json',m);write(OUT/'spell-contracts.json',{'revision':REV,'contracts':contracts,'support_spell_ids_unchanged':[40,41,42,43,44]});write(OUT/'shared-assets.json',{'revision':REV,'shared_existing_assets':assets,'new_art_assets':0})
    print(json.dumps({'shared_spells':len(COMMON),'variants':len(revised),'shared_assets':len(assets),'new_images':0}),flush=True)
if __name__=='__main__':main()
