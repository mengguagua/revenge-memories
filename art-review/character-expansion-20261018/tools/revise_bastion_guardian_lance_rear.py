#!/usr/bin/env python3
"""Repair rear lance continuity with one rigid drawn shaft; keep native body poses."""
import argparse,copy,json,math
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT
from export_gallery import font
from revise_cavalry_map import digest,translate
import import_knight_redraw_v3 as h
import import_bastion_guardian_v1 as art

REV='bastion-guardian-lance-rear-v5-20261022';OUT=ROOT/REV;SRC=OUT/'source';ASSETS=[]
# Existing rear shaft branches only, outside the shoulder; each segment follows
# the old embedded weapon. The rest of the existing full figure is retained.
OLD_REAR={0:([251,159],[264,152]),1:([250,158],[263,152]),2:([250,161],[265,153]),3:([255,162],[268,155]),4:([244,152],[276,132]),5:([245,157],[280,133]),6:([253,157],[286,134]),7:([248,157],[261,151]),8:([248,155],[262,148]),9:([252,159],[313,120])}

def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
    ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':p.stat().st_size,'sha256':digest(p)})
    return '../../../'+p.relative_to(ROOT).as_posix()

def axis(im,i):
    pts=[]
    for y in range(256):
        for x in range(320):
            p=im.getpixel((x,y));region=(x<190 and y>190)if i<10 else(x>250 and y<170)if i==10 else(x<180 and 140<y<180)
            if p[3]and p[:3]in[art.COLORS[10],art.COLORS[11]]and region:pts.append((x,y))
    c=h.parts(pts)[0];mx=sum(x for x,y in c)/len(c);my=sum(y for x,y in c)/len(c)
    slope=sum((x-mx)*(y-my)for x,y in c)/sum((x-mx)**2 for x,y in c);intercept=my-slope*mx
    gx=min(x for x,y in c)-10 if i==10 else max(x for x,y in c)+10
    return [gx,slope*gx+intercept],slope

def transformed(piece,grip,slope,reverse=False):
    sign=-1 if reverse else 1;dx=sign/math.sqrt(1+slope*slope);dy=dx*slope;gx,gy=grip
    # Inverse rigid transform; nearest neighbor keeps the indexed pixel edges.
    matrix=(dx,dy,-dx*gx-dy*gy,-dy,dx,dy*gx-dx*gy+(piece.height-1)/2)
    return piece.transform((320,256),Image.Transform.AFFINE,matrix,resample=Image.Resampling.NEAREST),[gx+dx*(piece.width-1),gy+dy*(piece.width-1)]

def clear_old_rear(im,i):
    out=im.copy();points=[];p=out.load()
    if i not in OLD_REAR:return out,points
    start,end=OLD_REAR[i];vx=end[0]-start[0];vy=end[1]-start[1];length=math.hypot(vx,vy);ux=vx/length;uy=vy/length
    for y in range(100,176):
        for x in range(230,320):
            dx=x-start[0];dy=y-start[1];along=dx*ux+dy*uy;distance=abs(dx*uy-dy*ux)
            old=p[x,y]
            selected=(0<=along<=length+6 and distance<=6)or(old[:3]in[art.COLORS[10],art.COLORS[11]]and x>=235 and y<166)
            if old[3]and selected:p[x,y]=(0,0,0,0);points.append([x,y])
    return out,points

def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());h.SRC=SRC
    raw,raw_meta=h.figures('rear-shaft-master-v1.png',1)[0];size=[110,round(raw.height*110/raw.width)];piece=raw.resize(size,Image.Resampling.NEAREST)
    piece.putdata([(*art.COLORS[art.material(p[:3])],p[3])if p[3]else(0,0,0,0)for p in piece.getdata()])
    marker=Image.new('RGBA',piece.size);marker.paste(piece.crop((piece.width-10,0,piece.width,piece.height)),(piece.width-10,0))
    old={i:Image.open((ROOT/'professions/class-22-ally/battle'/baseline['ally']['frame_mapping'][str(i)]).resolve()).convert('RGBA')for i in range(12)}
    repaired={};repairs={};layers={}
    for i,im in old.items():
        grip,slope=axis(im,i);rear,cap=transformed(piece,grip,slope,i==10);cap_layer,_=transformed(marker,grip,slope,i==10)
        clean,removed=clear_old_rear(im,i)
        if i==11:
            # The extended thrust holds the lance across the front of the chest.
            # The rear segment is in front here, with its gripping glove on top.
            revised=clean.copy();revised.alpha_composite(rear);glove=Image.new('RGBA',im.size);glove.paste(im.crop((155,156,184,179)),(155,156));revised.alpha_composite(glove)
        else:
            revised=rear.copy();revised.alpha_composite(clean)
        # Clear only detached fragments of the old rear outline. The new shaft
        # and the existing character remain one connected silhouette.
        components=h.parts((x,y)for y in range(256)for x in range(320)if revised.getpixel((x,y))[3]);strays=[]
        for component in components[1:]:
            if all(x>=230 and y<176 for x,y in component):
                for point in component:revised.putpixel(point,(0,0,0,0));strays.append(list(point))
        visible=[(x,y)for y in range(256)for x in range(320)if cap_layer.getpixel((x,y))[3]and revised.getpixel((x,y))==cap_layer.getpixel((x,y))]
        assert visible,(i,'rear butt must remain visible')
        assert revised.crop((190,128,225,162)).tobytes()==im.crop((190,128,225,162)).tobytes()
        repaired[i]=revised;layers[i]=rear
        repairs[str(i)]={'grip':grip,'axis_slope':slope,'butt_axis_endpoint':cap,'shared_asset_size':size,'visible_butt_pixels':len(visible),'visible_butt_bounds':[min(x for x,y in visible),min(y for x,y in visible),max(x for x,y in visible)+1,max(y for x,y in visible)+1],'removed_old_rear_pixels':removed,'removed_detached_rear_outline_pixels':strays,'composite_order':'in front of torso, below gripping glove'if i==11 else'behind existing body','changed_pixels':sum(a!=b for a,b in zip(im.getdata(),revised.getdata()))}
    drafts={};display={}
    for side in ['ally','enemy']:
        m=copy.deepcopy(baseline[side]);save(art.faction(piece,side),f'{side}/shared-rear-shaft.png','same complete rear handle used in every ordinary attack pose, no scaling between poses')
        frames={i:art.faction(im,side)for i,im in repaired.items()}
        for i in[13,24]:frames[i]=translate(frames[0],[-64,0])if side=='enemy'else frames[0].copy()
        for i,im in sorted(frames.items()):m['frame_mapping'][str(i)]=save(im,f'{side}/frame-{i:03}.png','rear shaft remains present with slight original pose rotation; body position retained')
        for record in m.get('records',[]):
            i=record['source_frame']
            if i in frames:record.update(path=m['frame_mapping'][str(i)],sha256=digest((ROOT/f'professions/class-22-{side}/battle'/m['frame_mapping'][str(i)]).resolve()),revision=REV)
        atlas=Image.new('RGBA',(320*len(m['frame_mapping']),256))
        for n,(key,path)in enumerate(sorted(m['frame_mapping'].items(),key=lambda v:int(v[0]))):atlas.alpha_composite(Image.open((ROOT/f'professions/class-22-{side}/battle'/path).resolve()).convert('RGBA'),(n*320,0))
        m.update(revision=REV,output_atlas=save(atlas,f'{side}/battle-atlas.png','repaired ordinary slots plus unchanged javelin slots'),review_note='普通攻击统一使用同一张完整长枪后柄；随姿势小幅转动，所有准备、出枪与收势姿势均保留可见的钝尾帽，不再短头与长柄交替闪现。身体位置、原动作顺序、535帧程序及结算时刻保持。',runtime_integrated=False,status='review_candidate',rear_shaft_review={'shared_asset':f'../../../{REV}/{side}/shared-rear-shaft.png','source_asset_size':size,'same_asset_all_ordinary_poses':True,'pose_records':repairs},batches=[{'id':'后柄连续性','review':f'../../../{REV}/{side}-poses-dark.png','status':'review_candidate'}])
        drafts[f'professions/class-22-{side}/battle/frame_mapping.json']=m;display[side]=frames
    for side in ['ally','enemy']:
        for light in[False,True]:
            bg=(220,222,216)if light else(32,45,53);fg=(30,43,56)if light else(235,243,242)
            board=Image.new('RGB',(1056,1200),bg);d=ImageDraw.Draw(board);d.text((528,24),('盟军'if side=='ally'else'敌方')+'壁垒卫士 · 长枪后柄连续',anchor='mm',font=font(23),fill=fg)
            for n,i in enumerate(range(12)):
                im=display[side][i];x=n%3*352+16;y=48+n//3*284;board.paste(im,(x,y),im);d.text((n%3*352+176,y+258),f'姿势{i} · 后柄保留',anchor='mt',font=font(15),fill=fg)
            save(board,f'{side}-poses-{"light"if light else"dark"}.png','all12 ordinary poses with persistent rear shaft, dark/light')
    write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'image_generation':'built-in image_gen','source_master':'source/rear-shaft-master-v1.png','source_piece':raw_meta,'palette':{'ally':art.ALLY,'enemy':art.ENEMY},'shared_rear_shaft_size':size,'pose_repairs':repairs,'runtime_integrated':False,'assets':ASSETS})
    if publish:
        for key,m in drafts.items():write(ROOT/key,m)
    print(json.dumps({'status':'published'if publish else'staged','shared_rear_size':size,'minimum_visible_butt_pixels':min(r['visible_butt_pixels']for r in repairs.values()),'assets':len(ASSETS)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
