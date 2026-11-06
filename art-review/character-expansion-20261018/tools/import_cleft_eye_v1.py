#!/usr/bin/env python3
"""Register authored enemy18 orb poses to the verified native slots."""
import argparse, copy, hashlib, json, math
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageChops
from export_gallery import font

ROOT=Path(__file__).resolve().parents[1]
REV='cleft-eye-complete-v1-20261024';OUT=ROOT/REV;SRC=OUT/'source'
MP=ROOT/'professions/class-18-enemy/maps/frame_mapping.json'
BP=ROOT/'professions/class-18-enemy/battle/frame_mapping.json'
HEX=['202c43','4d527a','77759a','a19bb8','dce2d6','afbdc8','7e99a8']
PALETTE=[tuple(bytes.fromhex(x))for x in HEX]
ASSETS=[];REG=[]
CORES={'tactical-idle':[(25,12,72,24),(25,24,35,58),(64,24,72,58),(35,54,64,58)],
       'up':[(40,33,89,80)],'right':[(42,39,89,89)],
       'down':[],
       'left':[(39,39,86,89)]}

def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
@lru_cache(maxsize=None)
def material(rgb):return min(PALETTE,key=lambda c:sum((x-y)**2 for x,y in zip(rgb,c)))
def quant(im):
    out=Image.new('RGBA',im.size)
    out.putdata([(*material(p[:3]),255)if p[3]>=200 else(0,0,0,0)for p in im.getdata()])
    return out
def save(im,path,purpose):
    p=OUT/path;p.parent.mkdir(parents=True,exist_ok=True)
    if im.mode=='RGBA':
        colors=sorted(set(im.getdata()));q=Image.new('P',im.size)
        q.putpalette([v for c in colors for v in c[:3]]+[0]*(768-3*len(colors)))
        lut={c:i for i,c in enumerate(colors)};q.putdata([lut[c]for c in im.getdata()])
        q.info['transparency']=bytes(c[3]for c in colors)
        assert q.convert('RGBA').tobytes()==im.tobytes()
    else:q=im
    q.save(p,optimize=True)
    rec={'path':'../../../'+p.relative_to(ROOT).as_posix(),'purpose':purpose,
         'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)}
    ASSETS.append(rec);return rec

def register(file,cell,body_box,target,height,size,slot):
    raw=Image.open(SRC/file).convert('RGBA');q=quant(raw.crop(cell))
    center=[(body_box[i]+body_box[i+2])/2 for i in(0,1)]
    factor=height/(body_box[3]-body_box[1]);dims=[round(x*factor)for x in q.size]
    scaled=q.resize(dims,Image.Resampling.NEAREST)
    at=[round(target[i]-center[i]*dims[i]/q.size[i])for i in(0,1)]
    out=Image.new('RGBA',size);out.alpha_composite(scaled,at)
    count=lambda im:sum(p[3]>0 for p in im.getdata())
    assert count(out)==count(scaled),(file,slot,'cropped art',at,scaled.getbbox())
    REG.append({'file':file,'slot':slot,'cell':cell,'authored_sphere_box':body_box,
        'target_sphere_center':target,'target_sphere_height':height,'uniform_scale':factor,
        'translation':at,'clipped_pixels':0})
    return out

def maps():
    file='maps-master.png';xs=[0,483,965,1448];ys=[0,362,724,1086]
    # Body ROIs exclude tails: the opaque sphere is registered independently
    # of the tail tip, so tail bending cannot translate the creature.
    specs=[('idle',0,0,0,[183,134,361,307],[48,36],40,(96,96)),
           ('idle',1,1,0,[153,134,334,307],[48,36],40,(96,96)),
           ('idle',2,2,0,[122,134,301,307],[48,36],40,(96,96)),
           ('walk',0,0,1,[183,124,360,295],[64,58],44,(128,96)),
           ('walk',1,0,2,[187,76,360,247],[64,58],44,(128,96)),
           ('walk',2,1,1,[190,124,352,296],[64,64],40,(128,96)),
           ('walk',3,1,2,[190,85,352,255],[64,64],40,(128,96)),
           ('walk',4,2,1,[137,132,309,302],[64,62],44,(128,96)),
           ('walk',5,2,2,[137,85,309,255],[64,62],44,(128,96))]
    idle={};walk={}
    for kind,slot,c,r,body,target,height,size in specs:
        (idle if kind=='idle'else walk)[slot]=register(file,[xs[c],ys[r],xs[c+1],ys[r+1]],body,target,height,size,kind+str(slot))
    for first,second,name in[(0,1,'up'),(2,3,'right')]:
        for box in CORES[name]:walk[second].paste(walk[first].crop(box),box[:2])
    # Native idle2 looks upward; native down0/1 glance right/left. Keep those
    # eye gestures inside a common sphere shell instead of freezing the face.
    gaze=[]
    boxes=[[137,143,381,373],[132,143,378,373],[130,143,376,373],
           [137,170,368,376],[141,170,371,376]]
    for i,box in enumerate(boxes):
        c=i%3;r=i//3
        gaze.append(register('map-gaze-master.png',[c*512,r*512,(c+1)*512,(r+1)*512],box,
            [48,36]if i<3 else[64,62],40 if i<3 else 44,(96,96)if i<3 else(128,96),'map-gaze'+str(i)))
    eye=(35,24,64,54);shell=(25,12,72,58)
    idle[0]=gaze[0]
    idle[1]=gaze[1].copy();idle[1].paste(idle[0].crop(shell),shell[:2])
    idle[2]=idle[0].copy()
    eye_mask=Image.new('L',(96,96));ImageDraw.Draw(eye_mask).rectangle((eye[0],eye[1],eye[2]-1,eye[3]-1),fill=255)
    eye_mask=ImageChops.multiply(eye_mask,idle[0].getchannel('A').filter(ImageFilter.MinFilter(5)))
    for slot in[1,2]:
        visible=ImageChops.multiply(eye_mask,gaze[slot].getchannel('A'))
        idle[slot]=Image.composite(gaze[slot],idle[slot],visible)
    # Use a single authored shell and its curved two-pixel rim for both frontal
    # phases. The eye-face layer stays inside it; rear tails come from the same
    # source sheet, avoiding a rectangular joint between different drawings.
    bodybox=(36,40,94,86);body=Image.new('RGBA',(128,96))
    body.paste(gaze[3].crop(bodybox),bodybox[:2]);interior=body.getchannel('A').filter(ImageFilter.MinFilter(5))
    save_mask=ImageChops.subtract(body.getchannel('A'),interior)
    save_mask.save(SRC/'down-fixed-rim-mask.png',optimize=True)
    for slot,i in[(4,3),(5,4)]:
        shell=body.copy()
        if slot==5:
            visible=ImageChops.multiply(interior,gaze[i].getchannel('A'))
            shell=Image.composite(gaze[i],shell,visible)
        walk[slot]=Image.new('RGBA',(128,96))
        walk[slot].paste(gaze[i].crop((56,0,79,40)),(56,0))
        walk[slot].alpha_composite(shell)
    # These mirrors are verified in the eight native CPU frame records.
    walk[6]=ImageOps.mirror(walk[2]);walk[7]=ImageOps.mirror(walk[3])
    return {'tactical-idle':{i:idle[j]for i,j in enumerate([0,1,2,1,0,1])},'tactical-walk':walk}

def battle():
    file='battle-master.png';xs=[0,464,928,1391,1855];ys=[0,424,848]
    boxes=[[80,125,314,362],[87,125,321,362],[65,125,299,362],[60,125,294,362],
           [80,91,314,328],[81,91,315,328],[58,91,292,328]]
    drawn={}
    for slot,box in enumerate(boxes):
        c=slot%4;r=slot//4
        drawn[slot]=register(file,[xs[c],ys[r],xs[c+1],ys[r+1]],box,[194,158],60,(320,256),slot)
    frames={0:drawn[0]};eye=(164,143,203,186);tail=(223,124,258,192)
    for slot in[1,2,3]:
        frames[slot]=frames[0].copy();frames[slot].paste(drawn[slot].crop(eye),eye[:2])
    for slot in[4,5,6]:
        frames[slot]=frames[0].copy();frames[slot].paste(drawn[slot].crop(tail),tail[:2])
    # Native BG frame7 equals OAM0 translated left16 logical pixels.
    native=Image.open(SRC/'native-battle-000.png').convert('RGBA')
    expected=Image.new('RGBA',native.size);expected.alpha_composite(native,(-16,0))
    assert expected.tobytes()==Image.open(SRC/'native-battle-007.png').convert('RGBA').tobytes()
    bg=Image.new('RGBA',(320,256));bg.alpha_composite(frames[0],(-64,0))
    frames[7]=bg;frames[13]=bg.copy()
    return frames

def boards(m,b):
    groups=[('maps',[('待机'+str(i),m['tactical-idle'][i])for i in range(3)]+[(name+str(i),m['tactical-walk'][i])for i,name in enumerate(['后','后','右','右','前','前','左','左'])],4,260,230),
            ('battle',[(label,b[i])for i,label in[(0,'正视'),(1,'下右视'),(3,'下左视'),(2,'上左视'),(4,'尾下摆'),(5,'尾上卷'),(6,'尾上摆'),(7,'背景别名')]],4,320,270)]
    for light in[False,True]:
        bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242)
        for kind,items,cols,cw,ch in groups:
            out=Image.new('RGB',(cw*cols,50+ch*math.ceil(len(items)/cols)),bg);d=ImageDraw.Draw(out)
            d.text((out.width/2,25),'裂目兽 · '+('地图全姿势'if kind=='maps'else'战斗环视与摆尾'),anchor='mm',font=font(20),fill=fg)
            for n,(label,im)in enumerate(items):
                if kind=='maps':im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
                x=n%cols*cw+(cw-im.width)//2;y=50+n//cols*ch
                out.paste(im,(x,y),im);d.text((n%cols*cw+cw/2,y+ch-18),label,anchor='mm',font=font(16),fill=fg)
            save(out,kind+('-light.png'if light else'-dark.png'),'深浅背景完整轮廓、眼球与尾部遮挡检查')

def main(publish=False):
    m=maps();b=battle();audit=json.loads((SRC/'native-audit.json').read_text())
    note='裂目兽：柔和蓝紫球壳、浅色眼白与不透明深色瞳孔；主体悬浮固定，细尾在后方摆动。没有手脚、翅膀、头发和衣服。环视、前冲撞击与退回沿原作姿势和节奏，不增加光线攻击。'
    scenes=[]
    for kind in['tactical-idle','tactical-walk']:
        idle=kind=='tactical-idle';size=[24,24]if idle else[32,24];outsize=[n*4 for n in size];anchor=[12,20]if idle else[16,24]
        frames=m[kind];rows=[];atlas=Image.new('RGBA',(outsize[0]*len(frames),outsize[1]))
        for i,im in frames.items():
            rec=save(im,kind+f'/frame-{i:03}.png','裂目兽地图原槽位，球体固定、尾部摆动')
            rows.append({'source_index':i,'source_frame':i,'output_index':i,'canonical_frame':([0,1,2,1,0,1][i]if idle else i),**rec,'revision':REV,'art_status':'review_candidate'})
            atlas.alpha_composite(im,(i*outsize[0],0))
        scene={'id':kind,'source_atlas':'../../../'+audit['inputs']['idle'if idle else'walk']['path'],
            'source_frame_size':size,'source_anchor':anchor,'source_frame_count':len(frames),
            'output_frame_size':outsize,'output_anchor':[n*4 for n in anchor],'logical_render_scale':.25,
            'class_id':18,'source_side':'enemy','character_id':'class-18-enemy','display_name':'敌方裂目兽',
            'frame_mapping':rows,'output_atlas':save(atlas,kind+'-atlas.png','原槽位地图图集')['path'],
            'revision':REV,'review_note':note,'required_drawn_frames':list(range(3 if idle else 8)),
            'ground_shadow':{'path':'gold-knight-walk-v3-20261020/ground-shadow.png','size':[9,1.5],
                'offset':[0,-1.5]if idle else[0,-.75],'alpha':.28}}
        if idle:scene.update(static_facing=True,directions={'all':[0,1,2,1]},source_aliases={str(i):j for i,j in enumerate([0,1,2,1,0,1])},timing={'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8],'cycle_ticks':44})
        else:
            checked=copy.deepcopy(audit['walk']);checked.update(native_record_status=checked['status'],status='verified_native_tactical',scope='native CPU phases verified for art review; no runtime integration',review_evidence='../../../'+REV+'/source/source-walk-verification.json')
            scene.update(directions={'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]},direction_mirror_x={},timing={'native_fps':60.0988,'frame_ticks':16,'cycle_ticks':32},source_audit=checked,
                direction_action_notes={direction:'原CPU两相摆尾，每相16帧；固定球体中心，尾部保持前后遮挡。三个循环，共96帧。'for direction in['up','right','down','left']})
        scenes.append(scene)
    maps_mapping={'schema_version':1,'width_height_scale':4,'scenarios':scenes,'character_id':'class-18-enemy','display_name':'敌方裂目兽','display_class_name':'裂目兽','class_id':18,'original_class_id':18,'source_side':'enemy','revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX}
    atlas=Image.new('RGBA',(320*15,256));paths={}
    for i,im in b.items():
        paths[str(i)]=save(im,f'battle/frame-{i:03}.png','裂目兽战斗原姿势或背景别名')['path'];atlas.alpha_composite(im,(i*320,0))
    battle_mapping={'schema_version':1,'character_id':'class-18-enemy','display_name':'敌方裂目兽','display_class_name':'裂目兽','original_class_id':18,'source_side':'enemy','source_atlas':'../../../'+audit['inputs']['battle']['path'],'source_frame_size':[80,64],'source_anchor':[40,64],'output_frame_size':[320,256],'source_idle_frame':7,'source_frame_count':15,'source_columns':16,'frame_mapping':paths,'required_source_frames':audit['body']['required_source_frames'],'variant_keys':['original_class_18_enemy_normal'],'output_atlas':save(atlas,'battle-atlas.png','原槽位战斗图集')['path'],'revision':REV,'status':'review_candidate','runtime_integrated':False,'review_note':note,'palette':HEX,'batches':[{'id':'裂目兽完整姿势','review':'../../../'+REV+'/battle-light.png','status':'review_candidate'}]}
    boards(m,b);write(OUT/'mapping-drafts.json',{'maps':maps_mapping,'battle':battle_mapping})
    write(OUT/'asset-manifest.json',{'revision':REV,'palette':HEX,'assets':ASSETS,'registration':REG,'fixed_core_regions':CORES,'runtime_integrated':False,'user_acceptance':'pending'})
    if publish:
        write(MP,maps_mapping);write(BP,battle_mapping)
        write(MP.parent.parent/'manifest.json',{'id':'class-18-enemy','revision':REV,'status':'review_candidate','runtime_integrated':False,'maps_mapping':'maps/frame_mapping.json','battle_mapping':'battle/frame_mapping.json','review_record':'../../'+REV+'/README.md'})
    print(json.dumps({'published':publish,'assets':len(ASSETS),'map_slots':14,'battle_slots':len(b)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');args=p.parse_args();main(args.publish)
