#!/usr/bin/env python3
"""Fix class-4 side motion using one complete painting and pinned leg roots.

No cross-pose horizontal splice: clothing, saddle, barrel, rider and tail stay
pixel-identical. Only the four isolated horse-leg components below y=64 move.
The existing detailed pixel clusters supply every painted pixel.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from build_gallery import ROOT
from revise_cavalry_map import digest, signature, translate

REVISION='knight-map-joints-v2-20261021'
OUT=ROOT/REVISION
PREVIOUS=ROOT/'knight-complete-v1-20261021'
ALIASES=[0,1,2,1,0,1]
ROOT_Y=64
COLLAR_END=66
# destination knee center/row and hoof center/last row; the source roots and
# first two rows stay untouched. Three native foot phases, not three bodies.
POSES={
  1:{'near_fore':[(23,69),(28,73)],'far_fore':[(42,71),(43,77)],
     'far_hind':[(55,71),(54,77)],'near_hind':[(64,71),(64,77)]},
  2:{'near_fore':[(23,69),(28,73)],'far_fore':[(44,71),(44,77)],
     'far_hind':[(54,71),(53,77)],'near_hind':[(60,69),(63,73)]},
}

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def components(image,min_y=0):
    remaining={(x,y) for y in range(min_y,image.height) for x in range(image.width) if image.getpixel((x,y))[3]}
    result=[]
    while remaining:
        pending=[remaining.pop()];part=list(pending)
        while pending:
            x,y=pending.pop()
            for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if p in remaining:remaining.remove(p);pending.append(p);part.append(p)
        result.append(part)
    return sorted(result,key=lambda c:min(x for x,y in c))

def leg_layers(base):
    parts=components(base,ROOT_Y)
    assert len(parts)==5,'Four legs plus a separate stationary tail tip expected'
    names=['near_fore','far_fore','far_hind','near_hind']
    layers={};static=base.copy()
    for name,part in zip(names,parts[:4]):
        layer=Image.new('RGBA',base.size)
        for p in part:layer.putpixel(p,base.getpixel(p));static.putpixel(p,(0,0,0,0))
        layers[name]=layer
    assert all(layer.getbbox()[1]==ROOT_Y for layer in layers.values())
    # The fifth component is the tail, deliberately kept in the fixed body.
    return static,layers

def interpolate(nodes,y):
    for a,b in zip(nodes,nodes[1:]):
        if a[1]<=y<=b[1]:
            t=(y-a[1])/(b[1]-a[1]);return a[0]+(b[0]-a[0])*t
    raise ValueError((nodes,y))

def bend(layer,targets):
    result=Image.new('RGBA',layer.size);box=layer.getbbox();last=box[3]-1
    rows={y:[x for x in range(layer.width) if layer.getpixel((x,y))[3]] for y in range(ROOT_Y,last+1)}
    center=lambda y:(min(rows[y])+max(rows[y]))/2
    root=(center(COLLAR_END),COLLAR_END)
    destination=[root,*targets]
    for y in range(ROOT_Y,COLLAR_END):
        for x in rows[y]:result.putpixel((x,y),layer.getpixel((x,y)))
    for y in range(COLLAR_END,targets[-1][1]+1):
        if y<=targets[0][1]:
            source_y=COLLAR_END+(y-COLLAR_END)*(70-COLLAR_END)/(targets[0][1]-COLLAR_END)
        else:
            source_y=70+(y-targets[0][1])*(last-70)/(targets[1][1]-targets[0][1])
        source_y=round(source_y)
        dx=round(interpolate(destination,y)-center(source_y))
        for x in rows[source_y]:
            assert 0<=x+dx<layer.width
            result.putpixel((x+dx,y),layer.getpixel((x,source_y)))
    assert len(components(result))==1,'Bent leg lost its connected pixel contour'
    assert result.crop((0,ROOT_Y,96,COLLAR_END)).tobytes()==layer.crop((0,ROOT_Y,96,COLLAR_END)).tobytes()
    return result

def painting(base):
    static,layers=leg_layers(base);poses=[base.copy()];records=[]
    for phase in [1,2]:
        pose=static.copy();leg_union=Image.new('RGBA',base.size)
        for name,layer in layers.items():
            moved=bend(layer,POSES[phase][name]);pose.alpha_composite(moved);leg_union.alpha_composite(moved)
            records.append({'phase':phase,'leg':name,'source_bounds':list(layer.getbbox()),
                'output_bounds':list(moved.getbbox()),'pinned_collar':[0,64,96,66],
                'knee_and_hoof_targets':POSES[phase][name]})
        assert len(components(leg_union))==4,'Separate horse legs merged together'
        assert len(components(pose))==1,'Leg disconnected from complete body'
        assert pose.crop((0,0,96,66)).tobytes()==base.crop((0,0,96,66)).tobytes()
        poses.append(pose)
    return poses,static,layers,records

def save(im,name,purpose,assets):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
    assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),
       'bytes':p.stat().st_size,'sha256':digest(p),'visible_colors':len({p[:3] for p in im.convert('RGBA').getdata() if p[3]})})
    return '../../../'+p.relative_to(ROOT).as_posix()

def boards(side,poses,assets):
    from export_gallery import font
    for light in [False,True]:
        bg=(220,222,216) if light else (32,45,53);ink=(40,49,57) if light else (235,243,242)
        canvas=Image.new('RGB',(1008,330),bg);draw=ImageDraw.Draw(canvas)
        draw.text((504,25),('盟军' if side=='ally' else '敌方')+'骑士 · 完整主体／固定腿根',anchor='mm',font=font(20),fill=ink)
        for row,(kind,ids) in enumerate([('待机',[0,1,2]),('侧向行走',[0,2])]):
            for col,i in enumerate(ids):
                im=poses[i];x=col*336+120;y=64+row*130;canvas.paste(im,(x,y),im)
                draw.text((col*336+168,y+104),f'{kind} · {i}',anchor='mt',font=font(14),fill=ink)
        save(canvas,f'{side}-poses-{"light" if light else "dark"}.png','offline continuity inspection board',assets)

def create():
    OUT.mkdir(exist_ok=True);baseline=OUT/'baseline.json'
    if not baseline.exists():
        data=json.loads((ROOT/'demos/gallery-data.json').read_text())
        paths=[ROOT/f'professions/class-4-{side}/maps/frame_mapping.json' for side in ['ally','enemy']]
        write(baseline,{'mappings':{str(p.relative_to(ROOT)):json.loads(p.read_text()) for p in paths},
          'all_mapping_hashes':{str(p.relative_to(ROOT)):digest(p) for p in ROOT.glob('**/frame_mapping.json') if 'source-input' not in p.parts},
          'digests':{a['id']:a['contentDigest'] for a in data['actions']},'timelines':{a['id']:signature(a) for a in data['actions']}})
    before=json.loads(baseline.read_text());assets=[];registrations=[]
    for side in ['ally','enemy']:
        base=Image.open(PREVIOUS/f'{side}/tactical-idle/frame-000.png').convert('RGBA')
        poses,static,layers,records=painting(base)
        for rec in records:rec['side']=side
        registrations.extend(records)
        save(static,f'{side}/fixed-body.png','complete fixed clothing, rider, saddle, horse barrel and tail',assets)
        for name,layer in layers.items():save(layer,f'{side}/source-legs/{name}.png','isolated canonical lower horse leg / fixed root',assets)
        frames={'tactical-idle':{i:poses[a].copy() for i,a in enumerate(ALIASES)},'tactical-walk':{}}
        for n,phase in enumerate([0,2]):
            left=Image.new('RGBA',(128,96));left.alpha_composite(poses[phase],(16,16))
            frames['tactical-walk'][6+n]=left
            frames['tactical-walk'][2+n]=translate(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT),[1,0])
        mapping_path=ROOT/f'professions/class-4-{side}/maps/frame_mapping.json'
        mapping=json.loads(json.dumps(before['mappings'][str(mapping_path.relative_to(ROOT))]))
        for scenario in mapping['scenarios']:
            kind=scenario['id'];size=scenario['output_frame_size'];atlas=Image.new('RGBA',(size[0]*len(scenario['frame_mapping']),size[1]))
            for rec in scenario['frame_mapping']:
                i=rec['source_index']
                if i in frames[kind]:
                    im=frames[kind][i];old=dict(rec);path=save(im,f'{side}/{kind}/frame-{i:03}.png','knight complete-body rooted-leg motion',assets)
                    rec.update(path=path,output_path=path,revision=REVISION,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],previous_record=old)
                else:im=Image.open((mapping_path.parent/rec['output_path']).resolve()).convert('RGBA')
                atlas.alpha_composite(im,(size[0]*i,0))
            scenario.update(revision=REVISION,output_atlas=save(atlas,f'{side}/{kind}-atlas.png','offline knight map atlas',assets),
              status='review_candidate',review_note='待机与左右行走改用同一完整主体，服饰、鞍具、马腹及尾巴完整固定；四条马腿从腿根独立弯折，保留连接处像素、原相位与节奏。向上／向下素材不变。',
              action_note='本轮修正待机与左右行走的腿根、衣甲衔接；完整主体固定。')
            motion=scenario['motion_review'];motion['side_motion_method']='complete canonical painting, four isolated legs below y64, pinned two-row collars; no horizontal cross-pose splice'
            if kind=='tactical-idle':motion['fixed_upper_box']=[0,0,96,66]
            else:motion['fixed_upper_box'].update(right=[0,0,128,82],left=[0,0,128,82])
        mapping.update(revision=REVISION,runtime_integrated=False,status='review_candidate')
        write(mapping_path,mapping);boards(side,poses,assets)
    write(OUT/'asset-manifest.json',{'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'method':'Every pose uses the same complete body. Four connected lower-leg pixel layers bend from pinned two-row roots; no donor body or clothing pasted across a horizontal line.',
      'source_revision':'knight-complete-v1-20261021','idle_aliases':ALIASES,'side_walk_phases':[0,2],
      'root_y':ROOT_Y,'collar_end_y':COLLAR_END,'registration':registrations,'assets':assets,'art_review_status':'pending_user_visual_acceptance'})
    print(json.dumps({'revision':REVISION,'updated_frames':20,'assets':len(assets)},ensure_ascii=False))

if __name__=='__main__':create()
