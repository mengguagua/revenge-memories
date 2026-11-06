#!/usr/bin/env python3
"""Native mounted-body registration and material recovery; accepted archer frozen."""
import argparse
import colorsys
import copy
import json
import math
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from build_gallery import ROOT, file_hash
from export_gallery import font
from revise_battle_appearance_20261031 import FACE

REV = 'mount-consistency-v2-20261101'
OUT = ROOT/REV
BASE = json.loads((OUT/'baseline.json').read_text())
OLDER = json.loads((ROOT/'battle-appearance-v1-20261031/baseline.json').read_text())
ASSETS = []
REG = []
NAVY = (23,38,56,255)
SCALE = {0:1,1:1,2:.88,3:1.21,4:.94,5:1.04,6:1,7:1,16:1,33:1,34:1,35:1}
HEAD_BOX = {0:[158,166,187,214],1:[124,153,155,204],2:[119,157,158,212],
            3:[127,165,153,204],4:[121,174,157,218],5:[124,152,154,199]}


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def save(im,name,purpose):
    path = OUT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    colors = sorted(set(im.getdata()))
    if im.mode == 'RGBA' and len(colors) <= 256:
        q = Image.new('P',im.size)
        q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-3*len(colors)))
        table = {c:i for i,c in enumerate(colors)}
        q.putdata([table[p] for p in im.getdata()])
        q.info['transparency'] = bytes(c[3] for c in colors)
        assert q.convert('RGBA').tobytes() == im.tobytes()
    else:
        q = im
    q.save(path,optimize=True)
    if name.split('/')[-1].startswith('frame-') and path.stat().st_size>=50000:
        subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','-q',str(path)],check=True)
        assert Image.open(path).convert('RGBA').tobytes()==im.convert('RGBA').tobytes()
    ASSETS.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,
                   'pixels':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path)})
    return '../../../'+path.relative_to(ROOT).as_posix()


def source(cid,f,older=False):
    data = OLDER if older else BASE
    return Image.open(ROOT/data['profiles'][str(cid)]['newFrames'][str(f)]).convert('RGBA')


def cavalry():
    guide = Image.open(OUT/'source/cavalry-dark-material-guide.png').convert('RGBA')
    poses = {}
    for n,key in enumerate(BASE['profiles']['1']['newFrames']):
        f = int(key)
        if f in [9,16]:
            n = 0
        im,old = source(1,f),source(1,f,True)
        cell = guide.crop((round(n%4*guide.width/4),round(n//4*guide.height/3),
                           round((n%4+1)*guide.width/4),round((n//4+1)*guide.height/3)))
        box = cell.getchannel('A').point(lambda a:255 if a>160 else 0).getbbox()
        oldbox = im.getbbox()
        cell = cell.crop(box).resize((oldbox[2]-oldbox[0],oldbox[3]-oldbox[1]),Image.Resampling.NEAREST)
        guide_mask = Image.new('L',im.size)
        for y in range(cell.height):
            for x in range(cell.width):
                r,g,b,a = cell.getpixel((x,y))
                h,s,v = colorsys.rgb_to_hsv(r/255,g/255,b/255)
                if a>160 and v<.39 and s<.4:
                    guide_mask.putpixel((x+oldbox[0],y+oldbox[1]),255)
        guide_mask = guide_mask.filter(ImageFilter.MaxFilter(7))
        # Protect the entire accepted rider; recover only actual dark neutral
        # pixels from the immutable original horse, guided by ImageGen materials.
        fx0,fy0,fx1,fy1 = FACE[f]
        cx = (fx0+fx1)/2
        rider = Image.new('L',im.size)
        dr = ImageDraw.Draw(rider)
        dr.rectangle((fx0-6,fy0-18,fx1+6,fy1+1),fill=255)
        dr.polygon([(cx-10,fy1-1),(cx+14,fy1-1),(cx+26,fy1+11),(cx+24,fy1+33),
                    (cx+12,fy1+30),(cx+14,fy1+65),(cx-2,fy1+65),(cx-6,fy1+28),(cx-12,fy1+22)],fill=255)
        q = im.copy()
        recovery = Image.new('L',im.size)
        count = 0
        for y in range(im.height):
            for x in range(im.width):
                a = old.getpixel((x,y))
                if not a[3]:
                    continue
                h,s,v = colorsys.rgb_to_hsv(*(c/255 for c in a[:3]))
                p = im.getpixel((x,y))
                pale = min(p[:3])>175 and max(p[:3])-min(p[:3])<38
                hair_zone = x>cx+35 or (x<cx+5 and y<fy1+25)
                extra_material = pale and ((hair_zone and v<.44) or (x>cx+35 and v<.57) or (y>fy1+55 and v<.42))
                guided = guide_mask.getpixel((x,y)) and not rider.getpixel((x,y))
                if s < .30 and v < .57 and (guided or extra_material):
                    q.putpixel((x,y),a)
                    recovery.putpixel((x,y),255)
                    count += 1
        assert q.getchannel('A').tobytes() == im.getchannel('A').tobytes()
        save(recovery,f'masks/cavalry-{f:03}.png','original charcoal mane/tail/hoof material recovery mask')
        poses[f] = q
        REG.append({'class_id':1,'frame':f,'recovered_pixels':count,
                    'alpha_and_positions_unchanged':True,'rider_protected':True,
                    'recovered_color_source':OLDER['profiles']['1']['newFrames'][key]})
    return poses


def transform(im,scale,pivot):
    # Native nearest-neighbour affine registration. Check the unclipped image
    # first, so no feather or hoof is silently lost at the sprite boundary.
    pad = 400
    canvas = Image.new('RGBA',(im.width+2*pad,im.height+2*pad))
    canvas.alpha_composite(im,(pad,pad))
    px,py = pivot[0]+pad,pivot[1]+pad
    q = canvas.transform(canvas.size,Image.Transform.AFFINE,
                         (1/scale,0,px-px/scale,0,1/scale,py-py/scale),Image.Resampling.NEAREST)
    full = q.getbbox()
    assert full is None or (full[0]>=pad and full[1]>=pad and full[2]<=pad+im.width and full[3]<=pad+im.height),full
    return q.crop((pad,pad,pad+im.width,pad+im.height))


def register_low_wing(im,scale,pivot):
    # Continuous inverse registration at the shoulder. The wide outer wing
    # retains its native horizontal span while the forequarters get the same
    # body correction in both axes. No cutout boundary or duplicate ink remains.
    shoulder = 196
    join = round(pivot[0]+(shoulder-pivot[0])*scale)
    left = im.transform(im.size,Image.Transform.AFFINE,
                        (1/scale,0,pivot[0]-pivot[0]/scale,0,1/scale,pivot[1]-pivot[1]/scale),Image.Resampling.NEAREST)
    right = im.transform(im.size,Image.Transform.AFFINE,
                         (1,0,shoulder-join,0,1/scale,pivot[1]-pivot[1]/scale),Image.Resampling.NEAREST)
    q = Image.new('RGBA',im.size)
    q.paste(left.crop((0,0,join,im.height)),(0,0))
    q.paste(right.crop((join,0,im.width,im.height)),(join,0))
    for y in range(im.height):
        for x in range(im.width):
            if im.getpixel((x,y))[3]:
                xx = pivot[0]+(x-pivot[0])*scale if x<shoulder else join+x-shoulder
                yy = pivot[1]+(y-pivot[1])*scale
                assert 0<=xx<im.width and 0<=yy<im.height,(x,y,xx,yy)
    return q


def pegasus():
    oldreg = json.loads((ROOT/'battle-appearance-v1-20261031/registration.json').read_text())['frames']
    oldreg = {r['frame']:r for r in oldreg if r['class_id']==3}
    layer = Image.open(ROOT/'battle-appearance-v1-20261031/layers/pegasus-canonical-head.png').convert('RGBA')
    specs = json.loads((ROOT/'battle-appearance-v1-20261031/source/pegasus-head-cells.json').read_text())
    specs = {int(r['frame']):r for r in specs}
    poses = {}
    for key in BASE['profiles']['3']['newFrames']:
        f = int(key)
        im = source(3,f)
        scale = SCALE[f]
        q = im.copy()
        face = specs[f]['face']
        pivot = [(face[0]+face[2])/2,(face[1]+face[3])/2]
        wings = None
        wing_at = [0,0]
        if scale != 1:
            dx,dy = oldreg[f]['translation']
            at = (163+dx,117+dy)
            # The accepted head stays one-to-one. Underpaint at the collar
            # avoids a gap when the separately registered torso gets larger.
            for y in range(layer.height):
                for x in range(layer.width):
                    if layer.getpixel((x,y))[3]:
                        gx,gy = at[0]+x,at[1]+y
                        q.putpixel((gx,gy),NAVY if gy>=face[3]-2 else (0,0,0,0))
            q = register_low_wing(q,scale,pivot) if f==3 else transform(q,scale,pivot)
            q.alpha_composite(layer,at)
        poses[f] = q
        reg = {'class_id':3,'frame':f,'body_uniform_scale':scale,'registration_pivot':pivot,
               'accepted_head_translation':oldreg[f]['translation'],'accepted_head_scale':1,
               'low_wing_registration':'continuous at x196 shoulder; native outer horizontal span' if f==3 else None,
               'no_clipped_pixels':True}
        if f in HEAD_BOX:
            bb = HEAD_BOX[f]
            reg['horse_skull_source_box'] = bb
            reg['horse_skull_registered_box'] = [round(pivot[i%2]+(v-pivot[i%2])*scale) for i,v in enumerate(bb)]
            reg['source_skull_visible_area'] = sum(p[3]>0 for p in im.crop(bb).getdata())
            reg['normalized_skull_visible_area_estimate'] = round(reg['source_skull_visible_area']*scale**2)
        REG.append(reg)
    return poses


def boards(cid,poses):
    for light in [False,True]:
        h = 440 if cid==3 else 315
        board = Image.new('RGB',(1440,3*h),(220,222,216) if light else (32,45,53))
        d = ImageDraw.Draw(board)
        for n,(f,im) in enumerate(poses.items()):
            x,y = n%4*360,n//4*h
            d.text((x+180,y+20),f'源姿势 {f}',font=font(17),anchor='mm',fill=(23,38,56) if light else (235,239,239))
            board.paste(im,(x+20,y+40),im)
        save(board,f'review/class-{cid}-'+('light' if light else 'dark')+'.png','native-size complete dark/light pose inspection')


def main(publish=False):
    for cid,poses in [(1,cavalry()),(3,pegasus())]:
        mapping = copy.deepcopy(BASE['mappings'][str(cid)])
        records = []
        for f,im in poses.items():
            path = save(im,f'class-{cid}/frame-{f:03}.png','native registered mounted animation pose')
            mapping['frame_mapping'][str(f)] = path
            records.append({'source_frame':f,'path':path,'size':list(im.size),
                            'bytes':(OUT/f'class-{cid}/frame-{f:03}.png').stat().st_size,
                            'sha256':file_hash(OUT/f'class-{cid}/frame-{f:03}.png')})
        atlas = Image.new('RGBA',(len(poses)*320,next(iter(poses.values())).height))
        for n,im in enumerate(poses.values()):
            atlas.alpha_composite(im,(n*320,0))
        mapping.update(previous_revision=mapping['revision'],revision=REV,status='review_candidate',
                       runtime_integrated=False,records=records,
                       output_atlas=save(atlas,f'class-{cid}/battle-atlas.png','offline full pose atlas'),
                       output_atlas_bytes=(OUT/f'class-{cid}/battle-atlas.png').stat().st_size,
                       review_note='保留白色马身和骑兵蓝白衣甲，仅恢复鬃毛、尾毛及蹄子原有深色。' if cid==1 else
                       '统一飞马各姿势的头颈、躯干和四肢比例，骑手已确认红发头部保持原尺寸；扑翼、攻防与结算节奏保留。',
                       qa_report='../../../'+REV+'/verification.json',
                       batches=[{'id':'坐骑体型／材质修订','review':'../../../'+REV+f'/review/class-{cid}-light.png','status':'pending_user_review'}])
        write(OUT/f'class-{cid}-mapping.json',mapping)
        boards(cid,poses)
        if publish:
            write(ROOT/BASE['profiles'][str(cid)]['mapping'],mapping)
    write(OUT/'registration.json',{'revision':REV,'frames':REG})
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':ASSETS,'runtime_integrated':False})
    write(OUT/'acceptance.json',{'archer':'user_accepted_20261101','archer_sprite_hashes':BASE['archer_files'],
                               'pegasus_hair':'user_accepted_20261101_preserved',
                               'cavalry_white_body_and_blue_white_uniform':'user_accepted_20261101_preserved',
                               'mount_body_and_dark_hair_hooves':'pending_user_review'})
    print(json.dumps({'published':publish,'poses':24}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--publish',action='store_true')
    main(p.parse_args().publish)
