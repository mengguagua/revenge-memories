#!/usr/bin/env python3
"""Import two whole drawn side poses with a folded empty arm."""
import argparse
import copy
import json
from pathlib import Path
from PIL import Image, ImageDraw
import import_knight_redraw_v3 as art
from revise_militia_walk_flat_blue import normalize, hair_center, PAL, write
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest

REV = 'militia-side-bent-arm-v4-20261021'
OUT = ROOT / REV
MAP = ROOT / 'professions/class-14-ally/maps/frame_mapping.json'

def build(publish=False):
    baseline = json.loads((OUT/'baseline-mapping.json').read_text())
    mapping = copy.deepcopy(baseline)
    scenario = next(s for s in mapping['scenarios'] if s['id']=='tactical-walk')
    old = {r['source_index']:r for r in scenario['frame_mapping']}
    art.SRC = OUT/'source'
    raw = art.figures('side-bent-arm-master-v1.png',2)
    scale = 64/max(im.height for im,meta in raw)
    frames = {}
    art.REG.clear()
    for i,(im,meta) in zip([2,3],raw):
        clean=normalize(im)
        frames[i]=art.register((clean,meta),(128,96),[hair_center(clean),0],
                              [64.5,32],scale,f'walk-{i}')
    registration = copy.deepcopy(art.REG)
    for dst,src in [(6,2),(7,3)]:
        frames[dst]=Image.new('RGBA',(128,96))
        frames[dst].alpha_composite(frames[src].transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0))
    assets=[]
    def save(im,name,purpose):
        p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,
                       'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        return '../../../'+p.relative_to(ROOT).as_posix()
    for i in [2,3,6,7]:
        target=save(frames[i],f'ally/frame-{i:03}.png','side walk with bent tucked empty arm')
        reg=registration[i-2] if i<4 else {'derived_from':i-4,'method':'whole-canvas horizontal mirror plus one output pixel of anchor compensation'}
        old[i].update(path=target,output_path=target,revision=REV,
                      bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],
                      alpha_bounds=list(frames[i].getbbox()),registration=reg,
                      art_status='review_candidate')
    atlas=Image.new('RGBA',(1024,96))
    for i in range(8):
        if i not in frames:
            frames[i]=Image.open((MAP.parent/old[i]['output_path']).resolve()).convert('RGBA')
        atlas.alpha_composite(frames[i],(128*i,0))
    scenario.update(revision=REV,status='review_candidate',
        output_atlas=save(atlas,'ally/walk-atlas.png','eight-slot atlas; up and down preserved'),
        review_note='左右行走空手臂改为屈肘收拢、拳头靠近腰腹，保留持剑手和原双相腿部步态；固定头部中心，沿用已确认待机色板。向上、向下及待机保持。',
        action_note='左右行走空手臂屈肘收近身体，保持两相步态与原节奏。',
        motion_review={'registration':registration,'palette':PAL,'runtime_integrated':False,
                       'changed_source_indices':[2,3,6,7]})
    assert mapping['scenarios'][1]==baseline['scenarios'][1]
    for i in [0,1,4,5]:
        assert old[i]==next(r for r in baseline['scenarios'][0]['frame_mapping'] if r['source_index']==i)
    write(OUT/'mapping-draft.json',mapping)
    for light in [False,True]:
        bg=(220,222,216) if light else (32,45,53)
        fg=(30,43,56) if light else (232,240,240)
        board=Image.new('RGB',(1024,304),bg);d=ImageDraw.Draw(board)
        d.text((512,26),'乡勇 · 左右行走空手屈肘',anchor='mm',font=font(22),fill=fg)
        for n,i in enumerate([6,7,2,3]):
            large=frames[i].resize((256,192),Image.Resampling.NEAREST)
            board.paste(large,(n*256,56),large)
            d.text((n*256+128,266),f'{"向左" if i>5 else "向右"} · 相位{i%2}',anchor='mm',font=font(16),fill=fg)
        save(board,f'poses-{"light" if light else "dark"}.png','side pose anatomy on light/dark backgrounds')
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,
          'palette':PAL,'registration':registration,'assets':assets,
          'status':'pending_user_visual_acceptance'})
    if publish:write(MAP,mapping)
    print(json.dumps({'status':'published' if publish else 'staged','assets':len(assets),
                      'registration':registration},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true')
    build(p.parse_args().publish)
