#!/usr/bin/env python3
"""Stage whole new class10 pose drawings with the unchanged native programs."""
import argparse,copy,json,math
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFilter
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_knight_redraw_v3 as helper
from revise_cavalry_map import translate

REV='swordmaster-complete-v1-20261022';OUT=ROOT/REV;SRC=OUT/'source'
HEX=['172638','3976b5','e4e1c8','dda77d','2c527e','b5a16c']
EHEX=['172638','4f4f7d','bbc1d6','dda77d','373e64','a394b1']
C=[tuple(bytes.fromhex(h))for h in HEX];EC=[tuple(bytes.fromhex(h))for h in EHEX]
ASSETS=[];REG=[];STABLE={}

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);q=im
    if im.mode=='RGBA':
        colors=sorted(set(im.getdata()));assert len(colors)<=256
        q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-3*len(colors)))
        table={c:i for i,c in enumerate(colors)};q.putdata([table[p]for p in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors);assert q.convert('RGBA').tobytes()==im.tobytes()
    q.save(path,optimize=True);ASSETS.append({'path':path.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path),'purpose':purpose});return'../../../'+path.relative_to(ROOT).as_posix()

@lru_cache(maxsize=80000)
def material(rgb):return min(range(6),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,C[i])))

def quant(im):
    out=Image.new('RGBA',im.size);out.putdata([(*C[material(p[:3])],255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()]);return out

def face(im,back=False):
    p=im.load();limit=round(im.height*(.43 if back else .70))
    points=[(x,y)for y in range(limit)for x in range(im.width)if p[x,y][3]and p[x,y][:3]==C[3]and(not back or im.width*.27<x<im.width*.73)]
    cs=helper.parts(points);assert cs,('missing face/ear',im.size)
    if back:
        top=min(y for x,y in points);cs=[c for c in cs if min(y for x,y in c)<=top+max(4,im.height*.025)];pts=[p for c in cs for p in c]
    else:pts=cs[0]
    b=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts)+1,max(y for x,y in pts)+1]
    return[(b[0]+b[2])/2,(b[1]+b[3])/2],b

@lru_cache(maxsize=20)
def figures(name,count,back_ids=()):
    helper.SRC=SRC;raw=helper.figures(name,count);out=[]
    for i,(im,meta)in enumerate(raw):
        im=quant(im);p,b=face(im,i in back_ids)
        # Material normalization only: hair has one navy fill, no blue glints.
        if i not in back_ids:
            radius=max(b[2]-b[0],b[3]-b[1]);box=[max(0,round(p[0]-radius*.95)),max(0,round(b[1]-radius*1.1)),min(im.width,round(p[0]+radius*.95)),min(im.height,round(b[1]+radius*.15))]
        else:
            box=[max(0,round(p[0]-im.width*.23)),max(0,round(p[1]-im.height*.25)),min(im.width,round(p[0]+im.width*.23)),round(p[1]-2)]
        for y in range(box[1],box[3]):
            for x in range(box[0],box[2]):
                if im.getpixel((x,y))[:3]in[C[1],C[4]]and im.getpixel((x,y))[3]:im.putpixel((x,y),(*C[0],255))
        out.append((im,{**meta,'face_point':p,'face_box':b,'hair_flatten_region':box,'back':i in back_ids}))
    return out

def register(fig,size,target,scale,label):
    im,meta=fig;p=meta['face_point'];dims=[round(im.width*scale),round(im.height*scale)];small=im.resize(dims,Image.Resampling.NEAREST);delta=[round(target[i]-p[i]*dims[i]/im.size[i])for i in range(2)];out=Image.new('RGBA',size);out.alpha_composite(small,tuple(delta));before=sum(p[3]>0 for p in small.getdata());after=sum(p[3]>0 for p in out.getdata());assert before==after,(label,'clipped',delta,dims,size)
    cs=helper.parts((x,y)for y in range(size[1])for x in range(size[0])if out.getpixel((x,y))[3]);removed=0
    for c in cs[1:]:
        assert len(c)<=12,(label,'detached limb',len(c))
        for xy in c:out.putpixel(xy,(0,0,0,0));removed+=1
    REG.append({**meta,'label':label,'target_face':target,'scale':scale,'size':dims,'translation':delta,'clipped_pixels':0,'removed_tiny_resampling_pixels':removed,'method':'whole-pose uniform scale and integer translation; no joint warping'});return out

def freeze_head(poses,ids,box,label):
    first=poses[ids[0]].crop(box)
    foreground=[]
    for i in ids[1:]:
        original=poses[i].copy();poses[i].paste(first,box[:2])
        # The upright blade can pass in front of the head, especially idle2.
        # Keep each pose's complete blade and dark edge over the shared head.
        white=helper.parts((x,y)for y in range(original.height)for x in range(original.width)if original.getpixel((x,y))[3]and original.getpixel((x,y))[:3]==C[2])
        mask=Image.new('L',original.size)
        for c in white:
            b=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]
            if b[3]-b[1]>=12 and b[3]-b[1]>1.4*(b[2]-b[0])and b[1]<(box[1]+box[3])/2:
                for xy in c:mask.putpixel(xy,255)
                foreground.append({'frame':i,'blade_bounds':b})
        mask=mask.filter(ImageFilter.MaxFilter(3))
        for y in range(box[1],box[3]):
            for x in range(box[0],box[2]):
                if mask.getpixel((x,y)):poses[i].putpixel((x,y),original.getpixel((x,y)))
    STABLE[label]={'frames':ids,'fixed_head_box':box,'same_registered_head':True,'own_blade_occlusion_retained':foreground,'extra_global_bob':[0,0]}

def idle_blades(poses):
    """Use the approved native straight blade at each class10 tip/hilt."""
    from rebuild_swordsman_maps import blade_asset,place_blade
    records={}
    for i,im in poses.items():
        cc=helper.parts((x,y)for y in range(45)for x in range(48)if im.getpixel((x,y))[3]and im.getpixel((x,y))[:3]==C[2])
        candidates=[c for c in cc if max(y for x,y in c)-min(y for x,y in c)>=11]
        c=max(candidates,key=len);b=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1];mask=Image.new('L',im.size)
        for xy in c:mask.putpixel(xy,255)
        mask=mask.filter(ImageFilter.MaxFilter(3));records[i]=(c,b,mask)
    source=blade_asset(None);proof=[]
    for i,im in poses.items():
        c,b,mask=records[i];base=[(b[0]+b[2])/2,b[3]];native=Image.open(SRC/f'native-ally-idle-{i:03}.png').convert('RGBA')
        whites=[(x,y)for y in range(8)for x in range(14)if(p:=native.getpixel((x,y)))[3]and min(p[:3])>220];top=min(y for x,y in whites);xs=[x for x,y in whites if y==top];tip=[(min(xs)+max(xs))/2*4,top*4]
        # Rigid straight-blade source avoids false serrations when the small
        # generated blade's staircase edge is rotated to the native position.
        layer=place_blade(im.size,source,tip,base)
        for y in range(im.height):
            for x in range(im.width):
                if mask.getpixel((x,y))and im.getpixel((x,y))[:3]in[C[0],C[2]]:im.putpixel((x,y),(0,0,0,0))
        im.alpha_composite(layer)
        cc=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3])
        for c in cc[1:]:
            assert len(c)<=4,('idle foreground connection',i,len(c))
            for xy in c:im.putpixel(xy,(0,0,0,0))
        proof.append({'frame':i,'native_tip_at_4x':tip,'own_hilt':base,'blade_source':'approved class9 native straight blade, same navy/ivory materials'})
    STABLE['idle-sword-registration']=proof

def map_art():
    raw=figures('map-idle-master.png',3);idle_raw=[figures('fix-idle-00-master.png',1)[0],raw[1],raw[2]];idle={}
    for i,f in enumerate(idle_raw):
        p=f[1]['face_point'];scale=(80-37)/(f[0].height-p[1]);idle[i]=register(f,(96,96),[48,37],scale,f'idle-{i}')
    # Native idle fixes the lower body; preserve only the independently drawn
    # arm/sword changes, while using one complete head/torso/stance reference.
    freeze_head(idle,[0,1,2],[36,22,60,45],'idle-head')
    for i in[1,2]:
        for b in[[37,45,59,58],[28,58,77,81]]:idle[i].paste(idle[0].crop(b),b[:2])
    idle_blades(idle)
    STABLE['idle-body']={'frames':[0,1,2],'fixed_regions':[[37,45,59,58],[28,58,77,81]],'identical_pixels':True}
    fb=figures('map-front-back-master.png',4,(0,1));side=figures('map-sides-master.png',4)
    raw_walk={0:fb[0],1:figures('fix-walk-01-master.png',1,(0,))[0],2:side[0],3:side[1],4:fb[2],5:figures('fix-walk-05-master.png',1)[0],6:figures('fix-walk-06-master.png',1)[0],7:side[3]}
    walk={};targets={0:[64,43],1:[64,43],2:[64,45],3:[64,45],4:[64,45],5:[64,45],6:[60,45],7:[60,45]}
    for i,f in raw_walk.items():
        p=f[1]['face_point'];scale=(95-targets[i][1])/(f[0].height-p[1]);walk[i]=register(f,(128,96),targets[i],scale,f'walk-{i}')
    for ids,box,label in[([0,1],[48,26,81,47],'walk-up'),([2,3],[51,29,79,52],'walk-right'),([4,5],[48,28,81,53],'walk-down'),([6,7],[46,28,75,53],'walk-left')]:freeze_head(walk,ids,box,label)
    return{'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

NATIVE_FACE={0:[46,35],1:[46,35],2:[46,35],3:[47,37],4:[46,43],5:[46,45],6:[46,46],8:[44,31],9:[52,39],10:[46,38],11:[46,39],12:[44,45],14:[46,35]}
def battle_art():
    ground=figures('battle-ground-master.png',6);action=figures('battle-action-master.png',6);overhead=figures('battle-overhead-master.png',2)
    raw=dict(enumerate(ground));raw.update({i:f for i,f in zip([6,8,9,10,11,12],action)});raw[6]=figures('fix-battle-06-master.png',1)[0];raw[11]=figures('fix-battle-11-master.png',1)[0];raw[14]=overhead[0];poses={}
    # Every complete pose is registered to the corresponding native face and
    # foot level, preserving intentional crouch/jump motion in its own cell.
    for i,f in raw.items():
        p=f[1]['face_point'];target=[v*4 for v in NATIVE_FACE[i]];native_bottom=58 if i==8 else 67 if i in[9,10]else 65 if i==12 else 64;scale=(native_bottom*4-target[1])/(f[0].height-p[1]);poses[i]=register(f,(320,288),target,scale,f'battle-{i}')
    # Source0/1/2 have exactly the same fixed head and stance while the hilt
    # reaching arm changes. Keep this core stable in the new art as well.
    freeze_head(poses,[0,1,2],[165,115,202,158],'battle-draw-head')
    for i in[1,2]:poses[i].paste(poses[0].crop((150,200,222,257)),(150,200))
    poses[15]=Image.new('RGBA',(320,288));poses[16]=poses[0].copy();poses[31]=poses[0].copy();poses[32]=poses[14].copy()
    # Native7 = native8 translated(-10,-24) plus the launch star; native13 =
    # native12 plus one slash arc. Preserve those effects exactly, unretouched.
    for side in['ally','enemy']:
        for target,source,delta in[(7,8,[-10,-24]),(13,12,[0,0])]:
            a=Image.open(SRC/f'native-{side}-battle-{target:03}.png').convert('RGBA');body=translate(Image.open(SRC/f'native-{side}-battle-{source:03}.png').convert('RGBA'),delta);fx=a.copy()
            for y in range(72):
                for x in range(80):
                    if body.getpixel((x,y))[3]:assert a.getpixel((x,y))==body.getpixel((x,y));fx.putpixel((x,y),(0,0,0,0))
            fx=fx.resize((320,288),Image.Resampling.NEAREST);save(fx,f'{side}/native-effect-{target:02}.png','exact native launch/slash effect separated from its own-faction body')
    return poses

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(C,EC));out=Image.new('RGBA',im.size);out.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return out

def board(entries,side,kind,light):
    cw,ch=(300,260)if kind=='maps'else(344,330);cols=4;out=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(out);fg=(23,38,56)if light else(235,243,242)
    d.text((out.width//2,26),('盟军'if side=='ally'else'敌方')+'剑豪 · '+('地图姿态'if kind=='maps'else'战斗姿态'),anchor='mm',font=font(21),fill=fg)
    for n,(label,im)in enumerate(entries):
        if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
        x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;out.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,y+ch-20),label,anchor='mm',font=font(16),fill=fg)
    save(out,f'{side}-{kind}-{"light"if light else"dark"}.png','full pose board for deep/light background inspection')

def build(publish=False):
    base=json.loads((OUT/'baseline.json').read_text());mapart=map_art();battle=battle_art();drafts={};template=json.loads((ROOT/'professions/class-9-ally/maps/frame_mapping.json').read_text());audit=json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())
    for side in['ally','enemy']:
        actor=f'class-10-{side}';name=('盟军'if side=='ally'else'敌方')+'剑豪';entries={'maps':[],'battle':[]};m=copy.deepcopy(template)
        m.update(character_id=actor,actor_id=actor,class_id=10,display_name=name,display_class_name='剑豪',source_side=side,revision=REV,modified_by='codex',status='review_candidate',runtime_integrated=False,review_note='剑豪新形象：宽肩轻甲、蓝白分层短衣与软质披风；六色哑光，纯色头发。原作方向槽、拔剑／跳跃／落地斩击顺序与时序保持。')
        for s in m['scenarios']:
            kind=s['id'];frames=mapart[kind];s.update(source_atlas=f'../../../source-input/corrected-tactical-walk/{actor}.png'if kind=='tactical-walk'else f'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_10_{side}.png',revision=REV,status='review_candidate',review_note=m['review_note'],motion_review={'revision':REV,'stable_regions':STABLE,'source_timing_modified':False,'independent_native_direction_slots':True,'cape_is_not_a_shield':True});s.pop('output_atlas_bytes',None)
            if kind=='tactical-walk':s['source_audit']={**audit['records'][actor],'status':'verified_native_tactical','overlay':'../../../source-input/corrected-tactical-walk/overlay.json'}
            w,h=s['output_frame_size'];atlas=Image.new('RGBA',(len(frames)*w,h))
            for row in s['frame_mapping']:
                i=row['source_index'];im=faction(frames[i],side);path=save(im,f'{side}/{kind}/frame-{i:03}.png','complete newly drawn native map pose with matte six-color materials');row.update(path=path,output_path=path,revision=REV,art_status='review_candidate',size=[w,h],bytes=ASSETS[-1]['bytes'],sha256=ASSETS[-1]['sha256']);atlas.alpha_composite(im,(i*w,0))
                if kind=='tactical-walk'or i<3:entries['maps'].append((('待机'if kind=='tactical-idle'else['上','上','右','右','下','下','左','左'][i])+f' {i}',im))
            s['output_atlas']=save(atlas,f'{side}/{kind}-atlas.png','native slot order')
        drafts[f'professions/{actor}/maps/frame_mapping.json']=m
        body=base['source_bodies'][side];poses={i:faction(im,side)for i,im in battle.items()}
        for t,s,delta in[(7,8,[-40,-96]),(13,12,[0,0])]:
            im=Image.open(OUT/side/f'native-effect-{t:02}.png').convert('RGBA');im.alpha_composite(translate(poses[s],delta));poses[t]=im
        records=[];paths={};order=sorted(poses);atlas=Image.new('RGBA',(len(order)*320,288))
        for n,i in enumerate(order):
            im=poses[i];shift=-64 if side=='enemy'and i in[16,31,32]else 0
            if shift:im=translate(im,[shift,0])
            paths[str(i)]=save(im,f'{side}/battle/frame-{i:03}.png','whole native battle body; original blank15, aliases and native effects retained');records.append({'source_frame':i,'path':paths[str(i)],'size':[320,288],'bytes':ASSETS[-1]['bytes'],'sha256':ASSETS[-1]['sha256'],'source_background_translation':[shift,0]});atlas.alpha_composite(im,(n*320,0))
            if i not in[16,31]:entries['battle'].append((f'原姿势 {i}',im))
        variants=list(base['variants'][side]);m={'schema_version':1,'character_id':actor,'display_name':name,'display_class_name':'剑豪','original_class_id':10,'source_side':side,'source_atlas':'../../../source-input/'+('original-motion/class-10.png'if side=='ally'else'enemy-motion/class-10-enemy.png'),'source_frame_size':[80,72],'output_frame_size':[320,288],'source_anchor':[40,64],'output_anchor':[160,256],'source_columns':16,'source_oam_frame_count':16,'source_idle_frame':16,'source_frame_count':33,'frame_mapping':paths,'canonical_frames':order,'required_source_frames':order,'variant_keys':variants,'records':records,'output_atlas_frame_order':order,'output_atlas':save(atlas,f'{side}/battle-atlas.png','all required new battle slots'),'status':'review_candidate','revision':REV,'modified_by':'codex','runtime_integrated':False,'review_note':'背负长剑、抬臂握柄、下蹲蓄势、起跳、离画空帧、举剑落地与斩击收势按原程序；不新增攻击次数。原起跳残影、刀弧和雷之剑外置效果保持。','batches':[{'id':'full-pose-review','review':f'../../../{REV}/{side}-battle-dark.png','status':'review_candidate'}],'palette':HEX if side=='ally'else EHEX,'source_semantics':{'0-6':'back-carried sword, reach hilt and crouch progressively','7':'body8 moved(-10,-24) plus original launch star','8-11':'original airborne leg and overhead sword phases','12':'one low landing slash follow-through','13':'same body12 plus original slash arc','14':'overhead recovery','15':'intentionally transparent native airborne interval','16/31':'idle aliases of0','32':'same pose as14; native background upload differs by one pale filler pixel','enemy16/31/32':'native background storage offset -16 logical X, renderer preserves faction flip/origin correction'},'art_provenance':'Built-in ImageGen new full poses; uniform whole-pose registration, indexed materials and fixed core; no anatomy generated in code.'};drafts[f'professions/{actor}/battle/frame_mapping.json']=m
        for kind,ims in entries.items():
            for light in[False,True]:board(ims,side,kind,light)
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'generator':'built-in image_gen','palette':{'ally':HEX,'enemy':EHEX},'map_palette_is_approved_swordsman_plus_two_colors':True,'assets':ASSETS,'registration':REG,'stable_regions':STABLE,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for p,m in drafts.items():write(ROOT/p,m)
        for side in['ally','enemy']:write(ROOT/f'professions/class-10-{side}/manifest.json',{'id':f'class-10-{side}','class_id':10,'display_name':('盟军'if side=='ally'else'敌方')+'剑豪','revision':REV,'status':'review_candidate','maps':'maps/frame_mapping.json','battle':'battle/frame_mapping.json','runtime_integrated':False})
    print(json.dumps({'assets':len(ASSETS),'mappings':len(drafts),'registrations':len(REG),'published':publish}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--inspect',action='store_true');a=p.parse_args()
    if a.inspect:
        for name,n,back in[('map-idle-master.png',3,()),('map-front-back-master.png',4,(0,1)),('map-sides-master.png',4,()),('fix-idle-00-master.png',1,()),('fix-walk-01-master.png',1,(0,)),('fix-walk-05-master.png',1,()),('fix-walk-06-master.png',1,()),('battle-ground-master.png',6,()),('battle-action-master.png',6,()),('battle-overhead-master.png',2,()),('fix-battle-06-master.png',1,()),('fix-battle-11-master.png',1,())]:
            print(name,[(list(im.size),m['face_point'],m['face_box'])for im,m in figures(name,n,back)],flush=True)
    else:build(a.publish)
