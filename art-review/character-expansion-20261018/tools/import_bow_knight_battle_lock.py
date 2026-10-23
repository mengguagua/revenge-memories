#!/usr/bin/env python3
"""Layer the shooting arms over one immutable class20 mounted core."""
import argparse, copy, json, math
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
from build_gallery import ROOT, file_hash
from export_gallery import font
import import_bow_knight_complete as old

REV='bow-knight-battle-lock-string-v2-20261023'
OUT=ROOT/REV
SRC=OUT/'source'
PREV=ROOT/'bow-knight-complete-v1-20261023'
C,EC=old.C,old.EC
REG=[]
ASSETS=[]
STRINGS={
    1:[[173,93],[264,162]],
    13:[[173,93],[264,162]],
    14:[[179,87],[211,117],[181,152]],
    15:[[181,42],[210,114],[181,178]],
    16:[[184,42],[184,178]],
    17:[[181,43],[237,114],[181,176]],
    18:[[182,43],[182,177]],
}
ARROW_ROW=114

def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def save(im,name,purpose):
    old.io.OUT=OUT
    path=old.io.save(im,name,purpose)
    ASSETS.append(old.io.ASSETS[-1])
    return path

def upper_layers():
    old.io.helper.SRC=SRC
    result={}
    for filename,ids in [('upper-prepare-master.png',[1,13,14,15]),('upper-release-master.png',[16,17,18])]:
        for slot,(im,meta)in zip(ids,old.io.helper.figures(filename,len(ids))):
            q=old.quant(im)
            comps=old.io.helper.parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))==(*C[3],255))
            face=old.io.box(comps[0]);head=old.io.center(face)
            skin=[old.io.box(c)for c in comps if len(c)>=500]
            for y in range(q.height):
                for x in range(q.width):
                    p=q.getpixel((x,y))
                    if p==(*C[3],255)and not any(b[0]<=x<b[2]and b[1]<=y<b[3]for b in skin):q.putpixel((x,y),(*C[2],255))
                    elif p[3]and p[:3]in[C[1],C[5]]and face[0]-60<=x<=face[2]+65 and face[1]-120<=y<face[3]:q.putpixel((x,y),(*C[0],255))
            scale=14/(face[2]-face[0]);dims=[round(q.width*scale),round(q.height*scale)]
            resized=q.resize(dims,Image.Resampling.NEAREST)
            at=[round(212-head[0]*dims[0]/q.width),round(104-head[1]*dims[1]/q.height)]
            out=Image.new('RGBA',(320,256));out.alpha_composite(resized,tuple(at))
            assert sum(p[3]>0 for p in resized.getdata())==sum(p[3]>0 for p in out.getdata())
            # Remove only detached rasterization dust, never an anatomical part.
            cs=old.io.helper.parts((x,y)for y in range(256)for x in range(320)if out.getpixel((x,y))[3])
            for component in cs[1:]:
                assert len(component)<=8,(slot,len(component))
                for xy in component:out.putpixel(xy,(0,0,0,0))
            result[slot]=out
            save(out,f'source/upper-{slot:03}.png','ImageGen rider/arms/whole bow; face registered, six matte materials')
            REG.append({**meta,'slot':slot,'face_box':face,'head':head,'skin_boxes':skin,'scale':scale,'translation':at,'clipped_pixels':0})
    return result

def core():
    im=Image.open(PREV/'ally/battle/frame-016.png').convert('RGBA')
    mask=Image.new('L',im.size);d=ImageDraw.Draw(mask)
    d.rectangle((0,139,319,255),fill=255)
    d.polygon([(148,141),(163,132),(175,130),(177,126),(181,124),(186,127),(195,141)],fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
    save(im,'source/shared-mounted-core.png','one unchanged horse, saddle, rider hips and legs shared by all shooting frames')
    mask.save(SRC/'shared-mounted-core-mask.png',optimize=True)
    return im

def rig(layers):
    # All generated pieces contain the full bow. Explicit strings stay readable
    # after logical downsampling, and are occluded naturally by the rider.
    for i,im in layers.items():
        if i==17:
            # Replace the generated white placeholder shaft with the same matte
            # arrow used in flight. Its center is exactly four-times logical y28.
            im.paste((0,0,0,0),(129,101,207,111))
            # The old shaft crossed the upper riser: restore that connected
            # generated bow section before placing the newly registered arrow.
            im.alpha_composite(layers[16].crop((151,98,166,113)),(149,98))
        vertices=STRINGS[i]
        cord=Image.new('RGBA',im.size);d=ImageDraw.Draw(cord)
        d.line(vertices,fill=(*C[0],255),width=3)
        d.line(vertices,fill=(*C[2],255),width=2)
        # Remove the old thin generated dark string where it occupies free
        # space. Colored limb/armor/skin silhouettes retain their outline.
        from PIL import ImageFilter
        colored=Image.new('L',im.size)
        colored.putdata([255 if p[3]and p[:3]!=C[0]else 0 for p in im.getdata()])
        protected=colored.filter(ImageFilter.MaxFilter(7))
        solid=im.getchannel('A').filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(9))
        corridor=Image.new('L',im.size)
        ImageDraw.Draw(corridor).line(vertices,fill=255,width=11)
        for y in range(im.height):
            for x in range(im.width):
                rider=solid.getpixel((x,y))>0
                if not rider and corridor.getpixel((x,y))and im.getpixel((x,y))==(*C[0],255)and not protected.getpixel((x,y)):im.putpixel((x,y),(0,0,0,0))
        # The two-pixel string is in front of the mount, behind the rider.
        merged=cord.copy();merged.alpha_composite(im)
        if i==17:
            arrow=Image.open(PREV/'flying-arrow.png').convert('RGBA').crop((36,10,62,13)).resize((104,12),Image.Resampling.NEAREST)
            merged.alpha_composite(arrow,(136,108))
        layers[i]=merged
        save(merged,f'source/rigged-upper-{i:03}.png','visible continuous limb-to-tip bowstring, neutral nocked arrow registered to flight')
    return layers

def projectile(side):
    source=Image.open(PREV/'flying-arrow.png').convert('RGBA');q=Image.new('RGBA',source.size)
    # Keep the CPU-extracted source path/anchor/ticks, calibrate only art inside
    # its existing frame: source shaft y11 becomes y2, with no alpha clipping.
    q.alpha_composite(source,(-10 if side=='ally'else -2,-9))
    assert sum(p[3]>0 for p in source.getdata())==sum(p[3]>0 for p in q.getdata())
    save(q,f'{side}/flying-arrow.png','same natural arrow, internal registration aligns first flying frame exactly to nocked arrow; no alpha clipping')
    return q

def board(poses,side,light):
    cw,ch=390,330;cols=4
    q=Image.new('RGB',(cw*cols,56+ch*math.ceil(len(poses)/cols)),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(q)
    fg=(23,38,56)if light else(235,243,242)
    d.text((q.width//2,26),('盟军'if side=='ally'else'敌方')+'弓骑士 · 固定马身／弓弦／箭轨',anchor='mm',font=font(22),fill=fg)
    for n,(i,im)in enumerate(poses.items()):
        x=n%cols*cw+(cw-im.width)//2;y=56+n//cols*ch
        q.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,y+im.height+22),f'原姿势 {i}',anchor='mm',font=font(18),fill=fg)
    save(q,f'{side}-battle-'+('light'if light else'dark')+'.png','complete shooting pose inspection, measured title/label safe areas')

def build(publish):
    layers=rig(upper_layers());mount=core();allposes={}
    for side,aliases in [('ally',{i:i for i in layers}),('enemy',{1:16,5:17,6:18})]:
        projectile(side)
        poses={};dx=0 if side=='ally'else -32
        for slot,src in aliases.items():
            full=mount.copy();full.alpha_composite(layers[src]);shifted=Image.new('RGBA',(320,256));shifted.alpha_composite(full,(dx,0))
            im=old.faction(shifted,side);poses[slot]=im
            save(im,f'{side}/battle/frame-{slot:03}.png','shared fixed mount + independent ImageGen shooting layer')
        allposes[side]=poses
        for light in[False,True]:board(poses,side,light)
    write(OUT/'registration.json',{'revision':REV,'upper_layers':REG,'mounted_core_sha256':file_hash(SRC/'shared-mounted-core.png'),'enemy_native_translation':[-32,0],'enemy_aliases':{'1':16,'5':17,'6':18},'bowstrings':STRINGS,'charged_arrow_output_origin':[136,108],'charged_shaft_output_rows':[112,116],'charged_shaft_center_y':ARROW_ROW,'flight_texture_shaft_y':2,'preserved_effect_anchor':[32,8],'flight_texture_translation':{'ally':[-10,-9],'enemy':[-2,-9]},'height_equation':'charged center: origin_y - 64 + 114/4 = 92.5; flight center: effect_y - 8 + 2.5 = 92.5; all near/far variants','first_flight_overlay':'entire nocked arrow and first external projectile coincide in world space, including enemy mirror offset'})
    if publish:publish_mappings(allposes)
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':ASSETS,'palette':{'ally':old.HEX,'enemy':old.EHEX},'runtime_integrated':False})
    print(json.dumps({'poses':{s:list(p)for s,p in allposes.items()},'published':publish}),flush=True)

def publish_mappings(poses):
    baseline=json.loads((OUT/'baseline.json').read_text())
    note='攻击校正：所有姿势共用同一马匹、马鞍与下肢底图；完整上下弓臂与可见弓弦，满弓箭和飞行箭对齐同一水平线。保留外传双方各自动作时序、外置效果路径与单次结算。'
    mappings={}
    for side,images in poses.items():
        m=copy.deepcopy(baseline['battle_mappings'][side]);order=sorted(images)
        atlas=Image.new('RGBA',(320*len(order),256));paths={};records=[]
        for n,i in enumerate(order):
            p=OUT/f'{side}/battle/frame-{i:03}.png'
            paths[str(i)]='../../../'+str(p.relative_to(ROOT))
            records.append({'source_frame':i,'path':paths[str(i)],'bytes':p.stat().st_size,'sha256':file_hash(p),'size':[320,256]})
            atlas.alpha_composite(images[i],(n*320,0))
        atlas_path=save(atlas,f'{side}/battle-atlas.png','all native shooting slots, one fixed mounted core')
        m.update(revision=REV,frame_mapping=paths,records=records,output_atlas=atlas_path,review_note=note,
            art_provenance='ImageGen separated rider/weapon layers on an immutable existing mounted core; indexed matte six-material palette; explicit visible bowstrings and registered arrow texture',
            motion_review={'fixed_mount_layer':'../../../'+REV+'/source/shared-mounted-core.png','unchanged_native_schedule':True,'charged_shaft_output_rows':[112,116],'flight_shaft_texture_row':2,'registration':'../../../'+REV+'/registration.json'},
            batches=[{'id':'固定马身／弓弦／箭轨','review':'../../../'+REV+f'/{side}-battle-light.png','status':'review_candidate'}])
        key='39768fc933fe67'if side=='ally'else'native-1487ce1e7365a7'
        m['effect_overrides'][key]='../../../'+REV+f'/{side}/flying-arrow.png'
        path=ROOT/f'professions/class-20-{side}/battle/frame_mapping.json'
        write(path,m);mappings[str(path.relative_to(ROOT))]=m
    write(OUT/'mapping-drafts.json',mappings)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');a=p.parse_args();build(a.publish)
