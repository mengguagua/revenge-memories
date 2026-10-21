#!/usr/bin/env python3
"""Import whole ImageGen knight poses. No body slicing or limb deformation."""
import argparse
import json
import math
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw
from build_gallery import ROOT
from revise_cavalry_map import digest, translate

REV='knight-redraw-v3-20261021'
OUT=ROOT/REV
SRC=OUT/'source'
ALLY=['181d29','303847','596574','a5b3c1','d6dfe4','f5f5ef','243756','3d5680',
      '7292b8','4d3428','85603e','b88b56','b38360','e8ba8d','c4a15a','fff8df']
ENEMY=['161b2b','292c49','343e68','4a5c86','64779e','8f9ec0','282c50','494876',
       '7579aa','29283d','444260','6d6688','947c7b','cfb2ad','9b8cae','c3cce2']
COLORS=[tuple(bytes.fromhex(v)) for v in ALLY]
ENEMY_COLORS=[tuple(bytes.fromhex(v)) for v in ENEMY]
REG=[]
ASSETS=[]

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def parts(points):
    points=set(points);out=[]
    while points:
        q=[points.pop()];c=list(q)
        while q:
            x,y=q.pop()
            for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1),(x-1,y-1),(x+1,y-1),(x-1,y+1),(x+1,y+1)]:
                if p in points:points.remove(p);q.append(p);c.append(p)
        out.append(c)
    return sorted(out,key=len,reverse=True)

@lru_cache(maxsize=12)
def figures(filename,count):
    """Separate full opaque figures, including tails that cross nominal cells."""
    im=Image.open(SRC/filename).convert('RGBA');pixels=im.load()
    comps=parts((x,y) for y in range(im.height) for x in range(im.width) if pixels[x,y][3]>=128)
    large=[c for c in comps if len(c)>1500]
    assert len(large)==count,(filename,'Expected whole figures',[(len(c))for c in large])
    records=[]
    for comp in large:
        b=(min(x for x,y in comp),min(y for x,y in comp),max(x for x,y in comp)+1,max(y for x,y in comp)+1)
        piece=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]));p=piece.load()
        for x,y in comp:p[x-b[0],y-b[1]]=(*pixels[x,y][:3],255)
        records.append((piece,{'source':filename,'source_sha256':digest(SRC/filename),'source_bounds':list(b),'opaque_pixels':len(comp)}))
    # Sort sheet rows using the top of the actual drawing, then by x.
    if count in [4,6]:
        rows=[sorted(records,key=lambda v:v[1]['source_bounds'][1])[:count//2],sorted(records,key=lambda v:v[1]['source_bounds'][1])[count//2:]]
        return tuple(v for row in rows for v in sorted(row,key=lambda v:v[1]['source_bounds'][0]))
    return tuple(sorted(records,key=lambda v:v[1]['source_bounds'][0]))

def landmark(im,back=False):
    pixels=im.load();pts=[]
    for y in range(round(im.height*.40 if not back else im.height*.28)):
        for x in range(round(im.width*.28),round(im.width*.75)):
            r,g,b,a=pixels[x,y]
            good=(min(r,g,b)>205 and max(r,g,b)-min(r,g,b)<35) if back else (r>190 and .55*r<g<.90*r and .30*r<b<.78*r)
            if a and good:pts.append((x,y))
    choices=parts(pts);assert choices,'Missing registration landmark'
    c=choices[0];box=[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]
    return [(box[0]+box[2])/2,(box[1]+box[3])/2],box

@lru_cache(maxsize=50000)
def color_index(rgb):
    return min(range(16),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,COLORS[i])))

def palette(im,side):
    colors=COLORS if side=='ally' else ENEMY_COLORS
    result=Image.new('RGBA',im.size)
    result.putdata([(*colors[color_index(p[:3])],255) if p[3] else (0,0,0,0) for p in im.getdata()])
    return result

def register(figure,size,point,target,scale,label):
    im,meta=figure;dims=[round(im.width*scale),round(im.height*scale)]
    scaled=im.resize(dims,Image.Resampling.NEAREST)
    ratios=[dims[0]/im.width,dims[1]/im.height]
    delta=[round(target[i]-point[i]*ratios[i]) for i in range(2)]
    result=Image.new('RGBA',size);result.alpha_composite(scaled,tuple(delta))
    before=sum(p[3]>0 for p in scaled.getdata());after=sum(p[3]>0 for p in result.getdata())
    assert before==after,(label,'Clipping',delta,dims,size)
    REG.append({**meta,'label':label,'method':'whole-pose uniform scale and integer translation only',
      'source_landmark':point,'target_landmark':target,'scale':scale,'resampled_size':dims,'translation':delta,
      'actual_landmark':[delta[i]+point[i]*ratios[i] for i in range(2)],'clipped_pixels':before-after})
    return result

def maps():
    raw=figures('map-idle-master-v1.png',3);points=[landmark(im)[0] for im,meta in raw]
    scale=64/raw[0][0].height;target=[48,round(80-(raw[0][0].height-points[0][1])*scale)]
    poses=[register(fig,(96,96),p,target,scale,f'idle-{i}') for i,(fig,p) in enumerate(zip(raw,points))]
    idle={i:poses[p] for i,p in enumerate([0,1,2,1,0,1])};walk={}
    fb=figures('map-up-down-master-v1.png',4)
    for start,ids,back,floor in [(0,[0,1],True,92),(2,[4,5],False,96)]:
        pair=fb[start:start+2];points=[landmark(im,back)[0] for im,meta in pair]
        scale=76/pair[0][0].height
        target=[64,round(floor-(pair[0][0].height-points[0][1])*scale)]
        # Use one pair scale/anchor so leg phases never rescale the body.
        for i,fig,p in zip(ids,pair,points):walk[i]=register(fig,(128,96),p,target,scale,f'walk-{i}')
    for n,p in enumerate([0,2]):
        left=Image.new('RGBA',(128,96));left.alpha_composite(poses[p],(16,16))
        walk[6+n]=left;walk[2+n]=translate(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT),[1,0])
    return {'tactical-idle':idle,'tactical-walk':walk}

def battle():
    ground=figures('battle-ground-master-v1.png',6);special=figures('battle-special-master-v1.png',6)
    points=[landmark(im)[0] for im,meta in ground]
    scale=(254-112)/max(fig[0].height-p[1] for fig,p in zip(ground,points))
    result={i:register(fig,(320,256),p,[184,112],scale,f'battle-{i}') for i,(fig,p) in enumerate(zip(ground,points)) if i!=2}
    for file,ids,floor in [('battle-002-master-v2.png',[2],254),('battle-008-009-master-v2.png',[8,9],254),('battle-throw-master-v2.png',[41,43],254)]:
        raw=figures(file,len(ids));points=[landmark(im)[0] for im,meta in raw]
        scale=(floor-112)/max(fig[0].height-p[1] for fig,p in zip(raw,points))
        for i,fig,p in zip(ids,raw,points):result[i]=register(fig,(320,256),p,[184,112],scale,f'battle-{i}')
    fig=special[0];p=landmark(fig[0])[0];scale=(254-100)/(fig[0].height-p[1])
    result[6]=register(fig,(320,256),p,[198,100],scale,'battle-6')
    fig=figures('battle-007-master-v2.png',1)[0];p=landmark(fig[0])[0]
    scale=min((216-84)/(fig[0].height-p[1]),(316-204)/(fig[0].width-p[0]),(204-4)/p[0])
    result[7]=register(fig,(320,256),p,[204,84],scale,'battle-7')
    result[21]=result[0].copy();result[40]=result[0].copy()
    enemy={i+10:im.copy() for i,im in result.items() if i<10}
    for i,source in [(31,0),(40,0),(41,41),(45,43)]:enemy[i]=translate(result[source],[-64,0])
    return result,enemy

def save(im,name,purpose):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    ASSETS.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),
       'bytes':path.stat().st_size,'sha256':digest(path),'colors':len({p[:3] for p in im.convert('RGBA').getdata() if p[3]})})
    return '../../../'+path.relative_to(ROOT).as_posix()

def projectile(side):
    raw,meta=figures('flying-lance-master-v1.png',1)[0]
    scale=min(152/raw.width,12/raw.height)
    dims=[round(raw.width*scale),round(raw.height*scale)]
    small=raw.resize(dims,Image.Resampling.NEAREST)
    # Keep original64x16 logical canvas, anchor32,8, and visible flight box.
    im=Image.new('RGBA',(256,64));im.alpha_composite(small,(100+(152-dims[0])//2,round(54-dims[1]/2)))
    return save(palette(im,side),f'{side}/flying-lance.png','new drawn lance; original logical canvas, anchor and flight envelope')

def boards(images):
    from export_gallery import font
    for side in ['ally','enemy']:
        for kind in ['maps','battle']:
            entries=images[side][kind]
            for light in [False,True]:
                cw,ch=(288,250) if kind=='maps' else (344,296);columns=3
                bg=(220,225,228) if light else (32,45,53);fg=(30,43,56) if light else (235,243,242)
                board=Image.new('RGB',(cw*columns,56+ch*math.ceil(len(entries)/columns)),bg);d=ImageDraw.Draw(board)
                d.text((board.width//2,25),('盟军骑士' if side=='ally' else '敌方骑士')+' · 完整重绘'+('地图' if kind=='maps' else '战斗'),anchor='mm',font=font(20),fill=fg)
                for n,(name,im) in enumerate(entries):
                    if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
                    x=n%columns*cw+(cw-im.width)//2;y=56+n//columns*ch
                    board.paste(im,(x,y),im)
                    d.text((n%columns*cw+cw//2,y+ch-26),name,anchor='mt',font=font(14),fill=fg)
                save(board,f'{side}-{kind}-{"light" if light else "dark"}.png','offline full-pose visual review board')

def stage(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());map_art=maps();ally,enemy=battle();drafts={};review={}
    for side,body in [('ally',ally),('enemy',enemy)]:
        review[side]={'maps':[],'battle':[]}
        key=f'professions/class-4-{side}/maps/frame_mapping.json';mapping=json.loads(json.dumps(baseline['mappings'][key]))
        for scenario in mapping['scenarios']:
            kind=scenario['id'];w,h=scenario['output_frame_size'];atlas=Image.new('RGBA',(w*len(map_art[kind]),h))
            for rec in scenario['frame_mapping']:
                i=rec['source_index'];im=palette(map_art[kind][i],side)
                path=save(im,f'{side}/{kind}/frame-{i:03}.png','whole drawn knight pose; '+kind)
                rec.clear();rec.update(source_index=i,source_frame=i,path=path,output_path=path,revision=REV,size=[w,h],bytes=ASSETS[-1]['bytes'],sha256=ASSETS[-1]['sha256'],art_status='review_candidate')
                atlas.alpha_composite(im,(w*i,0))
                if kind=='tactical-idle' and i<3:review[side]['maps'].append((f'待机 {i}',im))
                if kind=='tactical-walk':review[side]['maps'].append((['向上','向上','向右','向右','向下','向下','向左','向左'][i]+f' {i}',im))
            scenario.update(output_atlas=save(atlas,f'{side}/{kind}-atlas.png','offline whole-pose atlas'),revision=REV,
                motion_review={'registration':'whole-pose anchor; no body splicing or limb warp','runtime_integrated':False},
                review_note='按原作姿势重新绘制完整骑士与白马，整帧定位。蓝白／蓝紫16色；原相位、循环与节奏保留。',
                action_note='完整姿势重绘，按固定定位点登记；待本轮验收。',
                ground_shadow={'path':'gold-knight-walk-v3-20261020/ground-shadow.png','size':[12,3],'offset':[0,-1],'alpha':.35})
        mapping.update(revision=REV,status='review_candidate',runtime_integrated=False);drafts[key]=mapping
        key=f'professions/class-4-{side}/battle/frame_mapping.json';mapping=json.loads(json.dumps(baseline['mappings'][key]));paths={}
        atlas=Image.new('RGBA',(320*len(body),256))
        for n,(i,raw) in enumerate(sorted(body.items())):
            im=palette(raw,side);paths[str(i)]=save(im,f'{side}/battle/frame-{i:03}.png','whole drawn knight battle pose')
            atlas.alpha_composite(im,(n*320,0))
            if i not in [21,31,40]:review[side]['battle'].append((f'姿势 {i}',im))
        mapping.update(revision=REV,frame_mapping=paths,output_atlas=save(atlas,f'{side}/battle-atlas.png','offline whole battle atlas'),
            effect_overrides={('5660a52a5bb041' if side=='ally' else 'native-3a296bda027dbe'):projectile(side)},
            palette=ALLY if side=='ally' else ENEMY,body_review_records=[r for r in REG if r['label'].startswith('battle-')],
            batches=[{'id':'完整重绘全姿势','review':f'../../../{REV}/{side}-battle-dark.png','status':'pending_user_visual_acceptance'}],
            art_provenance='New built-in image_gen whole-pose drawings, original source pose references; whole-pose registration only.',
            review_note='双方骑士完整重绘，平地动作以同一面部定位点登记；保留原作冲锋、腾跃与回位。投枪准备仅一根水平长枪，释放帧空手。16色柔和蓝白／蓝紫配色。',
            runtime_integrated=False,status='review_candidate')
        drafts[key]=mapping
    boards(review)
    write(OUT/'mapping-drafts.json',drafts)
    write(OUT/'asset-manifest.json',{'revision':REV,'status':'staged_for_visual_inspection','image_generation':'built-in image_gen',
        'runtime_integrated':False,'palette':{'ally':ALLY,'enemy':ENEMY},'registration':REG,'assets':ASSETS,
        'body_splicing':False,'limb_warping':False,'native_timing_modified':False})
    if publish:
        for key,value in drafts.items():write(ROOT/key,value)
    print(json.dumps({'status':'published' if publish else 'staged','assets':len(ASSETS),'registrations':len(REG),'mapping_files':len(drafts)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--publish',action='store_true');stage(parser.parse_args().publish)
