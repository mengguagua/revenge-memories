#!/usr/bin/env python3
"""Import complete direction-preserving recolored militia walking poses."""
import argparse
import copy
import json
import colorsys
from functools import lru_cache
from PIL import Image, ImageDraw
import import_knight_redraw_v3 as art
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest

REV='militia-walk-flat-blue-v3-20261021'
OUT=ROOT/REV
IDLE=ROOT/'militia-idle-flat-archer-blue-v2-20261021'
RGB=lambda h:tuple(bytes.fromhex(h))
PAL=json.loads((IDLE/'asset-manifest.json').read_text())['palette']
COLORS=[RGB(h)for h in PAL]
DARK=RGB('172638');HAIR=RGB('79584c');BLUE=RGB('3976b5')
def near(rgb,colors):return min(colors,key=lambda c:sum((a-b)**2for a,b in zip(rgb,c)))
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

@lru_cache(maxsize=65536)
def approved_color(rgb):
    h,s,v=colorsys.rgb_to_hsv(*(c/255 for c in rgb))
    if .52<h<.69 and s>.40:return BLUE if v>.40 else DARK
    return near(rgb,COLORS)

def normalize(im):
    out=Image.new('RGBA',im.size)
    out.putdata([(*approved_color(p[:3]),255)if p[3]else(0,0,0,0)for p in im.getdata()])
    return out

def hair_center(im):
    px=im.load();pts=[(x,y)for y in range(round(im.height*.48))for x in range(im.width)if px[x,y][3]and px[x,y][:3]==HAIR]
    head=art.parts(pts)[0]
    return (min(x for x,y in head)+max(x for x,y in head)+1)/2

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());mapping=copy.deepcopy(baseline['mapping']);frames={}
    art.SRC=OUT/'source'
    figures=sorted(art.figures('six-walk-blue-white-master-v1.png',6),key=lambda f:f[1]['source_bounds'][1])
    figures=[f for n in range(0,6,2)for f in sorted(figures[n:n+2],key=lambda f:f[1]['source_bounds'][0])]
    for start in [0,2,4]:
        pair=figures[start:start+2];scale=64/max(fig[0].height for fig in pair)
        for i,(im,meta)in enumerate(pair,start):
            clean=normalize(im)
            frames[i]=art.register((clean,meta),(128,96),[hair_center(clean),0],[64.5,32],scale,f'walk-{i}')
    registration=art.REG
    for dst,src in [(6,2),(7,3)]:
        frames[dst]=Image.new('RGBA',(128,96))
        frames[dst].alpha_composite(frames[src].transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0))
    assets=[]
    def save(im,path,purpose):
        p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        return '../../../'+p.relative_to(ROOT).as_posix()
    scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-walk');atlas=Image.new('RGBA',(1024,96))
    for rec in scenario['frame_mapping']:
        i=rec['source_index'];target=save(frames[i],f'ally/frame-{i:03}.png','registered militia gait in accepted idle palette')
        rec.update(path=target,output_path=target,revision=REV,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],alpha_bounds=list(frames[i].getbbox()),
          registration=registration[i]if i<6 else{'derived_from':i-4,'method':'whole-canvas horizontal mirror plus one output pixel of anchor compensation'},art_status='review_candidate')
        atlas.alpha_composite(frames[i],(128*i,0))
    scenario.update(revision=REV,status='review_candidate',output_atlas=save(atlas,'ally/walk-atlas.png','four-direction eight-slot walking atlas'),
      review_note='同待机纯色棕发、弓箭手蓝和哑光白衣；完整姿势按固定头部参照登记，无整体上下位移。原双相腿部步态与16帧／相节奏保留。',
      action_note='四向统一待机色板，固定中心，保留原两相步态。',motion_review={'registration':registration,'palette':PAL,'runtime_integrated':False})
    assert mapping['scenarios'][1]==baseline['mapping']['scenarios'][1]
    write(OUT/'mapping-draft.json',mapping)
    if publish:write(ROOT/'professions/class-14-ally/maps/frame_mapping.json',mapping)
    idle=Image.open(IDLE/'ally/frame-001.png').convert('RGBA');idle_canvas=Image.new('RGBA',(128,96));idle_canvas.alpha_composite(idle,(16,16))
    for light in [False,True]:
        bg=(224,228,229)if light else(32,45,53);fg=(31,43,54)if light else(232,240,240)
        board=Image.new('RGB',(1120,812),bg);d=ImageDraw.Draw(board)
        d.text((560,24),'乡勇 · 四向行走与已确认待机配色',anchor='mm',font=font(22),fill=fg)
        entries=[(f'{["向上","向上","向右","向右","向下","向下","向左","向左"][i]} · 相位{i%2}',frames[i])for i in range(8)]+[('已确认待机配色',idle_canvas)]
        for n,(label,im)in enumerate(entries):
            x=n%4*280;y=48+n//4*252;large=im.resize((256,192),Image.Resampling.NEAREST);board.paste(large,(x+12,y),large)
            d.text((x+140,y+210),label,anchor='mt',font=font(16),fill=fg)
        save(board,f'poses-{"light"if light else"dark"}.png','four-direction phase and accepted idle palette review')
    write(OUT/'material-palette.json',{'source':'complete ImageGen recoloring of original walking poses, with accepted idle reference','palette_reference':IDLE.name,'palette':PAL,'registration':registration,'image_generation':'built-in image_gen','source_prompt':'source/prompt.json'})
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,'palette':PAL,'registration':registration,'assets':assets,'status':'pending_user_visual_acceptance'})
    print(json.dumps({'status':'published'if publish else'staged','assets':len(assets),'registered_whole_poses':len(registration)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
