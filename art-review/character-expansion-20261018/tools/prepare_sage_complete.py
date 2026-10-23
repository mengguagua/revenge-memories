#!/usr/bin/env python3
"""Freeze class19 ally references and produce image-edit pose guides."""
import json, hashlib, math
from PIL import Image, ImageDraw
from build_gallery import ROOT
from export_gallery import font
REV='sage-complete-v1-20261023'
OUT=ROOT/REV
SRC=OUT/'source'
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def target(kind,ids,cols,scale,name):
    frames=[Image.open(SRC/f'native-{kind}-{i:03}.png').convert('RGBA') for i in ids]
    w,h=frames[0].size
    q=Image.new('RGBA',(w*scale*cols,h*scale*math.ceil(len(ids)/cols)))
    for n,c in enumerate(frames):
        q.alpha_composite(c.resize((w*scale,h*scale),Image.Resampling.NEAREST),(n%cols*w*scale,n//cols*h*scale))
    q.save(SRC/name,optimize=True)
def main():
    SRC.mkdir(parents=True,exist_ok=True)
    full=json.loads((ROOT/'source-input/original-motion/full-original-motion.json').read_text())
    full['variants'].update(json.loads((ROOT/'source-input/corrected-ally-motion/overlay.json').read_text())['variants'])
    variants={k:v for k,v in full['variants'].items() if str(v.get('source_class_id'))=='19' and k.startswith('class_19_ally_')}
    if not (OUT/'baseline.json').exists():
        write(OUT/'baseline.json',{'gallery':json.loads((ROOT/'demos/gallery-data.json').read_text()),'body':full['original_bodies']['19'],'variants':variants})
    assets=[]
    for kind,path,size,ids in [
        ('idle',ROOT/'source-input/legacy-assets/assets/original/graphics/map_units/class_19_ally.png',(24,24),list(range(6))),
        ('walk',ROOT/'source-input/corrected-tactical-walk/class-19-ally.png',(32,24),list(range(8))),
        ('battle',ROOT/'source-input/original-motion/class-19.png',(80,64),[0,*range(16,37)])]:
        im=Image.open(path).convert('RGBA');cols=im.width//size[0];images=[]
        for i in ids:
            c=im.crop((i%cols*size[0],i//cols*size[1],i%cols*size[0]+size[0],i//cols*size[1]+size[1]))
            c.save(SRC/f'native-{kind}-{i:03}.png',optimize=True);images.append((i,c))
        cw,ch=(360,300) if kind=='battle' else (300,260)
        q=Image.new('RGB',(cw*4,44+ch*math.ceil(len(images)/4)),(32,45,53));dr=ImageDraw.Draw(q)
        for n,(i,c) in enumerate(images):
            scale=4 if kind=='battle' else 8
            c=c.resize((c.width*scale,c.height*scale),Image.Resampling.NEAREST)
            x=n%4*cw+(cw-c.width)//2;y=44+n//4*ch;q.paste(c,(x,y),c)
            dr.text((n%4*cw+cw//2,y+ch-18),str(i),anchor='mm',font=font(16),fill=(230,230,220))
        q.save(SRC/f'native-{kind}-guide.png',optimize=True)
        assets.append({'kind':kind,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    target('idle',[0,1,2],3,12,'target-idle.png')
    target('walk',[0,1,2,3,4,5],3,12,'target-walk.png')
    target('battle',[0,21,22,23,24,25],3,6,'target-battle-a.png')
    target('battle',[26,27,28,29,30,31],3,6,'target-battle-b.png')
    target('battle',[32,33,34,35,36],3,6,'target-battle-c.png')
    mp=json.loads((ROOT/'professions/class-15-ally/maps/frame_mapping.json').read_text())
    bm=json.loads((ROOT/'professions/class-15-ally/battle/frame_mapping.json').read_text())
    p=ROOT/'professions/class-15-ally';q=Image.new('RGB',(960,420),(32,45,53))
    for n,s in enumerate(mp['scenarios']):
        im=Image.open((p/'maps'/s['frame_mapping'][0]['output_path']).resolve()).convert('RGBA')
        im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);q.paste(im,(n*300,60),im)
    im=Image.open((p/'battle'/bm['frame_mapping']['0']).resolve()).convert('RGBA');q.paste(im,(625,45),im)
    q.save(SRC/'approved-mage-style.png',optimize=True)
    write(OUT/'native-reference-audit.json',{'assets':assets,'class_id':19,'side':'ally','variant_count':len(variants),'programs':sorted({v['source_program_address'] for v in variants.values()})})
    print(json.dumps({'native_variants':len(variants),'body_poses':22}),flush=True)
if __name__=='__main__':main()
