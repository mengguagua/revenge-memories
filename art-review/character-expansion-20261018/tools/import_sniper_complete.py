#!/usr/bin/env python3
"""New five-material class13 art; immutable native faction timelines."""
import argparse,copy,json,math
from functools import lru_cache
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_knight_redraw_v3 as helper

REV='sniper-complete-v1-20261022'
OUT=ROOT/REV;SRC=OUT/'source'
HEX=['172638','3976b5','e4e1c8','dda77d','8c6b45']
EHEX=['172638','4f4f7d','bbc1d6','dda77d','8c6b45']
C=[tuple(bytes.fromhex(x))for x in HEX];EC=[tuple(bytes.fromhex(x))for x in EHEX]
ASSETS=[];REG=[];STABLE={}

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    if im.mode=='RGBA':
        colors=sorted(set(im.getdata()));assert len(colors)<=256
        q=Image.new('P',im.size);q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-3*len(colors)))
        table={c:i for i,c in enumerate(colors)};q.putdata([table[c]for c in im.getdata()]);q.info['transparency']=bytes(c[3]for c in colors)
        assert q.convert('RGBA').tobytes()==im.tobytes()
    else:q=im
    q.save(p,optimize=True)
    ASSETS.append({'path':p.relative_to(ROOT).as_posix(),'size':list(im.size),'bytes':p.stat().st_size,'sha256':file_hash(p),'purpose':purpose})
    return '../../../'+p.relative_to(ROOT).as_posix()

@lru_cache(maxsize=30000)
def material(rgb):return min(range(5),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,C[i])))

def quant(im):
    q=Image.new('RGBA',im.size)
    q.putdata([(*C[material(p[:3])],255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()])
    return q

def box(points):return[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1]
def center(b):return[(b[0]+b[2])/2,(b[1]+b[3])/2]

def face(im):
    pts=[(x,y)for y in range(round(im.height*.70))for x in range(im.width)if im.getpixel((x,y))[3]and im.getpixel((x,y))[:3]==C[3]]
    cs=helper.parts(pts)
    candidates=[c for c in cs if len(c)>12 and center(box(c))[1]<im.height*.46 and .5<(box(c)[2]-box(c)[0])/(box(c)[3]-box(c)[1])<2.3]
    if not candidates:candidates=cs
    def score(c):
        x,y=center(box(c));return len(c)/(1+10*((x/im.width-.55)**2+(y/im.height-.28)**2))
    c=max(candidates,key=score);b=box(c)
    return center(b),b

def waist(im):
    pts=[(x,y)for y in range(round(im.height*.38),round(im.height*.76))for x in range(im.width)if im.getpixel((x,y))[3]and im.getpixel((x,y))[:3]==C[4]]
    cs=helper.parts(pts)
    good=[c for c in cs if box(c)[2]-box(c)[0]>1.65*(box(c)[3]-box(c)[1]) and len(c)>15]
    if not good:return [im.width*.55,im.height*.55],[]
    b=box(max(good,key=len));return center(b),b

@lru_cache(maxsize=20)
def figures(name,count):
    helper.SRC=SRC
    out=[]
    for n,(im,meta) in enumerate(helper.figures(name,count)):
        q=quant(im);fp,fb=face(q);wp,wb=waist(q)
        if name=='map-idle-master.png'and n==0:wp=[207,wp[1]]
        if name=='fix-walk-07-master.png':wp=[453,635]
        # Only remove generated blue glints within the actual head bounds.
        radius=max(fb[2]-fb[0],fb[3]-fb[1])
        hair=[max(0,round(fp[0]-radius)),max(0,round(fb[1]-radius*1.05)),min(q.width,round(fp[0]+radius)),fb[3]]
        for y in range(hair[1],hair[3]):
            for x in range(hair[0],hair[2]):
                p=q.getpixel((x,y))
                if p[3]and p[:3]==C[1]:q.putpixel((x,y),(*C[0],255))
        out.append((q,{**meta,'face':fp,'face_box':fb,'waist':wp,'waist_box':wb,'hair_flatten_region':hair}))
    return out

def register(fig,size,target,scale,label,landmark='waist'):
    im,meta=fig;p=meta[landmark];dims=[round(im.width*scale),round(im.height*scale)];small=im.resize(dims,Image.Resampling.NEAREST)
    at=[round(target[i]-p[i]*dims[i]/im.size[i])for i in range(2)]
    q=Image.new('RGBA',size);q.alpha_composite(small,tuple(at))
    assert sum(p[3]>0 for p in small.getdata())==sum(p[3]>0 for p in q.getdata()),(label,'clipped',at,dims)
    cc=helper.parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3]);removed=0
    for c in cc[1:]:
        assert len(c)<=8,(label,'detached component',len(c))
        for xy in c:q.putpixel(xy,(0,0,0,0));removed+=1
    REG.append({**meta,'label':label,'registration_landmark':landmark,'target':target,'scale':scale,'dimensions':dims,'translation':at,'clipped_pixels':0,'removed_resampling_specks':removed,'method':'whole drawn pose, uniform scale and integer translation'})
    return q

def fixed(poses,ids,region,label):
    patch=poses[ids[0]].crop(region)
    for i in ids[1:]:poses[i].paste(patch,region[:2])
    STABLE[label]={'frames':ids,'fixed_region':region,'global_bob':[0,0]}

def map_art():
    idle={};raw=figures('map-idle-master.png',3)
    scale=min(27/(im.height-m['waist'][1])for im,m in raw)
    for i,f in enumerate(raw):idle[i]=register(f,(96,96),[48,53],scale,f'idle-{i}')
    for b in [[37,18,60,41],[40,42,57,55],[26,57,72,81]]:fixed(idle,[0,1,2],b,'idle-'+str(b))
    fb=figures('map-front-back-master.png',4);side=figures('map-sides-master.png',4)
    # Register support legs to the native source footer, not an assumed phase.
    # Native up0 supports left/up1 right; down4 right/down5 left.
    raw_walk={0:fb[1],1:fb[0],2:side[0],3:side[1],4:figures('fix-walk-05-master.png',1)[0],5:fb[2],6:side[2],7:figures('fix-walk-07-master.png',1)[0]}
    walk={}
    for ids in [[0,1],[2,3],[4,5],[6,7]]:
        for i in ids:
            # Separate repaired masters have different source pixel density.
            # Normalize each full drawing to the same waist/ground span.
            scale=27/(raw_walk[i][0].height-raw_walk[i][1]['waist'][1])
            walk[i]=register(raw_walk[i],(128,96),[64,67],scale,f'walk-{i}')
        fixed(walk,ids,[51,30,79,54],'walk-head-'+str(ids))
        fixed(walk,ids,[57,60,71,69],'walk-core-'+str(ids))
    return {'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle_art():
    prepare=figures('battle-prepare-master.png',6);release=figures('battle-release-master.png',3);rest=figures('battle-rest-master.png',2)
    ally={1:rest[0],2:rest[1],**dict(zip([10,11,12,13],prepare[2:])),**dict(zip([14,15,16],release))}
    ep=figures('enemy-prepare-master.png',6);ea=figures('enemy-aim-master.png',6);er=figures('enemy-release-master.png',1)
    enemy={**dict(zip([1,16,17,18,19,20],ep)),**dict(zip([21,22,23,24,25,26],ea)),27:er[0]}
    out={}
    for side,raw in [('ally',ally),('enemy',enemy)]:
        poses={}
        for i,f in raw.items():
            target=[220,156]if side=='ally'else[124,140]
            if side=='ally'and i in[2,10]:target=[220,160]
            scale=(255-target[1])/(f[0].height-f[1]['face'][1])
            poses[i]=register(f,(320,256),target,scale,f'{side}-battle-{i}',landmark='face')
        out[side]=poses
    return out

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(C,EC));q=Image.new('RGBA',im.size)
    q.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()])
    return q

def board(entries,side,kind,light):
    cw,ch=(300,270)if kind=='maps'else(360,320);cols=4
    q=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242)
    d.text((q.width//2,25),('盟军'if side=='ally'else'敌方')+'狙击手 · '+('地图姿态'if kind=='maps'else'战斗姿态'),anchor='mm',font=font(21),fill=fg)
    for n,(label,im)in enumerate(entries):
        if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
        x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;q.paste(im,(x,y),im)
        assert d.textbbox((0,0),label,font=font(16))[2]<cw-32
        d.text((n%cols*cw+cw//2,y+ch-20),label,anchor='mm',font=font(16),fill=fg)
    save(q,f'{side}-{kind}-{"light"if light else"dark"}.png','complete pose board; measured text/figure gap')

def build(publish=False):
    b=json.loads((OUT/'baseline.json').read_text());maps=map_art();battle=battle_art();drafts={}
    template=json.loads((ROOT/'professions/class-10-ally/maps/frame_mapping.json').read_text());audit=json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())
    note='狙击手：弓箭手四色加柔和棕色，整片米白护甲、长弓与箭袋；固定地图头部和腰胯，双方按各自原作取箭、转弓、拉弦、单次释放及收势时序。'
    for side in ['ally','enemy']:
        actor=f'class-13-{side}';name=('盟军'if side=='ally'else'敌方')+'狙击手';entries={'maps':[],'battle':[]};m=copy.deepcopy(template)
        m.update(character_id=actor,actor_id=actor,class_id=13,source_side=side,display_name=name,display_class_name='狙击手',revision=REV,modified_by='codex',status='review_candidate',runtime_integrated=False,review_note=note)
        for scene in m['scenarios']:
            kind=scene['id'];frames=maps[kind];w,h=scene['output_frame_size'];atlas=Image.new('RGBA',(len(frames)*w,h))
            scene.update(source_atlas=f'../../../source-input/corrected-tactical-walk/{actor}.png'if kind=='tactical-walk'else f'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_13_{side}.png',revision=REV,status='review_candidate',review_note=note,motion_review={'revision':REV,'fixed_regions':STABLE,'source_timing_modified':False,'native_independent_direction_slots':True})
            if kind=='tactical-walk':scene['source_audit']={**audit['records'][actor],'status':'verified_native_tactical','overlay':'../../../source-input/corrected-tactical-walk/overlay.json'}
            for row in scene['frame_mapping']:
                i=row['source_index'];im=faction(frames[i],side);p=save(im,f'{side}/{kind}/frame-{i:03}.png','new native map pose in the five approved materials');row.update(path=p,output_path=p,revision=REV,bytes=ASSETS[-1]['bytes'],sha256=ASSETS[-1]['sha256'],size=[w,h]);atlas.alpha_composite(im,(i*w,0))
                if kind=='tactical-walk'or i<3:entries['maps'].append((('待机'if kind=='tactical-idle'else['上','上','右','右','下','下','左','左'][i])+f' {i}',im))
            scene['output_atlas']=save(atlas,f'{side}/{kind}-atlas.png','native map slot order')
        drafts[f'professions/{actor}/maps/frame_mapping.json']=m
        body=b['source_bodies'][side];poses={i:faction(im,side)for i,im in battle[side].items()};order=sorted(poses);records=[];paths={};atlas=Image.new('RGBA',(320*len(order),256))
        for n,i in enumerate(order):
            im=poses[i];paths[str(i)]=save(im,f'{side}/battle/frame-{i:03}.png','independently drawn faction-native bow preparation/draw/release pose');records.append({'source_frame':i,'path':paths[str(i)],'size':[320,256],'bytes':ASSETS[-1]['bytes'],'sha256':ASSETS[-1]['sha256']});atlas.alpha_composite(im,(n*320,0));entries['battle'].append((f'原姿势 {i}',im))
        m={'schema_version':1,'character_id':actor,'display_name':name,'display_class_name':'狙击手','original_class_id':13,'source_side':side,'source_atlas':'../../../source-input/'+('original-motion/class-13.png'if side=='ally'else'enemy-motion/class-13-enemy.png'),'source_frame_size':body['frame_size'],'output_frame_size':[320,256],'source_anchor':body['anchor'],'output_anchor':[160,256],'source_columns':16,'source_oam_frame_count':1,'source_idle_frame':1,'source_frame_count':body['frames'],'frame_mapping':paths,'canonical_frames':order,'required_source_frames':order,'variant_keys':list(b['variants'][side]),'records':records,'output_atlas_frame_order':order,'output_atlas':save(atlas,f'{side}/battle-atlas.png','all required faction-native battle slots'),'status':'review_candidate','revision':REV,'modified_by':'codex','runtime_integrated':False,'review_note':note,'palette':HEX if side=='ally'else EHEX,'art_provenance':'Built-in ImageGen new full poses, material indexing, uniform whole-pose registration; unchanged native projectile/effect timelines','batches':[{'id':'full-pose-review','review':f'../../../{REV}/{side}-battle-light.png','status':'review_candidate'}]}
        drafts[f'professions/{actor}/battle/frame_mapping.json']=m
        for kind,ims in entries.items():
            for light in [False,True]:board(ims,side,kind,light)
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'generator':'built-in image_gen','palette':{'ally':HEX,'enemy':EHEX},'base_archer_palette_plus_one':True,'assets':ASSETS,'registration':REG,'fixed_regions':STABLE,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for p,m in drafts.items():write(ROOT/p,m)
        for side in ['ally','enemy']:write(ROOT/f'professions/class-13-{side}/manifest.json',{'id':f'class-13-{side}','class_id':13,'display_name':('盟军'if side=='ally'else'敌方')+'狙击手','revision':REV,'status':'review_candidate','maps':'maps/frame_mapping.json','battle':'battle/frame_mapping.json','runtime_integrated':False})
    print(json.dumps({'assets':len(ASSETS),'registrations':len(REG),'mappings':len(drafts),'published':publish}),flush=True)

def inspect():
    for name,count in [('map-idle-master.png',3),('map-front-back-master.png',4),('map-sides-master.png',4),('fix-walk-05-master.png',1),('fix-walk-07-master.png',1),('battle-rest-master.png',2),('battle-prepare-master.png',6),('battle-release-master.png',3),('enemy-prepare-master.png',6),('enemy-aim-master.png',6),('enemy-release-master.png',1)]:
        if not(SRC/name).exists():continue
        print(name,[(list(im.size),m['face'],m['face_box'],m['waist'],m['waist_box'])for im,m in figures(name,count)],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');p.add_argument('--inspect',action='store_true');a=p.parse_args();inspect()if a.inspect else build(a.publish)
