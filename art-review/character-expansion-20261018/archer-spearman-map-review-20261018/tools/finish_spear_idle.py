"""Compose one fixed generated body with separately translated spear and holding arm."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import subprocess,json
V=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def layer(src,mask,dst):
    alpha=dst.with_name(dst.stem+'-alpha.png')
    run(src,'-alpha','extract',mask,'-compose','Multiply','-composite',alpha)
    run(src,alpha,'-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
def rectcopy(base,source,box,dst):
    x,y,r,b=box
    run(base,'(',source,'-crop',f'{r-x}x{b-y}+{x}+{y}','+repage',')','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',dst)
run(V/'source/spear-fixed-body-generated.png','-filter','point','-resize','192x96',V/'candidates/spear-fixed-bodies.png')
reports={}
def face_center(image,rect):
    pts={(x,y) for y in range(rect[1],rect[3]) for x in range(rect[0],rect[2]) if image.getpixel((x,y))==(221,167,125,255)};groups=[]
    while pts:
        todo=[pts.pop()];part=[]
        while todo:
            x,y=todo.pop();part.append((x,y))
            for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if q in pts:pts.remove(q);todo.append(q)
        groups.append(part)
    part=max(groups,key=len)
    return [sum(p[k] for p in part)/len(part) for k in [0,1]]
for index,key in enumerate(['class-6-ally','class-6-enemy']):
    C=V/'candidates'/key;O=V/'deliverables'/key;L=V/'layers'/key/'idle-layered';L.mkdir(parents=True,exist_ok=True)
    base=C/'frame-06.png';clean=L/'clean-raw.png';fixed=L/'fixed-body.png'
    run(V/'candidates/spear-fixed-bodies.png','-crop',f'96x96+{index*96}+0','+repage',clean)
    run(clean,'-alpha','extract','-threshold','50%',L/'clean-alpha.png')
    run(clean,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',C/'palette.png',L/'clean-rgb.png')
    run(L/'clean-rgb.png',L/'clean-alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',fixed)
    a=face_center(Image.open(base).convert('RGBA'),(25,20,48,41));b=face_center(Image.open(fixed).convert('RGBA'),(20,20,58,43))
    dx,dy=[round(a[i]-b[i]) for i in [0,1]]
    run('-size','96x96','xc:none',fixed,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',fixed)
    # Explicitly restore unchanged identity, planted legs, free arm and skirt.
    for box in [(25,17,48,41),(48,38,62,53),(0,61,96,96),(37,54,62,64)]:rectcopy(fixed,base,box,fixed)
    # These masks extract only existing generated pixels, not painted anatomy.
    shaft=Image.new('L',(96,96));d=ImageDraw.Draw(shaft)
    d.polygon([(20,67),(62,23),(67,23),(25,69)],fill=255)
    d.polygon([(59,25),(64,18),(70,14),(76,14),(76,23),(67,31)],fill=255)
    d.rectangle((25,17,47,40),fill=0);d.rectangle((47,37,61,52),fill=0)
    shaft.save(L/'spear-mask.png');layer(base,L/'spear-mask.png',L/'spear.png')
    original=Image.open(base).convert('RGBA');skin=Image.new('L',(96,96))
    for y in range(43,59):
        for x in range(23,39):
            if original.getpixel((x,y))==(221,167,125,255):skin.putpixel((x,y),255)
    expanded=skin.filter(ImageFilter.MaxFilter(3));arm=Image.new('L',(96,96))
    for y in range(40,60):
        for x in range(21,41):
            if expanded.getpixel((x,y)) and original.getpixel((x,y)) in [(221,167,125,255),(23,38,56,255)]:arm.putpixel((x,y),255)
    d=ImageDraw.Draw(arm);d.polygon([(25,42),(31,40),(34,42),(33,47),(25,48)],fill=255)
    arm.save(L/'holding-arm-mask.png');layer(base,L/'holding-arm-mask.png',L/'holding-arm.png')
    # The shaft is behind the fixed torso, matching native occlusion. The moving
    # holding arm remains in front; no copied free hand can travel with the pole.
    for n,(dx,dy) in enumerate([(0,0),(-4,0),(-4,-4)]):
        dst=O/f'idle-{n:02}.png'
        run('-size','96x96','xc:none',L/'spear.png','-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',fixed,'-geometry','+0+0','-compose','Over','-composite',L/'holding-arm.png','-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',dst)
        # Shoulder armour is the fixed pivot; the complete elbow/forearm/hand
        # passes beneath it, keeping the raised pose attached to the torso.
        rectcopy(dst,base,(26,41,35,46),dst)
        rectcopy(dst,base,(25,17,48,41),dst)
        run(dst,'-background','black','-alpha','background',dst)
    for dst,src in [(3,1),(4,0),(5,1)]:run(O/f'idle-{src:02}.png',O/f'idle-{dst:02}.png')
    a=Image.open(O/'idle-00.png').convert('RGBA');checks=[]
    for n in [1,2]:
        b=Image.open(O/f'idle-{n:02}.png').convert('RGBA')
        for label,box in [('head',(25,17,48,41)),('free_arm',(48,38,62,53)),('feet',(0,71,96,96)),('waist',(39,57,60,65))]:
            assert a.crop(box).tobytes()==b.crop(box).tobytes(),(key,n,label)
        checks.append({'frame':n,'head_free_arm_feet_waist_equal':True,'native_translation_pixels':[-4,0 if n==1 else -4]})
    reports[key]={'layers':str(L.relative_to(V)),'checks':checks,'native_translations':[[0,0],[-4,0],[-4,-4]],'body_underpaint':'Built-in ImageGen, fixed body; original head/free arm/skirt/legs restored'}
run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[V/f'deliverables/{k}/idle-{i:02}.png'for k in ['class-6-ally','class-6-enemy']for i in range(3)],'-tile','3x2','-geometry','96x96+8+8','-background','#d9d6c9',V/'reviews/spear-layered-idle.png')
run(V/'reviews/spear-layered-idle.png','-filter','point','-resize','400%',V/'reviews/spear-layered-idle-4x.png')
(V/'spear-idle-qa.json').write_text(json.dumps(reports,indent=2)+'\n')
print('Two fixed bodies plus complete independent spear/holding-arm layers assembled')
