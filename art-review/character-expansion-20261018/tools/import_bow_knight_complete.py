#!/usr/bin/env python3
"""Six-material class20 poses, stable map bodies, immutable native schedules."""
import argparse,copy,json,math
from functools import lru_cache
from collections import Counter
from PIL import Image,ImageDraw,ImageFilter
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_sniper_complete as io
from prepare_bow_knight_complete import REV,OUT,SRC

HEX=['172638','3976b5','e4e1c8','dda77d','8c6b45','889cab']
EHEX=['172638','4f4f7d','bbc1d6','dda77d','8c6b45','7c87a3']
C=[tuple(bytes.fromhex(c))for c in HEX];EC=[tuple(bytes.fromhex(c))for c in EHEX]
FILES={'map-idle-master.png':3,'map-front-back-master.png':4,'battle-prepare-master.png':4,'battle-release-master.png':3,'enemy-battle-master.png':3}
STABLE={}
SKIN_AUDIT=[]
WEAPON_AUDIT=[]

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def save(im,path,purpose):return io.save(im,path,purpose)

@lru_cache(maxsize=30000)
def material(p):return min(range(6),key=lambda i:sum((a-b)**2 for a,b in zip(p,C[i])))

def quant(im):
    q=Image.new('RGBA',im.size);q.putdata([(*C[material(p[:3])],255)if p[3]>=128 else(0,0,0,0)for p in im.getdata()]);return q

def face(im):
    cs=io.helper.parts((x,y)for y in range(round(im.height*.6))for x in range(im.width)if im.getpixel((x,y))[3]and im.getpixel((x,y))[:3]==C[3])
    good=[c for c in cs if len(c)>15 and io.center(io.box(c))[1]<im.height*.44]
    if not good:good=cs
    if not good:return [im.width*.55,im.height*.22],[]
    def score(c):
        x,y=io.center(io.box(c));return len(c)/(1+18*((x/im.width-.56)**2+(y/im.height-.24)**2))
    box=io.box(max(good,key=score));return io.center(box),box

def figures(filename):
    io.helper.SRC=SRC
    overrides=json.loads((SRC/'registration-landmarks.json').read_text())if(SRC/'registration-landmarks.json').exists()else{}
    out=[]
    for i,(im,meta)in enumerate(io.helper.figures(filename,FILES[filename])):
        q=quant(im);head,fb=face(q);m={**meta,'head':head,'face_box':fb}
        if filename in overrides and str(i)in overrides[filename]:m.update(overrides[filename][str(i)])
        if 'hair_region'not in m and m['face_box']:
            x0,y0,x1,y1=m['face_box'];w=x1-x0;h=y1-y0
            m['hair_region']=[max(0,round(x0-w*.6)),max(0,round(y0-h*1.25)),min(q.width,round(x1+w*.6)),y1]
        if m.get('hair_region'):
            x0,y0,x1,y1=m['hair_region']
            for y in range(y0,y1):
                for x in range(x0,x1):
                    p=q.getpixel((x,y))
                    if p[3]and p[:3]in[C[1],C[5]]:q.putpixel((x,y),(*C[0],255))
        out.append((q,m))
    return out

def fixed(poses,ids,box,label):
    patch=poses[ids[0]].crop(box)
    for i in ids[1:]:poses[i].paste(patch,box[:2])
    STABLE[label]={'source_pose':ids[0],'shared_poses':ids,'complete_upper_body_region':box,'global_translation':[0,0]}

def skin_materials(im,label,boxes=None):
    # The generator sometimes shades ivory horse armor with a peach-tinted
    # highlight. Preserve peach only on the rider's actual face/hands.
    if boxes is None:
        comps=io.helper.parts((x,y)for y in range(78,157)for x in range(im.width)if im.getpixel((x,y))[3]and im.getpixel((x,y))[:3]==C[3])
        boxes=[io.box(c)for c in comps[:3]]
    converted=0
    for y in range(im.height):
        for x in range(im.width):
            p=im.getpixel((x,y))
            if p[3]and p[:3]==C[3]and not any(b[0]<=x<b[2]and b[1]<=y<b[3]for b in boxes):
                im.putpixel((x,y),(*C[2],255));converted+=1
    SKIN_AUDIT.append({'label':label,'rider_skin_regions':boxes,'removed_peach_tinted_armor_pixels':converted})
    return im

def greatbow_asset():
    raw=Image.open(SRC/'map-greatbow-master.png').convert('RGBA');fill=Image.new('RGBA',raw.size)
    for y in range(raw.height):
        for x in range(raw.width):
            r,g,b,a=raw.getpixel((x,y))
            # Discard the unwanted generated glow, retaining the actual
            # ivory/wood drawing and a crisp contour at its native size.
            if a>=128 and ((r>180 and g>150 and b>90)or(r>90 and r>1.1*g and g>1.15*b)):
                c=min([C[2],C[4]],key=lambda c:sum((v-w)**2 for v,w in zip((r,g,b),c)));fill.putpixel((x,y),(*c,255))
    bb=fill.getbbox();cut=fill.crop(bb);small=cut.resize((round(cut.width*68/cut.height),68),Image.Resampling.NEAREST)
    q=Image.new('RGBA',(small.width+2,70));q.alpha_composite(small,(1,1));mask=q.getchannel('A').filter(ImageFilter.MaxFilter(3));outline=Image.new('RGBA',q.size,(*C[0],255));outline.putalpha(mask)
    points=[(x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3]]
    top=min(points,key=lambda p:(p[1],p[0]));bottom=max(points,key=lambda p:(p[1],-p[0]))
    # A taut one-pixel string joins the two actual generated limb tips.
    ImageDraw.Draw(outline).line([top,bottom],fill=(*C[0],255),width=1);outline.alpha_composite(q)
    brown=[(x,y)for y in range(outline.height)for x in range(outline.width)if outline.getpixel((x,y))==(*C[4],255)]
    grip=io.center(io.box(brown));save(outline,'source/map-greatbow-indexed.png','complete ImageGen greatbow, matte three-material limb drawing and native one-pixel string')
    WEAPON_AUDIT.append({'source':'source/map-greatbow-master.png','source_fill_bounds':bb,'indexed_size':list(outline.size),'grip':grip,'complete_upper_and_lower_limb':True})
    return outline,grip

def map_bow(im,asset,grip,view,label):
    q=im.copy();hand=(63,37,69,44)if view=='side'else(74,41,81,49);saved=q.crop(hand)
    for y in range(q.height):
        for x in range(q.width):
            erase=((y<23 and x>=57)or(23<=y<44 and x>=64))if view=='side'else(y<42 and x>=76)
            if erase:q.putpixel((x,y),(0,0,0,0))
    height=70 if view=='side'else 76;ratio=height/asset.height;small=asset.resize((round(asset.width*ratio),height),Image.Resampling.NEAREST)
    target=[65.5,41]if view=='side'else[77,45];at=[round(target[0]-grip[0]*small.width/asset.width),round(target[1]-grip[1]*small.height/asset.height)]
    q.alpha_composite(small,tuple(at));q.paste(saved,hand[:2])
    WEAPON_AUDIT.append({'label':label,'grip_target':target,'weapon_height':height,'translation':at,'uniform_scale':ratio,'hand_region_preserved':hand})
    return q

def maps():
    raw=figures('map-idle-master.png');idle={};bow,grip=greatbow_asset()
    scale=min(52/(im.height-m['head'][1])for im,m in raw)
    for i,f in enumerate(raw):
        q=skin_materials(io.register(f,(96,96),[43,28],scale,f'idle-{i}',landmark='head'),f'idle-{i}',[[39,23,48,32],[63,37,69,44]])
        idle[i]=map_bow(q,bow,grip,'side',f'idle-{i}')
    fixed(idle,[0,1,2],[0,0,96,56],'idle-connected-rider-and-horse-body')
    fb=figures('map-front-back-master.png');walk={}
    for ids,source in [([0,1],fb[:2]),([4,5],fb[2:])]:
        scale=min(60/(im.height-m['head'][1])for im,m in source)
        for i,f in zip(ids,source):
            q=io.register(f,(128,96),[64,34],scale,f'walk-{i}',landmark='head')
            boxes=[[49,43,56,51],[58,36,63,41]]if i<2 else[[58,30,70,39],[50,43,57,51],[74,41,81,50]]
            q=skin_materials(q,f'walk-{i}',boxes)
            walk[i]=map_bow(q,bow,grip,'front',f'walk-{i}')if i>=4 else q
        fixed(walk,ids,[0,0,128,68],'walk-connected-upper-body-'+str(ids))
    for i,j in [(6,0),(7,2)]:
        q=Image.new('RGBA',(128,96));q.alpha_composite(idle[j],(16,16));walk[i]=q
    for i,j in [(2,6),(3,7)]:walk[i]=walk[j].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return {'tactical-idle':{i:idle[j].copy()for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle():
    prepare=figures('battle-prepare-master.png');release=figures('battle-release-master.png');enemy=figures('enemy-battle-master.png')
    raw={'ally':dict(zip([1,13,14,15,16,17,18],prepare+release)),'enemy':dict(zip([1,5,6],enemy))};out={}
    for side,poses in raw.items():
        out[side]={};target=[212,104]if side=='ally'else[180,104]
        for i,f in poses.items():
            im,m=f;scale=(255-target[1])/(im.height-m['head'][1])
            out[side][i]=skin_materials(io.register(f,(320,256),target,scale,f'{side}-battle-{i}',landmark='head'),f'{side}-battle-{i}')
    return out

def faction(im,side):
    if side=='ally':return im.copy()
    table=dict(zip(C,EC));q=Image.new('RGBA',im.size);q.putdata([(*table[p[:3]],p[3])if p[3]else(0,0,0,0)for p in im.getdata()]);return q

def board(entries,side,kind,light):
    cw,ch=(320,280)if kind=='maps'else(390,330);cols=4
    q=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(entries)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56)if light else(235,243,242)
    d.text((q.width//2,26),('盟军'if side=='ally'else'敌方')+'弓骑士 · '+('地图姿态'if kind=='maps'else'战斗姿态'),anchor='mm',font=font(22),fill=fg)
    for n,(label,im)in enumerate(entries):
        if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
        x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch;q.paste(im,(x,y),im)
        assert d.textbbox((0,0),label,font=font(16))[2]<cw-32
        d.text((n%cols*cw+cw//2,y+ch-22),label,anchor='mm',font=font(16),fill=fg)
    save(q,f'{side}-{kind}-{"light"if light else"dark"}.png','full pose board; measured label and figure spacing')

def projectile():
    source=ROOT/'source-input/effects/39768fc933fe67.png';im=Image.open(source).convert('RGBA');shaft=Counter(p for p in im.getdata()if p[3]).most_common(1)[0][0]
    q=Image.new('RGBA',im.size);q.putdata([(*C[4 if p==shaft else 2],p[3])if p[3]else(0,0,0,0)for p in im.getdata()])
    assert q.getchannel('A').tobytes()==im.getchannel('A').tobytes()
    return save(q,'flying-arrow.png','native large-arrow footprint in the confirmed ImageGen wood/ivory materials; source material master sniper-arrow-natural-v3-20261023/source/natural-arrow-master.png')

def build(publish):
    io.OUT=OUT;io.REG.clear();io.ASSETS.clear();b=json.loads((OUT/'baseline.json').read_text());mapart=maps();battleart=battle();drafts={};arrow=projectile();audit=json.loads((ROOT/'source-input/corrected-tactical-walk/overlay.json').read_text())
    note='弓骑士：弓箭手四色加木色与冷色阴影，纯色头发、米白加厚骑甲、白马与大型反曲弓；完整连接的骑手与马身固定中心，四腿按原作姿态换步，双方分别保留各自抬弓、满弓、释放与收势时序。'
    for side in ['ally','enemy']:
        actor=f'class-20-{side}';name=('盟军'if side=='ally'else'敌方')+'弓骑士';entries={'maps':[],'battle':[]};m={'schema_version':1,'revision':REV,'character_id':actor,'actor_id':actor,'display_name':name,'display_class_name':'弓骑士','class_id':20,'source_side':side,'status':'review_candidate','modified_by':'codex','runtime_integrated':False,'review_note':note,'scenarios':[]}
        for kind in ['tactical-walk','tactical-idle']:
            w,h=(128,96)if kind=='tactical-walk'else(96,96);frames=mapart[kind];atlas=Image.new('RGBA',(w*len(frames),h));records=[]
            for i,pose in sorted(frames.items()):
                im=faction(pose,side);path=save(im,f'{side}/{kind}/frame-{i:03}.png','new six-material native-slot map pose');records.append({'source_index':i,'source_frame':i,'output_index':i,'path':path,'output_path':path,'revision':REV,'size':[w,h],'bytes':io.ASSETS[-1]['bytes'],'sha256':io.ASSETS[-1]['sha256']});atlas.alpha_composite(im,(i*w,0))
                if kind=='tactical-walk'or i<3:entries['maps'].append((('待机'if kind=='tactical-idle'else['上','上','右','右','下','下','左','左'][i])+f' {i}',im))
            scene={'id':kind,'revision':REV,'status':'review_candidate','source_atlas':f'../../../source-input/corrected-tactical-walk/{actor}.png'if kind=='tactical-walk'else f'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_20_{side}.png','source_frame_size':[32,24]if kind=='tactical-walk'else[24,24],'source_anchor':[16,24]if kind=='tactical-walk'else[12,20],'output_frame_size':[w,h],'output_anchor':[64,96]if kind=='tactical-walk'else[48,80],'logical_render_scale':.25,'frame_mapping':records,'output_atlas':save(atlas,f'{side}/{kind}-atlas.png','native map slot order'),'review_note':note,'motion_review':{'fixed_regions':STABLE,'whole_pose_mirror_aliases_only':True,'native_timing_modified':False},'timing':{'native_fps':60.0988,'frame_ticks':16,'cycle_ticks':32}if kind=='tactical-walk'else{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]}}
            if kind=='tactical-walk':scene.update(directions={'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},direction_mirror_x={},source_audit={**audit['records'][actor],'status':'verified_native_tactical','overlay':'../../../source-input/corrected-tactical-walk/overlay.json'})
            else:scene['static_facing']=True
            m['scenarios'].append(scene)
        drafts[f'professions/{actor}/maps/frame_mapping.json']=m
        body=b['source_bodies'][side];poses=battleart[side];order=sorted(poses);paths={};records=[];atlas=Image.new('RGBA',(320*len(order),256))
        for n,i in enumerate(order):
            im=faction(poses[i],side);path=save(im,f'{side}/battle/frame-{i:03}.png','faction-native complete mounted shooting pose');paths[str(i)]=path;records.append({'source_frame':i,'path':path,'bytes':io.ASSETS[-1]['bytes'],'sha256':io.ASSETS[-1]['sha256'],'size':[320,256]});atlas.alpha_composite(im,(320*n,0));entries['battle'].append((f'原姿势 {i}',im))
        m={'schema_version':1,'revision':REV,'character_id':actor,'display_name':name,'display_class_name':'弓骑士','original_class_id':20,'source_side':side,'source_atlas':'../../../source-input/'+('original-motion/class-20.png'if side=='ally'else'enemy-motion/class-20-enemy.png'),'source_frame_size':body['frame_size'],'output_frame_size':[320,256],'source_anchor':body['anchor'],'output_anchor':[160,256],'source_columns':16,'source_oam_frame_count':1,'source_idle_frame':1,'source_frame_count':body['frames'],'frame_mapping':paths,'canonical_frames':order,'required_source_frames':order,'variant_keys':list(b['variants'][side]),'records':records,'output_atlas_frame_order':order,'output_atlas':save(atlas,f'{side}/battle-atlas.png','all required native mounted archer poses'),'effect_overrides':{('39768fc933fe67'if side=='ally'else'native-1487ce1e7365a7'):arrow},'status':'review_candidate','modified_by':'codex','runtime_integrated':False,'review_note':note,'palette':HEX if side=='ally'else EHEX,'art_provenance':'Built-in ImageGen complete mounted poses; uniform whole-pose registration, indexed matte materials; native source timing/projectile positions retained','batches':[{'id':'全动作','review':f'../../../{REV}/{side}-battle-light.png','status':'review_candidate'}]};drafts[f'professions/{actor}/battle/frame_mapping.json']=m
        for kind,items in entries.items():
            for light in [False,True]:board(items,side,kind,light)
    write(OUT/'mapping-drafts.json',drafts);write(OUT/'asset-manifest.json',{'revision':REV,'palette':{'ally':HEX,'enemy':EHEX},'assets':io.ASSETS,'whole_pose_registrations':io.REG,'fixed_map_regions':STABLE,'rider_skin_material_regions':SKIN_AUDIT,'complete_greatbow_registration':WEAPON_AUDIT,'runtime_integrated':False,'user_visual_acceptance':'pending'})
    if publish:
        for path,m in drafts.items():write(ROOT/path,m)
        for side in ['ally','enemy']:write(ROOT/f'professions/class-20-{side}/manifest.json',{'id':f'class-20-{side}','class_id':20,'display_name':('盟军'if side=='ally'else'敌方')+'弓骑士','revision':REV,'maps':'maps/frame_mapping.json','battle':'battle/frame_mapping.json','runtime_integrated':False,'status':'review_candidate'})
    print(json.dumps({'assets':len(io.ASSETS),'registrations':len(io.REG),'published':publish}),flush=True)

def inspect():
    for name in FILES:
        if(SRC/name).exists():print(name,[{'size':list(im.size),'head':m['head'],'face_box':m['face_box'],'hair_region':m.get('hair_region')}for im,m in figures(name)],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inspect',action='store_true');p.add_argument('--publish',action='store_true');a=p.parse_args();inspect()if a.inspect else build(a.publish)
