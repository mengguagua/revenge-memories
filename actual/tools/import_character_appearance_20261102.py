#!/usr/bin/env python3
"""Sync only the three revised allied battle atlases; retain all motion programs."""
import copy
import gzip
import hashlib
import json
import os
import zlib
from pathlib import Path

from PIL import Image

GAME=Path(__file__).resolve().parents[1]
REVIEW=GAME.parent/'art-review/character-expansion-20261018'
REV='character-appearance-20261102'
OUT=GAME/'assets'/REV
REPORT=GAME/'reports'/REV
TARGETS={1:'mount-consistency-v2-20261101',3:'mount-consistency-v2-20261101',12:'battle-appearance-v1-20261031'}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def visible_hash(image):
    pixels=bytearray(image.convert('RGBA').tobytes())
    for i in range(0,len(pixels),4):
        if not pixels[i+3]:pixels[i:i+3]=b'\x00\x00\x00'
    return sha(pixels)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.appearance-tmp')
    temp.write_text((json.dumps(value,ensure_ascii=False,indent=2) if path.name=='manifest.json'
                     else json.dumps(value,ensure_ascii=False,separators=(',',':')))+'\n')
    os.replace(temp,path)


def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    source_path=GAME/'data/reviewed_animations.json'
    index_path=GAME/'data/animation_runtime/reviewed.json'
    manifest_path=GAME/'data/animation_runtime/manifest.json'
    raw=source_path.read_bytes()
    data=json.loads(raw)
    before=copy.deepcopy(data)
    index=json.loads(index_path.read_bytes())
    manifest=json.loads(manifest_path.read_bytes())
    entry=manifest['groups']['reviewed']
    assert entry['source_sha256']==sha(raw),'Existing source/index mismatch; do not replace a stale index'
    assert index['metadata']=={k:v for k,v in data.items() if k!='variants'}
    program_path=GAME/entry['programs'].removeprefix('res://')
    program_sha=sha(program_path.read_bytes())
    assert program_sha==entry['program_sha256']
    with program_path.open('rb') as stream:
        for key,(offset,length,raw_length) in index['variants'].items():
            stream.seek(offset)
            payload=zlib.decompress(stream.read(length))
            assert len(payload)==raw_length and json.loads(payload)==data['variants'][key]
    for path in [source_path,index_path,manifest_path]:
        backup=REPORT/('before-'+path.name+'.gz')
        if not backup.exists():
            with gzip.open(backup,'wb') as stream:stream.write(path.read_bytes())
    gallery=json.loads((REVIEW/'demos/gallery-data.json').read_bytes())
    profiles={p['id']:p for p in gallery['profiles']}
    inventory=[]
    actions=[]
    for cid,revision in TARGETS.items():
        key=f'{cid}_ally'
        pid=f'professions-class-{cid}-ally-battle'
        profile=profiles[pid]
        assert profile['revision']==revision and not profile.get('frameErrors')
        old=data['battle'][key]
        atlas=Image.open(GAME/old['path'].removeprefix('res://')).convert('RGBA')
        w,h=old['frame_size']
        columns=old['columns']
        assert profile['outputFrameSize']==[w,h]
        records=[]
        for frame,path in profile['newFrames'].items():
            number=int(frame)
            image=Image.open(REVIEW/path).convert('RGBA')
            assert image.size==(w,h) and number<int(old['frames'])
            x,y=number%columns*w,number//columns*h
            previous=atlas.crop((x,y,x+w,y+h))
            atlas.paste(image,(x,y))
            records.append({'slot':number,'review_path':path,'visible_rgba_sha256':visible_hash(image),
                            'changed_from_runtime':visible_hash(previous)!=visible_hash(image)})
        for action in (a for a in gallery['actions'] if a['profile']==pid):
            field='reviewed_variants' if action['kind']=='attack' else 'reviewed_reactions'
            label=action['key'] if field=='reviewed_variants' else action['key'].removeprefix('reaction-')
            runtime_key=old[field][label]
            variant=data['variants'][runtime_key]
            rows=action.get('revisedFrames',action['frames'])+action.get('reviewTailFrames',[])
            assert len(rows)==len(variant['frames'])
            assert action['contactTick']==variant['contact_tick']
            for src,raw_row in zip(rows,variant['frames']):
                row=copy.deepcopy(raw_row)
                row['effects']=[{**e,'sprite':data['sprites'][e['sprite']].get('source_effect_id',e['sprite'])}
                                for e in row.get('effects',[])]
                assert all(src[k]==row.get(k) for k in src),(action['id'],src,row)
            actions.append({'id':action['id'],'profile':pid,'class_id':cid,'key':key,'kind':action['kind'],
                            'source_key':action['key'],'runtime_key':runtime_key,'frames':len(rows),
                            'fps':action['fps'],'contact_tick':action['contactTick'],'content_digest':action['contentDigest']})
        target=OUT/(pid+'.png')
        atlas.save(target,optimize=True)
        import_settings=target.with_suffix('.png.import')
        if import_settings.exists():
            import_settings.write_text(import_settings.read_text().replace('process/fix_alpha_border=true','process/fix_alpha_border=false'))
        art=copy.deepcopy(old)
        art.update(path='res://'+target.relative_to(GAME).as_posix(),art_revision=revision,review_sync=REV,
                   appearance_source_digests={a['source_key']:a['content_digest'] for a in actions if a['profile']==pid})
        data['battle'][key]=art
        inventory.append({'key':key,'class_id':cid,'profile':pid,'revision':revision,
                          'previous_revision':old['art_revision'],'previous_path':old['path'],'path':art['path'],
                          'frame_size':[w,h],'columns':columns,'frames':old['frames'],'atlas_size':list(atlas.size),
                          'bytes':target.stat().st_size,'visible_rgba_sha256':visible_hash(atlas),'slots':records,
                          'quality_reason':'shared lossless native-slot animation atlas; preserve all registered poses and pixels'})
    assert before['variants']==data['variants']
    for key in before:
        if key!='battle':assert before[key]==data[key],key
    changed={f'{cid}_ally' for cid in TARGETS}
    assert all(before['battle'][key]==value for key,value in data['battle'].items() if key not in changed)
    # The programs are byte-identical. Refresh only the metadata index and its
    # source fingerprint so actual gameplay never falls back to the old atlas.
    index['metadata']={k:v for k,v in data.items() if k!='variants'}
    assert source_path.read_bytes()==raw,'Runtime source changed during import'
    write(source_path,data)
    write(index_path,index)
    entry['source_sha256']=sha(source_path.read_bytes())
    write(manifest_path,manifest)
    assert sha(program_path.read_bytes())==program_sha
    assert index['variants']==json.loads(gzip.decompress((REPORT/'before-reviewed.json.gz').read_bytes()))['variants']
    report={'revision':REV,'runtime_integrated':True,'inventory':inventory,'actions':actions,
            'source_poses':sum(len(a['slots']) for a in inventory),'action_count':len(actions),
            'motion_programs_unchanged':len(data['variants']),'program_bin_sha256':program_sha,
            'only_battle_profiles_changed':sorted(changed),'maps_effects_other_roles_unchanged':True,
            'native_timing_contacts_weapon_states_unchanged':True,'device_updated':False,'package_rebuilt':False}
    write(REPORT/'import.json',report)
    print(json.dumps({'profiles':len(inventory),'source_poses':report['source_poses'],
                      'changed_source_poses':sum(s['changed_from_runtime'] for a in inventory for s in a['slots']),
                      'actions':len(actions),'unchanged_motion_programs':len(data['variants'])}),flush=True)


if __name__=='__main__':main()
