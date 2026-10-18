#!/usr/bin/env python3
"""Audit every frozen ally selector and write an explicit, non-destructive bow reference overlay."""
from pathlib import Path
import copy,hashlib,json,sys
from PIL import Image

HERE=Path(__file__).resolve();PRODUCTION=HERE.parents[2];REPO=HERE.parents[4]
sys.path[:0]=[str(REPO/'tools'),str(REPO/'actual/tools')]
from extract_full_graphics import Source
from fe2_source_cpu import CPU
from extract_character_motion import OriginalBody,program_for
from extract_full_effects import run_effect,effect_image

def digest(value):return hashlib.sha256(value).hexdigest()

def main():
    source=Source(REPO/'.reference/fe2-source-956365ef')
    frozen_path=PRODUCTION/'source-input/original-motion/full-original-motion.json'
    before=digest(frozen_path.read_bytes());frozen=json.loads(frozen_path.read_text())
    destination=PRODUCTION/'source-input/corrected-ally-motion';destination.mkdir(exist_ok=True)
    records=[];differences=[]
    for key,trace in frozen['variants'].items():
        cid=trace['source_class_id'];item=trace['source_item_id'];promoted=key=='original_class_21_promoted';critical=key=='original_class_21_critical'
        cpu=CPU(source.rom);m=cpu.mem;cpu.x=0;m[0x306]=cid;m[0x307]=trace['opponent_class_id'];m[0x320]=item;m[0x744a]=int(promoted);m[0x353]=int(critical)
        refs={}
        for zero_page,table in[(0,'L058EF0'),(2,'L058FB1')]:
            ref=source.b[5][table]['dw'][cid-1];address=int(ref[3:],16);m[zero_page]=address&255;m[zero_page+1]=address>>8;refs[table]=ref
        cpu.hooks[(5,0x8c0f)]=lambda runner:None;cpu.call(5,0x8a17)
        native=[m[0x3eb],m[0x3ee],m[0x3be]];previous=list(program_for(source,cid,item,promoted,critical))
        record={'key':key,'class':cid,'item':item,'native_program_effect_idle':native,'frozen_extractor_program_effect_idle':previous,'match':native==previous,'tables':refs}
        records.append(record)
        if not record['match']:differences.append(record)
    assert len(differences)==6 and all(row['key'].startswith('class_21_ally_bow')for row in differences),differences
    body_meta=frozen['original_bodies']['21'];atlas_path=PRODUCTION/'source-input/original-motion/class-21.png';atlas_before=digest(atlas_path.read_bytes());atlas=Image.open(atlas_path).convert('RGBA');w,h=body_meta['frame_size'];existing=[];lookup={}
    for i in range(body_meta['frames']):
        frame=atlas.crop((i%16*w,i//16*h,i%16*w+w,i//16*h+h));existing.append(frame);lookup.setdefault(digest(frame.tobytes()),i)
    source_differences=[]
    for y in range(h):
        for x in range(w):
            a=existing[126].getpixel((x,y));b=existing[138].getpixel((x,y))
            if a!=b:source_differences.append({'pixel':[x,y],'correct126':list(a),'frozen138':list(b)})
    assert len(source_differences)==9 and all(not r['correct126'][3]and r['frozen138'][3]for r in source_differences)
    body=OriginalBody(source,21);variants={};corrections=[];sprites={}
    for record in differences:
        key=record['key'];old=frozen['variants'][key];program,effect,idle=record['native_program_effect_idle'];heavy=key.endswith('_vs_heavy')
        new=run_effect(source,21,'ally',program,effect,old['source_item_id'],idle,old['formation'],4 if heavy else None)
        mapping=body.compile(new['frames'],idle)
        for row,index in zip(new['frames'],mapping):
            fingerprint=digest(body.frames[index].tobytes());assert fingerprint in lookup,'New composed frame requires a separately appended atlas index'
            row['frame']=lookup[fingerprint]
            for state in row['effects']:
                image,size,anchor,ref=effect_image(source,state);identity=digest(image.tobytes()+str(anchor).encode())[:14]
                assert identity in frozen['sprites'],('Unfrozen effect',identity)
                keep={k:state[k]for k in['position','flip','priority']};state.clear();state.update(keep,sprite=identity)
        new['source_program_address']=old['source_program_address'];new['source_revision']=old['source_revision'];new['reference_status']='native_selector_corrected_reference';new['reference_correction']='Start from native bow idle65; source frame126 replaces frame138 with stale sword pixels.'
        assert len(new['frames'])==len(old['frames'])and new['contact_tick']==old['contact_tick']
        for a,b in zip(new['frames'],old['frames']):
            assert all(a.get(k)==b.get(k)for k in['offset','flip','effects']),('Timing/position/effect difference',key)
        changed=[{'tick':i,'old_frame':a['frame'],'corrected_frame':b['frame'],'old_source_pose':a['source_pose'],'corrected_source_pose':b['source_pose']}for i,(a,b)in enumerate(zip(old['frames'],new['frames']))if a['frame']!=b['frame']]
        variants[key]=new;corrections.append({'key':key,'old_idle':0,'native_idle':65,'ticks':len(new['frames']),'contact_tick':new['contact_tick'],'timing_offsets_flip_external_effects_unchanged':True,'changed_ticks':changed,'corrected_unique_frames':sorted(set(r['frame']for r in new['frames']))})
    overlay={'schema':1,'base_frozen_motion':'source-input/original-motion/full-original-motion.json','base_sha256':before,'source_revision':frozen['source_revision'],'label':'原作校正参考','variants':variants,'sprites':sprites,
      'atlas_policy':'Original frozen atlas and all139 indices retained unchanged; correct frame126 already exists, so no new index is necessary.',
      'art_aliases':{'21':{'126':{'mapped_art_frame':138,'reason':'Exact source body/bow geometry matches; frozen138 adds only9 stale sword pixels. The new full-draw bow artwork already excludes the stale sword.'}}},
      'corrections':corrections,'reference_note':'男主弓箭使用原生idle65起始及125/126/127完整弓姿势；冻结旧稿的138多出9个旧剑残留像素。只修隔离参考，不修改游戏数据或新增能力。'}
    (destination/'overlay.json').write_text(json.dumps(overlay,ensure_ascii=False,indent=2)+'\n')
    audit={'checked_variants':len(records),'matches':len(records)-len(differences),'differences':differences,'records':records,'routine':'native bank005:L058A17 to before L058C0F','frozen_motion_sha256':before,'frozen_atlas_sha256':atlas_before,'source126_vs138':{'difference_count':9,'bbox':[32,56,37,61],'all_differences_are_extra_opaque_pixels_in138':True,'pixels':source_differences},'corrected_bow_frames':[125,126,127],'runtime_modified':False}
    (destination/'selector-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    assert digest(frozen_path.read_bytes())==before and digest(atlas_path.read_bytes())==atlas_before
    print(json.dumps({'audited':len(records),'unchanged':len(records)-len(differences),'corrected':len(variants),'source_pixels_removed_from_reference':9,'new_art_regeneration_needed':False},ensure_ascii=False))

if __name__=='__main__':main()
