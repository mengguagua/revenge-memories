#!/usr/bin/env python3
"""Friendly mage map motion: approved warm robe, fixed head/torso, moving hem."""
import copy,hashlib,json
from PIL import Image,ImageDraw
from build_gallery import ROOT
from recolor_mage_robe_warm import PALETTE
from revise_mage_robe_idle import save

REVISION='mage-map-motion-v3-20261021'
OUT=ROOT/REVISION
MAPPING=ROOT/'professions/class-15-ally/maps/frame_mapping.json'
AXIS=64
HEM_START=77


def c(key):return (*bytes.fromhex(PALETTE[key]),255)


def head(source,dx,side):
    result=Image.new('RGBA',(128,96))
    for y in range(62 if side=='up'else 64):
        for x in range(source.width):
            red,green,blue,alpha=source.getpixel((x,y))
            if alpha<128:continue
            light=.2126*red+.7152*green+.0722*blue
            if side=='right'and 53<=y<64 and 44<=x<=67 and red>green*1.1 and green>blue*1.1:
                key='skin'if light>140 else'skin_shadow'
            elif light<35:key='outline'
            elif red>green*1.2 and green>blue*1.2 and light>95:key='trim'
            elif light<75:key='robe_shadow'
            elif light<145:key='robe_mid'
            else:key='robe_light'
            if 0<=x+dx<128:result.putpixel((x+dx,y),c(key))
    return result


def garment(direction):
    im=Image.new('RGBA',(128,96));d=ImageDraw.Draw(im)
    if direction=='up':
        # Closed sleeves under a broad back mantle. No hands or striding legs.
        d.polygon([(55,59),(70,59),(77,64),(80,73),(76,80),(52,80),(48,74),(50,65)],fill=c('robe_mid'),outline=c('outline'))
        d.polygon([(71,63),(77,67),(78,73),(73,78),(68,76),(68,65)],fill=c('robe_shadow'))
        d.line([(54,65),(52,70),(53,74),(57,76)],fill=c('robe_light'),width=1)
        d.line([(75,68),(73,73),(69,75)],fill=c('outline'),width=1)
        d.polygon([(54,75),(73,75),(76,83),(80,91),(83,94),(78,95),(49,95),(45,93),(49,86),(52,80)],fill=c('robe_mid'),outline=c('outline'))
        d.polygon([(67,76),(72,77),(74,84),(79,93),(72,93),(68,87)],fill=c('robe_shadow'))
        d.polygon([(54,79),(58,77),(57,85),(52,92),(49,92),(52,85)],fill=c('robe_light'))
        d.line([(58,80),(59,86),(57,93)],fill=c('robe_shadow'),width=1)
        d.line([(72,82),(74,88),(77,92)],fill=c('robe_light'),width=1)
        d.line([(50,93),(58,94),(65,94),(74,94),(79,93)],fill=c('trim'),width=1)
        d.line([(64,69),(64,93)],fill=c('robe_shadow'),width=1)
        d.line([(63,77),(63,89)],fill=c('robe_light'),width=1)
        d.line([(55,62),(63,65),(71,62)],fill=c('trim'),width=2)
    else:
        # Profile view of the same long, closed robe; arm folds stay still.
        d.polygon([(59,59),(69,59),(75,64),(77,73),(73,81),(55,81),(52,75),(53,66)],fill=c('robe_mid'),outline=c('outline'))
        d.polygon([(70,63),(74,67),(75,73),(71,78),(67,76),(67,64)],fill=c('robe_shadow'))
        d.line([(57,66),(56,72),(59,76),(64,77)],fill=c('robe_light'),width=1)
        d.line([(57,70),(62,73),(69,71)],fill=c('robe_shadow'),width=1)
        d.polygon([(56,76),(71,76),(73,84),(77,91),(80,94),(76,95),(51,95),(48,93),(52,85)],fill=c('robe_mid'),outline=c('outline'))
        d.polygon([(67,78),(70,78),(72,86),(76,93),(69,93),(67,86)],fill=c('robe_shadow'))
        d.polygon([(55,80),(58,78),(57,87),(53,93),(51,93)],fill=c('robe_light'))
        d.line([(52,93),(61,94),(70,94),(76,93)],fill=c('trim'),width=1)
        d.line([(64,75),(64,93)],fill=c('robe_shadow'),width=1)
        d.line([(63,79),(63,89)],fill=c('robe_light'),width=1)
        d.line([(59,62),(65,65),(72,62)],fill=c('trim'),width=2)
    return im


def sway(base,amplitude):
    result=base.copy()
    for y in range(HEM_START,96):
        bend=amplitude*((y-HEM_START)/(95-HEM_START))**1.35
        for x in range(128):
            if 62<=x<=66:continue
            sx=round(x-bend*min(1,abs(x-AXIS)/13))
            result.putpixel((x,y),base.getpixel((sx,y))if 0<=sx<128 else(0,0,0,0))
    return result


def mirror(im):
    result=Image.new('RGBA',im.size)
    # Reflect around pixel-center x=64, not canvas-edge x=63.5.
    result.alpha_composite(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0));return result


def create():
    OUT.mkdir(exist_ok=True);data=json.loads((ROOT/'demos/gallery-data.json').read_text());mapping=json.loads(MAPPING.read_text());baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'mapping':mapping,'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'rules_hash':hashlib.sha256((ROOT.parents[1]/'actual/data/legacy/rules_full.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());old=next(s for s in before['mapping']['scenarios']if s['id']=='tactical-walk');idle=next(s for s in before['mapping']['scenarios']if s['id']=='tactical-idle')
    previous={int(rec['source_index']):Image.open((MAPPING.parent/rec['output_path']).resolve()).convert('RGBA')for rec in old['frame_mapping']}
    frames={};fixed={}
    for direction,slot,dx,source_slot in [('up',0,2,0),('right',2,10,2)]:
        base=garment(direction);base.alpha_composite(head(previous[source_slot],dx,direction));fixed[direction]=base
        frames[slot]=sway(base,-2);frames[slot+1]=sway(base,2)
    for index,phase in [(4,0),(5,2)]:
        reference=next(rec for rec in idle['frame_mapping']if rec['source_index']==phase)
        im=Image.open((MAPPING.parent/reference['output_path']).resolve()).convert('RGBA')
        plate=Image.new('RGBA',(128,96));plate.alpha_composite(im,(16,16));frames[index]=plate
    frames[6]=mirror(frames[2]);frames[7]=mirror(frames[3])
    inventory=[];records=[];atlas=Image.new('RGBA',(1024,96))
    for index,im in sorted(frames.items()):
        target=OUT/f'walk/frame-{index:03}.png';save(target,im,inventory,'friendly mage / approved warm closed robe; registered head and body, lower hem motion')
        atlas.alpha_composite(im,(index*128,0));record=copy.deepcopy(old['frame_mapping'][index]);record['previous_registration']=record.get('registration',{})
        record.update(output_path='../../../'+target.relative_to(ROOT).as_posix(),path='../../../'+target.relative_to(ROOT).as_posix(),
          size=[128,96],bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),alpha_bounds=list(im.getbbox()),
          registration={'basis':'Approved idle robe, seven-color warm palette, stationary upper body and anatomical center',
            'axis_x':64,'fixed_upper_y_exclusive':77,'fixed_seam_x_inclusive':[62,66],'foot_y_exclusive':96,
            'head_source_slot':0 if index<2 else 2 if index in [2,3,6,7]else None,
            'down_idle_reuse':index in [4,5],'down_idle_phase':0 if index==4 else 2 if index==5 else None,
            'mirror_axis':64 if index in [6,7]else None})
        records.append(record)
    save(OUT/'walk-atlas.png',atlas,inventory,'eight original source slots, consistent warm robe and stationary anatomical axes')
    for direction,im in fixed.items():save(OUT/f'source/fixed-{direction}.png',im,inventory,'shared unmoving head and upper robe for both '+direction+' phases')
    scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-walk')
    scenario.update(frame_mapping=records,output_atlas='../../../'+(OUT/'walk-atlas.png').relative_to(ROOT).as_posix(),revision=REVISION,
      status='review_candidate',review_note='沿用已确认的友方红棕金色七色闭袖长袍；四向均固定头部、上身、中轴与脚底，仅下半袍摆动。向下复用已确认待机袍摆。',
      action_note='本轮统一术法师战斗地图行走造型与已确认待机；头身固定，袍子遮住双臂，仅下半袍摆循环，原两姿势16帧节奏保持。',
      motion_review='../../../'+(OUT/'README.md').relative_to(ROOT).as_posix())
    MAPPING.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    manifest={'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'palette':PALETTE,'approved_idle_revision':idle['revision'],'idle_scenario_unchanged':True,
      'axis_x':64,'hem_start_y':77,'fixed_seam_x_inclusive':[62,66],'hem_amplitude_pixels':[-2,2],
      'foot_y_exclusive':96,'head_registration':{'up':{'source':0,'translation':[2,0]},'right':{'source':2,'translation':[10,0]},'left':{'mirror_right_about_x':64},'down':{'approved_idle_phases':[0,2],'translation':[16,16]}},'assets':inventory}
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'frames':len(frames),'assets':len(inventory),'approved_idle_unchanged':True},ensure_ascii=False))


if __name__=='__main__':create()
