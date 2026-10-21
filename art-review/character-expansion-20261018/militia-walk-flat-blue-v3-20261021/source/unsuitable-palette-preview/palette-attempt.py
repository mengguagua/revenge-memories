#!/usr/bin/env python3
"""Rebuild militia walking palette and register whole existing poses by the head."""
import argparse
import copy
import json
from PIL import Image, ImageDraw
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest

REV='militia-walk-flat-blue-v3-20261021'
OUT=ROOT/REV
IDLE=ROOT/'militia-idle-flat-archer-blue-v2-20261021'
OLD=ROOT/'professions/class-14-ally/maps/tactical-native-frames'
RGB=lambda h:tuple(bytes.fromhex(h))
PAL=json.loads((IDLE/'asset-manifest.json').read_text())['palette']
COLORS=[RGB(h)for h in PAL]
INK=RGB('1e2532');DARK=RGB('172638');HAIR=RGB('79584c');BLUE=RGB('3976b5')
WHITE=RGB('e4e1c8');SHADE=RGB('a7b6c8')
SKIN=[RGB(h)for h in ['c88b73','f0c6a0','ffe0b8']]
METAL=[RGB(h)for h in ['303a50','a7b6c8','d6e0e7','f5f4ec']]
BOXES={
 0:{'hair':(48,32,77,54),'face':(70,47,77,55),'hands':[(37,35,48,52),(69,57,80,67)],'steel':(73,47,85,61)},
 1:{'hair':(47,32,77,54),'face':(70,47,77,55),'hands':[(36,34,48,51),(69,55,80,66)],'steel':(72,46,85,60)},
 2:{'hair':(51,32,82,56),'face':(63,43,80,57),'hands':[(34,54,44,64),(70,53,82,64)],'steel':(76,36,88,57)},
 3:{'hair':(51,32,82,56),'face':(63,43,80,57),'hands':[(34,54,44,64),(70,53,83,64)],'steel':(76,36,89,57)},
 4:{'hair':(45,32,77,57),'face':(54,43,73,59),'hands':[(39,59,50,68),(70,42,83,59)],'steel':(37,49,49,64)},
 5:{'hair':(45,32,77,57),'face':(54,43,73,59),'hands':[(39,59,50,68),(70,42,83,59)],'steel':(37,49,49,64)}}

def inside(x,y,b):return b[0]<=x<b[2]and b[1]<=y<b[3]
def near(rgb,colors):return min(colors,key=lambda c:sum((a-b)**2for a,b in zip(rgb,c)))
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def recolor(im,i):
    b=BOXES[i];out=Image.new('RGBA',im.size);p=out.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,bb,a=im.getpixel((x,y))
            if a<128:continue
            rgb=(r,g,bb);bright=(r+g+bb)/3;warm=r>g*1.08 and g>bb*1.06
            skin=warm and r>145 and g>85 and bb>45
            if max(rgb)<58 or bright<43:c=INK
            elif inside(x,y,b['steel'])and not warm:c=near(rgb,METAL)
            elif skin and(inside(x,y,b['face'])or any(inside(x,y,h)for h in b['hands'])):c=near(rgb,SKIN)
            elif inside(x,y,b['hair']):c=HAIR
            elif y>=82:c=DARK
            elif warm:
                # Bare arms have peach values; the orange sash and brown vest
                # have much less blue and belong to the allied blue costume.
                if skin and bb>r*.48 and bright>125:c=near(rgb,SKIN)
                else:c=BLUE if bright>62 else DARK
            elif y>=68:c=WHITE if bright>76 else SHADE if bright>55 else DARK
            elif bright>135:c=WHITE
            elif bright>95:c=SHADE
            else:c=DARK
            p[x,y]=(*c,255)
    # Brown material above the neckline is a stable anatomical reference,
    # independent of the sword, outstretched hands and moving feet.
    head=[(x,y)for y in range(32,53)for x in range(43,84)if p[x,y][:3]==HAIR and p[x,y][3]]
    box=[min(x for x,y in head),min(y for x,y in head),max(x for x,y in head)+1,max(y for x,y in head)+1]
    center=(box[0]+box[2])/2;dx=round(64-center)
    shifted=Image.new('RGBA',im.size);shifted.alpha_composite(out,(dx,0))
    assert sum(v[3]>0 for v in out.getdata())==sum(v[3]>0for v in shifted.getdata())
    return shifted,{'source_frame':i,'translation':[dx,0],'source_hair_bounds':box,'target_head_x':64,'actual_head_x':center+dx,'head_top':32,'scale':1,'clipped_pixels':0,'method':'whole-pose integer translation; no limb deformation or body splice'}

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());mapping=copy.deepcopy(baseline['mapping']);frames={};registration=[]
    for i in range(6):
        frames[i],reg=recolor(Image.open(OLD/f'frame-{i:03}.png').convert('RGBA'),i);registration.append(reg)
    frames[6]=frames[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);frames[7]=frames[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    assets=[]
    def save(im,path,purpose):
        p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        return '../../../'+p.relative_to(ROOT).as_posix()
    scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-walk');atlas=Image.new('RGBA',(1024,96))
    for rec in scenario['frame_mapping']:
        i=rec['source_index'];target=save(frames[i],f'ally/frame-{i:03}.png','registered militia gait in accepted idle palette')
        rec.update(path=target,output_path=target,revision=REV,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],alpha_bounds=list(frames[i].getbbox()),
          registration=registration[i]if i<6 else{'derived_from':i-4,'method':'exact whole-canvas horizontal mirror'},art_status='review_candidate')
        atlas.alpha_composite(frames[i],(128*i,0))
    scenario.update(revision=REV,status='review_candidate',output_atlas=save(atlas,'ally/walk-atlas.png','four-direction eight-slot walking atlas'),
      review_note='同待机纯色棕发、弓箭手蓝和哑光白衣；头部参照固定，整姿势平移校准，无整体上下位移。原双相腿部步态与16帧／相节奏保留。',
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
    write(OUT/'material-palette.json',{'source':'existing full walking poses','palette_reference':IDLE.name,'palette':PAL,'material_regions':BOXES,'registration':registration,'new_drawing':False})
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,'palette':PAL,'registration':registration,'assets':assets,'status':'pending_user_visual_acceptance'})
    print(json.dumps({'status':'published'if publish else'staged','assets':len(assets),'registration':registration}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
