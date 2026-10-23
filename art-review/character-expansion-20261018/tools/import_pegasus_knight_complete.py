#!/usr/bin/env python3
"""Five matte materials on native-registered ImageGen Pegasus anatomy."""
import argparse,colorsys,copy,json,math
from functools import lru_cache
from PIL import Image,ImageDraw,ImageChops,ImageFilter
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_sniper_complete as io
from prepare_pegasus_knight_complete import REV,OUT,SRC,write

HEX=['172638','3976b5','e4e1c8','dda77d','b96369']
C=[tuple(bytes.fromhex(h))for h in HEX]
REG=[]
STABLE=[]

def warm_red(p):
    h,s,v=colorsys.rgb_to_hsv(*(a/255 for a in p[:3]));return p[3]>=128 and (h<.075 or h>.96)and s>.64 and v>.4 and p[0]>1.35*p[1]

def hair(im):
    comps=io.helper.parts((x,y)for y in range(round(im.height*.70))for x in range(im.width)if warm_red(im.getpixel((x,y))))
    cs=[c for c in comps if len(c)>im.width*.08 and io.box(c)[2]-io.box(c)[0]>im.width*.025 and io.box(c)[3]-io.box(c)[1]>im.height*.018]
    if not cs:raise ValueError('Missing red hair reference')
    # The uppermost sizeable red cluster is hair; red boots/skirt are lower.
    top=min(io.box(c)[1]for c in cs)
    main=max(cs,key=lambda c:len(c)/(1+.12*(io.box(c)[1]-top)))
    b=io.box(main);return b

@lru_cache(maxsize=60000)
def matte(rgb,in_hair,skin_ok):
    r,g,b=rgb;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if v<.28 or .18*r+.72*g+.10*b<55:return C[0]
    if in_hair:
        return C[4]
    if skin_ok and r>155 and g>95 and b>55 and r>1.12*g and g>1.08*b and s<.64:return C[3]
    if (h<.13 or h>.94)and s>.32:
        # Warm leather/cloth becomes archer blue. Gold fittings become ivory.
        return C[2]if h>.095 and v>.68 else C[1]if v>.40 else C[0]
    if s<.30:return C[2]if v>.72 else C[1]if v>.49 else C[0]
    if .48<h<.82:return C[2]if v>.79 and s<.44 else C[1]if v>.54 else C[0]
    return C[2]if v>.63 else C[0]

def recolor(im,label):
    im=im.convert('RGBA');hb=hair(im);hc=io.center(hb);q=Image.new('RGBA',im.size)
    for y in range(im.height):
        for x in range(im.width):
            p=im.getpixel((x,y))
            if p[3]<128:continue
            # Upper hair highlights flatten to red; the face below the fringe
            # retains skin/eye pixels, and silver armor remains warm white.
            hair_region=hb[0]-2<=x<hb[2]+2 and hb[1]-4<=y<hb[1]+min(6,max(3,(hb[3]-hb[1])*.45))
            hue,sat,val=colorsys.rgb_to_hsv(*(v/255 for v in p[:3]))
            hair_warm=(hue<.055 and sat>.35)or((hue<.14 or hue>.96)and sat>.64)
            red_hair=hb[0]-1<=x<hb[2]+1 and hb[1]-1<=y<hb[3]+1 and hair_warm
            if label in['tactical-walk-0','tactical-walk-1']and hb[0]<=x<hb[2]and hb[1]<=y<hb[3]:hair_region=True
            skin_ok=hb[0]-im.width*.045<=x<hb[2]+im.width*.045 and hb[1]+(hb[3]-hb[1])*.35<=y<hb[3]+im.height*.22
            q.putpixel((x,y),(*matte(p[:3],hair_region or red_hair,skin_ok),255))
    REG.append({'label':label,'hair_bounds':hb,'source_sha256':__import__('hashlib').sha256(im.tobytes()).hexdigest(),'alpha_preserved_at_threshold_128':True})
    return q,hb

def map_anchor(im):
    pts=[(x,y)for y in range(min(48,im.height))for x in range(im.width)if im.getpixel((x,y))==(*C[4],255)]
    top=min(y for x,y in pts)
    cap=[(x,y)for x,y in pts if top+1<=y<=top+4]
    return [round((min(x for x,y in cap)+max(x for x,y in cap))/2),top]

def stabilize(poses,ids,label,target_x):
    anchors={i:map_anchor(poses[i])for i in ids};target=[target_x,max(a[1]for a in anchors.values())]
    for i in ids:
        im=poses[i];a=anchors[i];delta=[target[k]-a[k]for k in range(2)];cut=88 if im.width==128 else 96
        body=im.crop((0,0,im.width,cut));q=Image.new('RGBA',im.size);q.alpha_composite(body,tuple(delta))
        assert sum(p[3]>0 for p in body.getdata())==sum(p[3]>0 for p in q.getdata()),(label,i,'body clipping')
        if cut<im.height:q.paste(im.crop((0,cut,im.width,im.height)),(0,cut))
        assert map_anchor(q)==target,(label,i,map_anchor(q),target)
        poses[i]=q;STABLE.append({'label':label,'slot':i,'source_head_anchor':a,'fixed_head_anchor':target,'translation':delta,'projection_not_translated':cut<im.height,'clipped_pixels':0})

def save(im,name,purpose):
    io.OUT=OUT;return io.save(im,name,purpose)

def board(items,name,light):
    cols=4;cw,ch=(380,440)if name=='battle'else(320,280)
    q=Image.new('RGB',(cols*cw,56+ch*math.ceil(len(items)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(233,240,240)
    d.text((q.width//2,26),'盟军天马骑士 · '+('战斗姿态'if name=='battle'else'待机／四向移动'),anchor='mm',font=font(21),fill=fg)
    for n,(label,im)in enumerate(items):
        if name!='battle':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
        x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;q.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,y+im.height+22),label,anchor='mm',font=font(17),fill=fg)
    save(q,f'ally-{name}-'+('light'if light else'dark')+'.png','complete pose inspection, exact sprite dimensions and text safe margins')

def build(publish=False):
    b=json.loads((OUT/'baseline.json').read_text());maps={};battle={};mb=b['ally_maps'];bb=b['ally_battle'];items=[]
    for scene in mb['scenarios']:
        poses={};kind=scene['id']
        for f in scene['frame_mapping']:
            i=f['source_index'];source=(ROOT/'professions/class-3-ally/maps'/f['output_path']).resolve();im,hb=recolor(Image.open(source),f'{kind}-{i}')
            poses[i]=im
        maps[kind]=poses
    stabilize(maps['tactical-idle'],[0,1,2],'idle',48)
    for i,j in[(3,1),(4,0),(5,1)]:maps['tactical-idle'][i]=maps['tactical-idle'][j].copy()
    for ids,label in[([0,1],'up'),([4,5],'down'),([6,7],'left')]:stabilize(maps['tactical-walk'],ids,label,64)
    for i,j in[(2,6),(3,7)]:maps['tactical-walk'][i]=maps['tactical-walk'][j].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    for kind,poses in maps.items():
        for i in(range(3)if kind=='tactical-idle'else range(8)):items.append((('待机'if kind=='tactical-idle'else['上','上','右','右','下','下','左','左'][i])+f' {i}',poses[i]))
    for i,path in bb['frame_mapping'].items():
        source=(ROOT/'professions/class-3-ally/battle'/path).resolve();battle[int(i)]=recolor(Image.open(source),f'battle-{i}')[0]
    for light in[False,True]:board(items,'maps',light);board([(f'源姿势 {i}',im)for i,im in sorted(battle.items())],'battle',light)
    for kind,poses in {**maps,'battle':battle}.items():
        for i,im in poses.items():save(im,f'ally/{kind}/frame-{i:03}.png','native-registered existing ImageGen pose, five matte materials')
    projectile=Image.open(ROOT/'source-input/effects/3d558f7aa86343.png').convert('RGBA')
    projectile.putdata([(*C[2 if p[0]>230 else 1],p[3])if p[3]else(0,0,0,0)for p in projectile.getdata()])
    projectile_path=save(projectile,'ally/flying-javelin.png','native javelin alpha/anchor/frame retained; ivory steel and blue shaft match held spear')
    if publish:publish_mappings(b,maps,battle,projectile_path)
    write(OUT/'registration.json',{'palette':HEX,'material_registrations':REG,'fixed_map_centers':STABLE,'runtime_integrated':False})
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'runtime_integrated':False})
    print(json.dumps({'palette':HEX,'maps':{k:len(v)for k,v in maps.items()},'battle':len(battle)}),flush=True)

def publish_mappings(b,maps,battle,projectile_path):
    note='盟军天马：沿用原作逐帧扑翼、收腿、前刺和投枪姿势／循环／节奏；地图固定骑手头部锚点消除整体位移。弓箭手蓝白四色加一种柔和红色，保留肤色和眼睛，头发纯色、衣甲哑光。敌方按用户选择暂缓。'
    m=copy.deepcopy(b['ally_maps']);m.update(revision=REV,status='review_candidate',modified_by='codex',review_note=note,palette=HEX,art_mode='existing native-registered ImageGen anatomy; ImageGen material guide, five matte material assignment and rigid center registration',runtime_integrated=False)
    for scene in m['scenarios']:
        kind=scene['id'];poses=maps[kind];w,h=next(iter(poses.values())).size;atlas=Image.new('RGBA',(len(poses)*w,h));records=[]
        for i,im in sorted(poses.items()):
            p=OUT/f'ally/{kind}/frame-{i:03}.png';path='../../../'+str(p.relative_to(ROOT));atlas.alpha_composite(im,(i*w,0))
            records.append({'source_index':i,'source_frame':i,'output_index':i,'path':path,'output_path':path,'revision':REV,'size':[w,h],'bytes':p.stat().st_size,'sha256':file_hash(p)})
        scene.update(revision=REV,status='review_candidate',frame_mapping=records,output_atlas=save(atlas,f'ally/{kind}-atlas.png','native slot order, five matte materials'),review_status='pending_user_visual_acceptance',review_note=note,motion_review={'fixed_head_anchors':[x for x in STABLE if x['label']==('idle'if kind=='tactical-idle'else 'up')or(kind=='tactical-walk'and x['label']in['down','left'])],'pose_shape_transforms':'whole connected body integer translation only; native projection is not moved','native_timing_unchanged':True})
        scene.pop('parent_visual_review_passed',None)
    m.pop('parent_visual_review_passed',None)
    write(ROOT/'professions/class-3-ally/maps/frame_mapping.json',m)
    m=copy.deepcopy(b['ally_battle']);m.update(revision=REV,status='review_candidate',modified_by='codex',review_note=note,palette=HEX,runtime_integrated=False,display_class_name='天马骑士')
    order=sorted(battle);atlas=Image.new('RGBA',(len(order)*320,384));records=[];paths={}
    for n,i in enumerate(order):
        p=OUT/f'ally/battle/frame-{i:03}.png';path='../../../'+str(p.relative_to(ROOT));paths[str(i)]=path;atlas.alpha_composite(battle[i],(n*320,0));records.append({'source_frame':i,'path':path,'size':[320,384],'bytes':p.stat().st_size,'sha256':file_hash(p)})
    m.update(frame_mapping=paths,records=records,output_atlas=save(atlas,'ally/battle-atlas.png','all required native OAM/background slots'),output_atlas_order=order,effect_overrides={'3d558f7aa86343':projectile_path},batches=[{'id':'蓝白／纯色红发全姿态','review':'../../../'+REV+'/ally-battle-light.png','status':'review_candidate'}])
    m.pop('parent_visual_review_passed',None)
    write(ROOT/'professions/class-3-ally/battle/frame_mapping.json',m)
    write(OUT/'mapping-drafts.json',{'maps':json.loads((ROOT/'professions/class-3-ally/maps/frame_mapping.json').read_text()),'battle':m})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();build(a.publish)
