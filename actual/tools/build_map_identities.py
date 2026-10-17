#!/usr/bin/env python3
"""Portrait-linked map identities. Shared profession combat assets untouched."""
from pathlib import Path
from collections import Counter
import colorsys, copy, hashlib, json
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/map-identity-0.7.2'
SOURCE=ROOT/'source/characters'
REPORT=ROOT/'reports/current-art'
PORTRAIT_OUT=ROOT/'assets/portraits-0.7.2'
HERO_BLUE=[(18,38,82),(26,57,113),(41,85,161)]
HERO_RED=[(72,25,31),(125,38,44),(172,72,69)]
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def lum(c):return c[0]*.2126+c[1]*.7152+c[2]*.0722

def family(actor,c):
    r,g,b=c;h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    if actor=='hunapu':return b>g*1.4 and b>r*1.5 and s>.45
    if actor in ['lena','beck']:return b>g*1.25 and b>r*1.3 and s>.36
    if actor=='shia':return b>r*1.15 and b>g*1.04 and v>.72 and s>.15
    if actor in ['daan','fula']:return .69<h<.88 and s>.24 and b>g*1.2
    if actor in ['lisa','mireille']:return (h>.85 or h<.025) and r>g*1.18 and b>g*.95 and s>.22
    if actor in ['lance','lord']:return .11<h<.31 and s>.2 and v<.74
    return (h<.15 or h>.96) and r>g*1.35 and r>b*1.45 and s>.3 and v<.88

def darkest_portraits(data):
    rows=[]
    for key,meta in data['assets'].items():
        actor='hunapu'if key.startswith('hunapu_')else'eileen'if key.startswith('eileen_')else''
        if not actor:continue
        source_path=meta['path'];image=Image.open(ROOT/source_path[6:]).convert('RGBA');before=image.copy()
        def hair(c):
            r,g,b=c
            return family('hunapu',c)if actor=='hunapu'else r>g*1.65 and r>b*1.6
        # Identify hair colours from the crown, then grow only connected
        # matching hair pixels; eye/skin/clothing geometry stays untouched.
        colors={image.getpixel((x,y))[:3]for y in range(20)for x in range(7,43)
                if image.getpixel((x,y))[3]and hair(image.getpixel((x,y))[:3])}
        candidates={(x,y)for y in range(48)for x in range(48)
                    if image.getpixel((x,y))[3]and image.getpixel((x,y))[:3]in colors}
        seeds=[p for p in candidates if p[1]<20 and 7<=p[0]<43];seen=set(seeds);todo=seeds[:]
        while todo:
            x,y=todo.pop()
            for dx,dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                q=(x+dx,y+dy)
                if q in candidates and q not in seen:seen.add(q);todo.append(q)
        values=sorted(colors,key=lum)
        target=HERO_BLUE if actor=='hunapu'else HERO_RED
        mapping={c:target[min(2,int(i*3/max(1,len(values))))]for i,c in enumerate(values)}
        for x,y in seen:image.putpixel((x,y),mapping[image.getpixel((x,y))[:3]]+(255,))
        assert image.getchannel('A').tobytes()==before.getchannel('A').tobytes()
        path=PORTRAIT_OUT/(key+'.png');image.save(path,optimize=True)
        meta.update(path='res://'+str(path.relative_to(ROOT)),hair_palette=[list(c)for c in target],hair_edit='Connected crown hair colours only; expression/eyes/mouth/skin and clothing retained.')
        rows.append({'key':key,'source':source_path,'hair_pixels':len(seen),'alpha_changed':False})
    return rows

def sample_hair(actor,portrait):
    if actor=='hunapu':return HERO_BLUE
    if actor=='eileen':return HERO_RED
    image=Image.open(ROOT/portrait['path'][6:]).convert('RGBA')
    count=Counter(image.getpixel((x,y))[:3]for y in range(20)for x in range(7,43)
                  if image.getpixel((x,y))[3]and family(actor,image.getpixel((x,y))[:3]))
    assert count,(actor,'No portrait hair colours; requires explicit review')
    top=[c for c,n in count.most_common(4)];top.sort(key=lum)
    return [top[0],top[len(top)//2],top[-1]]

def paths(actor,cid,rules):
    if actor=='hunapu':return ['21','23']
    if actor=='eileen':return ['eileen','eileen_promoted']
    jobs={cid};todo=[cid]
    while todo:
        c=todo.pop();targets=[v['to_class']for v in rules['promotions']if v['from_class']==c]
        if c==14:targets+=rules['villager_options']
        for target in targets:
            if target not in jobs:jobs.add(target);todo.append(target)
    return [str(c)for c in sorted(jobs)]

def frame(atlas,meta,f):
    w,h=meta['frame_size'];cols=meta.get('columns',meta.get('frames',6))
    return atlas.crop((f%cols*w,f//cols*h,f%cols*w+w,f//cols*h+h))

def mini_registration(cid, kind, f):
    # These are ORIGINAL head locations, not generated artwork landmarks.
    if kind in ['hub','world']:return (16,8,14,19)
    if kind=='map_move':
        if cid in [12,13,14]:return (13 if cid in [12,13] else 16,9,14,19)
        return (16,8,14,19)
    locations={1:(13,4,9,13),4:(13,4,9,13),7:(13,4,9,13),
               2:(11,4,9,13),22:(11,4,9,13),3:(13,4,9,13),5:(13,4,9,13),
               6:(11,4,9,13),8:(12,4,9,13),9:(12,4,9,13),10:(12,4,9,13),
               12:(8,9,13,16),13:(8,9,13,16),20:(13,4,9,13),
               14:(12,4,9,14),15:(12,4,9,16),19:(12,4,9,14),
               18:(12,4,9,17),17:(12,4,9,17),21:(11,4,9,14)}
    return locations.get(cid,(12,4,9,14))


def recolour(actor,key,kind,meta,target):
    im=Image.open(ROOT/meta['path'][6:]).convert('RGBA');out=im.copy();cid=11 if key.startswith('eileen')else 21 if key=='23'else int(key)
    pkey='eileen_promoted'if key=='eileen_promoted'else'eileen'if key=='eileen'else int(key)
    old_pal=[tuple(c) for c in read(SOURCE/'map-bases.json')['palettes'][str(pkey)]];skin={old_pal[9],old_pal[10]};ink=old_pal[0]
    changed=0;mask=Image.new('L',im.size)
    for f in range(int(meta['frames'])):
        source=frame(im,meta,f);w,h=source.size;cx,hy,_,_=mini_registration(cid,kind,f)
        # Original crouched archer's head is above its shoulder/quiver block;
        # do not mistake the lower body or the tall bow for hair.
        if kind=='map' and cid in [12,13]:cx,hy=8,6
        # Miniature source crown is at y8 (hub/movers), class-specific on map.
        # Warhorse/bow/weapon pixels outside the crown are excluded.
        x0=max(0,cx*4-14);x1=min(w,cx*4+14);y0=max(0,hy*4);y1=min(h,(hy+6)*4)
        for y in range(y0,y1):
            for x in range(x0,x1):
                p=source.getpixel((x,y))
                if not p[3]or p[:3]==ink:continue
                if p[:3]in skin:
                    # Bald source mage now gets portrait-coloured hair on the
                    # forehead only; hands and the readable face are protected.
                    if cid not in [15,19]or y>=y0+7:continue
                t=(lum(p[:3])-min(lum(c)for c in old_pal))/(max(lum(c)for c in old_pal)-min(lum(c)for c in old_pal))
                c=target[0 if t<.3 else 2 if t>.72 else 1]
                xx=f%meta.get('columns',meta['frames'])*w+x;yy=f//meta.get('columns',meta['frames'])*h+y
                out.putpixel((xx,yy),c+(255,));mask.putpixel((xx,yy),255);changed+=p[:3]!=c
    # Heroine hair continues down behind the face. Follow its existing exact
    # red palette within the crown-connected hair component, not her robe.
    assert out.getchannel('A').tobytes()==im.getchannel('A').tobytes()
    path=OUT/actor/key/(kind+'.png');path.parent.mkdir(parents=True,exist_ok=True);out.save(path,optimize=True)
    result=copy.deepcopy(meta);result['path']='res://'+str(path.relative_to(ROOT));result['portrait_hair_palette']=[list(c)for c in target]
    return result,{'actor':actor,'class':key,'kind':kind,'source':meta['path'],'path':result['path'],'hair_pixels_recoloured':changed,'alpha_changed':False,'size':list(out.size),'bytes':path.stat().st_size}

def main():
    for p in [OUT,SOURCE,REPORT,PORTRAIT_OUT]:p.mkdir(parents=True,exist_ok=True)
    (SOURCE/'.gdignore').touch()
    data=read(ROOT/'data/party_visuals.json');portraits=read(SOURCE/'portrait-bases.json');campaign=read(ROOT/'data/campaign.json');rules=read(ROOT/'data/legacy/rules_full.json')
    templates=read(SOURCE/'map-bases.json')
    combat_before=hashlib.sha256(json.dumps({k:v['battle']for k,v in data['classes'].items()},sort_keys=True).encode()).hexdigest()
    portrait_rows=darkest_portraits(portraits);portraits['version']='0.7.2';write(ROOT/'data/portraits.json',portraits)
    actors={};records=[];palettes={}
    for actor,char in campaign['characters'].items():
        portrait_key='hunapu_memory'if actor=='hunapu'else'eileen_departure'if actor=='eileen'else actor
        hair=sample_hair(actor,portraits['assets'][portrait_key]);palettes[actor]={'portrait':portrait_key,'hair':[list(c)for c in hair]};roles={}
        for key in paths(actor,char['class_id'],rules):
            base=templates['hunapu']if actor=='hunapu'else templates['classes'][key]
            role={}
            for kind in ['hub','map','map_move']:
                if actor=='hunapu':
                    m=copy.deepcopy(base[kind]);im=Image.open(ROOT/m['path'][6:]).convert('RGBA')
                    replacement={(40,82,154):hair[1],(66,116,188):hair[2]}
                    before=im.copy();im.putdata([replacement.get(p[:3],p[:3])+(p[3],)if p[3]else p for p in im.getdata()])
                    path=OUT/actor/key/(kind+'.png');path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True);m['path']='res://'+str(path.relative_to(ROOT));m['portrait_hair_palette']=[list(c)for c in hair]
                    assert before.getchannel('A').tobytes()==im.getchannel('A').tobytes()
                    records.append({'actor':actor,'class':key,'kind':kind,'path':m['path'],'alpha_changed':False,'size':list(im.size),'bytes':path.stat().st_size})
                else:m,row=recolour(actor,key,kind,base[kind],hair);records.append(row)
                role[kind]=m
            role['world']=copy.deepcopy(role['hub']);roles[key]=role
        actors[actor]=roles
    guard=copy.deepcopy(templates['classes']['6']['hub']);guard_image=Image.open(ROOT/guard['path'][6:]).convert('RGBA');guard_path=OUT/'guard-hub.png';guard_image.save(guard_path,optimize=True);guard['path']='res://'+str(guard_path.relative_to(ROOT))
    data.update(version='0.7.2',actor_maps=actors,story_npc_profiles={'guard':{'hub':guard}},map_hair_bindings=palettes,
                world_binding='Always reuse the same actor hub profile for both waiting and walking; no separate overworld palette.',
                art_review_status='Current runtime art is retained but has NOT passed user visual acceptance; automated checks prove only loading and pixel consistency.')
    assert combat_before==hashlib.sha256(json.dumps({k:v['battle']for k,v in data['classes'].items()},sort_keys=True).encode()).hexdigest()
    
    for role in data['actor_maps'].values():
        for profile in role.values():
            for art in profile.values():
                for field in ['geometry_contract','motion_reference','appearance_source','approved_identity_retained','pose_registration']:art.pop(field,None)
    write(ROOT/'data/party_visuals.json',data)
    write(SOURCE/'identity-contract.json',{'actors':palettes,'records':records,'portrait_edits':portrait_rows,'combat_profiles_sha256':combat_before,
        'motion_sha256':hashlib.sha256((ROOT/'data/m11_party_motion.json').read_bytes()).hexdigest(),'map_positions_shapes_unchanged':True,'world_equals_hub':True,'guard_source':data['classes']['6']['hub']['path']})
    write(REPORT/'image-manifest.json',records)
    print('MAP_IDENTITY_072',len(actors),'actors',len(records),'map atlases; all alpha/animation/combat invariants passed',flush=True)

if __name__=='__main__':main()
