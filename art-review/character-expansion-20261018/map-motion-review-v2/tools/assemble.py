"""Assemble generated limb patches over shared fixed artwork. No body drawing."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,subprocess,shutil,hashlib

V=Path(__file__).resolve().parents[1]
G='/opt/homebrew/bin/magick'
C=json.loads((V/'layer-contract.json').read_text())

def run(*a):subprocess.run([G,*map(str,a)],check=True)

def mask_for(size,group):
    m=Image.new('L',size);d=ImageDraw.Draw(m)
    for a in group.get('moving_rects',[]):d.rectangle((a[0],a[1],a[2]-1,a[3]-1),fill=255)
    for a in group.get('moving_polys',[]):d.polygon([tuple(p)for p in a],fill=255)
    for a in group.get('protect_polys',[]):d.polygon([tuple(p)for p in a],fill=0)
    for a in group.get('protect_rects',[])+[group['head_core'],group['torso_core']]:d.rectangle((a[0],a[1],a[2]-1,a[3]-1),fill=0)
    return m

def translation(base,candidate,roi,vertical=False):
    a=base.load();b=candidate.load();w,h=base.size
    sample=[(x,y)for y in range(roi[1],roi[3])for x in range(roi[0],roi[2])if 0<=x<w and 0<=y<h]
    ranked=[]
    for dy in range(-6,7)if vertical else [0]:
        for dx in range(-7,8):
            score=0
            for x,y in sample:
                va=a[x,y];vb=b[x-dx,y-dy]if 0<=x-dx<w and 0<=y-dy<h else(0,0,0,0)
                score+=3*abs(va[3]-vb[3])
                if va[3]and vb[3]:score+=sum(abs(va[k]-vb[k])for k in range(3))
            ranked.append((score+2*(abs(dx)+abs(dy)),dx,dy))
    return min(ranked)[1:]

def fixed_diff(a,b,mask):
    return sum(pa!=pb for pa,pb,m in zip(a.getdata(),b.getdata(),mask.getdata())if m==0)

all_reports={}
for key,groups in C['groups'].items():
    p=V/'candidates'/key;o=V/'deliverables'/key;l=V/'layers'/key
    o.mkdir(parents=True,exist_ok=True);l.mkdir(parents=True,exist_ok=True)
    reports=[]
    for group in groups:
        f=group['base'];basepath=p/f'frame-{f:02}.png';base=Image.open(basepath).convert('RGBA')
        mask=mask_for(base.size,group);maskpath=l/f'movable-{f:02}.png';mask.save(maskpath)
        shutil.copy2(basepath,o/f'frame-{f:02}.png')
        inverse=l/f'fixed-mask-{f:02}.png';fixedalpha=l/f'fixed-alpha-{f:02}.png';fixed=l/f'fixed-layer-{f:02}.png'
        run(maskpath,'-negate',inverse)
        run(basepath,'-alpha','extract',inverse,'-compose','Multiply','-composite',fixedalpha)
        run(basepath,fixedalpha,'-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',fixed)
        # Fixed content is shared, including its transparent silhouette. Mask only
        # authorizes already-generated arms/legs/items and their occlusion sweep.
        for other in group['others']:
            candidate=Image.open(p/f'frame-{other:02}.png').convert('RGBA')
            dx,dy=translation(base,candidate,group['align'],f==8 and key=='hunapu')
            shifted=l/f'aligned-{other:02}.png'
            run('-size',f'{base.width}x{base.height}','xc:none',p/f'frame-{other:02}.png','-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',shifted)
            dst=o/f'frame-{other:02}.png'
            movingalpha=l/f'moving-alpha-{other:02}.png';moving=l/f'moving-layer-{other:02}.png'
            run(shifted,'-alpha','extract',maskpath,'-compose','Multiply','-composite',movingalpha)
            run(shifted,movingalpha,'-alpha','off','-compose','CopyOpacity','-composite',moving)
            run(fixed,moving,'-compose','Over','-composite','-background','black','-alpha','background',dst)
            final=Image.open(dst).convert('RGBA')
            outside=fixed_diff(base,final,mask)
            head_equal=base.crop(tuple(group['head_core'])).tobytes()==final.crop(tuple(group['head_core'])).tobytes()
            torso_equal=base.crop(tuple(group['torso_core'])).tobytes()==final.crop(tuple(group['torso_core'])).tobytes()
            changed=sum(a!=b for a,b in zip(base.getdata(),final.getdata()))
            assert outside==0 and head_equal and torso_equal,(key,f,other,outside,head_equal,torso_equal)
            reports.append({'base':f,'frame':other,'aligned_translation':[dx,dy],'mask':str(maskpath.relative_to(V)),'fixed_pixels_changed':outside,'head_core_rgba_equal':head_equal,'torso_core_rgba_equal':torso_equal,'moving_pixels_changed':changed,'head_core':group['head_core'],'torso_core':group['torso_core']})
    if key=='hunapu':
        # Original source proves cross-phase full-canvas mirror 6<-3, 7<-2.
        for dest,src in [(6,3),(7,2)]:run(o/f'frame-{src:02}.png','-flop',o/f'frame-{dest:02}.png')
    count=6 if key.endswith('-story')else 11
    colors=set();inventory=[]
    for f in range(count):
        path=o/f'frame-{f:02}.png';im=Image.open(path).convert('RGBA');colors|={tuple(x[:3])for x in im.getdata()if x[3]}
        assert set(im.getchannel('A').getdata())=={0,255},'Sprite must retain real transparent pixels and a hard opaque silhouette'
        inventory.append({'frame':f,'path':str(path.relative_to(V)),'size':list(im.size),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    assert len(colors)<=4,(key,colors)
    for c,name in [('#e3dfcf','light'),('#26343b','dark')]:
        run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[o/f'frame-{f:02}.png'for f in range(count)],'-tile','3x2'if count==6 else'4x3','-geometry','128x96+8+12','-background',c,o/f'contact-{name}.png')
        run(o/f'contact-{name}.png','-filter','point','-resize','300%',o/f'contact-{name}-3x.png')
    all_reports[key]={'fixed_region_checks':reports,'opaque_colors':sorted(list(colors)),'opaque_color_count':len(colors),'binary_alpha':True,'files':inventory,'artwork_source':'Built-in ImageGen; technical masked compositing only; pending final visual review.'}
(V/'fixed-layer-qa.json').write_text(json.dumps(all_reports,ensure_ascii=False,indent=2)+'\n')
print({k:{'colors':v['opaque_color_count'],'checks':len(v['fixed_region_checks'])}for k,v in all_reports.items()})
