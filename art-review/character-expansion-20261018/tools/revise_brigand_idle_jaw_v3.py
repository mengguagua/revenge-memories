#!/usr/bin/env python3
"""Register ImageGen's jaw/neck edit and preserve the rest of the accepted idle art."""
import argparse, copy, json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import revise_brigand_idle_shoulders_v2 as V

ROOT=V.ROOT
REV='brigand-idle-jaw-v3-20261023'
OUT=ROOT/REV
BASE=ROOT/'brigand-idle-shoulders-v2-20261023'
ROI=(37,36,62,49)

def write(p,d): V.write(p,d)
def sha(p): return V.digest(p)

def align_head(old,new,head):
    # Register on the face and hair above the jaw, never on the animated neck.
    x,y=map(round,head); b=(x-75,y-85,x+75,y+12)
    template=old.crop(b).resize((50,33))
    best=None
    for dy in range(-16,17,2):
        for dx in range(-28,29,2):
            q=new.crop((b[0]+dx,b[1]+dy,b[2]+dx,b[3]+dy)).resize((50,33))
            score=sum(ImageStat.Stat(ImageChops.difference(q,template)).sum)
            if best is None or score<best[0]: best=(int(score),dx,dy)
    return best

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mapping=json.loads(V.MAP.read_text())
    baseline=OUT/'maps-before-publish.json'
    if not baseline.exists(): write(baseline,mapping)
    recipe=json.loads((BASE/'pose-inputs.json').read_text())
    old=Image.open(BASE/'source/idle-shoulder-neck-master.png').convert('RGBA')
    new=Image.open(OUT/'source/jaw-neck-master.png').convert('RGBA')
    V.SRC=OUT/'source'
    poses=[]; records=[]; registrations=[]
    for i,spec in enumerate(recipe['poses']):
        spec=copy.deepcopy(spec)
        head=[spec['bounds'][j]+spec['head'][j] for j in (0,1)]
        score,dx,dy=align_head(old,new,head)
        spec['source']='jaw-neck-master.png'
        spec['bounds']=[v+(dx if j%2==0 else dy) for j,v in enumerate(spec['bounds'])]
        # Hair/face stay in the accepted image; only the authored jaw/neck area is used.
        spec.pop('hair_box',None)
        edited,registration=V.register(spec)
        registration.update(head_template_offset=[dx,dy],template_error=score,edit_region=list(ROI))
        base=Image.open(BASE/'frames'/f'frame-{i:03}.png').convert('RGBA')
        result=base.copy(); result.paste(edited.crop(ROI),ROI[:2])
        outside=result.copy(); outside.paste(base.crop(ROI),ROI[:2])
        assert outside.tobytes()==base.tobytes(),'only jaw/neck edit region may change'
        assert result.getbbox()==base.getbbox(),'whole-body extent must stay fixed'
        poses.append(result);registrations.append(registration)
    atlas=Image.new('RGBA',(576,96))
    for slot,canonical in enumerate(V.ORDER):
        record=V.save(poses[canonical],OUT/'frames'/f'frame-{slot:03}.png')
        record.update(source_index=slot,source_frame=slot,output_index=slot,canonical_frame=canonical,output_path=record['path'],revision=REV,art_status='review_candidate')
        records.append(record);atlas.alpha_composite(poses[canonical],(slot*96,0))
    atlas_record=V.save(atlas,OUT/'idle-atlas.png')
    V.OUT=OUT
    previews=V.preview(poses,False)+V.preview(poses,True)
    candidate=copy.deepcopy(next(s for s in mapping['scenarios'] if s['id']=='tactical-idle'))
    for row,record in zip(candidate['frame_mapping'],records): row.update(record)
    candidate.update(output_atlas=atlas_record['path'],revision=REV,review_note='待机加入细的深色弧形下颌线；颈部与V领随扭肩小幅变化，头部中心及下半身保持稳定。',motion_review={'revision':REV,'edit_region':list(ROI),'source':'ImageGen authored jaw/neck edit','upper_head_and_lower_body_pixels_unchanged':True,'registration':registrations,'native_timing_modified':False,'runtime_integrated':False})
    write(OUT/'idle-scenario-draft.json',candidate)
    write(OUT/'asset-manifest.json',{'revision':REV,'palette':V.HEX,'edit_region':list(ROI),'records':records,'atlas':atlas_record,'previews':previews,'registrations':registrations,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    # Production preview, not a new anatomy drawing.
    board=Image.new('RGB',(768,512),(220,222,216))
    for row in range(2):
        for col in range(3):
            im=Image.open(BASE/'frames'/f'frame-{col:03}.png').convert('RGBA') if row==0 else poses[col]
            im=im.resize((256,256),Image.Resampling.NEAREST)
            board.paste(im,(col*256,row*256),im)
    board.save(OUT/'before-after-light.png',optimize=True)
    print(json.dumps({'staged':True,'edit_region':ROI,'head_alignment_offsets':[r['head_template_offset'] for r in registrations]}))

def check_and_publish(publish=False):
    candidate=json.loads((OUT/'idle-scenario-draft.json').read_text())
    before=json.loads(V.MAP.read_text())
    prior=next(s for s in before['scenarios'] if s['id']=='tactical-idle')
    assert candidate['timing']==prior['timing'] and candidate['directions']==prior['directions']
    necks=[];records=[]
    for i in range(3):
        im=Image.open(OUT/'frames'/f'frame-{i:03}.png').convert('RGBA')
        base=Image.open(BASE/'frames'/f'frame-{i:03}.png').convert('RGBA')
        exterior=im.copy();exterior.paste(base.crop(ROI),ROI[:2])
        assert exterior.tobytes()==base.tobytes()
        assert set(im.getchannel('A').getdata())<={0,255}
        assert {p[:3] for p in im.getdata() if p[3]}<=set(V.COLORS)
        jaw=(44,40,56,44)
        count=lambda image:sum(p[:3]==V.COLORS[0] and p[3]>0 for p in image.crop(jaw).getdata())
        assert count(im)>count(base),'new dark jaw contour is visible'
        neck=im.crop((41,42,58,47));necks.append(neck.tobytes())
        skin=[(x,y) for y in range(42,47) for x in range(41,58) if im.getpixel((x,y))==(*V.COLORS[3],255)]
        assert len(skin)>=12,'neck skin must remain visible below/around the jawline'
        records.append({'frame':i,'new_dark_jaw_pixels':count(im)-count(base),'neck_skin_pixels':len(skin),'neck_skin_centroid':[sum(p[a] for p in skin)/len(skin) for a in (0,1)],'size':list(im.size),'bytes':(OUT/'frames'/f'frame-{i:03}.png').stat().st_size})
    assert len(set(necks))==3,'three neck shapes must remain distinct'
    write(OUT/'checks.json',{'passed':True,'scope':'jaw/neck edit only','upper_head_and_body_outside_edit_region_unchanged':True,'native_timing_unchanged':True,'neck_shapes_distinct':True,'frames':records})
    if publish:
        after=copy.deepcopy(before)
        index=next(i for i,s in enumerate(after['scenarios']) if s['id']=='tactical-idle')
        after['scenarios'][index]=candidate
        assert [{k:v for k,v in before.items() if k!='scenarios'},[s for s in before['scenarios'] if s['id']!='tactical-idle']]==[{k:v for k,v in after.items() if k!='scenarios'},[s for s in after['scenarios'] if s['id']!='tactical-idle']]
        assert json.loads(V.MAP.read_text())==before,'mapping changed concurrently'
        write(V.MAP,after)
        write(OUT/'publish-proof.json',{'only_scenario_changed':'tactical-idle','top_level_and_other_scenarios_unchanged':True,'runtime_integrated':False})
    print(json.dumps({'checks_passed':True,'published':publish}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');args=parser.parse_args()
    main();check_and_publish(args.publish)
