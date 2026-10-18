"""Technical compositing of ImageGen arms, solid-string bow and neutral-step legs."""
from pathlib import Path
from PIL import Image,ImageFilter
import json,shutil
from prepare import V,R,P,C,G,run,rgba,bbox,quantize
L=V/'layers'
def move(src,size,dx,dy,dst):run('-size',f'{size[0]}x{size[1]}','xc:none',src,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',dst)
def copyrect(base,source,rect,dst):
    x,y,r,b=rect;run(base,'(',source,'-crop',f'{r-x}x{b-y}+{x}+{y}','+repage',')','-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',dst)
def groups(pts):
    pts=set(pts);result=[]
    while pts:
        q=[pts.pop()];part=[]
        while q:
            x,y=q.pop();part.append((x,y))
            for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if n in pts:pts.remove(n);q.append(n)
        result.append(part)
    return result
def extract_arm(name,roi,sleeve,dst):
    src=C/f'{name}-aligned.png';a=rgba(src);skin={(x,y)for y in range(roi[1],roi[3])for x in range(roi[0],roi[2])if a.getpixel((x,y))==(221,167,125,255)}
    # Tiny warm antialiasing specks on the generated weapon are not body parts.
    valid=[g for g in groups(skin)if len(g)>=3];keep={p for g in valid for p in g}
    seed=Image.new('L',a.size)
    for p in keep:seed.putpixel(p,255)
    if sleeve:
        x,y,r,b=sleeve
        for yy in range(y,b):
            for xx in range(x,r):
                if a.getpixel((xx,yy))==(57,118,181,255):seed.putpixel((xx,yy),255)
    expanded=seed.filter(ImageFilter.MaxFilter(3));mask=Image.new('L',a.size)
    for y in range(a.height):
        for x in range(a.width):
            if seed.getpixel((x,y))or(expanded.getpixel((x,y))and a.getpixel((x,y))==(23,38,56,255)):mask.putpixel((x,y),255)
    mp=dst.with_name(dst.stem+'-mask.png');mask.save(mp)
    run(src,mp,'-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
    return {'skin_pixels':len(keep),'skin_components':sorted([len(g)for g in valid],reverse=True),'roi':roi,'sleeve':sleeve}

# Reuse the complete ImageGen weapon after the string-only edit. Dimensions and
# compositing origins match V2, and no body is repainted by the technical steps.
raw=V/'source/solid-strings.png';b=bbox(raw)
run(raw,'-crop',f'{b[2]-b[0]}x{b[3]-b[1]}+{b[0]}+{b[1]}','+repage',L/'bow-full-raw.png')
pal=Image.new('RGB',(2,1));pal.putdata([(23,38,56),(228,225,200)]);pal.save(L/'weapon-palette.png')
quantize(L/'bow-full-raw.png',L/'bow-full.png',L/'weapon-palette.png')
# Coverage-preserving reduction: point sampling repeatedly missed the narrow
# ivory string center. Retain its actual source coverage instead of sampling
# alternating dark edge pixels. Geometry still comes entirely from ImageGen.
run(L/'bow-full.png','-alpha','off','-fill','black','+opaque','#E4E1C8','-fill','white','-opaque','#E4E1C8','-colorspace','gray','-filter','box','-resize','44x44','-threshold','15%',L/'ivory-small-mask.png')
run(L/'bow-full.png','-alpha','extract','-filter','box','-resize','44x44','-threshold','5%',L/'alpha-small-mask.png')
sw,sh=Image.open(L/'ivory-small-mask.png').size
run('-size',f'{sw}x{sh}','xc:#E4E1C8',L/'ivory-small-mask.png','-alpha','off','-compose','CopyOpacity','-composite',L/'ivory-small.png')
run('-size',f'{sw}x{sh}','xc:#172638',L/'ivory-small.png','-compose','Over','-composite',L/'alpha-small-mask.png','-alpha','off','-compose','CopyOpacity','-composite',L/'bow-small.png')
run(L/'bow-small.png','-bordercolor','none','-border','1',L/'bow-padded.png')
run(L/'bow-padded.png','-alpha','extract','-morphology','Dilate','Diamond:1',L/'outline-alpha.png')
w,h=Image.open(L/'bow-padded.png').size
run('-size',f'{w}x{h}','xc:#172638',L/'outline-alpha.png','-alpha','off','-compose','CopyOpacity','-composite',L/'outline.png')
run(L/'outline.png',L/'bow-padded.png','-compose','Over','-composite','-background','black','-alpha','background',L/'bow-ne.png')
run(L/'bow-ne.png','-rotate','90',L/'bow-se.png');run(L/'bow-se.png','-flop',L/'bow-sw.png')

qa={}
qa['drawing']=extract_arm('down',(40,53,60,63),None,L/'drawing-down.png')
move(L/'drawing-down.png',(96,96),-10,-7,L/'drawing-idle.png')
run(L/'drawing-down.png','-flop',L/'drawing-flipped.png');move(L/'drawing-flipped.png',(128,96),4,0,L/'drawing-right.png')
qa['idle_holding']=extract_arm('idle',(48,32,69,51),(44,44,54,51),L/'holding-idle.png')
qa['down_holding']=extract_arm('down',(67,60,82,78),(69,58,78,66),L/'holding-down.png')
qa['right_holding']=extract_arm('right',(55,61,69,78),(62,59,72,68),L/'holding-right.png')
for name,size,bow,at in [('idle',(96,96),'ne',(34,15)),('down',(128,96),'se',(46,44)),('right',(128,96),'sw',(40,46))]:
    move(L/f'bow-{bow}.png',size,*at,L/f'weapon-{name}.png')
    run(L/f'holding-{name}.png',L/f'drawing-{name}.png','-compose','Over','-composite',L/f'weapon-{name}.png','-compose','Over','-composite',L/f'assembly-{name}.png')

for n,dy in [(0,0),(2,4)]:
    move(L/'assembly-idle.png',(96,96),0,dy,L/f'idle-moving-{n}.png')
    run(P/'layers/idle-body.png',L/f'idle-moving-{n}.png','-compose','Over','-composite',C/f'idle-{n}.png')
neutral=V/'source/neutral-body.png';shutil.copy2(P/'candidates/right-body-a.png',L/'right-body-neutral.png')
if neutral.exists():
    b=bbox(neutral);factor=63/(b[3]-b[1]);run(neutral,'-filter','point','-resize',f'{factor*100}%',C/'neutral-small.png');quantize(C/'neutral-small.png',C/'neutral-colored.png')
    b=bbox(C/'neutral-colored.png');dx=round(75-(b[0]+b[2])/2);dy=96-b[3]
    move(C/'neutral-colored.png',(128,96),dx,dy,C/'neutral-aligned.png')
    copyrect(L/'right-body-neutral.png',C/'neutral-aligned.png',(0,80,128,96),L/'right-body-neutral.png')
    qa['neutral_registration']={'scale':factor,'translation':[dx,dy],'leg_patch_y':80}
else:qa['neutral_pending']=True
for name,phase,body in [('down',0,P/'candidates/down-body-a.png'),('down',1,P/'candidates/down-body-b.png'),('right',0,L/'right-body-neutral.png'),('right',1,P/'candidates/right-body-b.png')]:
    run(body,L/f'assembly-{name}.png','-compose','Over','-composite',C/f'{name}-{phase}.png')
for key in ['class-12-ally','class-12-enemy']:
    O=V/'deliverables'/key;O.mkdir(parents=True,exist_ok=True)
    for n in [0,1]:shutil.copy2(P/f'deliverables/{key}/walk-{n:02}.png',O/f'walk-{n:02}.png')
    for n,name,phase in [(2,'right',0),(3,'right',1),(4,'down',0),(5,'down',1)]:
        src=C/f'{name}-{phase}.png';dst=O/f'walk-{n:02}.png'
        if key.endswith('enemy'):run(src,'-fill','#AE5148','-opaque','#3976B5',dst)
        else:shutil.copy2(src,dst)
    for n,src in [(6,2),(7,3)]:run(O/f'walk-{src:02}.png','-flop',O/f'walk-{n:02}.png')
    for n,src in enumerate([0,0,2,0,0,0]):
        dst=O/f'idle-{n:02}.png'
        if key.endswith('enemy'):run(C/f'idle-{src}.png','-fill','#AE5148','-opaque','#3976B5',dst)
        else:shutil.copy2(C/f'idle-{src}.png',dst)
    for bg,theme in [('#d9d6c9','light'),('#26343b','dark')]:
        run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'walk-{n:02}.png'for n in range(8)],O/'idle-00.png',O/'idle-02.png','-tile','4x3','-geometry','128x96+8+8','-background',bg,O/f'contact-{theme}.png')
        run(O/f'contact-{theme}.png','-filter','point','-resize','400%',O/f'contact-{theme}-4x.png')
(V/'assembly-qa.json').write_text(json.dumps(qa,indent=2)+'\n');print(qa)
