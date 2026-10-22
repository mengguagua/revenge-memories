#!/usr/bin/env python3
"""Register newly drawn, independently yawed swordmaster side-walk poses."""
import argparse, copy, json
from pathlib import Path
from PIL import Image, ImageDraw
from build_gallery import ROOT, file_hash
from export_gallery import font
from import_knight_redraw_v3 import parts
import import_swordmaster_complete as art

REV = 'swordmaster-side-turn-v2-20261022'
OUT = ROOT / REV
SRC = OUT / 'source'
ASSETS = []
REG = []

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def save(im, path, purpose):
    path.parent.mkdir(parents=True, exist_ok=True)
    if im.mode == 'RGBA':
        colors = sorted(set(im.getdata()))
        assert len(colors) <= 256
        q = Image.new('P', im.size)
        q.putpalette([v for c in colors for v in c[:3]] + [0] * (768 - 3 * len(colors)))
        indices = {c:i for i,c in enumerate(colors)}
        q.putdata([indices[c] for c in im.getdata()])
        q.info['transparency'] = bytes(c[3] for c in colors)
        assert q.convert('RGBA').tobytes() == im.tobytes()
    else:
        q = im
    q.save(path, optimize=True)
    record = {'path':path.relative_to(ROOT).as_posix(), 'size':list(im.size),
              'bytes':path.stat().st_size, 'sha256':file_hash(path), 'purpose':purpose}
    ASSETS.append(record)
    return '../../../' + record['path']

def whole_figures(name):
    art.helper.SRC = SRC
    raw = art.helper.figures(name, 2)
    return [(art.quant(im), meta) for im,meta in raw]

def register_pair(name, ids, inspect=False):
    raw = whole_figures(name)
    # Belt buckle is a body landmark, unlike an expressive face or a moving foot.
    # Explicit source coordinates are recorded after inspecting each generated pair.
    config = json.loads((SRC/'registration.json').read_text())[name]
    result = {}
    for n,(i,(im,meta),landmark) in enumerate(zip(ids,raw,config['belt_points'])):
        # Flatten generated hair/skin glints to the two approved head materials.
        hb=config['hair_boxes'][n]
        fb=art.face(im)[1]
        for y in range(hb[1],hb[3]):
            for x in range(hb[0],hb[2]):
                p=im.getpixel((x,y))
                if not p[3]:continue
                rgb=p[:3]
                if rgb in [art.C[0],art.C[1],art.C[4]]:rgb=art.C[0]
                elif rgb==art.C[5] or (fb[0]<=x<fb[2] and fb[1]<=y<fb[3]):rgb=art.C[3]
                im.putpixel((x,y),(*rgb,255))
        scale = config['scale']
        dims = [round(im.width*scale),round(im.height*scale)]
        small = im.resize(dims,Image.Resampling.NEAREST)
        at = [round(config['target_belt'][j]-landmark[j]*dims[j]/im.size[j]) for j in range(2)]
        out = Image.new('RGBA',(128,96));out.alpha_composite(small,tuple(at))
        assert sum(p[3]>0 for p in small.getdata()) == sum(p[3]>0 for p in out.getdata()), ('clipped',i)
        components = parts((x,y) for y in range(96) for x in range(128) if out.getpixel((x,y))[3])
        for c in components[1:]:
            assert len(c)<=3, ('detached body part',i,len(c))
            for xy in c:out.putpixel(xy,(0,0,0,0))
        result[i] = out
        REG.append({**meta,'slot':i,'scale':scale,'dimensions':dims,'belt_point':landmark,
                    'target_belt':config['target_belt'],'translation':at,'clipped_pixels':0,
                    'method':'uniform scale and integer translation of the newly drawn whole pose'})
    # Both native leg phases share one upper-body hold. Reuse the new turned
    # upper pose at the waist seam rather than add a global head/chest bounce.
    split = config.get('fixed_upper_end_y')
    if split:
        a,b = ids
        result[b].paste(result[a].crop((0,0,128,split)),(0,0))
    return result

def board(frames, light):
    bg = (220,222,216) if light else (32,45,53)
    fg = (23,38,56) if light else (235,243,242)
    im = Image.new('RGB',(1280,730),bg);d=ImageDraw.Draw(im)
    d.text((640,26),'剑豪 · 左右转身与两相步幅',anchor='mm',font=font(22),fill=fg)
    labels={2:'右 · 展步',3:'右 · 交叉步',6:'左 · 展步',7:'左 · 交叉步'}
    for row,side in enumerate(['ally','enemy']):
        for col,i in enumerate([2,3,6,7]):
            sprite=frames[side,i].resize((384,288),Image.Resampling.NEAREST)
            x=col*320-32;y=40+row*350
            im.paste(sprite,(x,y),sprite)
            label=('盟军' if side=='ally' else '敌方')+' · '+labels[i]
            lb=d.textbbox((0,0),label,font=font(18))
            assert lb[2]-lb[0]<288
            d.text((col*320+160,350+row*350),label,anchor='mm',font=font(18),fill=fg)
    save(im,OUT/f'side-turn-{"light" if light else "dark"}.png','full new side poses on light/dark background')

def build(publish=False):
    b=json.loads((OUT/'baseline.json').read_text())
    if not (SRC/'registration.json').exists():
        for name in ['right-master.png','left-master.png']:
            for im,meta in whole_figures(name):
                print(name, im.size, meta['source_bounds'], 'face',art.face(im),flush=True)
                save(im,SRC/(name.replace('-master','')+'-'+str(meta['source_bounds'][0])+'.png'),'quantized whole drawing for registration inspection')
        return
    poses={**register_pair('right-master.png',[2,3]),**register_pair('left-master.png',[6,7])}
    mappings={};frames={}
    note='左右行走重绘完整转身姿态：胸腹、肩线、持剑臂与腰胯一起朝行进方向转出透视；展步／交叉步按原槽，固定身体基准。'
    for side in ['ally','enemy']:
        m=copy.deepcopy(b['mappings'][side]);s=next(s for s in m['scenarios'] if s['id']=='tactical-walk')
        atlas=Image.new('RGBA',(1024,96))
        for r in s['frame_mapping']:
            i=r['source_index']
            if i in poses:
                im=art.faction(poses[i],side)
                path=save(im,OUT/side/f'walk-{i:02}.png','new whole-body perspective turn and source two-phase leg pose')
                r.update(path=path,output_path=path,revision=REV,bytes=ASSETS[-1]['bytes'],sha256=ASSETS[-1]['sha256'],size=[128,96])
                frames[side,i]=im
            else:
                im=Image.open((ROOT/f'professions/class-10-{side}/maps'/r['path']).resolve()).convert('RGBA')
            atlas.alpha_composite(im,(i*128,0))
        s.update(output_atlas=save(atlas,OUT/side/'tactical-walk-atlas.png','unchanged native eight-slot order; four side slots replaced'),revision=REV,review_note=note)
        for key in ['walk-right','walk-left']:
            s.setdefault('motion_review',{}).setdefault('stable_regions',{}).pop(key,None)
        s.setdefault('motion_review',{})['side_turn_revision']={'revision':REV,'native_slots':[2,3,6,7],'registration':REG,'source_timing_modified':False,'same_native_weapon_and_cape_sides':True,'fixed_upper_body_hold':True}
        mappings[f'professions/class-10-{side}/maps/frame_mapping.json']=m
        # Refresh the full map pose board so its old side frames cannot be
        # mistaken for the current drawings via the gallery's general links.
        entries=[]
        for scene in m['scenarios']:
            for row in scene['frame_mapping']:
                i=row['source_index']
                if scene['id']=='tactical-idle' and i>=3:continue
                img=Image.open((ROOT/f'professions/class-10-{side}/maps'/row['path']).resolve()).convert('RGBA')
                label=('待机' if scene['id']=='tactical-idle' else ['上','上','右','右','下','下','左','左'][i])+f' {i}'
                entries.append((label,img))
        old_out=art.OUT;art.OUT=OUT;old_count=len(art.ASSETS)
        for light in [False,True]:art.board(entries,side,'maps',light)
        ASSETS.extend(art.ASSETS[old_count:])
        art.OUT=old_out
    for light in [False,True]:board(frames,light)
    write(OUT/'mapping-drafts.json',mappings)
    write(OUT/'asset-manifest.json',{'revision':REV,'generator':'built-in image_gen','palette':{'ally':art.HEX,'enemy':art.EHEX},'assets':ASSETS,'registration':REG,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for path,m in mappings.items():write(ROOT/path,m)
    print(json.dumps({'frames':8,'assets':len(ASSETS),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
