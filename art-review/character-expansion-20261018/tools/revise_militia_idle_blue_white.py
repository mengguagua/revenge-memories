#!/usr/bin/env python3
"""Register whole militia idle poses and publish only the allied idle scenario."""
import argparse
import copy
import json
from functools import lru_cache
from PIL import Image, ImageDraw
import import_knight_redraw_v3 as art
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest

REV='militia-idle-blue-white-v1-20261021'
OUT=ROOT/REV
PALETTE=['1e2532','303a50','473638','79584c','ad8570','c88b73','f0c6a0','ffe0b8',
         '304461','536f92','8b9fba','a7b6c8','d6e0e7','f5f4ec','607569','746758']
COLORS=[tuple(bytes.fromhex(c))for c in PALETTE]

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def face_landmark(im):
    # Bright skin below the fringe, excluding sleeves and most hair highlights.
    px=im.load();pts=[]
    for y in range(round(im.height*.38)):
        for x in range(im.width):
            r,g,b,a=px[x,y]
            if a and r>235 and 135<g<220 and 90<b<180 and r-g>32:pts.append((x,y))
    largest=art.parts(pts)[0]
    b=[min(x for x,y in largest),min(y for x,y in largest),max(x for x,y in largest)+1,max(y for x,y in largest)+1]
    return [(b[0]+b[2])/2,(b[1]+b[3])/2]

@lru_cache(maxsize=65536)
def color(rgb):
    return min(COLORS,key=lambda c:sum((x-y)**2for x,y in zip(rgb,c)))

def palette(im):
    out=Image.new('RGBA',im.size)
    out.putdata([(*color(p[:3]),255)if p[3]else(0,0,0,0)for p in im.getdata()])
    return out

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());mapping=copy.deepcopy(baseline['mapping'])
    art.SRC=OUT/'source';raw=art.figures('three-idle-blue-white-master-v1.png',3)
    scale=64/raw[0][0].height
    poses=[palette(art.register(fig,(96,96),face_landmark(fig[0]),[48.5,34],scale,f'idle-{i}'))for i,fig in enumerate(raw)]
    assets=[]
    def save(im,path,purpose):
        p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        return '../../../'+p.relative_to(ROOT).as_posix()
    scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-idle');atlas=Image.new('RGBA',(576,96))
    for rec,i in zip(scenario['frame_mapping'],[0,1,2,1,0,1]):
        index=rec['source_index'];target=save(poses[i],f'ally/frame-{index:03}.png','allied militia whole idle pose')
        rec.update(path=target,output_path=target,revision=REV,size=[96,96],bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],alpha_bounds=list(poses[i].getbbox()),registration=art.REG[i],art_status='review_candidate')
        atlas.alpha_composite(poses[i],(96*index,0))
    scenario.update(revision=REV,status='review_candidate',output_atlas=save(atlas,'ally/idle-atlas.png','six-slot idle atlas'),
        review_note='头部面部参照固定登记，同一比例、无整帧位移；16色蓝白服装，白衬衣与白裤增加白色，头发与少量皮革保留自然色。',
        action_note='固定人物中心，原三姿势、0／1／2／1循环与14／8／14／8帧时长保留。',
        motion_review={'registration':'one scale and common bright-face center on complete poses','target_face_center':[48.5,34],'whole_frame_offsets':[0,0],'palette':PALETTE,'runtime_integrated':False})
    assert next(s for s in mapping['scenarios']if s['id']=='tactical-walk')==next(s for s in baseline['mapping']['scenarios']if s['id']=='tactical-walk')
    write(OUT/'mapping-draft.json',mapping)
    if publish:write(ROOT/'professions/class-14-ally/maps/frame_mapping.json',mapping)
    old=next(s for s in baseline['mapping']['scenarios']if s['id']=='tactical-idle')
    for light in [False,True]:
        bg=(224,228,229)if light else(32,45,53);fg=(31,43,54)if light else(232,240,240)
        board=Image.new('RGB',(672,540),bg);d=ImageDraw.Draw(board)
        d.text((336,24),'乡勇 · 待机中心与蓝白配色',anchor='mm',font=font(22),fill=fg)
        for i,im in enumerate(poses):
            rec=next(a for a in old['frame_mapping']if a['source_index']==i)
            before=Image.open((ROOT/'professions/class-14-ally/maps'/rec['output_path']).resolve()).convert('RGBA')
            for row,img,label in [(0,before,'修改前'),(1,im,'本轮蓝白')]:
                y=48+row*242;large=img.resize((192,192),Image.Resampling.NEAREST);board.paste(large,(16+224*i,y),large)
                d.text((112+224*i,y+206),label+' · 姿势 '+str(i),anchor='mt',font=font(16),fill=fg)
        save(board,f'poses-{"light"if light else"dark"}.png','before/after full pose review board')
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,'scope':'existing allied militia tactical idle only; enemy palette policy retained','palette':PALETTE,'registration':art.REG,'assets':assets,'status':'pending_user_visual_acceptance'})
    print(json.dumps({'status':'published'if publish else'staged','whole_poses':3,'assets':len(assets)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
