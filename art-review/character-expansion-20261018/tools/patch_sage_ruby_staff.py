#!/usr/bin/env python3
"""Replace only the scholar's held battle staff with the ImageGen ruby staff."""
import argparse,copy,colorsys,json,math
from PIL import Image,ImageDraw,ImageFilter
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_sniper_complete as io
REV='sage-battle-ruby-staff-v2-20261023';OUT=ROOT/REV;SRC=OUT/'source';io.OUT=OUT
P=['172638','9b5148','c3a56c','e8e3cb','b94f57','7e3c45'];C=[tuple(bytes.fromhex(h)) for h in P]

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def box(points):return [min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1]
def staff_master():
    raw=Image.open(SRC/'staff-master.png').convert('RGBA');px=raw.load();part=io.helper.parts((x,y) for y in range(raw.height) for x in range(raw.width) if px[x,y][3]>=128)[0];b=box(part);q=Image.new('RGBA',(b[2]-b[0],b[3]-b[1]))
    for x,y in part:
        r,g,bb=px[x,y][:3];h,s,v=colorsys.rgb_to_hsv(r/255,g/255,bb/255)
        if v<.24:color=C[0]
        elif (h>.93 or h<.028) and s>.32:color=C[4] if v>.54 else C[5]
        elif .028<=h<.075 and s>.35:color=C[1]
        elif .075<=h<.20 and s>.24:color=C[2] if v>.48 else C[1]
        else:color=min(C,key=lambda c:sum((a-z)**2 for a,z in zip(c,(r,g,bb))))
        q.putpixel((x-b[0],y-b[1]),(*color,255))
    io.save(q,'source/staff-clean.png','isolated original ImageGen alpha, six matte weapon materials')
    return q,{'source_bounds':b,'source_sha256':file_hash(SRC/'staff-master.png'),'palette':P}

def make_layer(asset):
    height=166;w=round(asset.width*height/asset.height);small=asset.resize((w,height),Image.Resampling.NEAREST);angle=-8.5
    small=small.rotate(angle,Image.Resampling.NEAREST,expand=True);b=small.getbbox();feet=[x for y in range(b[3]-3,b[3]) for x in range(small.width) if small.getpixel((x,y))[3]];fx=round((min(feet)+max(feet))/2);at=[217-fx,256-b[3]]
    q=Image.new('RGBA',(320,256));q.alpha_composite(small,tuple(at));assert sum(p[3]>0 for p in small.getdata())==sum(p[3]>0 for p in q.getdata())
    return q,{'master_height':height,'resampled_size':[w,height],'angle_degrees':angle,'rotated_size':list(small.size),'placement':at,'new_bounds':list(q.getbbox()),'bottom_anchor':[217,256],'clipped_pixels':0}

def remove_mask():
    mask=Image.new('L',(320,256));d=ImageDraw.Draw(mask)
    d.rectangle([217,90,254,135],fill=255)
    d.polygon([(230,124),(239,126),(224,244),(222,255),(211,255),(214,241)],fill=255)
    return mask

def patch(im,layer,mask):
    q=im.copy();q.paste((0,0,0,0),(0,0),mask);q.alpha_composite(layer)
    # Keep the original hand and its dark outline above the new shaft.
    hand=Image.new('L',im.size)
    for y in range(135,155):
        for x in range(221,240):
            if im.getpixel((x,y))==(226,183,141,255):hand.putpixel((x,y),255)
    expanded=hand.filter(ImageFilter.MaxFilter(3));kept=[]
    for y in range(134,156):
        for x in range(220,241):
            p=im.getpixel((x,y))
            if expanded.getpixel((x,y)) and p[3] and (p[:3] in [(23,38,56),(226,183,141),(232,227,203)]):q.putpixel((x,y),p);kept.append([x,y])
    return q,kept

def board(items,name):
    cw,ch=360,300;cols=4
    for light in [False,True]:
        q=Image.new('RGB',(cw*cols,48+ch*math.ceil(len(items)/cols)),(220,222,216) if light else (32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56) if light else (235,239,239)
        d.text((q.width//2,24),'博学术师 · 红宝珠法杖战斗姿势',anchor='mm',font=font(21),fill=fg)
        for n,(label,im) in enumerate(items):
            x=n%cols*cw+20;y=48+n//cols*ch;q.paste(im,(x,y),im);d.text((n%cols*cw+cw//2,y+ch-17),label,anchor='mm',font=font(16),fill=fg)
        io.save(q,name+('-light.png' if light else '-dark.png'),'all battle poses, complete staff and hand occlusion, dark/light background')

def main(publish=False):
    b=json.loads((OUT/'baseline.json').read_text());mapping=b['battle'];master,master_meta=staff_master();layer,reg=make_layer(master);mask=remove_mask();old={};poses={};hands={}
    for key,path in mapping['frame_mapping'].items():
        i=int(key);old[i]=Image.open((ROOT/'professions/class-19-ally/battle'/path).resolve()).convert('RGBA');poses[i],hands[key]=patch(old[i],layer,mask);io.save(poses[i],f'ally/battle/frame-{i:03}.png','existing body and free-arm pose, ruby orb/crescent staff replaces old crook')
    io.save(layer,'staff-layer.png','single rigid staff layer shared by all battle poses')
    io.save(mask,'old-staff-mask.png','explicit old-weapon removal region, no implicit body repaint')
    board([(str(i),im) for i,im in sorted(poses.items())],'ally-battle')
    for light in [False,True]:
        q=Image.new('RGB',(960,620),(220,222,216) if light else (32,45,53));d=ImageDraw.Draw(q);fg=(23,38,56) if light else (235,239,239)
        d.text((480,26),'博学术师 · 战斗法杖修改',anchor='mm',font=font(22),fill=fg)
        for n,(label,im) in enumerate([('修改前',old[0]),('修改后',poses[0])]):
            im=im.resize((640,512),Image.Resampling.NEAREST);q.paste(im,(n*480-120,48),im);d.text((n*480+240,590),label,anchor='mm',font=font(18),fill=fg)
        io.save(q,'before-after-'+('light' if light else 'dark')+'.png','same-scale before/after, only battle staff modified')
    if publish:
        m=copy.deepcopy(mapping);order=sorted(poses);atlas=Image.new('RGBA',(len(order)*320,256))
        for n,i in enumerate(order):atlas.alpha_composite(poses[i],(n*320,0))
        m.update(revision=REV,modified_by='codex',status='review_candidate',review_note='博学术师战斗法杖改为参考图的金色开口圆弧、红宝珠、红棕杖身与双飘带；所有姿势复用同一杖，原握手与遮挡、人物姿态、法术效果、动作时序及结算保持。',frame_mapping={str(i):'../../../'+(OUT/f'ally/battle/frame-{i:03}.png').relative_to(ROOT).as_posix() for i in order},output_atlas=io.save(atlas,'ally/battle-atlas.png','all native battle slots, new ruby staff'),qa_report='../../../'+REV+'/verification.json',batches=[{'id':'红宝珠法杖全姿势','review':'../../../'+REV+'/ally-battle-light.png','status':'review_candidate'}])
        m['palette']=list(dict.fromkeys(mapping.get('palette',[])+P))
        write(ROOT/'professions/class-19-ally/battle/frame_mapping.json',m);write(OUT/'mapping-draft.json',m)
    write(OUT/'registration.json',{'revision':REV,'weapon_master':master_meta,'placement':reg,'original_hand_pixels':hands,'old_staff_mask':'old-staff-mask.png','same_layer_all_22_poses':True,'runtime_integrated':False})
    write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS})
    print(json.dumps({'poses':len(poses),'weapon_bounds':reg['new_bounds'],'publish':publish}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');main(p.parse_args().publish)
