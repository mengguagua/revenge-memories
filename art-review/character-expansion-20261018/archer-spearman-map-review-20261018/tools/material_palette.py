"""Assign generated warm metal-edge pixels to ivory within known weapon-only regions."""
from pathlib import Path
from PIL import Image
import subprocess,json
V=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick';report=[]
def run(*a):subprocess.run([G,*map(str,a)],check=True)
for key in ['class-6-ally','class-6-enemy','class-12-ally','class-12-enemy']:
    O=V/'deliverables'/key;spear='class-6-'in key
    for context,count in [('walk',6),('idle',6)]:
        for f in range(count):
            p=O/f'{context}-{f:02}.png';before=Image.open(p).convert('RGBA')
            if spear:
                boxes=([(56,7,82,31)] if context=='idle' else [(75,27,88,49)] if f<2 else [(79,76,102,96)] if f<4 else [(40,79,56,96)])
            else:
                boxes=([(46,10,63,30),(68,12,82,29),(69,34,84,60)] if context=='idle' else [(34,42,44,58)] if f<2 else [(42,48,55,68),(44,74,54,79)] if f<4 else [(85,47,96,70),(84,75,96,87)])
            for x,y,r,b in boxes:
                run(p,'-region',f'{r-x}x{b-y}+{x}+{y}','-fill','#E4E1C8','-opaque','#DDA77D','+region',p)
            after=Image.open(p).convert('RGBA');changed=sum(a!=b for a,b in zip(before.getdata(),after.getdata()))
            assert before.getchannel('A').tobytes()==after.getchannel('A').tobytes()
            report.append({'path':str(p.relative_to(V)),'weapon_only_regions':boxes,'warm_metal_pixels_to_ivory':changed,'alpha_and_shape_unchanged':True})
    for dst,src in [(6,2),(7,3)]:run(O/f'walk-{src:02}.png','-flop',O/f'walk-{dst:02}.png')
    for bg,name in [('#d9d6c9','light'),('#26343b','dark')]:
        run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'walk-{i:02}.png'for i in range(8)],*[O/f'idle-{i:02}.png'for i in range(3)],'-tile','4x3','-geometry','128x96+8+8','-background',bg,O/f'contact-{name}.png')
        run(O/f'contact-{name}.png','-filter','point','-resize','300%',O/f'contact-{name}-3x.png')
(V/'material-palette-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print('Weapon material palette corrected without changing any sprite contour; pixels:',sum(r['warm_metal_pixels_to_ivory']for r in report))
