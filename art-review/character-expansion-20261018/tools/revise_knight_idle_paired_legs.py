#!/usr/bin/env python3
"""Replace only class-4 tactical idle with three complete redrawn leg poses."""
import argparse
import copy
import json
from PIL import Image, ImageDraw
import import_knight_redraw_v3 as art
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest

REV='knight-idle-paired-legs-v4-20261021'
OUT=ROOT/REV
PHASES=[0,1,2,1]
LABELS=['前双腿弯曲抬起','四腿站定','后双腿向前抬起','四腿站定']

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text())
    art.SRC=OUT/'source'
    raw=art.figures('map-idle-paired-legs-master-v1.png',3)
    # One scale for every complete figure, with the rider's face at one point.
    scale=64/raw[1][0].height
    poses=[art.register(fig,(96,96),art.landmark(fig[0])[0],[48,29],scale,f'idle-{i}') for i,fig in enumerate(raw)]
    assets=[]
    def save(im,path,purpose):
        p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        return '../../../'+p.relative_to(ROOT).as_posix()
    for side in ['ally','enemy']:
        path=ROOT/f'professions/class-4-{side}/maps/frame_mapping.json'
        original=baseline['mappings'][path.relative_to(ROOT.parent.parent).as_posix()]
        mapping=copy.deepcopy(original)
        scenario=next(s for s in mapping['scenarios'] if s['id']=='tactical-idle')
        colored=[art.palette(im,side) for im in poses]
        atlas=Image.new('RGBA',(576,96))
        for rec,i in zip(scenario['frame_mapping'],[0,1,2,1,0,1]):
            index=rec['source_index'];im=colored[i]
            target=save(im,f'{side}/frame-{index:03}.png','complete idle pose: '+LABELS[i])
            rec.update(path=target,output_path=target,revision=REV,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],size=[96,96],idle_pose=i)
            atlas.alpha_composite(im,(96*index,0))
        scenario.update(revision=REV,output_atlas=save(atlas,f'{side}/idle-atlas.png','six-slot tactical idle atlas'),
          review_note='双前腿弯曲抬起、四腿站定、双后腿向前抬起、四腿站定；固定骑手面部中心，沿用16色配色与原14／8／14／8帧节奏。',
          action_note='前双腿抬起→四腿站定→后双腿向前抬起→四腿站定。',
          motion_review={'registration':'one scale and one face anchor for complete drawings','phase_order':PHASES,'phase_ticks':[14,8,14,8],'runtime_integrated':False})
        assert scenario['timing']==next(s for s in original['scenarios'] if s['id']=='tactical-idle')['timing']
        assert next(s for s in mapping['scenarios'] if s['id']=='tactical-walk')==next(s for s in original['scenarios'] if s['id']=='tactical-walk')
        write(OUT/f'{side}-mapping-draft.json',mapping)
        if publish:write(path,mapping)
        for light in [False,True]:
            bg=(224,228,229) if light else (32,45,53);fg=(31,43,54) if light else (232,240,240)
            board=Image.new('RGB',(896,304),bg);d=ImageDraw.Draw(board)
            d.text((448,25),('盟军骑士' if side=='ally' else '敌方骑士')+' · 待机四阶段',anchor='mm',font=font(22),fill=fg)
            for n,i in enumerate(PHASES):
                im=colored[i].resize((192,192),Image.Resampling.NEAREST);board.paste(im,(16+224*n,51),im)
                d.text((112+224*n,257),str(n+1)+' · '+LABELS[n],anchor='mt',font=font(16),fill=fg)
                d.text((112+224*n,283),str([14,8,14,8][n])+' 帧',anchor='mm',font=font(13),fill=fg)
            save(board,f'{side}-four-stages-{"light" if light else "dark"}.png','four-stage visual review board')
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,'palette':{'ally':art.ALLY,'enemy':art.ENEMY},'registration':art.REG,'assets':assets,'phase_order':PHASES,'phase_ticks':[14,8,14,8],'status':'pending_user_visual_acceptance'})
    print(json.dumps({'status':'published' if publish else 'staged','whole_poses':3,'assets':len(assets)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
