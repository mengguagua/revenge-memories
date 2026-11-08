"""Retarget PixelFX choreography onto the current character sprites, for preview only."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = HERE.parents[4]
OUT = BASE / HERE.name
CHARACTER = BASE.parent
CINEMA = ROOT / 'art-review/critical-cinema-20261103'
DATA = json.loads((ROOT/'actual/data/critical_cinema.json').read_text())
SOURCE = json.loads((CINEMA/'assets.js').read_text().split('window.CinemaAssets=', 1)[1].split(';', 1)[0])
ANCHORS = {p['path']:p for c in SOURCE.values() for p in c.get('frames', [])}
FPS = 60
NN = Image.Resampling.NEAREST

# Pose source IDs are the shipped critical cinema's image indices. The rows
# are (seconds from contact, pose, advance in native pixels relative to the
# final stance, foot lift, reverse while the blade passes behind).
# Double slash: wind, downward cut, low bind, reverse cut, plant.
# Spin slash: coil, sweep into the far half, reverse facing, cut through and land.
HEROES = {
 'cinema-hunapu-sword':[
  (-.70,9,-44,0,False),(-.52,8,-28,0,False),(-.36,10,-22,8,False),
  (-.21,10,-13,9,False),(-.16,11,-6,0,False),(-.105,14,-3,0,False),
  (-.035,10,-1,4,False),(.038,10,3,4,False),(.085,11,2,0,False),(.165,14,0,0,False),
  (.53,14,0,0,False),
 ],
 'cinema-hunapu-sword-advanced':[
  (-.70,63,-53,2,False),(-.52,61,-30,0,False),(-.37,62,-21,0,False),
  (-.23,64,-14,9,False),(-.16,66,-5,0,False),(-.095,65,-4,0,False),
  (-.04,62,-2,0,False),(.042,62,3,0,False),(.10,66,2,0,False),
  (.23,66,0,0,False),(.53,65,0,0,False),
 ],
 'cinema-eileen-sword':[
  (-.70,45,-48,0,False),(-.48,44,-26,0,False),(-.31,44,-13,0,False),
  (-.235,48,-7,0,False),(-.176,49,-5,0,True),(-.118,48,-4,0,True),
  (-.062,47,-1,4,True),(-.016,48,0,0,False),(.068,48,3,0,False),
  (.185,49,0,0,False),(.53,49,0,0,False),
 ],
 'cinema-eileen-sword-advanced':[
  (-.70,95,-52,0,False),(-.49,94,-30,0,False),(-.32,93,-13,0,False),
  (-.235,93,-7,0,False),(-.178,93,-5,0,True),(-.118,95,-3,0,True),
  (-.058,96,-1,3,True),(-.012,93,0,0,False),(.068,99,3,0,False),
  (.205,103,0,0,False),(.53,99,0,0,False),
 ],
}


def game_point(scene, xy):
    return [scene['origin'][a]+p*scene['scale'] for a,p in enumerate(xy)]


def read_cinema_pose(index):
    rec = DATA['images'][int(index)]
    path = ROOT/'actual'/rec['path'].removeprefix('res://')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == rec['sha256']
    img = Image.open(path).convert('RGBA')
    x = ANCHORS.get(rec['source'], {}).get('body_anchor')
    if x is None:
        # Return poses have no authored body anchor. Choose the center of the
        # solid lowest band, away from the carried blade and streaming cloth.
        alpha = img.getchannel('A')
        box = alpha.crop((0,max(0,img.height-24),img.width,img.height)).getbbox()
        x = (box[0]+box[2])/2 if box else img.width/2
    return img,x,rec


@lru_cache(maxsize=128)
def pose(index, scale_x, scale_y=None):
    img, x, rec = read_cinema_pose(index)
    h = max(1,round(img.height*(scale_y or scale_x)))
    w = max(1,round(img.width*scale_x))
    return img.resize((w,h),NN),(x*w/img.width,h),rec


def interp(keys, t):
    a=keys[0]
    for b in keys[1:]:
        if t < b[0]:
            u=max(0,min(1,(t-a[0])/(b[0]-a[0])))
            return a,b,u*u*(3-2*u)
        a=b
    return a,a,0


def atlas(name, poses, pivot, size, fps=60):
    w,h=size
    cols = min(8, len(poses))
    tex=Image.new('RGBA',(cols*w, math.ceil(len(poses)/cols)*h))
    for i,(im, anchor) in enumerate(poses):
        x,y=(round(a-b) for a,b in zip(pivot,anchor))
        assert x>=0 and y>=0 and x+im.width<=w and y+im.height<=h,(name, x,y,im.size)
        tex.alpha_composite(im,(i%cols*w+x,i//cols*h+y))
    path=f'assets/r4/{name}.png'
    tex.save(OUT/path,optimize=True)
    return dict(path=path,frameSize=[w,h],pivot=list(pivot),columns=cols,fps=fps,frames=len(poses),loop=False)


def nearest_staged(capture, t):
    return min((f for f in capture['frames'] if f.get('cinema',{}).get('actor_op')),key=lambda f:abs(f['t']-t))


def hero(case, capture, rows):
    key=case['key']; c=case['contact']; keys=HEROES[key]; female='eileen' in key
    capture_hit=nearest_staged(capture,c+.05)['cinema']
    tx,fy=game_point(capture_hit,capture_hit['target'])
    # Keep the source's visual proportion, and put the lead foot close enough
    # that the crossed blade / ring enters the original target silhouette.
    advanced='advanced' in key
    native_scale=capture_hit['scale']*(.81 if advanced else .78 if female else 1.01)
    final=tx-(49 if female else 48)
    name='r4-actor-'+key
    tiles=[]; variants={}; paths={}; frames=[]

    def add(index, scale, height=None):
        k=(index,scale,height)
        if k not in variants:
            im,pivot,src=pose(index,scale,height)
            variants[k]=len(tiles);tiles.append((im,pivot));paths[str(index)]=src['source']
        return variants[k],tiles[variants[k]][1]

    # Keep the original tail particles suppressed through their full native
    # window. The staged body returns to the engine pose before this cutoff.
    start=math.ceil((c-.70)*FPS); end=math.ceil((c+1.34)*FPS)
    for n in range(start,end):
        t=n/FPS-c
        if t<-.66 or t>.57:
            sc=rows[n].get('cinema',{})
            op=sc.get('actor_op') or nearest_staged(capture,n/FPS)['cinema']['actor_op']
            _,i,x,y,w,h,sx,sy,sw,sh,flip,alpha=op
            ti,(ax,_)=add(int(i),round(w/sw*sc['scale'],4),round(h/sh*sc['scale'],4))
            im=tiles[ti][0]
            px,py=game_point(sc,[x,y+h])
            frames.append([ti,round(px+(im.width-ax if flip else ax)),round(py),bool(flip),round(alpha,3)])
            continue
        a,b,u=interp(keys,t); _,i,x,lift,flip=a
        ti,_=add(i,round(native_scale,4))
        px=final+x+(b[2]-x)*u; py=fy-lift-(b[3]-lift)*u
        if t<-.48:
            sc=rows[n]['cinema']
            _,idx,ox,oy,ow,oh,_,_,sw,sh,fl,_=sc['actor_op']
            im,an,_=pose(int(idx),round(ow/sw*sc['scale'],4),round(oh/sh*sc['scale'],4))
            ox,oy=game_point(sc,[ox,oy+oh]);ox+=im.width-an[0] if fl else an[0]
            k=max(0,min(1,(t+.66)/.18)); k=k*k*(3-2*k)
            px=ox+(px-ox)*k;py=oy+(py-oy)*k
        if t>.42:
            sc=rows[n]['cinema']
            _,idx,ox,oy,ow,oh,_,_,sw,sh,fl,_=sc['actor_op']
            im,an,_=pose(int(idx),round(ow/sw*sc['scale'],4),round(oh/sh*sc['scale'],4))
            ox,oy=game_point(sc,[ox,oy+oh]);ox+=im.width-an[0] if fl else an[0]
            k=max(0,min(1,(t-.42)/.15));px=px+(ox-px)*k;py=py+(oy-py)*k
        frames.append([ti,round(px),round(py),flip,1])
    spec=atlas(name,tiles,(85,126),(218,129))
    case.update(actorPlan=dict(effect=name,startFrame=start,frames=frames),
                replaceEffectsFrom=start/FPS,replaceEffectsUntil=end/FPS,
                actionTime=c-(.09 if female else .12),impactTime=c+(.035 if female else .055),chargeTime=c-.36)
    if female:
        start_fx=c-.17/.70
        at=[round(final+1),round(fy)]
        case['fxPlan']=[dict(effect='r4-hero-spin-'+layer,layer=layer,start=start_fx,anchor=at,alpha=1 if advanced else .93)
                        for layer in ['back','front']]
    else:
        start_fx=c-.152/.80
        at=[round(tx-8),round(fy-39)]
        case['fxPlan']=[dict(effect='r4-hero-double',start=start_fx,anchor=at,alpha=1 if advanced else .91)]
    original=DATA['cases'][case['source']['program']]
    assert original['weapon']=='剑' and original['hero']==case['source']['event']['attacker']
    case['actionEvidence']={'stock':'melee/spin-slash' if female else 'melee/double-slash',
                            'gamePoseSources':paths,'staging':keys,'gameContactCount':1,
                            'resultAt':c,'weapon':'原角色佩剑',
                            'originalMove':original['title'],'originalMoveBeats':original['beats'],
                            'gameActor':case['source']['event']['attacker']}
    return {name:spec}


@lru_cache(maxsize=1)
def guard_refs():
    # Approved battle art already has the shield, current lance, and the
    # weapon-free patch used to restore the breastplate under the old shaft.
    tools_dir=CHARACTER/'tools'
    sys.path.insert(0,str(tools_dir))
    import revise_bastion_knight_lance as v6
    old=CHARACTER/'bastion-guardian-lance-rear-v5-20261022'
    previous=json.loads((old/'baseline.json').read_text())
    grips=json.loads((old/'asset-manifest.json').read_text())['pose_repairs']
    current=CHARACTER/'bastion-guardian-knight-lance-v6-20261022'
    manifest=json.loads((current/'asset-manifest.json').read_text())
    sha={}
    for side in ('ally','enemy'):
        sha[side]=hashlib.sha256((current/side/'shared-battle-lance.png').read_bytes()).hexdigest()
        assert sha[side] in {r['sha256'] for r in manifest['assets']}
    return v6,previous,grips,current,sha


@lru_cache(maxsize=4)
def guard_parts(i):
    v6,previous,grips,_,_=guard_refs()
    old=Image.open((CHARACTER/'professions/class-22-ally/battle'/previous['ally']['frame_mapping'][str(i)]).resolve()).convert('RGBA')
    gp=list(grips[str(i)]['grip']);slope=grips[str(i)]['axis_slope'];direction=[-1,-slope]
    if i==10:
        gp=[244,gp[1]+slope*(244-248)];direction=[1,slope]
    clean,_=v6.clear_old_rear(old,i);clean,_=v6.strip(clean,gp,direction,8,150)
    if i==11:
        restore=v6.restoration()
        for y in range(145,200):
            for x in range(180,280):
                if abs((y-gp[1])-slope*(x-gp[0]))/math.sqrt(1+slope*slope)<=6.5:
                    clean.putpixel((x,y),restore.getpixel((x,y)))
    return clean,v6.glove(old,gp,8),gp


def guard_pose(side, i, angle):
    v6,_,_,current,_=guard_refs()
    if angle is None:
        src=Image.open(current/side/'battle'/f'frame-{i:03}.png').convert('RGBA')
        return src.resize((80,64),NN),(40,64)
    clean,glove,gp=guard_parts(i);native_lance,anchor=v6.weapon(82)
    lance=Image.open(current/side/'shared-battle-lance.png').convert('RGBA')
    assert v6.faction(native_lance,side).tobytes()==lance.tobytes()
    # The polearm is a rigid transform about its approved grip. The guard,
    # shaft, point, and pommel remain the original bitmap.
    ux,uy=-math.cos(angle),-math.sin(angle)
    gx,gy=gp[0]+40,gp[1]+40
    im=Image.new('RGBA',(400,336))
    pole=lance.transform(im.size,Image.Transform.AFFINE,
         (ux,uy,anchor[0]-ux*gx-uy*gy,-uy,ux,anchor[1]+uy*gx-ux*gy),resample=NN)
    assert all(v>1 and v < lim-1 for v,lim in zip(pole.getbbox(),[400,336,400,336]))
    im.alpha_composite(v6.faction(clean,side),(40,40))
    hand=Image.new('RGBA',im.size);hand.alpha_composite(v6.faction(glove,side),(40,40))
    # Coverage fallback for a thin rotated shaft. A native pixel that the
    # nearest sampler misses may take an opaque color already in that 4×4
    # square. The bitmap keeps the original palette and all edges stay crisp.
    native=pole.resize((100,84),NN)
    px=native.load()
    x0,y0,x1,y1=pole.getbbox()
    for y in range(y0//4,math.ceil(y1/4)):
        for x in range(x0//4,math.ceil(x1/4)):
            if px[x,y][3]:
                continue
            colors=Counter(v for v in pole.crop((x*4,y*4,x*4+4,y*4+4)).getdata() if v[3]>=128)
            if sum(colors.values())>=2:
                px[x,y]=colors.most_common(1)[0][0]
    im=im.resize((100,84),NN);im.alpha_composite(native);im.alpha_composite(hand.resize((100,84),NN))
    return im,(50,74)


def guard(case, capture, rows):
    c=case['contact']; side=case['side']; flip=side=='enemy'; direction=1 if flip else -1
    # Start low, draw up and behind the shield, turn through the front, then
    # lower the polearm. Use the original forward stance at the end.
    keys=[
        (-.82,8,0,2.61),(-.68,9,1,3.05),(-.51,10,2,4.82),
        (-.28,10,4,4.47),(-.18,10,6,3.94),(-.095,11,11,3.45),
        (0,11,15,3.30),(.15,11,13,2.99),(.31,11,7,2.84),
        (.55,11,2,3.28),(.72,11,0,3.345),(.90,11,0,3.345),
    ]
    start=math.ceil((c-.82)*FPS);end=math.ceil((c+.90)*FPS)
    poses=[]; tracks=[]; lookup={}
    for n in range(start,end):
        t=n/FPS-c; a,b,u=interp(keys,t); i=a[1]
        angle=None if t<-.74 or t>.71 else round((a[3]+(b[3]-a[3])*u)*44)/44
        off=round(a[2]+(b[2]-a[2])*u)
        k=(i,angle)
        if k not in lookup:
            lookup[k]=len(poses);poses.append(guard_pose(side,i,angle))
        ax,ay=rows[n]['actor']
        tracks.append([lookup[k],round(ax+direction*off+(16 if flip else 0)),round(ay),flip,1])
    name='r4-actor-guard-'+side
    spec=atlas(name,poses,(57,76),(114,91))
    base=min(rows,key=lambda row:abs(row['t']-c+.02))
    ax,ay=base['actor']
    # The real sprite is offset from its OAM origin, particularly on the
    # mirrored side. Anchor the reaping trail to the hand, near the impact.
    anchor=[round(ax+(16 if flip else 0)-direction*4),round(ay)]
    case.update(actorPlan=dict(effect=name,startFrame=start,frames=tracks),
                replaceEffectsFrom=start/FPS,replaceEffectsUntil=end/FPS,
                actionTime=c-.085,impactTime=c+.09,chargeTime=c-.36)
    case['fxPlan']=[dict(effect='r4-bastion-reap-'+layer,start=c-.186/1.02,layer=layer,rate=1.02/.88,
                         anchor=anchor,flip=not flip) for layer in ['back','front']]
    case['actionEvidence']={'stock':'melee/scythe-reap','gameContactCount':1,
         'staging':keys,'resultAt':c,'gameActor':case['source']['event']['attacker'],
         'originalMove':case['move'],'originalProgram':case['source']['program'],
         'weapon':'现有骑士长枪和盾牌','lanceSha256':guard_refs()[4][side]}
    return {name:spec}
