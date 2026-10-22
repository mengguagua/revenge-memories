#!/usr/bin/env python3
"""Import the corrected frontal and left-walking drawings; preserve native timing."""
import argparse, copy, json, math
from PIL import Image, ImageDraw
from build_gallery import ROOT, file_hash
import import_sniper_complete as art

REV='sniper-down-left-v2-20261022'
OUT=ROOT/REV
SRC=OUT/'source'

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def mask_where(test):
    mask=Image.new('L',(128,96))
    mask.putdata([255 if test(x,y) else 0 for y in range(96) for x in range(128)])
    return mask

def masked(im,mask):
    q=Image.new('RGBA',im.size);q.paste(im,(0,0),mask);return q

def clear(im,mask):im.paste((0,0,0,0),(0,0,128,96),mask)

def correction_board(side):
    q=Image.new('RGB',(960,1200),(220,222,216));d=ImageDraw.Draw(q)
    labels=['下行 · 右脚支撑','下行 · 左脚支撑','左行 · 收腿','左行 · 迈步']
    for n,i in enumerate([4,5,6,7]):
        im=Image.open(OUT/f'{side}/tactical-walk/frame-{i:03}.png').convert('RGBA').crop((43,30,88,96)).resize((360,528),Image.Resampling.NEAREST)
        x=n%2*480+60;y=n//2*600+30;q.paste(im,(x,y),im)
        d.text((x+180,y+550),labels[n],anchor='mm',font=art.font(20),fill=(23,38,56))
    art.save(q,f'{side}-correction-check.png','four corrected phases at nearest-neighbor zoom, with clear label spacing')

def pairs():
    art.SRC=SRC;art.OUT=OUT;art.helper.SRC=SRC
    poses={}
    for kind,ids in [('down',[4,5]),('left',[6,7])]:
        figs=list(art.figures(kind+'-master.png',2))
        if kind=='left':
            # The brown bow grip must not be mistaken for the waist belt.
            for (_,m),p in zip(figs,[[180.5,392.5],[241.5,394.0]]):
                m['waist']=p;m['manual_waist_reason']='center between the two belt fittings; excludes bow grip and quiver'
        scale=min(27/(im.height-m['waist'][1]) for im,m in figs)
        for i,f in zip(ids,figs):poses[i]=art.register(f,(128,96),[64,67],scale,f'{kind}-{i}')
    # A complete coherent frontal head/neck/collar/torso, from a single
    # drawing, stays fixed through both alternating-foot phases.
    front_core=mask_where(lambda x,y:y<69 or x>=72 or (x<56 and y<77))
    poses[5].paste(poses[4],(0,0),front_core)
    art.save(front_core,'source/down-fixed-core-mask.png','complete connected frontal upper-body region')

    # Use one connected drawing for the entire left-facing upper body.
    # Animate its generated arm as a rigid piece about the shoulder, rather
    # than stitching a head from one pose onto a separately aligned neck.
    base=poses[6].copy()
    def empty_arm(x,y):
        edge=58 if 60<=y<=62 else 60 if 63<=y<=66 else 59 if y==67 else 57
        return 60<=y<=73 and x<=edge
    arm_mask=mask_where(empty_arm)
    arm=masked(base,arm_mask)
    # Whole bow, grip, hand and forearm move together by one native output
    # pixel; the upper arm continues to overlap the fixed shoulder.
    bow_mask=mask_where(lambda x,y: (x>=77 and y<90) or (72<=x and 64<=y<70) or (75<=x and 82<=y<89))
    bow=masked(base,bow_mask)
    core=base.copy();clear(core,arm_mask);clear(core,bow_mask)
    core.paste((0,0,0,0),(0,69,128,96))
    core_mask=mask_where(lambda x,y:y<69 and not empty_arm(x,y) and not bow_mask.getpixel((x,y)))
    art.save(core,'source/left-connected-core.png','one complete drawn head, neck, collar, chest and waist shared by both phases')
    art.save(core_mask,'source/left-fixed-core-mask.png','unchanged torso/head region, excluding articulated limbs')
    art.save(arm,'source/left-empty-arm.png','drawn empty arm isolated at the shoulder for rigid animation')
    art.save(bow,'source/left-bow-hand-forearm.png','complete drawn bow and gripping forearm; single rigid layer')
    for i,angle,dy in [(6,-15,0),(7,30,1)]:
        q=poses[i].copy();q.paste((0,0,0,0),(0,0,128,69))
        # Remove the original hanging hand / bow below the common torso.
        lower_cleanup=mask_where(lambda x,y:69<=y<90 and (empty_arm(x,y) or bow_mask.getpixel((x,y))))
        clear(q,lower_cleanup)
        q.alpha_composite(core)
        rotated=arm.rotate(angle,resample=Image.Resampling.NEAREST,center=(57,60))
        # This is joint animation of an ImageGen-drawn part, with no stretch.
        q.alpha_composite(rotated)
        q.alpha_composite(bow,(0,dy))
        # The shoulder plate covers the arm's pivot, as in the source drawing.
        shoulder=(53,54,60,60);q.paste(base.crop(shoulder),shoulder[:2])
        poses[i]=q
    for i,q in poses.items():
        cc=art.helper.parts((x,y)for y in range(96)for x in range(128)if q.getpixel((x,y))[3])
        for comp in cc[1:]:
            assert len(comp)<=3,('disconnected anatomy',i,len(comp))
            for xy in comp:q.putpixel(xy,(0,0,0,0))
    return poses,core_mask,front_core

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());poses,core_mask,front_core=pairs();drafts={}
    for side in ['ally','enemy']:
        m=copy.deepcopy(baseline['mappings'][side]);scene=next(s for s in m['scenarios']if s['id']=='tactical-walk');atlas=Image.new('RGBA',(1024,96))
        scene.update(revision=REV,review_note='下行正脸朝前；左行头颈及躯干固定为同一连贯绘稿，空手臂绕肩摆动，持弓臂与完整长弓轻微上下运动，双腿按原作两相交替。')
        scene.setdefault('motion_review',{})['down_left_correction']={'revision':REV,'native_timing_modified':False,'frontal_head_neck_torso_shared':True,'left_head_neck_torso_shared':True,'left_empty_arm_pivot':[57,60],'left_empty_arm_angles':[-15,30],'bow_and_forearm_vertical_offsets':[0,1],'full_pose_scale_shared_within_pair':True}
        entries=[]
        for row in scene['frame_mapping']:
            i=row['source_index']
            if i in poses:
                im=art.faction(poses[i],side);path=art.save(im,f'{side}/tactical-walk/frame-{i:03}.png','corrected down/left walking pose; native slot/timing unchanged')
                row.update(path=path,output_path=path,revision=REV,bytes=art.ASSETS[-1]['bytes'],sha256=art.ASSETS[-1]['sha256'],size=[128,96])
            else:im=Image.open((ROOT/f'professions/class-13-{side}/maps'/row['path']).resolve()).convert('RGBA')
            atlas.alpha_composite(im,(i*128,0));entries.append((['上','上','右','右','下','下','左','左'][i]+f' {i}',im))
        scene['output_atlas']=art.save(atlas,f'{side}/tactical-walk-atlas.png','native eight-directional-slot atlas with only down/left slots replaced')
        idle=next(s for s in m['scenarios']if s['id']=='tactical-idle')
        for row in idle['frame_mapping'][:3]:
            im=Image.open((ROOT/f'professions/class-13-{side}/maps'/row['path']).resolve()).convert('RGBA');entries.append((f'待机 {row["source_index"]}',im))
        for light in [False,True]:art.board(entries,side,'maps',light)
        correction_board(side)
        drafts[f'professions/class-13-{side}/maps/frame_mapping.json']=m
    write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'generator':'built-in image_gen','assets':art.ASSETS,'whole_pose_registrations':art.REG,'palette':{'ally':art.HEX,'enemy':art.EHEX},'art_method':'two new full-pose pairs; one connected upper body per direction; rigid shoulder animation of the generated empty arm; one-pixel bow/forearm movement; no body or neck translation','runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for path,m in drafts.items():write(ROOT/path,m)
    print(json.dumps({'assets':len(art.ASSETS),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
