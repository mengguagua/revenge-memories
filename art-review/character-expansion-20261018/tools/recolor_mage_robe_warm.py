#!/usr/bin/env python3
"""Palette-only correction: friendly mage warm red-brown and gold, unchanged pixels."""
import copy,hashlib,json
from PIL import Image
from build_gallery import ROOT
from revise_mage_robe_idle import save

REVISION='mage-robe-idle-warm-v2-20261021'
OUT=ROOT/REVISION
MAPPING=ROOT/'professions/class-15-ally/maps/frame_mapping.json'
OLD={'outline':'292b35','robe_shadow':'494856','robe_mid':'706777','robe_light':'a29aaa',
     'trim':'b7ac8b','skin_shadow':'957b69','skin':'d1b096'}
PALETTE={'outline':'30272a','robe_shadow':'633e3a','robe_mid':'9b5148','robe_light':'cf9070',
         'trim':'d0a85a','skin_shadow':'a77b60','skin':'e2b78d'}


def create():
    OUT.mkdir(exist_ok=True);data=json.loads((ROOT/'demos/gallery-data.json').read_text());mapping=json.loads(MAPPING.read_text())
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'mapping':mapping,'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'action':next(a for a in data['actions']if a['id']=='professions-class-15-ally-maps-tactical-idle--idle-cycle')},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-idle')
    previous=next(s for s in before['mapping']['scenarios']if s['id']=='tactical-idle')
    remap={tuple(bytes.fromhex(OLD[k])):tuple(bytes.fromhex(v))for k,v in PALETTE.items()};assets=[];records=[]
    atlas=Image.new('RGBA',(576,96))
    for index,old in enumerate(previous['frame_mapping']):
        source=(MAPPING.parent/old['output_path']).resolve();im=Image.open(source).convert('RGBA')
        im.putdata([(*remap[px[:3]],px[3])if px[3]else px for px in im.getdata()])
        target=OUT/f'frames/idle-{index:03}.png';save(target,im,assets,'friendly mage / warm seven-color palette; exact original contour and pose')
        atlas.alpha_composite(im,(index*96,0));record=copy.deepcopy(old)
        record.update(output_path='../../../'+target.relative_to(ROOT).as_posix(),path='../../../'+target.relative_to(ROOT).as_posix(),
          palette_source=source.relative_to(ROOT).as_posix(),color_revision=REVISION,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        records.append(record)
    save(OUT/'idle-atlas.png',atlas,assets,'warm recolor of six unchanged pose slots')
    scenario.update(frame_mapping=records,output_atlas='../../../'+(OUT/'idle-atlas.png').relative_to(ROOT).as_posix(),revision=REVISION,
      review_note='友方术法师采用红棕袍与金色饰边，恢复适中的暖色饱和度；七色简化保留。双臂藏袍、固定头身和中轴、下半袍摆动作逐像素保持。',
      action_note='友方不套用敌军蓝紫色：本轮恢复红棕与金色暖色，仅调整七色调色板；所有姿势、透明轮廓与时序沿用闭袖袍稿。',
      motion_review='../../../'+(OUT/'README.md').relative_to(ROOT).as_posix())
    MAPPING.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'chat_image_output':False,
      'image_generation_invoked':False,'palette_only':True,'previous_palette':OLD,'palette':PALETTE,'assets':assets},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'palette':PALETTE,'assets':len(assets)},ensure_ascii=False))


if __name__=='__main__':create()
