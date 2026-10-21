#!/usr/bin/env python3
"""Class-4 sideways four-stage gait and more tightly folded airborne rear view."""
import argparse
import copy
import json
from PIL import Image, ImageDraw
import import_knight_redraw_v3 as art
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest, translate

REV='knight-walk-paired-legs-v5-20261021'
OUT=ROOT/REV
IDLE=ROOT/'knight-idle-paired-legs-v4-20261021'

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text())
    art.SRC=OUT/'source'
    raw=art.figures('up-airborne-folded-master-v1.png',1)[0]
    # Keep the original 35px upper-body width, rather than enlarging the new
    # shorter airborne silhouette to the height of an extended leg pose.
    up=art.register(raw,(128,96),art.landmark(raw[0],True)[0],[64,26],35/raw[0].width,'up-airborne')
    assets=[]
    def save(im,path,purpose):
        p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        return '../../../'+p.relative_to(ROOT).as_posix()
    for side in ['ally','enemy']:
        path=ROOT/f'professions/class-4-{side}/maps/frame_mapping.json'
        original=baseline['mappings'][path.relative_to(ROOT).as_posix()]
        mapping=copy.deepcopy(original);scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-walk')
        poses={0:art.palette(up,side)}
        for source,index in [(0,6),(2,7),(1,8)]:
            im=Image.open(IDLE/f'{side}/frame-{source:03}.png').convert('RGBA')
            left=Image.new('RGBA',(128,96));left.alpha_composite(im,(16,16));poses[index]=left
        for dst,src in [(2,6),(3,7),(9,8)]:
            poses[dst]=translate(poses[src].transpose(Image.Transpose.FLIP_LEFT_RIGHT),[1,0])
        records={r['source_index']:r for r in scenario['frame_mapping']}
        for i,im in sorted(poses.items()):
            target=save(im,f'{side}/frame-{i:03}.png','tucked airborne rear view'if i==0 else 'side gait from complete corrected idle drawing')
            rec=copy.deepcopy(records.get(i,{}));rec.update(source_index=i,source_frame={8:6,9:2}.get(i,i),path=target,output_path=target,revision=REV,size=[128,96],bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],art_status='review_candidate')
            records[i]=rec
        scenario['frame_mapping']=[records[i]for i in sorted(records)]
        atlas=Image.new('RGBA',(128*10,96));images={}
        for i,rec in records.items():
            im=Image.open((path.parent/rec['output_path']).resolve()).convert('RGBA');images[i]=im
            atlas.alpha_composite(im,(128*i,0))
        scenario.update(revision=REV,output_atlas=save(atlas,f'{side}/walk-atlas.png','ten-slot gait atlas with additional standing poses'),
          direction_preview_cycles={'left':{'frames':[6,8,7,8],'frame_ticks':[8,8,8,8]},'right':{'frames':[2,9,3,9],'frame_ticks':[8,8,8,8]}},
          review_frame_sources={'8':6,'9':2},review_frame_labels={'8':'新增站定姿势 · 向左','9':'新增站定姿势 · 向右'},
          direction_action_notes={**scenario.get('direction_action_notes',{}),'left':'新稿前双腿抬起→四腿站定→后双腿向前抬起→四腿站定；每阶段8帧，保持原32帧总周期。','right':'新稿前双腿抬起→四腿站定→后双腿向前抬起→四腿站定；每阶段8帧，保持原32帧总周期。','up':'腾空相四腿向后收屈、抬高并部分遮挡；落地相保留。每相16帧，中心与阴影固定。'},
          review_note='左右四阶段双腿循环，每相8帧、总周期32帧；向上腾空相四腿向后收屈、减少露出。沿用固定中心与16色蓝白／蓝紫。',
          action_note='本轮修改左右四阶段和向上腾空姿势。',
          motion_review={'side_cycle_ticks':32,'side_phase_ticks':[8,8,8,8],'up_phase_ticks':[16,16],'runtime_integrated':False})
        assert mapping['scenarios'][0]==original['scenarios'][0]
        for i in [1,4,5]:assert records[i]==next(r for r in original['scenarios'][1]['frame_mapping']if r['source_index']==i)
        write(OUT/f'{side}-mapping-draft.json',mapping)
        if publish:write(path,mapping)
        for light in [False,True]:
            bg=(224,228,229)if light else(32,45,53);fg=(31,43,54)if light else(232,240,240)
            board=Image.new('RGB',(1120,812),bg);d=ImageDraw.Draw(board)
            d.text((560,25),('盟军骑士'if side=='ally'else'敌方骑士')+' · 行走修订',anchor='mm',font=font(22),fill=fg)
            entries=[('向左 · 前双腿抬起',6),('向左 · 四腿站定',8),('向左 · 后双腿向前抬起',7),('向左 · 四腿站定',8),('向右 · 前双腿抬起',2),('向右 · 四腿站定',9),('向右 · 后双腿向前抬起',3),('向右 · 四腿站定',9),('向上 · 四腿向后收屈',0),('向上 · 落地姿势',1)]
            for n,(label,i)in enumerate(entries):
                x=n%4*280;y=48+n//4*252;im=images[i].resize((256,192),Image.Resampling.NEAREST);board.paste(im,(x+12,y),im)
                d.text((x+140,y+210),label,anchor='mt',font=font(16),fill=fg)
            save(board,f'{side}-poses-{"light"if light else"dark"}.png','final directional phase review board')
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,'palette':{'ally':art.ALLY,'enemy':art.ENEMY},'registration':art.REG,'assets':assets,'side_phases':['front_pair_up','all_standing','rear_pair_forward_up','all_standing'],'side_phase_ticks':[8,8,8,8],'status':'pending_user_visual_acceptance'})
    print(json.dumps({'status':'published'if publish else'staged','assets':len(assets)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
