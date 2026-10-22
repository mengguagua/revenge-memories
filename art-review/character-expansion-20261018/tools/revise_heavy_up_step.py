#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Import the ImageGen opposite leg phase, locking approved upper-body pixels."""
import argparse,copy,json
from PIL import Image,ImageDraw
from build_gallery import ROOT
import import_knight_redraw_v3 as helper
from import_heavy_infantry_v1 import back_helmet,matte,faction
from revise_cavalry_map import digest
from export_gallery import font

REV='heavy-infantry-up-step-v2-20261022';OUT=ROOT/REV;SRC=OUT/'source'
LEG_BOX=(54,70,76,96)

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def leg_boxes(im):
    # Knees can touch diagonally while the boots remain distinct. Measure each
    # boot's center columns, avoiding the shared inner outline at the midline.
    boxes=[]
    for left,right in[(54,63),(67,76)]:
        points={(x,y)for y in range(78,96)for x in range(left,right)if im.getpixel((x,y))[3]}
        assert len(points)>=6,('Missing boot',left,right)
        boxes.append([min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1])
    return boxes

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());helper.SRC=SRC
    fig=helper.figures('opposite-up-master-v1.png',1)[0];point=back_helmet(fig[0]);converted=matte(fig,point,True)
    original=Image.open(SRC/'before-up-1.png').convert('RGBA');oldreg=json.loads((ROOT/'heavy-infantry-redraw-v1-20261022/asset-manifest.json').read_text())['registration'];target=next(r['target_landmark']for r in oldreg if r['label']=='map-walk-1')
    helper.REG=[];registered=helper.register(converted,(128,96),point,target,88/fig[0].height,'opposite-up-edit')
    # Only the generated lower-body edit enters the runtime candidate. The
    # approved helmet, torso, skirt, arms, shield and entire spear stay immutable.
    first=original.copy();first.paste(registered.crop(LEG_BOX),LEG_BOX[:2]);second=original.copy();poses=[first,second]
    boxes=[leg_boxes(im)for im in poses]
    assert boxes[0][0][3]+6<=boxes[0][1][3],('left boot should be raised',boxes[0])
    assert boxes[1][1][3]+6<=boxes[1][0][3],('right boot should be raised',boxes[1])
    for y in range(96):
        for x in range(128):
            if not(LEG_BOX[0]<=x<LEG_BOX[2]and LEG_BOX[1]<=y<LEG_BOX[3]):assert first.getpixel((x,y))==second.getpixel((x,y))==original.getpixel((x,y))
    drafts={};assets=[];records={}
    for side in['ally','enemy']:
        mapping=copy.deepcopy(baseline['mappings'][side]);walk=next(s for s in mapping['scenarios']if s['id']=='tactical-walk');frames=[]
        for i,raw in enumerate(poses):
            im=faction(raw,side);path=OUT/side/f'frame-{i:03}.png';path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True);relative='../../../'+path.relative_to(ROOT).as_posix();record=next(r for r in walk['frame_mapping']if r['source_index']==i)
            record.update(path=relative,output_path=relative,revision=REV,size=list(im.size),bytes=path.stat().st_size,sha256=digest(path),art_status='review_candidate');assets.append({'path':path.relative_to(ROOT).as_posix(),'purpose':'left leg raised / right leg raised whole phase','size':list(im.size),'bytes':path.stat().st_size,'sha256':digest(path)})
        atlas=Image.new('RGBA',(128*8,96))
        for rec in walk['frame_mapping']:
            path=(ROOT/f'professions/class-2-{side}/maps'/rec['path']).resolve();im=Image.open(path).convert('RGBA');atlas.alpha_composite(im,(128*rec['source_index'],0));frames.append(im)
        path=OUT/side/'walk-atlas.png';atlas.save(path,optimize=True);walk.update(revision=REV,output_atlas='../../../'+path.relative_to(ROOT).as_posix(),output_atlas_bytes=path.stat().st_size,status='review_candidate');assets.append({'path':path.relative_to(ROOT).as_posix(),'purpose':'map walk atlas; other six frames reused unchanged','size':list(atlas.size),'bytes':path.stat().st_size,'sha256':digest(path)})
        walk['direction_action_notes']=dict(walk.get('direction_action_notes',{}),up='向上两相：左腿抬起、右腿支撑，再右腿抬起、左腿支撑。头盔、躯干、裙甲、手臂、盾牌和长枪两相像素一致；每相仍16帧。')
        walk['motion_review']={**walk.get('motion_review',{}),'up_step_revision':REV,'up_phase_order':['left raised, right support','right raised, left support'],'up_core':'pixel-identical approved upper body and equipment','up_leg_edit_box':list(LEG_BOX),'up_leg_bounds':boxes}
        drafts[side]=mapping;records[side]=frames
    for light in[False,True]:
        bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242);board=Image.new('RGB',(1024,864),bg);draw=ImageDraw.Draw(board)
        for row,side in enumerate(['ally','enemy']):
            for phase in[0,1]:
                im=records[side][phase].resize((512,384),Image.Resampling.NEAREST);board.paste(im,(phase*512,row*432),im);label=('盟军'if side=='ally'else'敌方')+' · '+('左腿抬起／右腿支撑'if phase==0 else'右腿抬起／左腿支撑');draw.text((phase*512+256,row*432+398),label,anchor='mt',font=font(18),fill=fg)
        path=OUT/f'up-pair-{"light"if light else"dark"}.png';board.save(path,optimize=True);assets.append({'path':path.relative_to(ROOT).as_posix(),'purpose':'both factions alternate leg inspection','size':list(board.size),'bytes':path.stat().st_size,'sha256':digest(path)})
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','source_master':'source/opposite-up-master-v1.png','prompt':'source/imagegen-prompt.json','registration':helper.REG,'upper_body_and_equipment_pixel_identical':True,'leg_edit_box':list(LEG_BOX),'leg_bounds_by_phase':boxes,'native_ticks_per_pose':16,'runtime_integrated':False,'assets':assets})
    if publish:
        for side,m in drafts.items():write(ROOT/f'professions/class-2-{side}/maps/frame_mapping.json',m)
    print(json.dumps({'status':'published'if publish else'staged','leg_bounds_by_phase':boxes,'upper_body_pixel_identical':True}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
