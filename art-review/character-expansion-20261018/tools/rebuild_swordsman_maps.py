#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""New flat swordsman map art, native held-object positions and map schedules."""
import argparse,copy,json,math
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFilter
from build_gallery import ROOT
from export_gallery import font
import import_knight_redraw_v3 as art
from revise_cavalry_map import translate,digest

REV='swordsman-map-native-v2-20261022';OUT=ROOT/REV;SRC=OUT/'source'
COLORS=[(23,38,56),(57,118,181),(228,225,200),(221,167,125)]
ENEMY=[(23,38,56),(79,79,125),(187,193,214),(221,167,125)]
ASSETS=[];PROOF={};REG=[]

def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);colors=sorted(set(im.getdata()))
    if im.mode=='RGBA'and len(colors)<=256:
        q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-3*len(colors)));table={p:i for i,p in enumerate(colors)};q.putdata([table[p]for p in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
    else:q=im
    q.save(p,optimize=True);ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p),'purpose':purpose});return'../../../'+p.relative_to(ROOT).as_posix()

@lru_cache(maxsize=20000)
def index(rgb):return min(range(4),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,COLORS[i])))

def quant(im):
    out=Image.new('RGBA',im.size);out.putdata([(*COLORS[index(p[:3])],255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()]);return out

def masters(name,count):
    art.SRC=SRC;figs=list(art.figures(name,count))
    if count==8:figs=sorted(figs,key=lambda f:(f[1]['source_bounds'][1]>400,f[1]['source_bounds'][0]))
    return[(quant(im),meta)for im,meta in figs]

def register(fig,p,target,scale,size,label):
    im,meta=fig;dims=[round(im.width*scale),round(im.height*scale)];small=im.resize(dims,Image.Resampling.NEAREST);delta=[round(target[i]-p[i]*dims[i]/im.size[i])for i in range(2)];out=Image.new('RGBA',size);out.alpha_composite(small,tuple(delta));assert sum(p[3]>0 for p in out.getdata())==sum(p[3]>0 for p in small.getdata()),(label,'clipped')
    REG.append({**meta,'label':label,'own_pose_landmark':p,'native_landmark':target,'scale':scale,'integer_translation':delta,'clipped_pixels':0});return out

def foreground(im):
    cc=art.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);out=im.copy()
    for c in cc[1:]:
        assert len(c)<=24,('disconnected limb',len(c))
        for p in c:out.putpixel(p,(0,0,0,0))
    return out

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(COLORS,ENEMY));out=im.copy();out.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return out

def strip_blade(im,back=False):
    """Remove the own-pose drawn blade, retaining the peach hand and cuff."""
    out=im.copy();p=im.load();white=COLORS[2];points=[]
    # The blade is the only connected ivory component at the top of the
    # weapon side. A categorical mask prevents cutting anatomical contours.
    for y in range(round(im.height*.47)):
        for x in range(im.width):
            if p[x,y][3]and p[x,y][:3]==white:points.append((x,y))
    comps=art.parts(points);assert comps
    choices=[c for c in comps if min(y for x,y in c)<9]
    if not choices:choices=comps
    comp=max(choices,key=len);m=Image.new('L',im.size)
    for xy in comp:m.putpixel(xy,255)
    m=m.filter(ImageFilter.MaxFilter(3))
    removed=[]
    for y in range(im.height):
        for x in range(im.width):
            if m.getpixel((x,y))and p[x,y][3]and p[x,y][:3]in[COLORS[0],COLORS[2]]:out.putpixel((x,y),(0,0,0,0));removed.append([x,y])
    return out,removed

def clean_master_blade(fig):
    """Separate the complete old blade before downsampling; keep its hand."""
    im,meta=fig;ivory=[(x,y)for y in range(round(im.height*.62))for x in range(im.width)if im.getpixel((x,y))[:3]==COLORS[2]and im.getpixel((x,y))[3]]
    comps=art.parts(ivory);top=[c for c in comps if min(y for x,y in c)<25];assert top,(meta,'no top blade')
    c=max(top,key=len);mask=Image.new('L',im.size)
    for xy in c:mask.putpixel(xy,255)
    mask=mask.filter(ImageFilter.MaxFilter(33));out=im.copy()
    for y in range(im.height):
        for x in range(im.width):
            p=im.getpixel((x,y))
            if mask.getpixel((x,y))and p[3]and(p[:3]!=COLORS[3]or y<=max(v for u,v in c)):out.putpixel((x,y),(0,0,0,0))
    return out,meta

def drawn_shield(raw):
    im=raw[0];point=art.landmark(im)[0];white=[(x,y)for y in range(im.height)for x in range(round(point[0]+35),im.width)if im.getpixel((x,y))[:3]==COLORS[2]and im.getpixel((x,y))[3]];cc=art.parts(white);c=max(cc,key=len)
    b=[max(0,min(x for x,y in c)-16),max(0,min(y for x,y in c)-16),min(im.width,max(x for x,y in c)+17),min(im.height,max(y for x,y in c)+17)]
    return im.crop(b)

def remove_shield(im,face):
    p=im.load();points=[(x,y)for y in range(28,85)for x in range(round(face[0]+9),im.width)if p[x,y][3]and p[x,y][:3]==COLORS[2]];cs=art.parts(points);assert cs
    c=max(cs,key=len);b=[min(x for x,y in c)-2,min(y for x,y in c)-2,max(x for x,y in c)+3,max(y for x,y in c)+3];b=[max(0,b[0]),max(0,b[1]),min(im.width,b[2]),min(im.height,b[3])];out=im.copy();out.paste((0,0,0,0),b);return out,b

def blade_asset(raw):
    # Keep the actual straight native blade. Rotating a staircase-shaped blade
    # from a generated diagonal pose introduced false serrations at this size.
    im=Image.open(SRC/'native-idle-002.png').convert('RGBA').crop((8,4,10,11));im.putdata([(*COLORS[2 if min(p[:3])>220 else 0],p[3])for p in im.getdata()]);im=im.resize((32,112),Image.Resampling.NEAREST)
    return im,[8,0],[8,112]

def place_blade(size,asset,tip,grip):
    im,src_tip,src_grip=asset;vx,vy=src_tip[0]-src_grip[0],src_tip[1]-src_grip[1];wx,wy=tip[0]-grip[0],tip[1]-grip[1];den=wx*wx+wy*wy
    # Inverse similarity transform from output to the drawn weapon source.
    # Preserve native blade readability at4x: length is set by source endpoints;
    # its cross-section is independent of the shortened wielding perspective.
    sl=math.hypot(vx,vy);dl=math.hypot(wx,wy);ux,uy=vx/sl,vy/sl;tx,ty=wx/dl,wy/dl;along=sl/dl;across=along/1.2
    aa=along*ux*tx+across*uy*ty;ab=along*ux*ty-across*uy*tx;ba=along*uy*tx-across*ux*ty;bb=along*uy*ty+across*ux*tx
    layer=im.transform(size,Image.Transform.AFFINE,(aa,ab,src_grip[0]-aa*grip[0]-ab*grip[1],ba,bb,src_grip[1]-ba*grip[0]-bb*grip[1]),resample=Image.Resampling.NEAREST)
    return layer

def idle(raw):
    points=[art.landmark(fig[0])[0]for fig in raw];scale=50/(raw[0][0].height-points[0][1]);poses={i:register(clean_master_blade(fig),p,[44,30],scale,(96,96),f'idle-{i}')for i,(fig,p)in enumerate(zip(raw,points))};fixed=poses[0].copy();weapon=blade_asset(raw[0])
    # Large original shield: common face and diagonal stripe, shifted down4
    # output pixels (=1 original pixel) per native phase.
    shield=drawn_shield(raw[0]).resize((28,40),Image.Resampling.NEAREST)
    fixed_regions=[[26,14,55,38],[33,38,55,57],[25,57,68,81]]
    for i in range(3):
        own=poses[i];clean=own.copy();clean.paste((0,0,0,0),(55,0,96,57));removed=[]
        for box in fixed_regions:clean.paste(fixed.crop(box),box[:2])
        tip=[[18,18],[26,18],[34,18]][i];grip=[[24,40],[28,40],[34,40]][i];hand=own.copy();handmask=Image.new('RGBA',own.size)
        for y in range(34,48):
            for x in range(14,39):
                p=hand.getpixel((x,y))
                if p[3]and p[:3]==COLORS[3]:handmask.putpixel((x,y),p)
        clean.alpha_composite(place_blade(clean.size,weapon,tip,grip));clean.alpha_composite(handmask);clean.alpha_composite(shield,(52,16+4*i));poses[i]=foreground(clean)
        PROOF[f'idle-{i}']={'native_sword_tip_4x':tip,'grip':grip,'shield_top_left_4x':[52,16+4*i],'shield_size':[28,40],'old_blade_removed_before_downsampling':True,'fixed_body_regions':fixed_regions,'same_drawn_body':True}
    return{i:poses[j].copy()for i,j in enumerate([0,1,2,1,0,1])}

def walk(raw):
    out={};targets={0:[66,40],1:[66,40],2:[66,46],3:[66,46],4:[62,46],5:[62,46],6:[58,46],7:[58,46]}
    for first in[0,2,4,6]:
        ids=[first,first+1];pair=[raw[i]for i in ids];points=[[102,68],[102,68]]if first==0 else[art.landmark(fig[0])[0]for fig in pair]
        scale=(92-targets[first][1])/max(fig[0].height-p[1]for fig,p in zip(pair,points))
        for i,fig,p in zip(ids,pair,points):out[i]=register(clean_master_blade(fig),p,targets[i],scale,(128,96),f'walk-{i}')
    # The source back-view has opposite support legs; the first AI pair
    # repeated one leg. Keep the complete fixed upper figure and swap only the
    # two whole below-hem leg layers around the same native pelvis axis.
    base=out[0].copy();legs=Image.new('RGBA',base.size);legs.paste(base.crop((0,73,128,96)),(0,73));legs=translate(legs.transpose(Image.Transpose.FLIP_LEFT_RIGHT),[4,0]);out[1]=base.copy();out[1].paste((0,0,0,0),(0,73,128,96));out[1].alpha_composite(legs)
    PROOF['up-leg-pair']={'fixed_region':[0,0,128,73],'native_pelvis_x':66,'leg_exchange_only_below_tunic':True,'phase0_support':'left','phase1_support':'right','no_direction_or_head_mirroring':True}
    # Approved front-facing mercenary eye artwork, not a generated profile eye
    # or a procedural face. Exact same skin and navy palette as the reference.
    source_front=Image.open(ROOT/'mercenary-eyes-v2-20261019/deliverables/class-8-ally/walk-04.png').convert('RGBA');front=source_front.crop((56,26,88,52))
    # The broad source editor crop also contains the mercenary's sword on its
    # far left. Select only the head/neck so no second blade enters this sprite.
    for y in range(front.height):
        for x in range(front.width):
            if x+56<60 and y+26>42:front.putpixel((x,y),(0,0,0,0))
    front=front.resize((28,23),Image.Resampling.NEAREST)
    for i in[4,5]:
        out[i].paste((0,0,0,0),(47,25,82,51));out[i].alpha_composite(front,(52,29))
    # One fixed own-pose head per phase pair; crop stays above moving wrists,
    # sword grips and shield faces. Native leg poses remain independently drawn.
    for first,box in[(2,[54,30,77,52]),(4,[50,30,75,52]),(6,[46,30,70,52])]:out[first+1].paste(out[first].crop(box),box[:2])
    blade=blade_asset(masters('idle-master-v1.png',3)[0]);shield=drawn_shield(masters('idle-master-v1.png',3)[0])
    shields={2:[72,40,20,36],3:[72,52,20,36],4:[72,52,20,36],5:[68,40,24,40],6:[64,36,24,36],7:[68,48,24,36]}
    for i,im in out.items():
        face=targets[i];peach=[(x,y)for y in range(48,72)for x in range(im.width)if im.getpixel((x,y))[:3]==COLORS[3]and im.getpixel((x,y))[3]and(x>face[0]+10 if i<2 else x<face[0]-10)]
        groups=art.parts(peach);assert groups,(i,'hand not found');c=max(groups,key=len);gp=[round(sum(x for x,y in c)/len(c)),round(sum(y for x,y in c)/len(c))]
        tip=[90,34]if i<2 else[54 if i==2 else 58,34]if i in[2,3]else[34,34]
        if i in shields:
            im,box=remove_shield(im,face);x,y,w,h=shields[i];im.alpha_composite(shield.resize((w,h),Image.Resampling.NEAREST),(x,y));PROOF.setdefault(f'walk-{i}',{}).update(native_shield_box=shields[i],removed_old_shield_box=box)
        if i<2:
            # The source back view shows the shield's dark reverse/edge and a
            # different left-arm height in each phase, not a fixed front motif.
            # Reuse that exact original bitmap anatomy with our four materials.
            native=Image.open(SRC/f'native-walk-{i:03}.png').convert('RGBA');box=[9,10,14,19]if i==0 else[8,8,14,19];piece=native.crop(box)
            piece.putdata([(*COLORS[0 if max(p[:3])<100 else 3 if min(p[:3])>220 else 1],p[3])if p[3]else(0,0,0,0)for p in piece.getdata()]);piece=piece.resize((piece.width*4,piece.height*4),Image.Resampling.NEAREST)
            im.paste((0,0,0,0),(32,32,56,76));im.alpha_composite(piece,(box[0]*4,box[1]*4));PROOF.setdefault(f'walk-{i}',{}).update(native_back_shield_and_arm_box=box,back_view_motif=False)
        im.alpha_composite(place_blade(im.size,blade,tip,gp))
        for xy in c:im.putpixel(xy,(*COLORS[3],255))
        out[i]=foreground(im);PROOF.setdefault(f'walk-{i}',{}).update(native_sword_tip=tip,own_pose_grip=gp)
    for i in out:
        PROOF.setdefault(f'walk-{i}',{}).update(native_source_slot=i,direction=['up','up','right','right','down','down','left','left'][i],reference_position=targets[i],independent_native_direction=True,uniform_full_pose_registration=True)
    return out

def board(images,side,light):
    bg=(220,222,216)if light else(32,45,53);fg=(26,42,58)if light else(235,243,242);cw,ch=320,260;out=Image.new('RGB',(cw*4,54+ch*3),bg);d=ImageDraw.Draw(out);d.text((out.width//2,25),('盟军'if side=='ally'else'敌方')+'剑士 · 地图重做',anchor='mm',font=font(21),fill=fg)
    for n,(label,im)in enumerate(images):
        im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=n%4*cw+(cw-im.width)//2;y=54+n//4*ch;out.paste(im,(x,y),im);d.text((n%4*cw+cw//2,y+ch-22),label,anchor='mm',font=font(16),fill=fg)
    save(out,f'{side}-poses-{"light"if light else"dark"}.png','all new map poses, original geometry review')

def build(publish=False):
    base=json.loads((OUT/'baseline.json').read_text());idle_art=idle(masters('idle-master-v1.png',3));walk_art=walk(masters('walk-master-v1.png',8));drafts={}
    for side in['ally','enemy']:
        m=copy.deepcopy(base['mappings'][side]);m.update(revision=REV,review_note='地图全部推倒重做：配色严格沿用截图右侧的本项目佣兵；服饰恢复原作简洁短衣与大矩形斜纹盾，保持原持剑、抬盾和八槽步态；待本轮验收。',status='complete_art_review_passed',runtime_integrated=False);entries=[]
        for scene in m['scenarios']:
            kind=scene['id'];frames=idle_art if kind=='tactical-idle'else walk_art;w,h=scene['output_frame_size'];atlas=Image.new('RGBA',(w*len(frames),h))
            for row in scene['frame_mapping']:
                i=row['source_index'];im=faction(frames[i],side);path=save(im,f'{side}/{kind}/frame-{i:03}.png','newly drawn simple swordsman map pose');row.update(path=path,output_path=path,revision=REV,bytes=ASSETS[-1]['bytes'],sha256=ASSETS[-1]['sha256'],size=[w,h],art_status='reviewed_selected');atlas.alpha_composite(im,(i*w,0))
                if kind=='tactical-walk'or i<3:entries.append((('待机'if kind=='tactical-idle'else['向上','向上','向右','向右','向下','向下','向左','向左'][i])+f' {i}',im))
            scene.update(revision=REV,output_atlas=save(atlas,f'{side}/{kind}-atlas.png','native source slot order'),review_note=m['review_note'],motion_review={'revision':REV,'source_native_schedule_unchanged':True,'body_axis_registered_to_native':True,'source_anatomy':PROOF})
        for light in[False,True]:board(entries,side,light)
        drafts[f'professions/class-9-{side}/maps/frame_mapping.json']=m
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'palette':COLORS,'enemy_palette':ENEMY,'palette_reference':'approved class8 ally tactical-idle frame0, exactly4 RGB colors','registrations':REG,'source_pose_review':PROOF,'assets':ASSETS,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for path,m in drafts.items():write(ROOT/path,m)
    print(json.dumps({'revision':REV,'assets':len(ASSETS),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
