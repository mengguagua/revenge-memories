#!/usr/bin/env python3
"""Rebuild indexed militia colors with matte materials; preserve every alpha pixel."""
import argparse
import copy
import json
from PIL import Image, ImageDraw
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest

REV='militia-idle-flat-archer-blue-v2-20261021'
OUT=ROOT/REV
SOURCE=ROOT/'militia-idle-blue-white-v1-20261021'
ARCHER=ROOT/'body-volume-motion-20261018/deliverables/class-12-ally/idle-00.png'
RGB=lambda h:tuple(bytes.fromhex(h))
BLUE=RGB('3976b5')
BLUE_SHADOW=RGB('172638')
HAIR=RGB('79584c')
CLOTH=RGB('e4e1c8')
CLOTH_SHADOW=RGB('a7b6c8')
OLD=json.loads((SOURCE/'asset-manifest.json').read_text())['palette']
INDEX={RGB(c):i for i,c in enumerate(OLD)}
# These boxes contain the blade and its guard, excluding the torso; cool
# connected pixels inside are kept as steel rather than treated as fabric.
WEAPON_BOXES=[(17,34,36,53),(27,31,36,59),(39,33,44,57)]

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def material_colors(im,phase):
    src=im.load();out=im.copy();dst=out.load();weapon=set()
    x0,y0,x1,y1=WEAPON_BOXES[phase]
    for y in range(y0,y1):
        for x in range(x0,x1):
            if src[x,y][3]and INDEX[src[x,y][:3]]in [1,8,9,10,11,12,13,14]:weapon.add((x,y))
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=src[x,y]
            if not a:continue
            index=INDEX[(r,g,b)];c=(r,g,b)
            if y<28 and index!=0:
                # All opaque non-outline pixels above the forehead are hair,
                # including peach-colored generated sheen in the old palette.
                c=HAIR
            elif y<38 and index in [2,3,4]:c=HAIR
            elif index==15:c=HAIR
            elif index==2:c=BLUE_SHADOW
            elif index==4:c=RGB('c88b73')
            elif y>=38 and(x,y)not in weapon:
                if index in [8,9,10]:c=BLUE_SHADOW if y>=70 else BLUE
                elif index==1:c=BLUE_SHADOW
                elif index in [12,13]:c=CLOTH
                elif index==11:c=CLOTH_SHADOW
            dst[x,y]=(*c,a)
    assert out.getchannel('A').tobytes()==im.getchannel('A').tobytes()
    assert all(out.getpixel(p)==im.getpixel(p)for p in weapon)
    return out,weapon

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());mapping=copy.deepcopy(baseline['mapping']);assets=[]
    poses=[];protected=[]
    for i in range(3):
        im=Image.open(SOURCE/f'ally/frame-{i:03}.png').convert('RGBA');flat,weapon=material_colors(im,i);poses.append(flat);protected.append(len(weapon))
    def save(im,path,purpose):
        p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
        return '../../../'+p.relative_to(ROOT).as_posix()
    scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-idle');atlas=Image.new('RGBA',(576,96))
    for rec,i in zip(scenario['frame_mapping'],[0,1,2,1,0,1]):
        index=rec['source_index'];target=save(poses[i],f'ally/frame-{index:03}.png','matte material palette, same indexed pose geometry')
        rec.update(path=target,output_path=target,revision=REV,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'])
        atlas.alpha_composite(poses[i],(96*index,0))
    scenario.update(revision=REV,output_atlas=save(atlas,'ally/idle-atlas.png','six-slot matte idle atlas'),
        review_note='棕发平涂，去除头发和布料高光；主蓝色复用盟军弓箭手待机#3976b5，保留暗部、白衣和原轮廓。',
        action_note='仅修改材质色板，三姿势轮廓、固定中心及原循环完全保留。')
    palette=sorted({p[:3]for im in poses for p in im.getdata()if p[3]})
    scenario['motion_review'].update(palette_revision=REV,palette=['%02x%02x%02x'%p for p in palette])
    write(OUT/'mapping-draft.json',mapping)
    if publish:write(ROOT/'professions/class-14-ally/maps/frame_mapping.json',mapping)
    archer=Image.open(ARCHER).convert('RGBA')
    for light in [False,True]:
        bg=(224,228,229)if light else(32,45,53);fg=(31,43,54)if light else(232,240,240)
        board=Image.new('RGB',(896,540),bg);d=ImageDraw.Draw(board)
        d.text((448,24),'乡勇 · 纯色头发、哑光衣料与弓箭手蓝色',anchor='mm',font=font(22),fill=fg)
        for col in range(4):
            old=Image.open(SOURCE/f'ally/frame-{col:03}.png').convert('RGBA')if col<3 else archer
            new=poses[col]if col<3 else archer
            for row,im in enumerate([old,new]):
                y=48+242*row;large=im.resize((192,192),Image.Resampling.NEAREST);board.paste(large,(16+224*col,y),large)
                label=('修改前'if row==0 else'本轮平涂')+f' · 姿势{col}'if col<3 else'弓箭手待机 · 配色参照'
                d.text((112+224*col,y+206),label,anchor='mt',font=font(16),fill=fg)
        save(board,f'poses-{"light"if light else"dark"}.png','before/after matte materials and archer palette reference')
    write(OUT/'material-palette.json',{'method':'editable indexed palette parameters; no new drawing or image generation',
        'source_revision':SOURCE.name,'archer_reference':ARCHER.relative_to(ROOT).as_posix(),'archer_sha256':digest(ARCHER),
        'blue':'3976b5','blue_shadow':'172638','hair_flat':'79584c','white_cloth':'e4e1c8','cloth_shadow':'a7b6c8',
        'hair_cap_below_y':28,'hair_fringe_below_y':38,'protected_steel_boxes':WEAPON_BOXES,'protected_steel_pixel_counts':protected})
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,'source_revision':SOURCE.name,'palette':['%02x%02x%02x'%p for p in palette],'assets':assets,
        'alpha_and_pose_pixels_preserved':True,'registration':json.loads((SOURCE/'asset-manifest.json').read_text())['registration'],'status':'pending_user_visual_acceptance'})
    print(json.dumps({'status':'published'if publish else'staged','assets':len(assets),'colors':len(palette)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
