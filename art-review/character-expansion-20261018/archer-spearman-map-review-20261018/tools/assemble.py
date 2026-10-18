"""Lock generated fixed layers and compose complete moving regions, never draw anatomy."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,subprocess,shutil
V=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def mask(size,rects=(),polys=(),protect=()):
    m=Image.new('L',size);d=ImageDraw.Draw(m)
    for x,y,r,b in rects:d.rectangle((x,y,r-1,b-1),fill=255)
    for poly in polys:d.polygon(poly,fill=255)
    for x,y,r,b in protect:d.rectangle((x,y,r-1,b-1),fill=0)
    return m
def xalign(a,b,roi):
    values=[]
    for dx in range(-6,7):
        score=abs(dx)
        for y in range(roi[1],roi[3]):
            for x in range(roi[0],roi[2]):
                p=a.getpixel((x,y));q=b.getpixel((x-dx,y)) if 0<=x-dx<b.width else (0,0,0,0)
                score+=sum(abs(p[i]-q[i])for i in range(4))
        values.append((score,dx))
    return min(values)[1]
contracts={
 'archer':[
  {'base':0,'other':1,'align':[48,33,77,55],'rects':[[44,78,79,96]],'head':[45,32,80,55]},
  {'base':2,'other':3,'align':[62,33,87,53],'rects':[[49,79,94,96]],'protect':[[49,79,63,84]],'head':[58,31,91,54]},
  {'base':4,'other':5,'align':[56,34,80,54],'rects':[[48,78,78,96]],'head':[53,33,82,54]},
  {'base':6,'others':[7,8],'transforms':[[0,0],[0,4]],'rects':[[47,10,83,58]],
   'polys':[[(43,45),(49,38),(60,36),(60,54),(47,59),(43,53)]],
   'protect':[[20,25,47,47],[20,47,40,59],[35,56,47,80]],'head':[22,27,46,47],'torso':[37,55,44,62]},
 ],
 'spear':[
  {'base':0,'other':1,'align':[55,36,74,50],'rects':[[42,49,56,76],[72,28,89,96],[44,78,80,96]],
   'protect':[[53,34,77,53],[56,54,72,77]],'head':[53,34,77,53],'torso':[57,56,71,74]},
  {'base':2,'other':3,'align':[56,35,73,53],'rects':[[34,54,56,78],[48,53,49,54],[70,54,84,79],[30,79,100,96]],
   'polys':[[(33,27),(47,27),(65,54),(53,59)],[(71,62),(97,80),(100,96),(82,96),(67,74)]],
   'protect':[[51,31,76,55],[55,55,70,78]],'head':[51,31,76,55],'torso':[56,57,68,74]},
  {'base':4,'other':5,'align':[57,35,73,55],'rects':[[40,28,57,96],[71,52,88,77],[50,78,82,96]],
   'protect':[[54,34,76,57],[57,57,71,78]],'head':[54,34,76,57],'torso':[58,59,70,75]},
  {'base':6,'others':[7,8],'align':[31,30,45,40],'idle_part_offsets':[[-4,0],[-4,-2]],
   'rects':[[17,41,39,61]],
   'polys':[[(41,41),(65,10),(81,10),(81,24),(52,50)],[(12,69),(33,48),(43,48),(21,70)]],
   'protect':[[25,17,48,41],[48,40,61,53],[38,54,51,80],[0,71,96,96],[34,61,64,71]],
   'head':[25,17,48,41],'torso':[39,52,48,60]},
 ]}
report={}
for key in ['class-12-ally','class-12-enemy','class-6-ally','class-6-enemy']:
    kind='archer' if '12' in key else 'spear';C=V/'candidates'/key;O=V/'deliverables'/key;L=V/'layers'/key
    O.mkdir(parents=True,exist_ok=True);L.mkdir(parents=True,exist_ok=True);checks=[]
    for group in contracts[kind]:
        n=group['base'];basepath=C/f'frame-{n:02}.png';base=Image.open(basepath).convert('RGBA')
        shutil.copy2(basepath,O/f'pose-{n:02}.png')
        protected=group.get('protect',[])+[group[label] for label in ['head','torso'] if label in group]
        moving=mask(base.size,group.get('rects',[]),group.get('polys',[]),protected)
        mp=L/f'mask-{n:02}.png';moving.save(mp)
        run(mp,'-negate',L/'inverse.png')
        run(basepath,'-alpha','extract',L/'inverse.png','-compose','Multiply','-composite',L/'fixed-alpha.png')
        run(basepath,L/'fixed-alpha.png','-alpha','off','-compose','CopyOpacity','-composite',L/f'fixed-{n:02}.png')
        others=group.get('others',[group.get('other')])
        for j,f in enumerate(others):
            candidate=C/f'frame-{f:02}.png';dx=0;dy=0
            if 'transforms'in group:
                candidate=basepath;dx,dy=group['transforms'][j]
            elif kind=='archer' and f==3:
                candidate=C/'side-b.png';dx=-2;dy=2
            else:
                dx=xalign(base,Image.open(candidate).convert('RGBA'),group['align'])
                if 'idle_part_offsets'in group:
                    extra=group['idle_part_offsets'][j];dx+=extra[0];dy+=extra[1]
            aligned=L/f'aligned-{f:02}.png'
            run('-size',f'{base.width}x{base.height}','xc:none',candidate,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',aligned)
            run(aligned,'-alpha','extract',mp,'-compose','Multiply','-composite',L/'moving-alpha.png')
            run(aligned,L/'moving-alpha.png','-alpha','off','-compose','CopyOpacity','-composite',L/f'moving-{f:02}.png')
            dst=O/f'pose-{f:02}.png'
            run(L/f'fixed-{n:02}.png',L/f'moving-{f:02}.png','-compose','Over','-composite','-background','black','-alpha','background',dst)
            final=Image.open(dst).convert('RGBA');outside=sum(a!=b for a,b,m in zip(base.getdata(),final.getdata(),moving.getdata())if not m)
            assert outside==0
            for label in ['head','torso']:
                if label in group:assert base.crop(tuple(group[label])).tobytes()==final.crop(tuple(group[label])).tobytes(),(key,n,f,label)
            changed=sum(a!=b for a,b in zip(base.getdata(),final.getdata()))
            assert changed>0 or kind=='archer'and f==7,(key,f)
            checks.append({'base':n,'pose':f,'translation':[dx,dy],'method':'native local translation'if'transforms'in group else'generated whole-limb patch','fixed_pixels_changed':outside,'head_rgba_equal':True,'changed_pixels':changed,'mask':str(mp.relative_to(V))})
    # Native left phases for BOTH classes are same-phase reflection (not hero cross-phase).
    for dst,src in [(6,2),(7,3)]:run(O/f'pose-{src:02}.png','-flop',O/f'walk-{dst:02}.png')
    for i in range(6):shutil.copy2(O/f'pose-{i:02}.png',O/f'walk-{i:02}.png')
    aliases=[6,6,8,6,6,6] if kind=='archer' else [6,7,8,7,6,7]
    for i,src in enumerate(aliases):shutil.copy2(O/f'pose-{src:02}.png',O/f'idle-{i:02}.png')
    colors=set()
    for p in [*O.glob('walk-*.png'),*O.glob('idle-*.png')]:
        image=Image.open(p).convert('RGBA');assert set(image.getchannel('A').getdata())=={0,255};colors|={p[:3]for p in image.getdata()if p[3]}
    assert len(colors)==4
    for bg,name in [('#d9d6c9','light'),('#26343b','dark')]:
        run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'walk-{i:02}.png'for i in range(8)],*[O/f'idle-{i:02}.png'for i in range(3)],'-tile','4x3','-geometry','128x96+8+8','-background',bg,O/f'contact-{name}.png')
        run(O/f'contact-{name}.png','-filter','point','-resize','300%',O/f'contact-{name}-3x.png')
    report[key]={'checks':checks,'palette':sorted(colors),'idle_source_aliases':aliases,'mirror_pairs':[[6,2],[7,3]],'status':'candidate visual inspection pending'}
(V/'layer-contract.json').write_text(json.dumps(contracts,indent=2)+'\n')
(V/'motion-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:[c['changed_pixels']for c in v['checks']]for k,v in report.items()})
