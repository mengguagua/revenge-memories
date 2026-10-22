#!/usr/bin/env python3
"""Replace only the idle blade with the saved narrower, pointed drawing."""
import argparse, copy, json, math
from PIL import Image, ImageFilter
from build_gallery import ROOT, file_hash
from import_knight_redraw_v3 import parts
from export_gallery import font
import import_swordmaster_complete as art
from rebuild_swordsman_maps import blade_asset, place_blade
from revise_swordmaster_side_turn import save as save_indexed
import revise_swordmaster_side_turn as io

REV='swordmaster-idle-blade-v3-20261022'
OUT=ROOT/REV
SRC=OUT/'source'
TIPS=[[16,16],[20,16],[28,16]]
HILTS=[[32.5,41],[34.5,43],[38.5,42]]
ALIASES=[0,1,2,1,0,1]
PROOF=[]

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):return save_indexed(im,OUT/name,purpose)

def new_asset():
    raw=Image.open(SRC/'pointed-blade-master.png').convert('RGBA')
    cc=parts((x,y)for y in range(raw.height)for x in range(raw.width)if raw.getpixel((x,y))[3]>=128)
    c=cc[0];bounds=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]
    cut=Image.new('RGBA',(bounds[2]-bounds[0],bounds[3]-bounds[1]))
    for x,y in c:
        p=raw.getpixel((x,y));rgb=min([art.C[0],art.C[2]],key=lambda rgb:sum((a-b)**2 for a,b in zip(p[:3],rgb)))
        cut.putpixel((x-bounds[0],y-bounds[1]),(*rgb,255))
    save(cut,'source/pointed-blade-indexed.png','isolated two-material ImageGen drawing; original source retained')
    return cut,bounds

def layer(asset,tip,grip,width):
    w,h=asset.size;dx,dy=tip[0]-grip[0],tip[1]-grip[1];length=math.hypot(dx,dy)
    tx,ty=dx/length,dy/length;nx,ny=-ty,tx
    across=w/width;along=(h-1)/length
    # Target blade endpoints retain the native pose's tip/hilt. Only its
    # cross-section is reduced, independent of its wielding angle.
    aa=nx*across;ab=ny*across;ba=-tx*along;bb=-ty*along
    sampling=8
    coeff=(aa/sampling,ab/sampling,(w-1)/2-aa*grip[0]-ab*grip[1],ba/sampling,bb/sampling,h-1-ba*grip[0]-bb*grip[1])
    large=asset.transform((96*sampling,96*sampling),Image.Transform.AFFINE,coeff,resample=Image.Resampling.NEAREST)
    mask=large.getchannel('A').resize((96,96),Image.Resampling.BOX).point(lambda v:255 if v>=160 else 0)
    # Normalize a complete one-pixel navy contour after the small angled
    # resample; subpixel source borders must not become disconnected specks.
    inner=mask.filter(ImageFilter.MinFilter(3));out=Image.new('RGBA',(96,96))
    for y in range(96):
        for x in range(96):
            if mask.getpixel((x,y)):out.putpixel((x,y),(*art.C[2 if inner.getpixel((x,y))else 0],255))
    return out

def revise():
    b=json.loads((OUT/'baseline.json').read_text());asset,bounds=new_asset();poses={};oldasset=blade_asset(None)
    m=b['mappings']['ally'];scene=next(s for s in m['scenarios']if s['id']=='tactical-idle')
    old={i:Image.open((ROOT/'professions/class-10-ally/maps'/next(r['path']for r in scene['frame_mapping']if r['source_index']==i)).resolve()).convert('RGBA')for i in range(3)}
    for i in range(3):
        tip,grip=TIPS[i],HILTS[i];dx,dy=tip[0]-grip[0],tip[1]-grip[1];length=math.hypot(dx,dy);unit=[dx/length,dy/length]
        previous=place_blade((96,96),oldasset,tip,grip)
        width=32*length/112*1.2*.84
        replacement=layer(asset,tip,grip,width);im=old[i].copy();allowed=Image.new('L',(96,96))
        for y in range(96):
            for x in range(96):
                along=(x-grip[0])*unit[0]+(y-grip[1])*unit[1]
                if previous.getpixel((x,y))[3] and along>1:
                    allowed.putpixel((x,y),255)
                    if im.getpixel((x,y))==previous.getpixel((x,y)):
                        im.putpixel((x,y),(0,0,0,0))
                        # The common approved head is behind the old blade in
                        # pose2. Reveal its existing navy hair when narrowed.
                        if 36<=x<60 and 22<=y<41:im.putpixel((x,y),old[0].getpixel((x,y)))
                if replacement.getpixel((x,y))[3]:allowed.putpixel((x,y),255)
        im.alpha_composite(replacement)
        for y in range(96):
            for x in range(96):
                if not allowed.getpixel((x,y)):assert im.getpixel((x,y))==old[i].getpixel((x,y))
        assert im.crop((40,43,96,96)).tobytes()==old[i].crop((40,43,96,96)).tobytes()
        poses[i]=im
        save(allowed,f'source/pose-{i}-edit-mask.png','exact union of old/new blade footprints; unmasked pixels preserved')
        save(replacement,f'source/pose-{i}-blade.png','narrower blade with the existing native tip/hilt positions')
        PROOF.append({'pose':i,'tip':tip,'hilt':grip,'nominal_width_before':width/.84,'nominal_width_after':width,'width_ratio':.84,'source_bounds':bounds,'unchanged_outside_blade_mask':True})
    return b,poses

def build(publish=False):
    b,poses=revise();mappings={};frames={}
    for side in ['ally','enemy']:
        m=copy.deepcopy(b['mappings'][side]);s=next(s for s in m['scenarios']if s['id']=='tactical-idle');atlas=Image.new('RGBA',(576,96))
        for row in s['frame_mapping']:
            i=row['source_index'];im=art.faction(poses[ALIASES[i]],side);frames[side,i]=im
            p=save(im,f'{side}/idle-{i:02}.png','same native idle pose with narrower pointed blade')
            row.update(path=p,output_path=p,revision=REV,bytes=io.ASSETS[-1]['bytes'],sha256=io.ASSETS[-1]['sha256'],size=[96,96]);atlas.alpha_composite(im,(i*96,0))
        s.update(output_atlas=save(atlas,f'{side}/idle-atlas.png','native idle aliases unchanged'),revision=REV,review_note='待机剑身轻微收窄，顶部曲线收成尖端；剑柄、手臂、身体中心与三相节奏保持。')
        s.setdefault('motion_review',{})['idle_blade_revision']={'revision':REV,'poses':PROOF,'body_and_native_timing_unchanged':True}
        mappings[f'professions/class-10-{side}/maps/frame_mapping.json']=m
        entries=[]
        for sc in m['scenarios']:
            for row in sc['frame_mapping']:
                i=row['source_index']
                if sc['id']=='tactical-idle' and i>=3:continue
                im=Image.open((ROOT/f'professions/class-10-{side}/maps'/row['path']).resolve()).convert('RGBA')
                label=('待机'if sc['id']=='tactical-idle'else['上','上','右','右','下','下','左','左'][i])+f' {i}'
                entries.append((label,im))
        old_out=art.OUT;art.OUT=OUT;n=len(art.ASSETS)
        for light in [True,False]:art.board(entries,side,'maps',light)
        io.ASSETS.extend(art.ASSETS[n:]);art.OUT=old_out
    from PIL import ImageDraw
    for light in [False,True]:
        board=Image.new('RGB',(1152,760),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(board);fg=(23,38,56)if light else(235,243,242)
        d.text((576,26),'剑豪 · 待机窄剑与尖端',anchor='mm',font=font(21),fill=fg)
        for row,side in enumerate(['ally','enemy']):
            for i in range(3):
                im=frames[side,i].resize((384,384),Image.Resampling.NEAREST);x=i*384;y=42+row*350-55
                board.paste(im,(x,y),im)
                text=('盟军'if side=='ally'else'敌方')+f' · 待机 {i}'
                d.text((i*384+192,355+row*350),text,anchor='mm',font=font(18),fill=fg)
        save(board,f'idle-pointed-{"light"if light else"dark"}.png','three blade phases, deep/light background inspection')
    write(OUT/'mapping-drafts.json',mappings)
    write(OUT/'asset-manifest.json',{'revision':REV,'source':'built-in image_gen blade-only edit','assets':io.ASSETS,'blade_registration':PROOF,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for p,m in mappings.items():write(ROOT/p,m)
    print(json.dumps({'frames':12,'assets':len(io.ASSETS),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
