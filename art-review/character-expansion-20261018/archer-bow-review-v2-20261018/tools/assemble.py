"""Compose generated bodies, hands and complete bow bitmap. No anatomy is drawn."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import subprocess,json,shutil
from prepare import V,C,G,run,register,quantize,bbox
R=V.parent;OLD=R/'archer-spearman-map-review-20261018';L=V/'layers';L.mkdir(exist_ok=True)
def rectcopy(base,src,box,dst):
    x,y,r,b=box;run(base,'(',src,'-crop',f'{r-x}x{b-y}+{x}+{y}','+repage',')','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',dst)
def move(src,size,dx,dy,dst):run('-size',f'{size[0]}x{size[1]}','xc:none',src,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',dst)
def face_center(p,rect):
    a=Image.open(p).convert('RGBA');pts=[(x,y)for y in range(rect[1],rect[3])for x in range(rect[0],rect[2])if a.getpixel((x,y))==(221,167,125,255)]
    return [sum(q[i]for q in pts)/len(pts)for i in [0,1]]
def align_face(src,target,rect,dst):
    a=face_center(target,rect);b=face_center(src,rect);dx,dy=[round(a[i]-b[i])for i in [0,1]];move(src,Image.open(target).size,dx,dy,dst)
def extract_hand(src,rect,dst):
    a=Image.open(src).convert('RGBA');m=Image.new('L',a.size)
    for y in range(rect[1],rect[3]):
        for x in range(rect[0],rect[2]):
            if a.getpixel((x,y))==(221,167,125,255):m.putpixel((x,y),255)
    dil=m.filter(ImageFilter.MaxFilter(3));out=Image.new('L',a.size)
    for y in range(rect[1]-1,rect[3]+1):
        for x in range(rect[0]-1,rect[2]+1):
            if dil.getpixel((x,y)) and a.getpixel((x,y)) in [(221,167,125,255),(23,38,56,255)]:out.putpixel((x,y),255)
    mp=dst.with_name(dst.stem+'-mask.png');out.save(mp)
    run(src,mp,'-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)

# Complete isolated ImageGen weapon, common for all orientations. Quarter-turns
# preserve every pixel of both limbs, both strings, grip and arrow shaft.
wp=V/'source/complete-weapon.png';b=bbox(wp)
run(wp,'-crop',f'{b[2]-b[0]}x{b[3]-b[1]}+{b[0]}+{b[1]}','+repage','-filter','point','-resize','44x44',L/'bow-ne-raw.png')
pal=Image.new('RGB',(2,1));pal.putdata([(23,38,56),(228,225,200)]);pal.save(L/'weapon-palette.png')
run(L/'bow-ne-raw.png','-alpha','extract','-threshold','50%',L/'weapon-alpha.png')
run(L/'bow-ne-raw.png','-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',L/'weapon-palette.png',L/'weapon-rgb.png')
run(L/'weapon-rgb.png',L/'weapon-alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',L/'bow-ne.png')
# Preserve the generated outline through downsampling: add one opaque navy
# pixel around its existing alpha contour, without replacing weapon geometry.
run(L/'bow-ne.png','-bordercolor','none','-border','1',L/'bow-padded.png')
run(L/'bow-padded.png','-alpha','extract','-morphology','Dilate','Diamond:1',L/'bow-outline-alpha.png')
ow,oh=Image.open(L/'bow-padded.png').size
run('-size',f'{ow}x{oh}','xc:#172638',L/'bow-outline-alpha.png','-alpha','off','-compose','CopyOpacity','-composite',L/'bow-outline.png')
run(L/'bow-outline.png',L/'bow-padded.png','-compose','Over','-composite','-background','black','-alpha','background',L/'bow-ne.png')
run(L/'bow-ne.png','-rotate','90',L/'bow-se.png');run(L/'bow-se.png','-flop',L/'bow-sw.png')

register(V/'source/fixed-idle-body.png',L/'idle-body-fit.png',(96,96),58,47,80)
align_face(L/'idle-body-fit.png',C/'idle-full.png',(25,28,47,44),L/'idle-body.png')
rectcopy(L/'idle-body.png',C/'idle-full.png',(0,16,46,45),L/'idle-body.png')
rectcopy(L/'idle-body.png',C/'idle-full.png',(0,60,96,96),L/'idle-body.png')
extract_hand(C/'idle-full.png',(22,46,42,54),L/'forearm.png')
extract_hand(C/'idle-full.png',(64,28,71,37),L/'holding-hand.png')
# Forearm and rear holding hand form one moving assembly with the foreground bow.
move(L/'forearm.png',(96,96),5,0,L/'idle-hands.png')
run(L/'idle-hands.png',L/'holding-hand.png','-compose','Over','-composite',L/'idle-hands.png')
move(L/'bow-ne.png',(96,96),34,15,L/'idle-bow.png')
run(L/'idle-hands.png',L/'idle-bow.png','-compose','Over','-composite',L/'idle-assembly.png')
for n,dy in [(0,0),(2,4)]:
    move(L/'idle-assembly.png',(96,96),0,dy,L/f'idle-moving-{n}.png')
    run(L/'idle-body.png',L/f'idle-moving-{n}.png','-compose','Over','-composite',C/f'idle-final-{n}.png')

for phase,filename in [('a','fixed-walk-bodies.png'),('b','walk-second-step.png')]:
    raw=V/'source'/filename
    if not raw.exists():continue
    w,h=Image.open(raw).size
    for col,name in enumerate(['down','right']):
        cell=C/f'{name}-{phase}-raw.png';run(raw,'-crop',f'{w//2}x{h}+{col*w//2}+0','+repage',cell)
        register(cell,C/f'{name}-{phase}-fit.png',(128,96),64,68 if name=='down' else 75,96)
        roi=(57,40,81,57)if name=='down'else(67,40,90,56)
        align_face(C/f'{name}-{phase}-fit.png',C/f'{name}-full.png',roi,C/f'{name}-body-{phase}.png')
        if phase=='b':
            # Only generated leg region can differ. Original head and all fixed
            # body pixels are taken from phase A, not independently regenerated.
            body=C/f'{name}-body-b.png';temp=C/f'{name}-legs-b.png';shutil.copy2(body,temp)
            shutil.copy2(C/f'{name}-body-a.png',body);rectcopy(body,temp,(0,80,128,96),body)
        body=C/f'{name}-body-{phase}.png'
        if name=='down':
            move(L/'forearm.png',(128,96),16,8,L/'down-hands.png')
            move(L/'holding-hand.png',(128,96),6,40,L/'down-hold.png')
            run(L/'down-hands.png',L/'down-hold.png','-compose','Over','-composite',L/'down-hands.png')
            move(L/'bow-se.png',(128,96),46,44,L/'down-bow.png')
        else:
            run(L/'forearm.png','-flop',L/'forearm-mirror.png')
            move(L/'forearm-mirror.png',(128,96),19,9,L/'right-hands.png')
            move(L/'holding-hand.png',(128,96),-9,42,L/'right-hold.png')
            run(L/'right-hands.png',L/'right-hold.png','-compose','Over','-composite',L/'right-hands.png')
            move(L/'bow-sw.png',(128,96),40,46,L/'right-bow.png')
        run(body,L/f'{name}-hands.png','-compose','Over','-composite',L/f'{name}-bow.png','-compose','Over','-composite',C/f'{name}-final-{phase}.png')

for key in ['class-12-ally','class-12-enemy']:
    O=V/'deliverables'/key;O.mkdir(parents=True,exist_ok=True)
    for i in [0,1]:shutil.copy2(OLD/f'deliverables/{key}/walk-{i:02}.png',O/f'walk-{i:02}.png')
    for i,name,phase in [(2,'right','a'),(3,'right','b'),(4,'down','a'),(5,'down','b')]:
        src=C/f'{name}-final-{phase}.png'
        if not src.exists():continue
        dst=O/f'walk-{i:02}.png'
        if key.endswith('enemy'):run(src,'-fill','#AE5148','-opaque','#3976B5',dst)
        else:shutil.copy2(src,dst)
    for i,src in [(6,2),(7,3)]:
        if(O/f'walk-{src:02}.png').exists():run(O/f'walk-{src:02}.png','-flop',O/f'walk-{i:02}.png')
    for i,src in enumerate([0,0,2,0,0,0]):
        dst=O/f'idle-{i:02}.png'
        if key.endswith('enemy'):run(C/f'idle-final-{src}.png','-fill','#AE5148','-opaque','#3976B5',dst)
        else:shutil.copy2(C/f'idle-final-{src}.png',dst)
    items=[p for p in [*sorted(O.glob('walk-*.png')),O/'idle-00.png',O/'idle-02.png']if p.exists()]
    for bg,name in [('#d9d6c9','light'),('#26343b','dark')]:
        run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*items,'-tile','4x3','-geometry','128x96+8+8','-background',bg,O/f'contact-{name}.png')
        run(O/f'contact-{name}.png','-filter','point','-resize','400%',O/f'contact-{name}-4x.png')
print('Layered bows and archer frames assembled')
