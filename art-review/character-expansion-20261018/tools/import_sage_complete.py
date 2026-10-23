#!/usr/bin/env python3
"""Register ImageGen scholar poses to immutable class19 ally motion."""
import argparse, copy, colorsys, json, math
from functools import lru_cache
from PIL import Image, ImageDraw
from build_gallery import ROOT, file_hash
from export_gallery import font
from prepare_sage_complete import REV, OUT, SRC, write
import import_knight_redraw_v3 as helper
import import_sniper_complete as io
io.OUT=OUT
HEX=['172638','2a4662','3976b5','e8e3cb','9b5148','c3a56c','e2b78d','53382f']
C=[tuple(bytes.fromhex(h)) for h in HEX]
REG=[];STABLE=[]

@lru_cache(maxsize=50000)
def material(rgb):
    r,g,b=rgb;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if v<.22:return C[0]
    if (h>.90 or h<.045) and s>.32:return C[4] if v>.29 else C[7]
    if .045<=h<.18 and v>.52 and s<.40:return C[3]
    if s<.32 and v>.51:return C[3]
    if .48<h<.79:return C[2] if v>.32 else C[1]
    return min(C,key=lambda q:sum((a-b)**2 for a,b in zip(q,rgb)))

def quant(im):
    q=Image.new('RGBA',im.size)
    q.putdata([(*material(p[:3]),255) if p[3]>=128 else (0,0,0,0) for p in im.getdata()])
    return q

def bbox(points):return [min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1]
def center(b):return [(b[0]+b[2])/2,(b[1]+b[3])/2]

def landmark(im,back=False):
    points=[(x,y) for y in range(round(im.height*.48)) for x in range(im.width) if im.getpixel((x,y))==(*C[7 if back else 6],255)]
    parts=helper.parts(points)
    if back:
        candidates=[p for p in parts if len(p)>30 and bbox(p)[3]-bbox(p)[1]>im.height*.08]
    else:
        candidates=[p for p in parts if len(p)>20 and bbox(p)[1]<im.height*.34 and center(bbox(p))[0]<im.width*.74]
    assert candidates,('missing head landmark',im.size,back)
    def score(p):
        b=bbox(p);return len(p)/(1+20*(center(b)[1]/im.height-.21)**2)
    b=bbox(max(candidates,key=score));return center(b),b

@lru_cache(maxsize=8)
def figures(name,count,back_ids=()):
    # Connected alpha components retain all drawn cape/weapon pixels even when
    # they extend beyond a nominal sheet cell. Tiny generation specks are excluded.
    raw=Image.open(SRC/name).convert('RGBA');pix=raw.load()
    parts=helper.parts((x,y) for y in range(raw.height) for x in range(raw.width) if pix[x,y][3]>=128)
    parts=[p for p in parts if len(p)>1500]
    assert len(parts)==count,(name,'figure count',len(parts))
    parts.sort(key=lambda p:center(bbox(p))[1])
    if count>3:
        parts=sorted(parts[:3],key=lambda p:bbox(p)[0])+sorted(parts[3:],key=lambda p:bbox(p)[0])
    else:parts.sort(key=lambda p:bbox(p)[0])
    out=[]
    for i,points in enumerate(parts):
        b=bbox(points);im=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
        for x,y in points:im.putpixel((x-b[0],y-b[1]),pix[x,y])
        im=quant(im)
        reviewed=json.loads((SRC/'head-landmarks.json').read_text())[name][i]
        p,fb=reviewed['point'],reviewed['box']
        # Hair is one matte brown fill; the dark outer contour and skin remain.
        radius=max(fb[2]-fb[0],fb[3]-fb[1])
        hair=[max(0,round(p[0]-radius*1.1)),max(0,round(fb[1]-radius*1.05)),min(im.width,round(p[0]+radius*1.1)),fb[3] if i in back_ids else round(fb[1]+radius*.25)]
        for y in range(hair[1],hair[3]):
            for x in range(hair[0],hair[2]):
                px=im.getpixel((x,y))
                if px[3] and px[:3] in [C[4],C[5],C[7]]:im.putpixel((x,y),(*C[7],255))
        if i not in back_ids:
            for y in range(fb[1],fb[3]):
                for x in range(fb[0],fb[2]):
                    if im.getpixel((x,y))==(*C[3],255):im.putpixel((x,y),(*C[0],255))
        out.append((im,{'source':name,'source_sha256':file_hash(SRC/name),'source_bounds':b,'head_point':p,'head_box':fb,'hair_region':hair,'back':i in back_ids}))
    return out

def register(fig,size,target,floor,label):
    im,meta=fig;p=meta['head_point'];scale=(floor-target[1])/(im.height-p[1]);dims=[round(im.width*scale),round(im.height*scale)]
    small=im.resize(dims,Image.Resampling.NEAREST);at=[round(target[0]-p[0]*dims[0]/im.width),floor-dims[1]]
    q=Image.new('RGBA',size);q.alpha_composite(small,tuple(at))
    count=lambda z:sum(px[3]>0 for px in z.getdata())
    assert count(q)==count(small),(label,'clipped',at,dims)
    REG.append({**meta,'label':label,'fixed_head_target':target,'floor':floor,'uniform_scale':scale,'scaled_size':dims,'translation':at,'clipped_opaque_pixels':0})
    return q

def freeze(poses,ids,boxes,label,protect_hands=False):
    base=poses[ids[0]]
    for i in ids[1:]:
        original=poses[i].copy()
        for b in boxes:
            poses[i].paste(base.crop(b),b[:2])
            if protect_hands:
                for y in range(b[1],b[3]):
                    for x in range(b[0],b[2]):
                        if b==[155,99,199,144] and original.getpixel((x,y))==(*C[6],255) and base.getpixel((x,y))[:3]!=C[6] and x<165:
                            poses[i].putpixel((x,y),original.getpixel((x,y)))
    STABLE.append({'label':label,'frames':ids,'fixed_regions':boxes,'fixed_region_reference':ids[0],'skin_hand_occlusion_retained':protect_hands,'global_bob':[0,0]})

def maps():
    idle={i:register(f,(96,96),[48,32],80,f'idle-{i}') for i,f in enumerate(figures('idle-master.png',3))}
    freeze(idle,[0,1,2],[[34,13,58,43],[34,43,55,57],[29,73,66,81]],'idle head torso and planted boots')
    walk={}
    for i,f in enumerate(figures('walk-master.png',6,(0,1))):
        target=[64,43] if i<2 else [64,47]
        walk[i]=register(f,(128,96),target,96,f'walk-{i}')
    for ids,label in [([0,1],'up'),([2,3],'right'),([4,5],'down')]:
        y=43 if ids[0]==0 else 47
        freeze(walk,ids,[[50,y-20,79,y+20]],'walk '+label+' fixed head neck torso')
    walk[6]=walk[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT);walk[7]=walk[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return {'tactical-idle':{i:idle[j].copy() for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def cape_width(poses):
    # Native frames16..20 narrow only the hanging cape; reproduce its per-row
    # silhouette by resampling the drawn cape toward the same fixed shoulder.
    base=poses[0]
    for i in range(16,21):
        native=Image.open(SRC/f'native-battle-{i:03}.png').convert('RGBA');q=base.copy()
        # The native cape's extreme left edge determines its amount of folding.
        # Blend the horizontal compression below the fixed shoulder so that a
        # coarse source row cannot tear holes across the much finer new cloth.
        factor=(41-native.getbbox()[0])/(41-25)
        for y in range(155,230):
            ratio=1-(1-factor)*min(1,(y-155)/30)
            boundary=164
            for x in range(80,boundary):q.putpixel((x,y),(0,0,0,0))
            for x in range(80,boundary):
                src=round(boundary-(boundary-x)/ratio)
                if 0<=src<boundary:q.putpixel((x,y),base.getpixel((src,y)))
        poses[i]=q

def battle():
    poses={}
    for name,ids in [('battle-a-master.png',[0,21,22,23,24,25]),('battle-b-master.png',[26,27,28,29,30,31]),('battle-c-master.png',[32,33,34,35,36])]:
        for i,f in zip(ids,figures(name,len(ids))):poses[i]=register(f,(320,256),[175,128],256,f'battle-{i}')
    # The source fixes feet, belt, torso and staff throughout these gestures.
    # Use one complete painted body rather than accepting generator body drift.
    foreground={i:poses[i].copy() for i in [26,28,29]}
    freeze(poses,[0,*range(21,37)],[[155,99,199,144],[165,146,206,230],[150,229,222,256],[209,79,267,256]],'battle shared anatomical core and full staff')
    # These three hands pass in front of the fixed head. Keep the complete
    # painted hand/cuff including its outline, rather than skin pixels alone.
    for i,box in [(26,[145,107,168,142]),(28,[139,125,165,150]),(29,[137,99,167,133])]:
        poses[i].alpha_composite(foreground[i].crop(box),box[:2])
    cape_width(poses)
    for i,im in poses.items():
        parts=helper.parts((x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3])
        for part in parts[1:]:
            assert len(part)<=10,(i,'detached drawn part',len(part))
            for point in part:im.putpixel(point,(0,0,0,0))
    return poses

def board(entries,name,battle=False):
    cw,ch=(360,300) if battle else (300,270);cols=4
    for light in [False,True]:
        q=Image.new('RGB',(cw*cols,48+ch*math.ceil(len(entries)/cols)),(220,222,216) if light else (32,45,53));d=ImageDraw.Draw(q);fg=(32,43,53) if light else (235,239,239)
        d.text((q.width//2,24),'我方博学术师 · '+('战斗姿势' if battle else '待机与四向行走'),anchor='mm',font=font(21),fill=fg)
        for n,(label,im) in enumerate(entries):
            if not battle:im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
            x=n%cols*cw+(cw-im.width)//2;y=48+n//cols*ch;q.paste(im,(x,y),im)
            d.text((n%cols*cw+cw//2,y+ch-17),label,anchor='mm',font=font(16),fill=fg)
        io.save(q,name+('-light.png' if light else '-dark.png'),'complete pose inspection on light/dark backgrounds')

def build(publish=False):
    map_poses=maps();battle_poses=battle();note='我方博学术师：修长收腰、分层肩披、米白长袍与蓝色内衣，保留术法师暖红棕与金饰；自然肤色、双眼及纯色棕发。地图固定头颈与上身，杖手、袍摆与脚步按本类原作变化；战斗依原抬臂、施法、恢复及收势程序，原法术效果与结算保持。'
    for kind,poses in {**map_poses,'battle':battle_poses}.items():
        for i,im in poses.items():io.save(im,f'ally/{kind}/frame-{i:03}.png','ImageGen scholar pose, registered to native class19, eight matte materials')
    board([(kind+' '+str(i),im) for kind,poses in map_poses.items() for i,im in poses.items() if kind!='tactical-idle' or i<3],'ally-maps')
    board([(str(i),im) for i,im in sorted(battle_poses.items())],'ally-battle',True)
    if publish:
        p=ROOT/'professions/class-19-ally';template=json.loads((ROOT/'professions/class-15-ally/maps/frame_mapping.json').read_text())
        m={k:v for k,v in template.items() if k in ['schema_version','width_height_scale']}
        m.update(character_id='class-19-ally',actor_id='class-19-ally',class_id=19,source_side='ally',display_name='盟军博学术师',display_class_name='博学术师',status='review_candidate',revision=REV,modified_by='codex',runtime_integrated=False,review_note=note,palette=HEX,scenarios=[])
        for old in template['scenarios']:
            kind=old['id'];poses=map_poses[kind];s={k:copy.deepcopy(v) for k,v in old.items() if k in ['id','source_frame_size','source_anchor','output_frame_size','output_anchor','logical_render_scale','default_facing','directions','direction_mirror_x','timing','source_aliases','native_actor_origin']}
            source=ROOT/('source-input/corrected-tactical-walk/class-19-ally.png' if kind=='tactical-walk' else 'source-input/legacy-assets/assets/original/graphics/map_units/class_19_ally.png')
            s.update(class_id=19,character_id='class-19-ally',source_side='ally',display_name='盟军博学术师',source_atlas='../../../'+source.relative_to(ROOT).as_posix(),revision=REV,review_note=note,status='review_candidate',frame_mapping=[])
            if kind=='tactical-walk':s['source_audit']={'status':'verified_native_tactical','proof':'../../../source-input/corrected-tactical-walk/verification.json','overlay':'../../../source-input/corrected-tactical-walk/overlay.json','reference_key':'class-19-ally'}
            w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*len(poses),h))
            for i,im in sorted(poses.items()):
                asset=OUT/f'ally/{kind}/frame-{i:03}.png';path='../../../'+asset.relative_to(ROOT).as_posix();atlas.alpha_composite(im,(i*w,0));s['frame_mapping'].append({'source_index':i,'source_frame':i,'output_index':i,'path':path,'output_path':path,'size':[w,h],'bytes':asset.stat().st_size,'sha256':file_hash(asset)})
            s['output_atlas']=io.save(atlas,f'ally/{kind}-atlas.png','exact source slot order');m['scenarios'].append(s)
        write(p/'maps/frame_mapping.json',m)
        baseline=json.loads((OUT/'baseline.json').read_text());body=baseline['body'];order=sorted(battle_poses);atlas=Image.new('RGBA',(320*len(order),256))
        for n,i in enumerate(order):atlas.alpha_composite(battle_poses[i],(320*n,0))
        bm={'schema_version':1,'character_id':'class-19-ally','original_class_id':19,'source_side':'ally','display_name':'盟军博学术师','display_class_name':'博学术师','status':'review_candidate','runtime_integrated':False,'revision':REV,'modified_by':'codex','review_note':note,'palette':HEX,'output_frame_size':[320,256],'source_idle_frame':0,'variant_keys':list(baseline['variants']),'frame_mapping':{str(i):'../../../'+(OUT/f'ally/battle/frame-{i:03}.png').relative_to(ROOT).as_posix() for i in order},'output_atlas':io.save(atlas,'ally/battle-atlas.png','all required native battle slots'),'output_atlas_order':order,'qa_report':'../../../'+REV+'/verification.json','batches':[{'id':'博学术师全姿势','review':'../../../'+REV+'/ally-battle-light.png','status':'review_candidate'}]}
        write(p/'battle/frame_mapping.json',bm);write(p/'manifest.json',{'id':'class-19-ally','revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
        write(OUT/'mapping-drafts.json',{'maps':m,'battle':bm})
    write(OUT/'registration.json',{'revision':REV,'palette':HEX,'registrations':REG,'stable_regions':STABLE,'cape_native_frames':[16,17,18,19,20],'native_idle_aliases':[0,1,2,1,0,1],'runtime_integrated':False})
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS})
    print(json.dumps({'map_slots':14,'battle_slots':len(battle_poses),'published':publish}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)
