#!/usr/bin/env python3
"""Register the ImageGen left-profile head; preserve approved map pose pixels."""
import argparse, copy, json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
from build_gallery import ROOT, file_hash
from export_gallery import font
from import_knight_redraw_v3 import parts
from rebuild_swordsman_maps import COLORS, ENEMY, faction

REV='swordsman-left-profile-v3-20261022'
OUT=ROOT/REV
OLD=ROOT/'swordsman-map-native-v2-20261022'
BOX=(45,32,67,54)

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def save(im, path):
    path.parent.mkdir(parents=True,exist_ok=True)
    colors=sorted(set(im.getdata()));q=Image.new('P',im.size)
    q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-3*len(colors)))
    table={p:i for i,p in enumerate(colors)};q.putdata([table[p]for p in im.getdata()])
    q.info['transparency']=bytes(c[3]for c in colors)
    assert q.convert('RGBA').tobytes()==im.tobytes()
    q.save(path,optimize=True)
    return {'path':path.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path)}

def build(publish=False):
    if not (OUT/'baseline.json').exists():
        d=json.loads((ROOT/'demos/gallery-data.json').read_text())
        write(OUT/'baseline.json',{'actions':{a['id']:a for a in d['actions']},'mappings':{side:json.loads((ROOT/f'professions/class-9-{side}/maps/frame_mapping.json').read_text())for side in['ally','enemy']}})
    base=json.loads((OUT/'baseline.json').read_text())
    # The only new drawing comes from the saved ImageGen edit. Crop its head,
    # snap to the existing two head materials and register once for both phases.
    raw=Image.open(OUT/'source/left-head-master.png').convert('RGBA').crop((532,330,770,574))
    raw=raw.resize((22,22),Image.Resampling.NEAREST)
    head=Image.new('RGBA',raw.size)
    head.putdata([(*min([COLORS[0],COLORS[3]],key=lambda c:sum((p[i]-c[i])**2 for i in range(3))),255)if p[3]>=128 else(0,0,0,0)for p in raw.getdata()])
    assets=[save(head,OUT/'source/registered-head.png')];frames={};checks=[];mappings={}
    for side in['ally','enemy']:
        mapping=copy.deepcopy(base['mappings'][side]);scene=next(s for s in mapping['scenarios']if s['id']=='tactical-walk')
        for i in[6,7]:
            old=Image.open(OLD/side/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA');new=old.copy()
            patch=faction(head,side)
            new.paste((0,0,0,0),BOX);new.alpha_composite(patch,BOX[:2])
            # The original sword crosses the foreground at the lower left;
            # shield edge occludes the back of the head. Preserve those pixels.
            for y in range(BOX[1],BOX[3]):
                for x in range(BOX[0],BOX[2]):
                    if (x<48 and y>=43) or (x>=64 and y>=36):new.putpixel((x,y),old.getpixel((x,y)))
            diff=ImageChops.difference(old,new).getbbox()
            # ImageChops RGBA getbbox ignores RGB-only changes; compare all channels.
            diff=ImageChops.difference(old,new).convert('RGB').getbbox()
            assert diff and diff[0]>=BOX[0]and diff[1]>=BOX[1]and diff[2]<=BOX[2]and diff[3]<=BOX[3]
            cs=parts((x,y)for y in range(new.height)for x in range(new.width)if new.getpixel((x,y))[3])
            assert len(cs)==1,(side,i,list(map(len,cs)))
            assets.append(save(new,OUT/side/f'walk-{i:02}.png'));frames[side,i]=new
            row=next(r for r in scene['frame_mapping']if r['source_index']==i)
            row.update(path='../../../'+assets[-1]['path'],output_path='../../../'+assets[-1]['path'],revision=REV,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],size=list(new.size))
            checks.append({'side':side,'source_slot':i,'only_changed_box':list(diff),'head_registration':list(BOX),'body_sword_shield_unchanged':True,'opaque_components':1})
        atlas=Image.new('RGBA',(128*8,96))
        for i in range(8):atlas.alpha_composite(frames[side,i]if i in[6,7]else Image.open(OLD/side/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA'),(i*128,0))
        assets.append(save(atlas,OUT/side/'tactical-walk-atlas.png'))
        scene.update(output_atlas='../../../'+assets[-1]['path'],revision=REV,review_note='仅修正左向两相头部为朝左侧脸；原身体、剑盾、腿部和时序保持。')
        scene.setdefault('motion_review',{})['left_profile_fix']={'revision':REV,'source_slots':[6,7],'head_box':list(BOX),'direction':'left','same_head_both_phases':True,'body_pixels_unchanged':True}
        mappings[f'professions/class-9-{side}/maps/frame_mapping.json']=mapping
    for light in[True,False]:
        board=Image.new('RGB',(1024,700),(220,222,216)if light else(32,45,53));draw=ImageDraw.Draw(board)
        for n,(side,i)in enumerate([('ally',6),('ally',7),('enemy',6),('enemy',7)]):
            im=frames[side,i].resize((384,288),Image.Resampling.NEAREST);x=(n%2)*512+64;y=(n//2)*350+5
            board.paste(im,(x,y),im);draw.text(((n%2)*512+256,(n//2)*350+322),('盟军'if side=='ally'else'敌方')+f' · 左行 {i-6}',anchor='mm',font=font(18),fill=(23,38,56)if light else(235,243,242))
        path=OUT/f'left-profile-{"light"if light else"dark"}.png';board.save(path,optimize=True);assets.append({'path':path.relative_to(ROOT).as_posix(),'size':list(board.size),'bytes':path.stat().st_size,'sha256':file_hash(path)})
    write(OUT/'mapping-drafts.json',mappings);write(OUT/'asset-manifest.json',{'revision':REV,'source':'Built-in image_gen targeted head edit','head_box':list(BOX),'assets':assets,'checks':checks,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for path,mapping in mappings.items():write(ROOT/path,mapping)
    print(json.dumps({'revision':REV,'frames':4,'assets':len(assets),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
